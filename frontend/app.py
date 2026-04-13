import streamlit as st
import requests
import pandas as pd
import json

# Page config
st.set_page_config(page_title="AI Job Finder Pro", page_icon="💼", layout="wide")

# Custom CSS for modern look
st.markdown("""
<style>
    .main { background-color: #f5f7f9; }
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 5px;
        width: 100%;
        font-weight: bold;
    }
    .job-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .tag {
        display: inline-block;
        background: #e3f2fd;
        color: #1565c0;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8em;
        margin: 2px;
    }
    .missing-tag {
        display: inline-block;
        background: #fce4ec;
        color: #b71c1c;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8em;
        margin: 2px;
    }
    .phase-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
    }
    .match-badge-green { color: #2e7d32; font-weight: bold; }
    .match-badge-orange { color: #e65100; font-weight: bold; }
    .match-badge-red { color: #b71c1c; font-weight: bold; }
    .job-card-html {
        background: linear-gradient(135deg, #ffffff, #f0f4ff);
        border-left: 5px solid #4a90e2;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(74,144,226,0.12);
        transition: box-shadow 0.2s;
    }
    .job-card-html:hover { box-shadow: 0 6px 20px rgba(74,144,226,0.22); }
    .job-card-title { font-size: 1.05em; font-weight: 700; color: #1a237e; margin-bottom: 4px; }
    .job-card-meta { font-size: 0.85em; color: #555; margin-bottom: 8px; }
    .job-score-pill {
        display: inline-block;
        background: linear-gradient(90deg, #43e97b, #38f9d7);
        color: #1b5e20;
        font-weight: 700;
        padding: 3px 14px;
        border-radius: 20px;
        font-size: 0.85em;
        margin-right: 8px;
    }
    .source-pill {
        display: inline-block;
        background: #e8eaf6;
        color: #283593;
        font-weight: 600;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.8em;
    }
    .apply-btn {
        display: inline-block;
        background: linear-gradient(90deg, #f093fb, #f5576c);
        color: white !important;
        font-weight: 700;
        padding: 8px 22px;
        border-radius: 25px;
        text-decoration: none !important;
        font-size: 0.9em;
        box-shadow: 0 3px 10px rgba(245,87,108,0.35);
        transition: opacity 0.2s;
        margin-top: 10px;
        letter-spacing: 0.5px;
    }
    .apply-btn:hover { opacity: 0.88; }
</style>
""", unsafe_allow_html=True)

st.title("💼 AI-Powered Job Finder Pro")
st.caption("Find jobs • Analyze resume match • Get career roadmap — Powered by Gemini AI")

# ─── SIDEBAR ─────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])

    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()

    if uploaded_file and uploaded_file.name not in st.session_state.processed_files:
        with st.spinner("Reading your resume with AI..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                res = requests.post("http://localhost:8000/extract-from-resume", files=files)
                if res.status_code == 200:
                    params = res.json()
                    st.session_state.role_input = params.get("role", "")
                    st.session_state.skills_input = ", ".join(params.get("skills", []))
                    st.session_state.exp_input = params.get("experience", 2)
                    st.session_state.loc_input = params.get("location", "")
                    # Store resume text for match explanations
                    st.session_state.resume_raw = uploaded_file.getvalue()
                    st.session_state.processed_files.add(uploaded_file.name)
                    st.session_state.run_search = True
                    st.success("✅ Resume parsed!")
                    st.rerun()
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Resume error: {e}")

    st.divider()
    st.header("🤖 AI Chat Assistant")
    chat_input = st.chat_input("e.g. I want a Senior Python job in Bangalore with 5 years exp")
    if chat_input:
        with st.spinner("AI analyzing..."):
            try:
                res = requests.post("http://localhost:8000/extract-params", json={"message": chat_input})
                if res.status_code == 200:
                    params = res.json()
                    st.session_state.role_input = params.get("role", "")
                    st.session_state.skills_input = ", ".join(params.get("skills", []))
                    st.session_state.exp_input = params.get("experience", 2)
                    st.session_state.loc_input = params.get("location", "")
                    st.session_state.run_search = True
                    st.rerun()
            except Exception as e:
                st.error(f"Chat error: {e}")

    st.divider()
    st.header("Your Profile")
    role = st.text_input("Job Role", key="role_input", placeholder="e.g. Data Engineer")
    skills_raw = st.text_input("Skills (comma separated)", key="skills_input", placeholder="e.g. Python, SQL")
    experience = st.number_input("Experience (years)", min_value=0, max_value=40, key="exp_input")
    location = st.text_input("Location (Optional)", key="loc_input", placeholder="e.g. Bangalore")

    with st.expander("🔍 AI Extraction Details"):
        st.write(f"**Role:** {st.session_state.get('role_input', '—')}")
        st.write(f"**Skills:** {st.session_state.get('skills_input', '—')}")
        st.write(f"**Exp:** {st.session_state.get('exp_input', 0)} yrs")

    find_button = st.button("🔍 Find Matching Jobs")

# ─── MAIN CONTENT TABS ───────────────────────────────────
tab_jobs, tab_advisor = st.tabs(["💼 Job Matches", "🧠 AI Career Advisor"])

# ═══════════════ TAB 1: JOB MATCHES ═══════════════════════
with tab_jobs:
    if find_button or st.session_state.get("run_search", False):
        st.session_state.run_search = False

        current_role = st.session_state.get("role_input", "")
        current_skills = st.session_state.get("skills_input", "")
        current_exp = st.session_state.get("exp_input", 0)
        current_loc = st.session_state.get("loc_input", "")

        if not current_role or not current_skills:
            st.error("⚠️ Please provide both **Role** and **Skills** in the sidebar.")
        else:
            skills_list = [s.strip() for s in current_skills.split(",") if s.strip()]
            with st.spinner("🔍 Fetching & ranking jobs with AI..."):
                try:
                    payload = {
                        "role": current_role,
                        "skills": skills_list,
                        "experience": int(current_exp),
                        "location": current_loc if current_loc else None
                    }
                    response = requests.post("http://localhost:8000/search-jobs", json=payload)

                    if response.status_code == 200:
                        results = response.json().get("jobs", [])
                        if not results:
                            st.warning("No matching jobs found. Try adjusting your search.")
                        else:
                            st.success(f"✅ Found **{len(results)}** matches from Naukri, LinkedIn & Indeed!")

                            # Store results for match explanation
                            st.session_state.job_results = results

                            # Styled HTML results table with Apply buttons
                            import html
                            source_colors = {"Naukri": "#fff3e0", "LinkedIn": "#e8f4fd", "Indeed": "#e8f5e9"}
                            
                            table_html = "<style>"
                            table_html += ".results-table { width:100%; border-collapse:collapse; font-size:0.86em; border-radius:12px; overflow:hidden; box-shadow:0 4px 16px rgba(0,0,0,0.08); }"
                            table_html += ".results-table thead tr { background: linear-gradient(90deg,#4a90e2,#764ba2); color:white; text-align:left; }"
                            table_html += ".results-table th { padding:10px 12px; }"
                            table_html += ".results-table td { padding:9px 12px; border-bottom:1px solid #f0f0f0; vertical-align:middle; }"
                            table_html += ".results-table tr:last-child td { border-bottom:none; }"
                            table_html += ".results-table tr:hover td { background:#f5f8ff; }"
                            table_html += ".score-cell { font-weight:700; color:#2e7d32; }"
                            table_html += ".src-badge { padding:2px 10px; border-radius:12px; font-weight:600; font-size:0.8em; }"
                            table_html += ".apply-mini { background:linear-gradient(90deg,#f093fb,#f5576c); color:white!important; padding:4px 14px; border-radius:20px; text-decoration:none!important; font-size:0.8em; font-weight:700; white-space:nowrap; }"
                            table_html += "</style>"
                            table_html += '<table class="results-table">'
                            table_html += '<thead><tr><th>#</th><th>Score</th><th>Source</th><th>Title</th><th>Company</th><th>Location</th><th>Apply</th></tr></thead>'
                            table_html += '<tbody>'
                            
                            for idx, job in enumerate(results):
                                row_bg = source_colors.get(job.get("source", ""), "#ffffff")
                                src_badge_color = {"Naukri":"#ff6f00","LinkedIn":"#0a66c2","Indeed":"#2164f3"}.get(job.get("source",""),"#555")
                                
                                safe_title = html.escape(job.get('title', ''))
                                safe_company = html.escape(job.get('company', ''))
                                safe_location = html.escape(job.get('location', ''))
                                safe_link = job.get('link', '#')

                                table_html += f'<tr style="background:{row_bg};">'
                                table_html += f'<td style="color:#999;">{idx+1}</td>'
                                table_html += f'<td class="score-cell">{job.get("score","")}</td>'
                                table_html += f'<td><span class="src-badge" style="background:{src_badge_color}22;color:{src_badge_color};">{job.get("source","")}</span></td>'
                                table_html += f'<td><b>{safe_title}</b></td>'
                                table_html += f'<td>{safe_company}</td>'
                                table_html += f'<td>📍 {safe_location}</td>'
                                table_html += f'<td><a href="{safe_link}" target="_blank" class="apply-mini">🚀 Apply</a></td>'
                                table_html += '</tr>'
                                
                            table_html += "</tbody></table>"
                            
                            st.markdown(table_html, unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)



                            st.subheader("📋 Detailed Job Cards")
                            has_resume = "resume_raw" in st.session_state

                            for i, job in enumerate(results[:10]):
                                rec_color = ""
                                # Colourful HTML job card
                                st.markdown(f"""
                                <div class="job-card-html">
                                    <div class="job-card-title">💼 {job['title']}</div>
                                    <div class="job-card-meta">
                                        🏢 <b>{job['company']}</b> &nbsp;|&nbsp;
                                        📍 {job['location']} &nbsp;|&nbsp;
                                        <span class="source-pill">{job['source']}</span>
                                        &nbsp;<span class="job-score-pill">⭐ {job['score']}</span>
                                    </div>
                                    <a href="{job['link']}" target="_blank" class="apply-btn">🚀 Apply Now →</a>
                                </div>
                                """, unsafe_allow_html=True)

                                # AI Match Explanation toggle
                                with st.expander(f"🔍 More details & AI Analysis — {job['title'][:40]}"):

                                    # AI Match Explanation
                                    if has_resume:
                                        if st.button(f"🔥 Explain This Match", key=f"explain_{i}"):
                                            with st.spinner("Generating AI match analysis..."):
                                                try:
                                                    # Get resume text via re-extraction (cached via session state)
                                                    files = {"file": (
                                                        list(st.session_state.processed_files)[0],
                                                        st.session_state.resume_raw,
                                                        "application/pdf"
                                                    )}
                                                    res_text = requests.post("http://localhost:8000/extract-from-resume", files=files).text
                                                    resume_text_raw = res_text  # Raw extracted text

                                                    exp_res = requests.post("http://localhost:8000/match-explanation", json={
                                                        "resume_text": current_skills + " " + current_role,
                                                        "job_title": job["title"],
                                                        "job_snippet": job.get("description", job["title"])[:500]
                                                    })
                                                    if exp_res.status_code == 200:
                                                        exp = exp_res.json()
                                                        score = exp.get("match_score", 0)
                                                        rec = exp.get("recommendation", "N/A")

                                                        if rec == "APPLY NOW":
                                                            rec_color = "match-badge-green"
                                                        elif rec == "WORTH TRYING":
                                                            rec_color = "match-badge-orange"
                                                        else:
                                                            rec_color = "match-badge-red"

                                                        st.write(f"**🎯 Match Score:** {score}/100")
                                                        st.write(f"**💡 Why This Matches:** {exp.get('why_this_job_matches', '')}")
                                                        st.markdown(f"**✅ Matching Skills:** " + " ".join([f'<span class="tag">{s}</span>' for s in exp.get("matching_skills", [])]), unsafe_allow_html=True)
                                                        if exp.get("skill_gaps"):
                                                            st.markdown(f"**❌ Skill Gaps:** " + " ".join([f'<span class="missing-tag">{s}</span>' for s in exp.get("skill_gaps", [])]), unsafe_allow_html=True)
                                                        st.markdown(f"**📣 Recommendation:** <span class='{rec_color}'>{rec}</span>", unsafe_allow_html=True)
                                                except Exception as e:
                                                    st.error(f"Match error: {e}")
                                    else:
                                        st.info("💡 Upload your resume to see an **AI Match Explanation** for this job!")
                    else:
                        st.error(f"Backend error: {response.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
                    st.info("Make sure the backend is running on http://localhost:8000")
    else:
        st.info("👈 Fill your profile and click **Find Matching Jobs** — or upload your resume!")

# ═══════════════ TAB 2: AI CAREER ADVISOR ══════════════════
with tab_advisor:
    st.header("🧠 AI Career Advisor")
    st.markdown("Tell the AI your dream role and it will give you a **complete roadmap** — required skills, missing skills, salary expectations, and top companies.")

    advisor_col1, advisor_col2 = st.columns([2, 1])
    with advisor_col1:
        target_role = st.text_input("🎯 What role do you want to become?", placeholder="e.g. SDET, Data Scientist, DevOps Engineer, Backend Developer")
    with advisor_col2:
        current_skills_advisor = st.text_input("Your current skills (optional)", placeholder="e.g. Python, Selenium")

    if st.button("🚀 Get My Career Roadmap", type="primary"):
        if not target_role:
            st.error("Please enter a target role!")
        else:
            with st.spinner(f"AI is building your roadmap for **{target_role}**... 🧠"):
                try:
                    skills_for_advice = [s.strip() for s in current_skills_advisor.split(",") if s.strip()] if current_skills_advisor else None
                    
                    # Also use profile skills if advisor skills are empty
                    if not skills_for_advice and st.session_state.get("skills_input"):
                        skills_for_advice = [s.strip() for s in st.session_state.get("skills_input", "").split(",") if s.strip()]

                    res = requests.post("http://localhost:8000/career-advisor", json={
                        "target_role": target_role,
                        "current_skills": skills_for_advice
                    })

                    if res.status_code == 200:
                        advice = res.json()

                        if "error" in advice:
                            st.error(advice["error"])
                        else:
                            st.success(f"✅ Career Roadmap for **{advice.get('target_role', target_role)}**")

                            # Summary
                            st.info(f"💬 {advice.get('summary', '')}")

                            # Salary + Companies
                            c1, c2 = st.columns(2)
                            with c1:
                                st.metric("💰 Avg Salary Range", advice.get("avg_salary_range", "N/A"))
                            with c2:
                                companies = ", ".join(advice.get("top_companies_hiring", []))
                                st.write(f"🏢 **Top Hiring Companies:** {companies}")

                            st.divider()

                            # Skills Grid
                            sc1, sc2, sc3 = st.columns(3)
                            with sc1:
                                st.subheader("✅ Must-Have Skills")
                                for skill in advice.get("must_have_skills", []):
                                    st.markdown(f'<span class="tag">✓ {skill}</span>', unsafe_allow_html=True)
                            with sc2:
                                st.subheader("⭐ Good-to-Have")
                                for skill in advice.get("good_to_have_skills", []):
                                    st.markdown(f'<span class="tag">★ {skill}</span>', unsafe_allow_html=True)
                            with sc3:
                                st.subheader("❌ Your Missing Skills")
                                missing = advice.get("missing_skills", [])
                                if missing:
                                    for skill in missing:
                                        st.markdown(f'<span class="missing-tag">✗ {skill}</span>', unsafe_allow_html=True)
                                else:
                                    st.success("🎉 You have all the required skills!")

                            st.divider()

                            # Roadmap
                            st.subheader("🗺️ Your Step-by-Step Roadmap")
                            for phase in advice.get("roadmap", []):
                                with st.expander(f"📌 {phase.get('phase', '')}"):
                                    st.write(f"**Action:** {phase.get('action', '')}")
                                    resources = phase.get("resources", [])
                                    if resources:
                                        st.write("**Resources:**")
                                        for r in resources:
                                            st.write(f"  → {r}")

                            # Find jobs for this role
                            st.divider()
                            if st.button(f"💼 Search Jobs for {target_role}", key="advisor_search_btn", type="primary", use_container_width=True):
                                st.session_state.role_input = target_role
                                if advice.get("must_have_skills"):
                                    st.session_state.skills_input = ", ".join(advice.get("must_have_skills", [])[:6])
                                st.session_state.exp_input = max(1, st.session_state.get("exp_input", 2))
                                st.session_state.run_search = True
                                # Switch user to Job Matches tab by showing a message
                                st.success("✅ Profile updated! Switch to **💼 Job Matches** tab to see results!")
                                st.rerun()
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")

    # AI Architecture Flowchart (Moved to inside Career Advisor tab)
    st.markdown("---")
    st.subheader("⚙️ How It Works — Powered By Gemini AI")
    ai_flow_html = """
<style>
.ai-flow-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #1e1e2f, #2a2a40);
    padding: 25px;
    border-radius: 15px;
    margin-top: 10px;
    color: white;
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
}
.flow-step {
    text-align: center;
    flex: 1;
    position: relative;
}
.flow-icon {
    font-size: 2.5em;
    background: linear-gradient(45deg, #4a90e2, #9013fe);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}
.flow-title {
    font-weight: 700;
    font-size: 0.9em;
    margin-bottom: 5px;
    color: #e0e0e0;
}
.flow-desc {
    font-size: 0.75em;
    color: #a0a0a0;
}
.flow-arrow {
    flex: 0.2;
    text-align: center;
    font-size: 1.5em;
    color: #555;
    animation: moveRight 1.5s infinite;
}
@keyframes moveRight {
    0% { transform: translateX(0); color: #555; }
    50% { transform: translateX(5px); color: #4a90e2; }
    100% { transform: translateX(0); color: #555; }
}
</style>

<div class="ai-flow-container">
    <div class="flow-step">
        <div class="flow-icon">📄</div>
        <div class="flow-title">1. Parse Profile</div>
        <div class="flow-desc">Gemini AI extracts skills<br>& experience from Resume</div>
    </div>
    <div class="flow-arrow">➔</div>
    <div class="flow-step">
        <div class="flow-icon">🕸️</div>
        <div class="flow-title">2. Web Scrape</div>
        <div class="flow-desc">Tavily Search API finds<br>live jobs (Naukri/Indeed)</div>
    </div>
    <div class="flow-arrow">➔</div>
    <div class="flow-step">
        <div class="flow-icon">🧠</div>
        <div class="flow-title">3. AI Matching</div>
        <div class="flow-desc">Gemini analyzes Job vs Resume<br>for Match Score & Skill Gaps</div>
    </div>
    <div class="flow-arrow">➔</div>
    <div class="flow-step">
        <div class="flow-icon">🚀</div>
        <div class="flow-title">4. Career Advisor</div>
        <div class="flow-desc">Builds actionable roadmaps<br>to achieve your dream role</div>
    </div>
</div>
"""
    st.markdown(ai_flow_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# Footer
st.markdown("Built with ❤️ using Streamlit, FastAPI, and Google Gemini.")
