"""
app.py — Streamlit web interface for the Resume Analyzer.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

import analyzer
from parse import read_resume_pdf
from report import render_markdown


# ── App Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📄",
)

st.title("📄 Resume × JD Analyzer")
st.caption(
    "Upload your résumé, paste a job description, and get instant diagnostic feedback."
)

VALID_DEGREES = ["RTIS", "IMGD", "UXGD", "BFA"]
ATS_PASS_THRESHOLD = 60


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Inputs")

    uploaded_pdf = st.file_uploader(
        "Resume PDF",
        type=["pdf"],
    )

    jd_text = st.text_area(
        "Job Description",
        height=260,
        placeholder="Paste the full job posting here…",
    )

    degree = st.selectbox(
        "Degree Program",
        VALID_DEGREES,
    )

    analyze_btn = st.button(
        "🔍 Analyze Resume",
        use_container_width=True,
        type="primary",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def validate_inputs(uploaded_pdf, jd_text):
    errors = []

    if uploaded_pdf is None:
        errors.append("Please upload a PDF résumé.")

    if not jd_text or len(jd_text.strip()) < 100:
        errors.append("Job description is too short (minimum 100 characters).")

    return errors


def tick(value):
    return "✓" if value else "✗"


def save_uploaded_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


# ── Main Analysis Flow ────────────────────────────────────────────────────────
if analyze_btn:

    errors = validate_inputs(uploaded_pdf, jd_text)

    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    pdf_path = save_uploaded_pdf(uploaded_pdf)

    progress = st.progress(0, text="Starting analysis…")

    try:
        # Step 1 — Read PDF
        progress.progress(5, text="[1/8] Reading PDF…")

        try:
            resume_text = read_resume_pdf(pdf_path)
        except ValueError as exc:
            st.error(f"Could not read PDF: {exc}")
            st.stop()

        # Step 2 — Read JD
        progress.progress(10, text="[2/8] Reading job description…")
        jd_text = jd_text.strip()

        # Step 3 — Resume Profile
        progress.progress(20, text="[3/8] Extracting résumé profile (LLM)…")
        resume_profile = analyzer.extract_resume_profile(resume_text)

        # Step 4 — JD Profile
        progress.progress(30, text="[4/8] Extracting JD profile (LLM)…")
        jd_profile = analyzer.extract_jd_profile(jd_text)

        # Step 5 — Keyword Match
        progress.progress(42, text="[5/8] Keyword match (LLM)…")
        keyword_match = analyzer.analyse_keyword_match(
            resume_profile,
            jd_profile,
        )

        # Step 6 — Bullet Audit
        progress.progress(55, text="[6/8] Bullet quality audit (LLM)…")
        bullets = analyzer.analyse_bullets(resume_profile)

        # Step 7 — Remaining Checks
        progress.progress(
            68,
            text="[7/8] Jargon, structure, degree alignment (LLM ×3)…",
        )

        jargon = analyzer.analyse_jargon(
            resume_profile,
            degree,
            jd_profile,
        )

        structure = analyzer.analyse_structure(resume_text)

        degree_alignment = analyzer.analyse_degree_alignment(
            jd_profile,
            degree,
        )

        # Build Report
        report = {
            "resume_profile": resume_profile,
            "jd_profile": jd_profile,
            "keyword_match": keyword_match,
            "bullets": bullets,
            "jargon": jargon,
            "structure": structure,
            "degree_alignment": degree_alignment,
        }

        overall_score = analyzer.compute_overall_score(report)

        report["overall_score"] = overall_score
        report["passes_ats_threshold"] = (
            overall_score >= ATS_PASS_THRESHOLD
        )

        # Step 8 — Summary
        progress.progress(
            85,
            text="[8/8] Generating executive summary (LLM)…",
        )

        report["summary"] = analyzer.summarise_overall(report)

        progress.progress(100, text="Done!")
        progress.empty()

    except RuntimeError as exc:
        progress.empty()
        st.error(f"Analysis failed: {exc}")
        st.stop()

    # ── Results ───────────────────────────────────────────────────────────────
    passes = report["passes_ats_threshold"]

    if passes:
        st.success(
            f"**Overall Score: {overall_score}/100** "
            f"— ✅ PASS (above {ATS_PASS_THRESHOLD}% ATS threshold)"
        )
    else:
        st.error(
            f"**Overall Score: {overall_score}/100** "
            f"— ❌ FAIL (below {ATS_PASS_THRESHOLD}% ATS threshold)"
        )

    # Executive Summary
    st.subheader("Executive Summary")
    st.write(report["summary"])

    # Score Breakdown
    st.subheader("Score Breakdown")

    km = report["keyword_match"]
    buls = report["bullets"]
    jarg = report["jargon"]
    strc = report["structure"]
    degr = report["degree_alignment"]

    st.table({
        "Component": [
            "Keyword Match (40%)",
            "Bullet Quality (25%)",
            "Structure (15%)",
            "Jargon (10%)",
            "Degree Alignment (10%)",
        ],
        "Raw Score": [
            km.get("keyword_match_score", 0),
            buls.get("bullet_quality_avg", 0),
            strc.get("structure_score", 0),
            jarg.get("jargon_score", 0),
            degr.get("degree_alignment_score", 0),
        ],
        "Contribution": [
            round(km.get("keyword_match_score", 0) * 0.40, 1),
            round(buls.get("bullet_quality_avg", 0) * 0.25, 1),
            round(strc.get("structure_score", 0) * 0.15, 1),
            round(jarg.get("jargon_score", 0) * 0.10, 1),
            round(degr.get("degree_alignment_score", 0) * 0.10, 1),
        ],
    })

    # Keyword Match
    st.subheader("Keyword Match")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Found ✓**")

        for item in km.get("present", [])[:20]:
            st.write(
                f"- `{item.get('keyword', '')}` "
                f"({item.get('category', '')})"
            )

    with col2:
        st.write("**Missing ✗**")

        for item in km.get("missing", [])[:20]:
            importance = (
                "🔴"
                if item.get("importance") == "required"
                else "🟡"
            )

            st.write(
                f"- {importance} "
                f"**{item.get('keyword', '')}** "
                f"— {item.get('why_it_matters', '')}"
            )

    # Bullet Quality
    st.subheader("Bullet Quality Audit")

    bullet_list = buls.get("bullets", [])

    if bullet_list:
        st.table([
            {
                "Project / Role": b.get("parent_title", ""),
                "Bullet": b.get("bullet_text", "")[:80],
                "Action": "✓" if b.get("has_action_verb") else "✗",
                "Tech": "✓" if b.get("has_specific_technology") else "✗",
                "Impact": "✓" if b.get("has_measurable_impact") else "✗",
                "Level": b.get("level", ""),
                "What's Missing": b.get("what_is_missing", ""),
            }
            for b in bullet_list
        ])
    else:
        st.info("No bullets found to audit.")

    # Jargon
    st.subheader("Game-Dev Jargon Flags")

    jargon_flags = jarg.get("flags", [])

    if jargon_flags:
        for flag in jargon_flags:

            severity = flag.get("severity", "low")

            icon = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(severity, "⚪")

            with st.expander(
                f"{icon} {flag.get('term_used', '')} ({severity})"
            ):
                st.write(f"**Bullet:** {flag.get('bullet_text', '')}")

                st.write(
                    f"**Suggested translation:** "
                    f"{flag.get('suggested_translation', '')}"
                )
    else:
        st.success("No game-dev jargon flags. ✓")

    # Structure Audit
    st.subheader("Structure & ATS Audit")

    tt = strc.get("three_thirds", {})

    col_a, col_b = st.columns(2)

    with col_a:
        st.write("**Three-Thirds Compliance**")

        st.write(
            f"- {tick(tt.get('top_third_has_name'))} "
            f"Name in top third"
        )

        st.write(
            f"- {tick(tt.get('top_third_has_contact'))} "
            f"Contact in top third"
        )

        st.write(
            f"- {tick(tt.get('top_third_has_summary_or_featured'))} "
            f"Summary / featured project"
        )

        st.write(
            f"- {tick(tt.get('middle_third_has_projects_or_experience'))} "
            f"Projects / experience in middle"
        )

        st.write(
            f"- {tick(tt.get('bottom_third_has_skills_keywords'))} "
            f"Skills in bottom third"
        )

    with col_b:
        st.write("**ATS Red Flags**")

        ats_flags = strc.get("ats_red_flags", [])

        if ats_flags:
            for flag in ats_flags:
                st.write(
                    f"- 🚩 **{flag.get('issue', '')}** "
                    f"— {flag.get('evidence', '')}"
                )
        else:
            st.success("No ATS red flags. ✓")

    # Degree Alignment
    st.subheader("Degree Alignment")

    st.write(
        f"**Score:** "
        f"{degr.get('degree_alignment_score', 0)}/100"
    )

    st.write(
        f"**Degree:** "
        f"{degr.get('student_degree', degree)}"
    )

    st.write(
        f"**JD Title:** "
        f"{degr.get('jd_title', '')}"
    )

    st.write(
        f"**On suggested list:** "
        f"{tick(degr.get('title_on_suggested_list'))}"
    )

    st.info(degr.get("fit_commentary", ""))

    # Downloads
    st.subheader("Download Reports")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_bytes = json.dumps(
        report,
        indent=2,
    ).encode("utf-8")

    with tempfile.NamedTemporaryFile(
        suffix=".md",
        delete=False,
    ) as md_tmp:
        md_path = md_tmp.name

    render_markdown(report, out_path=md_path)

    md_bytes = Path(md_path).read_bytes()

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "⬇️ Download JSON",
            data=json_bytes,
            file_name=f"match_report_{timestamp}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            "⬇️ Download Markdown",
            data=md_bytes,
            file_name=f"match_report_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )

else:
    st.info(
        "👈 Fill in the sidebar and click "
        "**Analyze Resume** to get started."
    )