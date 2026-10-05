import base64
import types

import services


class FakeClient:
    def __init__(self, translated):
        self.text = types.SimpleNamespace(translate=lambda **kw: types.SimpleNamespace(translated_text=translated))
        self.text_to_speech = types.SimpleNamespace(
            convert=lambda **kw: types.SimpleNamespace(audios=[base64.b64encode(b"RIFFfake").decode()]))


def _setup(tmp_path, monkeypatch, translated="X {term} {said} {actual}"):
    monkeypatch.setattr(services, "WORK", tmp_path)
    monkeypatch.setattr(services, "client", lambda: FakeClient(translated))


def test_translate_keeps_placeholders_and_caches(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    tpl = "You were told {said} for {term}, but the agreement says {actual}."
    assert services.translate_template(tpl, "hi", live=True) == "X {term} {said} {actual}"
    monkeypatch.setattr(services, "client", lambda: (_ for _ in ()).throw(AssertionError("should hit cache")))
    assert services.translate_template(tpl, "hi", live=False) == "X {term} {said} {actual}"


def test_translate_rejects_lost_placeholder(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, translated="no placeholders here")
    assert services.translate_template("Value {said} for {term}", "ta", live=True) is None


def test_translate_offline_without_cache_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "WORK", tmp_path)
    assert services.translate_template("Hello {term}", "hi", live=False) is None
    assert services.translate_template("Hello {term}", "en", live=False) == "Hello {term}"


def test_speak_caches_audio(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert services.speak("hello", "hi", live=True) == b"RIFFfake"
    monkeypatch.setattr(services, "client", lambda: (_ for _ in ()).throw(AssertionError("should hit cache")))
    assert services.speak("hello", "hi", live=False) == b"RIFFfake"
    assert services.speak("other", "hi", live=False) is None


def test_demo_agreements_and_sample_clip_offline():
    demos = services.demo_agreements()
    assert len(demos) == 5
    clip = next(c for c in services.sample_clips() if str(c["id"]) == "6")
    res = services.claims_from_sample(clip, live=False)
    assert res["source"] == "sample" and len(res["claims"]) == 3


def test_audio_not_cached_and_offline_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "WORK", tmp_path)
    assert services.claims_from_audio(b"abc", "x.wav", live=False) is None
