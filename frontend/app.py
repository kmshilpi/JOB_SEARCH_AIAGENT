import streamlit as st
import requests
import pandas as pd
import json

# Page config
st.set_page_config(page_title="AI Job Finder", page_icon="💼", layout="wide")

# Custom CSS for modern look
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
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
    .score-badge {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

st.title("💼 AI-Powered Job Finder")
st.markdown("Find the best job matches based on your profile using Naukri.com and AI ranking.")

# Sidebar for inputs
with st.sidebar:
    st.header("📄 Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
    
    # Track processed files to avoid infinite loops with st.rerun()
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()

    if uploaded_file and uploaded_file.name not in st.session_state.processed_files:
        with st.spinner("Extracting info from your resume..."):
            try:
                # Call resume extraction endpoint
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                resume_res = requests.post("http://localhost:8000/extract-from-resume", files=files)
                
                if resume_res.status_code == 200:
                    params = resume_res.json()
                    # Directly update session state keys used by widgets
                    st.session_state.role_input = params.get("role", "")
                    st.session_state.skills_input = ", ".join(params.get("skills", []))
                    st.session_state.exp_input = params.get("experience", 2)
                    st.session_state.loc_input = params.get("location", "")
                    
                    st.session_state.processed_files.add(uploaded_file.name)
                    st.session_state.run_search = True
                    st.rerun()
                else:
                    st.error(f"Failed to parse resume: {resume_res.text}")
            except Exception as e:
                st.error(f"Resume error: {e}")

    st.divider()
    st.header("🤖 AI Chat Assistant")
    st.info("Tell the AI what kind of job you're looking for, or upload a resume above!")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    chat_input = st.chat_input("e.g. I need a Remote Python Developer job with 5 years experience in Bangalore")
    
    if chat_input:
        with st.spinner("AI is analyzing your request..."):
            try:
                # Call extraction endpoint
                extract_url = "http://localhost:8000/extract-params"
                extract_res = requests.post(extract_url, json={"message": chat_input})
                
                if extract_res.status_code == 200:
                    params = extract_res.json()
                    # Directly update session state keys
                    st.session_state.role_input = params.get("role", "")
                    st.session_state.skills_input = ", ".join(params.get("skills", []))
                    st.session_state.exp_input = params.get("experience", 2)
                    st.session_state.loc_input = params.get("location", "")
                    
                    st.session_state.run_search = True
                    st.rerun()
                else:
                    st.error("AI failed to understand. Please fill manually.")
            except Exception as e:
                st.error(f"Chat error: {e}")

    st.divider()
    st.header("Your Profile")
    
    # Use 'key' to link widgets directly to session state
    role = st.text_input("Job Role", key="role_input", placeholder="e.g. Data Engineer")
    skills_raw = st.text_input("Skills (comma separated)", key="skills_input", placeholder="e.g. Python, SQL")
    experience = st.number_input("Experience (years)", min_value=0, max_value=40, key="exp_input")
    location = st.text_input("Location (Optional)", key="loc_input", placeholder="e.g. Bangalore")
    
    with st.expander("🔍 AI Extraction Details"):
        st.write(f"**Extracted Role:** {st.session_state.get('role_input', 'None')}")
        st.write(f"**Extracted Skills:** {st.session_state.get('skills_input', 'None')}")
        st.write(f"**Extracted Exp:** {st.session_state.get('exp_input', 'None')} years")
    
    find_button = st.button("Find Matching Jobs")

# Main content area
# Trigger search if button clicked OR auto-search flag is set
if find_button or st.session_state.get("run_search", False):
    # Reset auto-search flag
    st.session_state.run_search = False
    
    # Get current values from widgets (which are in session state via keys)
    current_role = st.session_state.get("role_input", "")
    current_skills = st.session_state.get("skills_input", "")
    current_exp = st.session_state.get("exp_input", 0)
    current_loc = st.session_state.get("loc_input", "")

    if not current_role or not current_skills:
        st.error("Please provide both Role and Skills.")
    else:
        skills_list = [s.strip() for s in current_skills.split(",")]
        
        with st.spinner("Fetching and ranking jobs..."):
            try:
                # Backend API details
                api_url = "http://localhost:8000/search-jobs"
                payload = {
                    "role": current_role,
                    "skills": skills_list,
                    "experience": int(current_exp),
                    "location": current_loc if current_loc else None
                }
                
                response = requests.post(api_url, json=payload)
                
                if response.status_code == 200:
                    results = response.json().get("jobs", [])
                    
                    if not results:
                        st.warning("No matching jobs found. Try adjusting your search.")
                    else:
                        st.success(f"Found {len(results)} matches from multiple sources!")
                        
                        # Display as a table
                        df = pd.DataFrame(results)
                        df = df[["score", "source", "title", "company", "location", "link"]]
                        st.table(df)
                        
                        st.subheader("Direct Links")
                        for job in results[:10]:
                            with st.expander(f"{job['title']} @ {job['company']} [{job['source']}] - {job['score']}"):
                                st.write(f"**Location:** {job['location']}")
                                st.write(f"**Source:** {job['source']}")
                                st.write(f"[Apply now]({job['link']})")
                else:
                    st.error(f"Error from backend: {response.text}")
            
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
                st.info("Make sure the backend server is running on http://localhost:8000")

else:
    st.info("🤖 **Try the AI Chat Assistant in the sidebar! Just say what you're looking for, or fill the fields manually.**")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, FastAPI, and Google Gemini.")
