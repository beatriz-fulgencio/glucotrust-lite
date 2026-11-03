from __future__ import annotations

import sys
import logging
import html
import json
import re
import os
from urllib.parse import urlparse
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Streamlit reruns app.py on source updates; its installed wheel can be older.
# Use the same checked-out src package that the offline tests exercise.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from glucotrust.assess import AssessmentUnavailable, create_assessor
from glucotrust.corpus import load_corpus
from glucotrust.feedback import save_feedback
from glucotrust.pipeline import assess_claim, is_dosing_request
from glucotrust.retrieve import DenseRetriever
from glucotrust.literature import EuropePMCLiterature

load_dotenv(ROOT / ".env")
st.set_page_config(page_title="GlucoTrust Lite", page_icon="🔎", layout="wide")
# Community Cloud supplies root-level secrets; load only this app's settings.
try:
    for setting in ("GLUCOTRUST_PROVIDER", "GROQ_API_KEY", "GLUCOTRUST_GROQ_MODEL",
                    "GLUCOTRUST_GROQ_REVISION", "GLUCOTRUST_TIMEOUT_SECONDS", "GLUCOTRUST_FEEDBACK_PATH"):
        if setting in st.secrets:
            os.environ[setting] = str(st.secrets[setting])
except FileNotFoundError:
    pass
st.html('<style>' + (ROOT / 'assets/style.css').read_text() + '</style>')


@st.cache_resource
def resources(corpus_version):
    passages = load_corpus(ROOT / "data/curated/passages.jsonl")
    return DenseRetriever(passages, cache_dir=ROOT / "data/curated")


def highlighted(text, quotes):
    # Escape all corpus/model data before inserting our own markup.
    spans = []
    for quote in quotes:
        pattern = r"\s+".join(re.escape(token) for token in quote.split())
        if pattern:
            spans.extend((match.start(), match.end()) for match in re.finditer(pattern, text))
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    output, cursor = [], 0
    for start, end in merged:
        output.extend([html.escape(text[cursor:start]), "<mark>" + html.escape(text[start:end]) + "</mark>"])
        cursor = end
    output.append(html.escape(text[cursor:]))
    return '<div style="white-space:pre-wrap;line-height:1.7">' + "".join(output) + "</div>"


# Read metadata without initializing the embedding model on the landing page.
@st.cache_data
def corpus_record_count(version):
    return len({passage.qid for passage in load_corpus(ROOT / "data/curated/passages.jsonl")})


@st.cache_data
def current_references(version):
    return json.loads((ROOT / "data/curated/current_references.json").read_text())["references"]


def toggle_portuguese():
    st.session_state.portuguese_display = not st.session_state.get("portuguese_display", False)
    if st.session_state.portuguese_display and st.session_state.get("summary_translation", {}).get("error"):
        st.session_state.pop("summary_translation", None)


def retry_summary_translation():
    st.session_state.pop("summary_translation", None)


st.button("Show original / English" if st.session_state.get("portuguese_display") else "Traduzir título e resumo para português",
          key="toggle_portuguese", on_click=toggle_portuguese)
portuguese_display = st.session_state.get("portuguese_display", False)


def ui_text(english, portuguese):
    return portuguese if portuguese_display else english


corpus_path = ROOT / "data/curated/passages.jsonl"
record_count = corpus_record_count(corpus_path.stat().st_mtime_ns)
st.html('<div class="site-notice"><span class="notice-icon" aria-hidden="true">ⓘ</span>'
        'Educational research prototype. Not a clinical decision-support tool. '
        'Do not use it to make health or treatment decisions.</div>')
st.html(f'''<div class="site-header"><div class="header-inner">
    <div class="brand"><span class="brand-pulse" aria-hidden="true">ϟ</span><div><div class="brand-name">GlucoTrust Lite</div>
    <div class="brand-subtitle">{ui_text("Evidence check for diabetes-related claims", "Verificação de evidências sobre afirmações relacionadas ao diabetes")}</div></div></div>
    <div class="corpus-badge">Corpus: {record_count} MedQuAD records · diabetes subset</div>
    </div></div>''')
host = os.getenv("GLUCOTRUST_OLLAMA_HOST", "http://localhost:11434")
local = urlparse(host).hostname in {"localhost", "127.0.0.1", "::1"}
hosted = os.getenv("GLUCOTRUST_PROVIDER", "ollama").strip().lower() == "groq"
with st.container(key="claim-card"):
    with st.form("claim_form"):
        st.title(ui_text("Check a claim against the evidence", "Verifique uma afirmação com base nas evidências"))
        st.write(ui_text("Enter a diabetes-related scientific or medical claim. The app retrieves the three closest "
                 "passages from the corpus and assesses whether they support it, contradict it, or leave insufficient evidence to decide.",
                 "Insira uma afirmação científica ou médica relacionada ao diabetes. O aplicativo busca os três trechos mais próximos e avalia se eles sustentam ou contradizem a afirmação, ou se as evidências são insuficientes."))
        claim = st.text_area("Claim", placeholder="A low prediction error means a glucose-forecasting model is clinically safe.", max_chars=2000)
        input_language = st.selectbox("Input language / Idioma da afirmação", ["English", "Português"])
        st.caption("Portuguese claims use an English search translation; explanations follow the claim language. Source quotations remain verbatim. / Afirmações em português usam tradução para busca; as citações mantêm o idioma original.")
        search_literature = st.checkbox("Search research literature if local evidence is insufficient", value=True)
        st.caption("When enabled, topic keywords are sent to Europe PMC. Retrieved abstracts and open-access excerpts are assessed by the configured model.")
        st.caption("Do not enter personal health information. "
                   + ("Claims and evidence are sent to Groq for assessment." if hosted else
                      "Claims and evidence are processed locally by Ollama." if local else
                      "Claims and evidence are sent to the configured Ollama server for assessment.")
                   + " Reviewer feedback is stored on the app server.")
        method, action = st.columns([3, 1], vertical_alignment="bottom")
        with method:
            st.caption("Semantic retrieval · Top 3 local passages · Optional research fallback")
        with action:
            submitted = st.form_submit_button("Assess claim →", key="assess_claim", type="primary", width="stretch")
if submitted:
    st.session_state.pop("result", None)
    st.session_state.pop("feedback_saved", None)
    st.session_state.pop("summary_translation", None)
    if not claim.strip():
        st.error("Enter a claim first.")
    elif is_dosing_request(claim):
        st.info("This prototype cannot provide personal treatment or insulin dosing advice.")
    else:
        stage = "retrieval"
        try:
            with st.spinner("Retrieving passages and assessing evidence…"):
                corpus = ROOT / "data/curated/passages.jsonl"
                retriever = resources(corpus.stat().st_mtime_ns)
                stage = "assessment"
                st.session_state.result = assess_claim(claim, retriever, create_assessor(cache_dir=ROOT / "data/cache/assessments"),
                    literature=EuropePMCLiterature() if search_literature else None,
                    language="pt" if input_language == "Português" else "en")
        except Exception as exc:
            logging.getLogger(__name__).exception("Claim pipeline failed during %s", stage)
            action = "load evidence retrieval" if stage == "retrieval" else "assess the claim"
            st.error(f"Could not {action} ({type(exc).__name__}). Check the app server logs and installation instructions in README.md.")
result = st.session_state.get("result")
if result:
    summary_column, evidence_column = st.columns([1, 2], gap="large")
    with summary_column:
        with st.container(key="assessment-card"):
            translation = result.run.get("query_translation")
            if translation:
                with st.expander("English search translation / Tradução usada na busca"):
                    st.write(translation["english_query"])
                    st.caption("Used for retrieval only; the original claim is assessed. / Usada apenas na busca; a afirmação original é avaliada.")
            st.html('<div class="eyebrow">' + ui_text("Assessment", "Avaliação") + '</div>')
            if result.assessment:
                assessment = result.assessment
                labels = {"supported": ui_text("Supported", "Sustentada pelas evidências"), "contradicted": ui_text("Contradicted", "Contradita pelas evidências"), "insufficient": ui_text("Insufficient evidence", "Evidências insuficientes")}
                st.html(f'<div class="verdict {assessment.verdict}">{labels[assessment.verdict]}</div>')
                st.html('<div class="verdict-scale" aria-label="Assessment categories">' + ''.join(
                    f'<div class="scale-item {value}{" active" if value == assessment.verdict else ""}">'
                    f'{label}</div>' for value, label in [("supported", labels["supported"]), ("insufficient", labels["insufficient"]), ("contradicted", labels["contradicted"])]
                ) + '</div>')
                st.subheader(ui_text("Why", "Justificativa"))
                display_explanation = assessment.explanation
                if portuguese_display and assessment.validation_failed:
                    display_explanation = "A avaliação falhou na validação das citações; não foi possível estabelecer uma conclusão."
                elif portuguese_display and result.run.get("identity", {}).get("explanation_language") != "pt":
                    saved = st.session_state.get("summary_translation", {})
                    if saved.get("original") != assessment.explanation:
                        try:
                            with st.spinner("Traduzindo o resumo…"):
                                text = create_assessor(cache_dir=ROOT / "data/cache/assessments").translate_summary(assessment.explanation, quotes=[c.quote for c in assessment.citations])
                            saved = {"original": assessment.explanation, "text": text}
                        except AssessmentUnavailable as exc:
                            logging.getLogger(__name__).warning("Summary translation unavailable: %s", exc)
                            saved = {"original": assessment.explanation, "error": str(exc)}
                        st.session_state.summary_translation = saved
                    if "text" in saved:
                        display_explanation = saved["text"]
                        st.caption("Tradução automática para leitura; a avaliação original e as citações não foram alteradas.")
                        with st.expander("Resumo original"):
                            st.write(assessment.explanation)
                    else:
                        error = saved.get("error", "")
                        if "usage limit" in error:
                            reason = "O limite de uso do provedor foi atingido. Aguarde antes de tentar novamente."
                        elif "authentication" in error or "not configured" in error:
                            reason = "O serviço de tradução precisa ser configurado pelo responsável pelo aplicativo."
                        elif "preserve source quotations" in error:
                            reason = "A tradução não preservou as citações e foi descartada."
                        else:
                            reason = "O serviço de tradução não concluiu a solicitação."
                        st.warning("Não foi possível traduzir o resumo. " + reason + " A avaliação original foi mantida.")
                        st.button("Tentar traduzir o resumo novamente", key="retry_summary_translation", on_click=retry_summary_translation)
                st.write(display_explanation)
                if assessment.verdict == "insufficient":
                    st.caption(ui_text("A conclusion could not be established from the available evidence. This does not prove the claim false.", "Não foi possível estabelecer uma conclusão com as evidências disponíveis. Isso não prova que a afirmação seja falsa."))
                if assessment.validation_failed:
                    st.warning("The assessment’s citations could not all be verified against the retrieved passages. The result is shown as insufficient evidence.")
                    with st.expander("Citation validation details"):
                        for error in assessment.validation_errors:
                            st.text(error)
            else:
                st.subheader(ui_text("Assessment unavailable", "Avaliação indisponível"))
                st.info(result.message)
            with st.expander(ui_text("Claim assessed", "Afirmação avaliada")):
                st.write(result.claim)
            st.divider()
            st.caption(f"Model: {result.model} · Prompt: {result.prompt_version}")
            st.caption("Retrieval: Semantic · MiniLM")
        if result.assessment:
            with st.container(key="feedback-card"):
                with st.form("feedback"):
                    st.subheader("Your review")
                    st.caption("Is this assessment correct? Reviews are saved on the app server for evaluation.")
                    correct = st.radio("Is this assessment correct?", ["Correct", "Incorrect"], horizontal=True, label_visibility="collapsed")
                    note = st.text_area("Optional reviewer note", placeholder="What should the model have noticed?", max_chars=4000)
                    if st.form_submit_button("Save feedback", disabled=bool(st.session_state.get("feedback_saved"))):
                        try:
                            feedback_path = Path(os.getenv("GLUCOTRUST_FEEDBACK_PATH", str(ROOT / "feedback.jsonl")))
                            save_feedback(result, correct == "Correct", note, feedback_path)
                            st.session_state.feedback_saved = True
                            st.success("Feedback saved.")
                        except OSError:
                            st.error("Feedback could not be saved. Check file permissions.")
    with evidence_column:
        with st.container(key="evidence-list"):
            st.html(f'<div class="evidence-heading"><h2>Evidence used</h2>'
                    f'<span>{len(result.hits)} retrieved passages</span></div>')
            if result.literature:
                st.info(result.literature.get("note", "Literature search attempted."))
                if result.literature["status"] == "assessed":
                    st.caption("Assessment includes externally retrieved research evidence. This search is not a systematic review.")
                else:
                    st.caption("The local assessment is retained.")
                with st.expander("Literature search details"):
                    st.write("Status: " + result.literature["status"])
                    st.write(result.literature.get("queries", []))
                    st.write("Initial local assessment", result.literature["local_assessment"])
            for index, hit in enumerate(result.hits, 1):
                passage = hit.passage
                with st.container(border=True, key=f"evidence-card-{index}"):
                    st.html(f'<div class="evidence-header"><span class="evidence-rank">{index}</span>'
                            f'<span class="evidence-question">{html.escape(passage.question)}</span>'
                            f'<span class="evidence-score">Retrieval score {hit.score:.3f}</span></div>')
                    st.divider()
                    quotes = [c.quote for c in result.assessment.citations if c.passage_id == passage.passage_id] if result.assessment else []
                    st.markdown(highlighted(passage.text, quotes), unsafe_allow_html=True)
                    st.divider()
                    with st.container(key=f"source-footer-{index}"):
                        st.write(f"Source: {passage.source}")
                        badge = "URL and content verified; not a guarantee of current guidance" if passage.provenance_status == "url_verified" else "Archived dataset record — not verified current guidance"
                        if passage.provenance_status == "retrieved":
                            badge = "Retrieved research excerpt — not independently verified or a clinical guideline"
                        st.caption(badge + (f" · Checked {passage.checked_on}" if passage.checked_on else " · Not yet checked"))
                        st.caption(f"Record: {passage.passage_id}")
                        if passage.provenance_status == "archived_record":
                            st.caption("The original link may no longer work. This is historical dataset content.")
                        if passage.source_type == "research":
                            st.info("Research source — not a clinical guideline")
                        if passage.url:
                            st.link_button("Open original source ↗", passage.url)
                        reference_path = ROOT / "data/curated/current_references.json"
                        for reference in current_references(reference_path.stat().st_mtime_ns):
                            if passage.passage_id in reference["passage_ids"]:
                                st.link_button("Current reference: " + reference["title"], reference["url"])
                                st.caption(f"Content compared on {reference['checked_on']} by an agent · "
                                           f"Scope: {reference['statement']} {reference['scope_limit']} "
                                           "This linked page was not supplied to the model; the assessment uses the displayed passages.")
            st.caption("Passages are shown as retrieved, with validated quotes highlighted. Source labels describe provenance, not clinical reliability.")
