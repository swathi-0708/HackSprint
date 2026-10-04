"""Offline tests for pipeline.py: no API calls, a stub client stands in for Sarvam."""
import json
import pathlib
import types

import pytest

import pipeline
from normalize import normalize_claim

KEY = pathlib.Path(__file__).with_name("voice_eval_multilingual.xlsx")
needs_key = pytest.mark.skipif(not KEY.exists(), reason="put voice_eval_multilingual.xlsx next to this file")


@pytest.mark.parametrize("name,cid", [
    ("clip01_priya.wav", 1), ("clip_10.mp3", 10), ("clipT6_ravi.wav", "T6"), ("T1.wav", "T1"), ("07_x.wav", 7),
])
def test_clip_id_from_name(name, cid):
    assert pipeline.clip_id_from_name(name) == cid


def test_extract_json_handles_think_blocks_and_fences():
    reply = '<think>hmm {not json}</think>\n```json\n{"claims": [{"term": "monthly_rent"}]}\n```'
    assert pipeline.extract_json(reply) == {"claims": [{"term": "monthly_rent"}]}
    assert pipeline.extract_json("no json here") is None
    assert pipeline.extract_json('{"claims": [') is None


def test_score_counts_value_and_unit():
    exp = [dict(term="monthly_rent", value=20000, unit="inr", hedged=False),
           dict(term="notice_period", value=15, unit="days", hedged=False)]
    got = [normalize_claim(dict(term="monthly_rent", value="twenty thousand", unit="inr")),
           normalize_claim(dict(term="notice_period", value=15, unit="months"))]  # wrong unit
    rows = pipeline.score(exp, got)
    assert [r["value_ok"] for r in rows] == ["Y", "N"]
    assert pipeline.score(exp[:1], [])[0]["term_ok"] == "N"


@needs_key
def test_load_key_reads_sheet():
    lang, expected = pipeline.load_key(str(KEY))
    assert lang[1] == "English" and lang[3] == "Hinglish" and lang["T1"] == "Tamil"
    assert sum(len(v) for v in expected.values()) == 24
    assert expected[5][0]["hedged"] is True and expected[9][0]["value"] is None


def test_parse_claims_with_stub_and_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "WORK", tmp_path)
    calls = []

    class Chat:
        def completions(self, **kw):
            calls.append(kw)
            msg = types.SimpleNamespace(content='{"claims": [{"term": "notice_period", "value": 15, "unit": "days"}]}')
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    client = types.SimpleNamespace(chat=Chat())
    first = pipeline.parse_claims(client, "Notice period is fifteen days.", "clip08_x.codemix")
    again = pipeline.parse_claims(client, "Notice period is fifteen days.", "clip08_x.codemix")
    assert first == again == [{"term": "notice_period", "value": 15, "unit": "days"}]
    assert len(calls) == 1 and calls[0]["model"] == "sarvam-105b"  # second call served from cache


def test_parse_claims_retries_then_gives_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "WORK", tmp_path)

    class Chat:
        n = 0

        def completions(self, **kw):
            Chat.n += 1
            msg = types.SimpleNamespace(content="sorry, I cannot")
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    assert pipeline.parse_claims(types.SimpleNamespace(chat=Chat()), "x", "bad") == [] and Chat.n == 2
