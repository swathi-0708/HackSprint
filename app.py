"""Rental claim checker - Streamlit UI.

Flow: pick an agreement (sample or PDF) + a voice note (sample, record, upload) -> Check now.
Real work happens in services.py (Sarvam APIs with caching + offline fallback) and compare.py.
"""
import html

import streamlit as st

import services
from compare import compare_all
from i18n import LANGS, SENTENCES_EN, T

st.set_page_config(page_title="DocVox", page_icon="🎙️", layout="centered",
                   initial_sidebar_state="collapsed")

# outcome -> (icon, solid colour, text on solid, light tint)
STYLE = {
    "MATCH":         ("✅", "#0E9F4F", "#FFFFFF", "#D9F7E4"),
    "MISMATCH":      ("❌", "#E5302B", "#FFFFFF", "#FFE0DE"),
    "NOT_MENTIONED": ("⚠️", "#F59E0B", "#2E1F00", "#FFF1CC"),
    "UNCLEAR":       ("❓", "#2F6FED", "#FFFFFF", "#DCE8FF"),
}
ORDER = ["MISMATCH", "NOT_MENTIONED", "UNCLEAR", "MATCH"]  # problems first

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans+Tamil:wght@400;600;700&display=swap');
html { font-size: 18px; }
.stApp { background: #EAF4FF !important; color: #0F1F33 !important; }
.stApp, .stApp *:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]) { font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Tamil', sans-serif; }
[data-testid="stToast"], [data-testid="stToastContainer"] { display: none !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"], [data-testid="stDecoration"] { display: none !important; }
.block-container { max-width: 860px; padding-top: 1.4rem; padding-bottom: 3rem; }

/* language picker */
div[role="radiogroup"] { gap: .6rem; flex-wrap: wrap; }
div[role="radiogroup"] label { background: #FFFFFF; border: 2px solid #1F6BFF; border-radius: 999px; padding: .35rem 1.1rem; cursor: pointer; }
div[role="radiogroup"] label p { color: #1F6BFF !important; font-weight: 700; font-size: 1.05rem; margin: 0; }
div[role="radiogroup"] label:has(input:checked) { background: #1F6BFF; }
div[role="radiogroup"] label:has(input:checked) p { color: #FFFFFF !important; }
div[role="radiogroup"] label[data-testid="stRadioOption"] > div > div:first-child { display: none !important; }
.brand { display: flex; align-items: center; gap: .6rem; margin: 0 0 1.1rem; }
.brand .logo { background: #1F6BFF; border-radius: 12px; padding: .25rem .5rem; font-size: 1.3rem; }
.brand .bname { font-size: 1.7rem; font-weight: 700; color: #0F1F33; letter-spacing: -.01em; }
.brand .bname b { color: #1F6BFF; }
.brand .tag { color: #35506E; font-size: .95rem; margin-left: .3rem; }
.pick { color: #35506E; font-size: .95rem; margin: 0 0 .3rem; }

h1.title { font-weight: 700; font-size: 2.1rem; line-height: 1.25; margin: 1rem 0 .4rem; color: #0F1F33; }
p.sub { color: #35506E; font-size: 1.05rem; margin: 0 0 1.2rem; line-height: 1.6; }
.headline { background: #1F6BFF; color: #FFFFFF; font-size: 1.5rem; font-weight: 700; line-height: 1.4; padding: 1rem 1.3rem; border-radius: 16px; margin-bottom: 1rem; }
.bar { display: flex; height: 18px; border-radius: 9px; overflow: hidden; gap: 3px; margin-bottom: .6rem; }
.legend { display: flex; flex-wrap: wrap; gap: .4rem 1.3rem; font-size: 1rem; color: #0F1F33; margin-bottom: 1.6rem; }
.legend i { display: inline-block; width: 14px; height: 14px; border-radius: 4px; margin-right: .45rem; vertical-align: -2px; }

.card { background: #FFFFFF; border: 2px solid #D3E3F7; border-left-width: 10px; border-radius: 16px; padding: 1.1rem 1.3rem; margin-bottom: 1.1rem; }
.top { display: flex; justify-content: space-between; align-items: center; gap: .7rem; flex-wrap: wrap; }
.term { font-weight: 700; font-size: 1.3rem; color: #0F1F33; }
.pill { font-size: 1.05rem; font-weight: 700; padding: .35rem 1rem; border-radius: 999px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0 .8rem; }
.pair > div { border-radius: 12px; padding: .7rem .9rem; }
.pair .lbl { font-size: .95rem; color: #35506E; margin-bottom: .15rem; }
.pair .val { font-size: 1.9rem; font-weight: 700; color: #0F1F33; line-height: 1.3; }
.pair .val.none { font-size: 1.3rem; color: #5A6B80; }
.why { font-size: 1.05rem; color: #0F1F33; margin: 0; }
.meta { font-size: .9rem; color: #4A5F78; margin-top: .6rem; }
.note { color: #35506E; font-size: .95rem; margin: .3rem 0; }
.heard { background: #FFFFFF; border: 2px dashed #9DB8DA; border-radius: 12px; padding: .7rem 1rem; margin: .8rem 0; color: #0F1F33; }
.step { font-weight: 700; font-size: 1.25rem; margin: 1.2rem 0 .4rem; color: #0F1F33; }
.conv { font-size: .95rem; color: #1F4E8C; margin: .3rem 0 0; }
.foot { color: #4A5F78; font-size: .9rem; margin-top: 1.5rem; }
@media (max-width: 600px) { .pair { grid-template-columns: 1fr; } .headline { font-size: 1.25rem; } }

[data-testid="stSelectbox"] label p, [data-testid="stFileUploader"] label p, [data-testid="stAudioInput"] label p, .stCheckbox p, [data-testid="stExpander"] summary p, [data-testid="stCaptionContainer"] p { color: #0F1F33 !important; }
[data-testid="stExpander"], [data-testid="stFileUploaderDropzone"] { background: #FFFFFF !important; border-radius: 12px; }
div.stButton > button { background: #1F6BFF; color: #FFFFFF; border: 0; border-radius: 12px; font-weight: 700; font-size: 1.15rem; padding: .6rem 1.6rem; }
div.stButton > button:hover { background: #1556CC; color: #FFFFFF; }
div.stButton > button p { color: #FFFFFF !important; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stAlert"] * { color: #0F1F33 !important; }
[data-testid="stExpander"] summary { padding: .5rem .8rem; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background: #FFFFFF !important; border: 2px solid #D3E3F7; border-radius: 12px; }
[data-testid="stSelectbox"] div[data-baseweb="select"] * { color: #0F1F33 !important; }
[data-testid="stAudioInput"] { border-radius: 12px; }
</style>''', unsafe_allow_html=True)

# ---------------- language ----------------
st.markdown('<div class="brand"><span class="logo">🎙️</span><span class="bname">Doc<b>Vox</b></span><span class="tag">Rental agreement × voice note</span></div>', unsafe_allow_html=True)
st.markdown(f'<p class="pick">{T["en"]["pick_lang"]} · {T["hi"]["pick_lang"]} · {T["ta"]["pick_lang"]}</p>', unsafe_allow_html=True)
choice = st.radio("Language", list(LANGS), horizontal=True, label_visibility="collapsed")
lang = LANGS[choice]
tx = T[lang]

# ---------------- settings ----------------
key_ok = services.live_available()
with st.expander(tx["settings"]):
    live = st.checkbox(tx["live_on"], value=False, disabled=not key_ok)
    st.caption(tx["st_live"] if live else (tx["st_off"] if key_ok else tx["st_nokey"]))


def fmt(value, unit):
    if value is None:
        return None
    num = f"{value:,.0f}" if isinstance(value, (int, float)) and float(value).is_integer() else str(value)
    u = (unit or "").lower()
    if u == "inr":
        return f"₹{num}"
    if u in ("", "none"):
        return num
    if u in tx["units"]:
        k = u[:-1] if (value == 1 and u in ("months", "days")) else u
        return f"{num} {tx['units'][k]}"
    return f"{num} {unit}"


def term_name(t):
    return tx["terms"].get(t, t.replace("_", " ").capitalize())


def said_text(r):
    return tx["included"] if r.included_in_rent else (fmt(r.said_value, r.said_unit) or "-")


def sentence(r):
    """Result sentence: Sarvam Translate template (cached/live) or built-in text; numbers filled in code."""
    key = "UNSURE" if (r.reason == "speaker_unsure") else r.outcome
    tpl, via = None, "builtin"
    if lang == "en":
        tpl = SENTENCES_EN[key]
    else:
        tpl = services.translate_template(SENTENCES_EN[key], lang, live)
        via = "translate" if tpl else "builtin"
        tpl = tpl or tx["sent"][key]
    actual = fmt(r.agreement_value, r.agreement_unit) or ""
    return tpl.format(term=term_name(r.term), said=said_text(r), actual=actual), via


# ---------------- inputs ----------------
st.markdown(f'<div class="step">{html.escape(tx["step1"])}</div>', unsafe_allow_html=True)
ag_mode = st.radio("ag", [tx["ag_sample"], tx["ag_upload"]], horizontal=True, label_visibility="collapsed")
agreement = None  # (name, bytes|None, facts|None)
if ag_mode == tx["ag_sample"]:
    demos = services.demo_agreements()
    name = st.selectbox(tx["pick_ag"], list(demos), format_func=lambda n: n.replace("syn_", "Sample ").replace("_", " "))
    agreement = (name, None, demos[name]) if name else None
else:
    up = st.file_uploader(tx["pick_ag"], type=["pdf"])
    agreement = (up.name, up.getvalue(), None) if up else None

st.markdown(f'<div class="step">{html.escape(tx["step2"])}</div>', unsafe_allow_html=True)
v_mode = st.radio("v", [tx["v_sample"], tx["v_record"], tx["v_upload"]], horizontal=True, label_visibility="collapsed")
voice = None  # ("sample", clip) | ("audio", name, bytes)
if v_mode == tx["v_sample"]:
    clips = services.sample_clips()
    if clips:
        c = st.selectbox(tx["pick_clip"], clips, format_func=lambda c: f"{c['id']} · {c['language']} · {c['script'][:60]}")
        voice = ("sample", c)
elif v_mode == tx["v_record"]:
    rec = st.audio_input(tx["pick_clip"])
    voice = ("audio", "recording.wav", rec.getvalue()) if rec else None
else:
    up = st.file_uploader(tx["pick_clip"], type=["wav", "mp3", "opus", "ogg", "m4a", "flac"], key="aup")
    voice = ("audio", up.name, up.getvalue()) if up else None

if st.button(tx["go"], type="primary"):
    if not agreement or not voice:
        st.warning(tx["pick_first"])
    else:
        try:
            name, data, facts = agreement
            ag_src = "demo"
            if facts is None:
                facts, ag_src = services.facts_for_pdf(data, name, live)
            vres = None
            if facts is not None:
                if voice[0] == "sample":
                    vres = services.claims_from_sample(voice[1], live)
                else:
                    vres = services.claims_from_audio(voice[2], voice[1], live)
            if facts is None:
                st.session_state["out"] = dict(error=tx["need_live"])
            elif vres is None:
                st.session_state["out"] = dict(error=tx["need_live_a"])
            else:
                st.session_state["out"] = dict(results=compare_all(vres["claims"], facts), transcript=vres["transcript"],
                                               v_src=vres["source"], ag_src=ag_src)
        except Exception as e:  # keep the demo alive; show a readable message
            st.session_state["out"] = dict(error=tx["err"].format(x=str(e)[:200]))

out = st.session_state.get("out")
if not out:
    st.stop()
if out.get("error"):
    st.error(out["error"])
    st.stop()

rows = sorted(out["results"], key=lambda r: ORDER.index(r.outcome))
total = len(rows)
if total == 0:
    st.info(tx["no_claims"])
    st.stop()

# ---------------- results ----------------
st.markdown(f'<div class="heard"><b>{html.escape(tx["heard"])}:</b> {html.escape(out["transcript"])}</div>', unsafe_allow_html=True)
counts = {k: sum(1 for r in rows if r.outcome == k) for k in STYLE}
st.markdown(f'<h1 class="title">{html.escape(tx["title"])}</h1>', unsafe_allow_html=True)
if counts["MISMATCH"]:
    head = tx["head_bad"].format(n=counts["MISMATCH"], t=total)
elif counts["NOT_MENTIONED"] or counts["UNCLEAR"]:
    head = tx["head_mixed"].format(ok=counts["MATCH"], t=total)
else:
    head = tx["head_ok"].format(t=total)
st.markdown(f'<div class="headline">{html.escape(head)}</div>', unsafe_allow_html=True)
bar = "".join(f'<span style="width:{counts[k] / total * 100:.1f}%;background:{STYLE[k][1]}"></span>' for k in ORDER if counts[k])
legend = "".join(f'<span><i style="background:{STYLE[k][1]}"></i>{counts[k]} {html.escape(tx[k][0])}</span>' for k in ORDER if counts[k])
st.markdown(f'<div class="bar">{bar}</div><div class="legend">{legend}</div>', unsafe_allow_html=True)

used_translate = False
for i, r in enumerate(rows):
    icon, solid, on_solid, tint = STYLE[r.outcome]
    name = tx[r.outcome][0]
    said = said_text(r)
    actual = fmt(r.agreement_value, r.agreement_unit) if r.agreement_value is not None else None
    actual_html = f'<div class="val">{html.escape(actual)}</div>' if actual else f'<div class="val none">{html.escape(tx["none"])}</div>'
    sent, via = sentence(r)
    used_translate |= via == "translate"
    conv = ""
    if r.converted_amount is not None:
        conv = f'<p class="conv">{html.escape(tx["conv"].format(said=(said if r.said_unit == "months_of_rent" else fmt(r.agreement_value, r.agreement_unit)), amount=fmt(r.converted_amount, "inr"), rent=fmt(r.rent_used, "inr")))}</p>'
    meta = []
    if r.page:
        meta.append(tx["page"].format(x=r.page))
    if r.confidence is not None:
        meta.append(tx["conf"].format(x=f"{r.confidence:.0%}"))
    if r.hedged:
        meta.append(tx["unsure"])
    st.markdown(
        f'''
<div class="card" style="border-left-color:{solid}">
  <div class="top"><span class="term">{html.escape(term_name(r.term))}</span>
    <span class="pill" style="background:{solid};color:{on_solid}">{icon} {html.escape(name)}</span></div>
  <div class="pair">
    <div style="background:#F1F6FC"><div class="lbl">{html.escape(tx["told"])}</div><div class="val">{html.escape(said)}</div></div>
    <div style="background:{tint}"><div class="lbl">{html.escape(tx["says"])}</div>{actual_html}</div>
  </div>
  <p class="why">{html.escape(sent)}</p>{conv}
  <div class="meta">{" · ".join(html.escape(m) for m in meta)}</div>
</div>''', unsafe_allow_html=True)
    if st.button(f"🔊 {tx['listen']}", key=f"listen{i}"):
        wav = services.speak(sent, lang, live)
        if wav:
            st.audio(wav, format="audio/wav", autoplay=True)
        else:
            st.caption(tx["no_audio"])

notes = [tx["src_" + out["v_src"]] if ("src_" + out["v_src"]) in tx else "", tx["src_demo"] if out["ag_src"] == "demo" else ""]
if used_translate:
    notes.append(tx["tr_note"])
st.markdown('<p class="foot">' + " ".join(html.escape(n) for n in notes if n) + "<br>" + html.escape(tx["foot"]) + "</p>", unsafe_allow_html=True)