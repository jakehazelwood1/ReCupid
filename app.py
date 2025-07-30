import streamlit as st
import os
import openai
import json
import docx2txt
import PyPDF2
from io import BytesIO
import base64

# --- Sidebar ---
with st.sidebar:
    st.image("timeisprecious.jpg", width=180)
    st.markdown("## 🔍 ReCupid")
    st.markdown("Evaluate candidate fit in seconds using GPT-4.")
    st.markdown("""<hr style="margin-top: 0.5rem; margin-bottom: 1rem;">""", unsafe_allow_html=True)

    st.markdown("#### 🧠 How it works")
    st.markdown("""
    1. Upload up to 15 CVs (PDF or DOCX).  
    2. Paste the job description.  
    3. Click Evaluate CVs.  
    4. Review the results & follow-up questions.
    """)

    st.markdown("""<hr style="margin-top: 1rem; margin-bottom: 1rem;">""", unsafe_allow_html=True)

    st.markdown("#### ✍️ Tips for Job Descriptions")
    st.markdown("""
    - Be clear about required skills  
    - Highlight responsibilities  
    - State experience level  
    - Include culture & soft skills
    """)

    st.markdown("""<hr style="margin-top: 1rem; margin-bottom: 1rem;">""", unsafe_allow_html=True)

    st.markdown("#### 📊 Scoring Guide")
    st.markdown("""
    - **80–100**: Strong fit  
    - **60–79**: Moderate fit  
    - **Below 60**: Needs review
    """)

    st.markdown("""<hr style="margin-top: 1rem; margin-bottom: 1rem;">""", unsafe_allow_html=True)

    st.markdown("#### 📁 Upload Details")
    st.markdown("""
    - Format: **PDF/DOCX**  
    - Size: **200MB max**  
    - Max: **15 CVs**
    """)

    st.markdown("""<hr style="margin-top: 1rem; margin-bottom: 1rem;">""", unsafe_allow_html=True)

    st.markdown("#### ℹ️ About")
    st.markdown("""
    Powered by GPT-4. Quickly assess candidate fit for your open roles.  
    Contact us at: [email@example.com](mailto:email@example.com)
    """)


# --- Custom Styling ---
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #f7f9fc;
    font-family: 'Inter', system-ui, sans-serif;
    color: #333333;
}

textarea {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 12px;
    font-size: 1rem;
    color: #1e293b;
}

.stButton > button {
    background-color: #3b82f6;
    color: white;
    font-weight: 600;
    padding: 10px 24px;
    border: none;
    border-radius: 8px;
    transition: background-color 0.3s ease;
}

.stButton > button:hover {
    background-color: #2563eb;
    cursor: pointer;
}

.glass-card {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}
</style>
""", unsafe_allow_html=True)


# --- API Key ---
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Helper Functions ---
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""

def extract_text_from_docx(file):
    try:
        return docx2txt.process(file).strip()
    except Exception:
        return ""

def get_cv_text(uploaded_file):
    fname = uploaded_file.name.lower()
    try:
        if fname.endswith(".pdf"):
            return extract_text_from_pdf(uploaded_file)
        elif fname.endswith(".docx"):
            # Read bytes and wrap in BytesIO
            return extract_text_from_docx(BytesIO(uploaded_file.read()))
        else:
            return ""
    except Exception:
        return ""

def build_prompt(cv_text, job_description):
    return f"""
You are an expert recruiter with over 15 years of experience in evaluating technical and non-technical candidates for mid-to-senior level roles. Your goal is to evaluate the candidate's CV against the job description provided — simulating how a highly discerning human recruiter would assess their fit.

When assessing years of experience, **extract the numeric range of required years from the job description** and **compare it exactly** to the candidate's stated years of experience.  
- If the candidate's experience falls within the required range (inclusive), including being exactly at the minimum or maximum, do NOT list experience as a weakness.  
- Only flag experience as a weakness if it is numerically below the minimum or significantly above the maximum (which may indicate overqualification).  
- Similarly, if comparing multiple candidates, only mention experience differences if the difference is at least one full year.  
- Avoid vague or generic comments about "limited experience" if all candidates have similar experience levels. Instead, highlight meaningful differentiators.
- Do NOT phrase meeting the minimum required years of experience as a weakness. Statements like "experience is at the minimum required level" or similar should never appear under weaknesses. If experience meets or exceeds the minimum, treat it as satisfying the requirement, not as a gap.

Do **not** rely solely on keyword matching. Instead, assess the candidate holistically based on the following dimensions:

1. **Technical Fit** – Do their skills and experience directly match the technical requirements of the role? Evaluate based on relevance, depth, and recency.
2. **Industry & Domain Relevance** – Have they worked in similar sectors, environments, or project types?
3. **Achievements & Impact** – Look for demonstrated results, measurable impact, leadership or ownership.
4. **Career Progression & Motivation** – Does their trajectory align with the opportunity? Does this role make sense for them next?
5. **Cultural & Communication Fit** – Based on tone, language, and soft skills. Would they likely work well with the team and values?
6. **Uniqueness** – What makes them stand out from other candidates with similar skills?

Be objective, human-like, and critical. If multiple candidates are similar, still attempt to differentiate them.

---

Respond strictly in the following **valid JSON format only**, without any extra commentary:

{{
  "score": <integer between 0-100>,
  "breakdown": {{
    "technical_fit": <0-40>,
    "industry_relevance": <0-20>,
    "impact_and_achievements": <0-15>,
    "cultural_fit": <0-15>,
    "career_alignment": <0-10>
  }},
  "overview": "<1-sentence recruiter-style summary>",
  "summary": "<Concise paragraph overview of the candidate’s fit and gaps>",
  "strengths": ["<bullet point>", "..."],
  "weaknesses": ["<bullet point>", "..."],
  "differentiator": "<What makes this candidate stand out or worth shortlisting>"
}}

---

### JOB DESCRIPTION:
{job_description}

---

### CANDIDATE CV:
{cv_text}
"""
    return template.format(job_description=job_description, cv_text=cv_text)


def get_candidate_score(cv_text, job_description):
    prompt = build_prompt(cv_text, job_description)
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=700,
        )
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        return parsed
    except json.JSONDecodeError:
        return {
            "score": None,
            "summary": "⚠️ Failed to parse AI response — invalid JSON format.",
            "overview": "",
            "strengths": [],
            "weaknesses": []
        }
    except Exception as e:
        return {
            "score": None,
            "summary": f"⚠️ Error calling OpenAI API: {str(e)}",
            "overview": "",
            "strengths": [],
            "weaknesses": []
        }

def get_follow_up_questions(weaknesses, job_description):
    if not weaknesses:
        return []

    prompt = f"""
You are an expert recruiter writing in British English. Given the following candidate weaknesses and the job description, suggest 3 personalised, insightful follow-up questions the recruiter can ask the candidate to better evaluate their fit.

Job Description:
{job_description}

Candidate Weaknesses:
{weaknesses}

Provide the questions as a bullet list.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        questions_text = response.choices[0].message.content.strip()
        questions = [q.strip("- ").strip() for q in questions_text.split("\n") if q.strip()]
        return questions
    except Exception as e:
        return [f"⚠️ Failed to generate follow-up questions: {str(e)}"]

def render_candidate_result(filename, score, summary, overview, strengths, weaknesses, follow_up_questions):
    html_content = f"""
<div style="
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    color: #1e293b;
">
    <h3>📄 Results for: <span style="color:#111827;">{filename}</span> — Score: <span style="font-weight:700;">{score if score is not None else 'N/A'} / 100</span></h3>
"""

    if score is None:
        html_content += '<p style="color:red; font-weight:bold;">❌ No score available</p>'
    elif score >= 80:
        html_content += '<p style="color:green; font-weight:bold;">✅ Strong fit for the role</p>'
    elif 60 <= score < 80:
        html_content += '<p style="color:orange; font-weight:bold;">🟡 Moderate fit for the role</p>'
    else:
        html_content += '<p style="color:red; font-weight:bold;">⚠️ Weak fit for the role</p>'

    html_content += f"""
    <h4>Summary:</h4>
    <p>{summary}</p>
"""
    if overview:
        html_content += f"<p><em>{overview}</em></p>"

    if strengths:
        html_content += "<h4>✅ Strengths:</h4><ul>"
        for s in strengths:
            html_content += f"<li>{s}</li>"
        html_content += "</ul>"

    if weaknesses:
        html_content += "<h4>⚠️ Weaknesses:</h4><ul>"
        for w in weaknesses:
            html_content += f"<li>{w}</li>"
        html_content += "</ul>"

    if follow_up_questions:
        html_content += """
        <div style="
            margin-top: 20px;
            background: #f0f9ff;
            border-left: 6px solid #3b82f6;
            padding: 12px 20px;
            border-radius: 6px;
            color: #1e293b;
        ">
            <strong>❓ Suggested Follow-up Questions:</strong>
            <ul style="margin-top: 8px; padding-left: 20px;">
        """
        for q in follow_up_questions:
            html_content += f"<li>{q}</li>"
        html_content += "</ul></div>"

    html_content += "</div>"

    st.markdown(html_content, unsafe_allow_html=True)

# --- Main app ---
st.title("ReCupid")

# --- Label and Upload Field ---
st.markdown("#### 📄 Upload Candidate CVs")
st.caption("Upload up to 15 CVs in PDF or DOCX format.")
uploaded_files = st.file_uploader(
    label="",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    help="Accepted formats: PDF, DOCX (Max 15 files)"
)

# --- Show Uploaded File Names ---
if uploaded_files:
    st.markdown("##### ✅ Files Uploaded:")
    st.markdown(
        "<ul style='padding-left:20px;'>"
        + "".join(
            f"<li style='margin-bottom:4px; color:#1e293b;'>📄 <strong>{file.name}</strong></li>"
            for file in uploaded_files
        )
        + "</ul>",
        unsafe_allow_html=True,
    )

# --- Label and Job Description Field ---
st.markdown("#### 📋 Paste Job Description")
st.caption("Include full responsibilities, required skills, experience level, and cultural expectations.")
job_description = st.text_area(
    label="",
    height=150,
    placeholder="Example: We're hiring a software engineer with strong Python skills, 3+ years experience...",
    help="Paste the complete job description you're hiring for."
)


# --- Evaluate Button ---
evaluate_clicked = st.button("🚀 Evaluate CVs")


if evaluate_clicked:
    # Initialize the list here:
    candidate_results = []
    if not uploaded_files:
        st.warning("Please upload at least one CV to evaluate.")
    elif not job_description.strip():
        st.warning("Please paste a job description to evaluate candidates against.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_files = len(uploaded_files)
        for idx, uploaded_file in enumerate(uploaded_files, start=1):
            status_text.text(f"Evaluating {uploaded_file.name} ({idx}/{total_files})...")

            cv_text = get_cv_text(uploaded_file)
            if not cv_text:
                st.error(f"⚠️ Could not extract text from {uploaded_file.name}. Please upload a valid PDF or DOCX file.")
                progress_bar.progress(idx / total_files)
                continue

            candidate_data = get_candidate_score(cv_text, job_description)
            score = candidate_data.get("score")
            summary = candidate_data.get("summary", "")
            overview = candidate_data.get("overview", "")
            strengths = candidate_data.get("strengths", [])
            weaknesses = candidate_data.get("weaknesses", [])

            follow_up_questions = get_follow_up_questions(weaknesses, job_description)

            render_candidate_result(
                uploaded_file.name,
                score,
                summary,
                overview,
                strengths,
                weaknesses,
                follow_up_questions
            )
            progress_bar.progress(idx / total_files)
            
            # Save results for export
            candidate_results.append({
                "filename": uploaded_file.name,
                "score": score,
                "summary": summary,
                "overview": overview,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "follow_up_questions": follow_up_questions
            })

#        status_text.text("Evaluation complete.")

        # --- Export Button ---
        if candidate_results:
            def generate_export_html(job_desc, results):
                html = f"""
                <html>
                <head>
                <meta charset="utf-8" />
                <title>ReCupid Export</title>
                <style>
                body {{ font-family: 'Inter', system-ui, sans-serif; background-color: #f7f9fc; color: #1e293b; padding: 20px; }}
                h1 {{ color: #2563eb; }}
                .job-desc {{ background: #e0e7ff; border-left: 6px solid #3b82f6; padding: 15px; margin-bottom: 30px; border-radius: 8px; }}
                .candidate-result {{ background: #fff; border-radius: 12px; border: 1px solid #e5e7eb; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
                h2 {{ color: #1e40af; }}
                ul {{ margin-top: 0; }}
                .strong-fit {{ color: green; font-weight: 700; }}
                .moderate-fit {{ color: orange; font-weight: 700; }}
                .weak-fit {{ color: red; font-weight: 700; }}
                </style>
                </head>
                <body>
                <h1>ReCupid - Candidate Analysis Export</h1>
                <section class="job-desc">
                    <h2>Job Description</h2>
                    <p>{job_desc.replace('\n', '<br>')}</p>
                </section>
                """

                for r in results:
                    score_class = (
                        "strong-fit" if (r['score'] is not None and r['score'] >= 80) else
                        "moderate-fit" if (r['score'] is not None and 60 <= r['score'] < 80) else
                        "weak-fit"
                    ) if r['score'] is not None else ""

                    html += f"""
                    <section class="candidate-result">
                        <h2>📄 {r['filename']} — Score: <span class="{score_class}">{r['score'] if r['score'] is not None else 'N/A'} / 100</span></h2>
                    """

                    if r['score'] is None:
                        html += '<p style="color:red; font-weight:bold;">❌ No score available</p>'
                    elif r['score'] >= 80:
                        html += '<p class="strong-fit">✅ Strong fit for the role</p>'
                    elif 60 <= r['score'] < 80:
                        html += '<p class="moderate-fit">🟡 Moderate fit for the role</p>'
                    else:
                        html += '<p class="weak-fit">⚠️ Weak fit for the role</p>'

                    html += f"""
                        <h3>Summary:</h3>
                        <p>{r['summary']}</p>
                    """

                    if r['overview']:
                        html += f"<p><em>{r['overview']}</em></p>"

                    if r['strengths']:
                        html += "<h4>✅ Strengths:</h4><ul>"
                        for s in r['strengths']:
                            html += f"<li>{s}</li>"
                        html += "</ul>"

                    if r['weaknesses']:
                        html += "<h4>⚠️ Weaknesses:</h4><ul>"
                        for w in r['weaknesses']:
                            html += f"<li>{w}</li>"
                        html += "</ul>"

                    if r['follow_up_questions']:
                        html += """
                        <h4>❓ Suggested Follow-up Questions:</h4>
                        <ul>
                        """
                        for q in r['follow_up_questions']:
                            html += f"<li>{q}</li>"
                        html += "</ul>"

                    html += "</section>"

                html += "</body></html>"
                return html

            export_html = generate_export_html(job_description, candidate_results)
            b64 = base64.b64encode(export_html.encode()).decode()
            href = f'<a href="data:text/html;base64,{b64}" download="ReCupid_match_export.html">📥 Download Analysis Export</a>'
            st.markdown(href, unsafe_allow_html=True)
