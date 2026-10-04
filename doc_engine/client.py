"""Thin Sarvam Document AI wrapper: rate limit (10 req/min), polling with backoff, 429 handling.

Both jobs are submitted, then polled together in one loop so we stay under the rate limit.
"""
import json
import logging
import time
from collections import deque

from .config import LANGUAGE, get_api_key
from .terms import extract_schema_json

log = logging.getLogger("doc_engine")
TERMINAL = {"completed", "partially_completed", "failed", "rejected"}


class RateLimiter:
    def __init__(self, max_calls=9, per=60.0, clock=time.monotonic, sleep=time.sleep):
        self.max_calls, self.per, self.clock, self.sleep = max_calls, per, clock, sleep
        self.calls = deque()

    def wait(self):
        now = self.clock()
        while self.calls and now - self.calls[0] >= self.per:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            self.sleep(self.per - (now - self.calls[0]) + 0.1)
            return self.wait()
        self.calls.append(self.clock())


class DocClient:
    def __init__(self, sdk=None, limiter=None, sleep=time.sleep, poll_start=8.0, poll_max=20.0, timeout=600):
        if sdk is None:
            from sarvamai import SarvamAI
            sdk = SarvamAI(api_subscription_key=get_api_key())
        self.doc = sdk.doc_ai
        self.rl = limiter or RateLimiter(sleep=sleep)
        self.sleep, self.poll_start, self.poll_max, self.timeout = sleep, poll_start, poll_max, timeout

    def _call(self, fn, *a, **kw):
        """Rate-limited call; retry on 429/503 with backoff (max 4 tries)."""
        delay = 10.0
        for attempt in range(4):
            self.rl.wait()
            try:
                return fn(*a, **kw)
            except Exception as e:  # SDK raises ApiError with status_code
                code = getattr(e, "status_code", None)
                if code in (429, 503) and attempt < 3:
                    log.warning("HTTP %s, retrying in %.0fs", code, delay)
                    self.sleep(delay)
                    delay *= 2
                    continue
                raise

    def submit(self, pdf_path):
        name = str(pdf_path).replace("\\", "/").split("/")[-1]
        with open(pdf_path, "rb") as f1:
            dig = self._call(self.doc.digitise, file=[(name, f1, "application/pdf")],
                             language=LANGUAGE, output_format="md")
        with open(pdf_path, "rb") as f2:
            ext = self._call(self.doc.extract, file=[(name, f2, "application/pdf")],
                             schema=extract_schema_json(), language=LANGUAGE, output_format="json")
        log.info("submitted digitise=%s extract=%s", dig.job_id, ext.job_id)
        return dig.job_id, ext.job_id

    def wait_all(self, job_ids):
        pending, status, delay, start = set(job_ids), {}, self.poll_start, time.monotonic()
        while pending:
            if time.monotonic() - start > self.timeout:
                raise TimeoutError(f"jobs not finished: {pending}")
            self.sleep(delay)
            for jid in list(pending):
                st = self._call(self.doc.get_status, job_id=jid).status
                log.info("job %s: %s", jid, st)
                if st in TERMINAL:
                    status[jid] = st
                    pending.discard(jid)
            delay = min(delay * 1.3, self.poll_max)
        return status

    def digitise_result(self, job_id):
        """Download Digitise ZIP and return page-level text and blocks."""
        import io
        import urllib.request
        import zipfile

        res = self._call(self.doc.get_download_url, job_id=job_id)
        data = urllib.request.urlopen(res.url).read()
        z = zipfile.ZipFile(io.BytesIO(data))

        md_files = [n for n in z.namelist() if n.endswith(".md")]
        if not md_files:
            raise RuntimeError("Digitise ZIP contains no Markdown output.")

        full_text = z.read(md_files[0]).decode("utf-8")

        pages = []
        for name in sorted(z.namelist()):
            if "/metadata/page_" not in name or not name.endswith(".json"):
                continue

            meta = json.loads(z.read(name).decode("utf-8"))
            page_num = meta.get("page_num")

            blocks = meta.get("blocks") or []
            page_text = "\n".join(
                b.get("text", "")
                for b in sorted(blocks, key=lambda b: b.get("reading_order", 0))
                if b.get("text")
            )

            pages.append({
                "page": page_num,
                "text": page_text,
                "blocks": blocks,
            })

        if not pages:
            raise RuntimeError("Digitise ZIP contains no page metadata.")

        return {
            "job_id": job_id,
            "pages": pages,
            "full_text": full_text,
        }

    def extract_result(self, job_id):
        res = self._call(self.doc.get_results, job_id=job_id)
        return {"job_id": job_id, "status": res.status,
                "result": res.result, "annotations": res.annotations}
