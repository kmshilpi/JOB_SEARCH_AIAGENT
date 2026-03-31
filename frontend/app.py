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
    st.header("Your Profile")
    role = st.text_input("Job Role", placeholder="e.g. Data Engineer, Backend Developer")
    skills_raw = st.text_input("Skills (comma separated)", placeholder="e.g. Python, SQL, FastAPI")
    experience = st.number_input("Experience (years)", min_value=0, max_value=40, value=2)
    location = st.text_input("Location (Optional)", placeholder="e.g. Bangalore, Remote")
    
    find_button = st.button("Find Matching Jobs")

# Main content area
if find_button:
    if not role or not skills_raw:
        st.error("Please provide both Role and Skills.")
    else:
        skills = [s.strip() for s in skills_raw.split(",")]
        
        with st.spinner("Fetching and ranking jobs..."):
            try:
                # Backend API details
                # Assuming backend runs on localhost:8000
                api_url = "https://job-search-aiagent.onrender.com/search-jobs"
                payload = {
                    "role": role,
                    "skills": skills,
                    "experience": int(experience),
                    "location": location if location else None
                }
                
                response = requests.post(api_url, json=payload)
                
                if response.status_code == 200:
                    results = response.json().get("jobs", [])
                    
                    if not results:
                        st.warning("No matching jobs found. Try adjusting your search.")
                    else:
                        st.success(f"Found {len(results)} matches!")
                        
                        # Display as a table with links
                        df = pd.DataFrame(results)
                        # Reorder columns
                        df = df[["score", "title", "company", "location", "link"]]
                        
                        # Modern display: Cards (optional) or Table
                        st.table(df)
                        
                        # Or use a more interactive approach with column config
                        st.subheader("Direct Links")
                        for job in results:
                            with st.expander(f"{job['title']} @ {job['company']} - {job['score']}"):
                                st.write(f"**Location:** {job['location']}")
                                st.write(f"[Apply on Naukri.com]({job['link']})")
                else:
                    st.error(f"Error from backend: {response.text}")
            
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
                st.info("Make sure the backend server is running on http://localhost:8000")

else:
    st.info("Enter your profile details in the sidebar and click 'Find Matching Jobs'.")

# Footer
st.markdown("---")
st.markdown("Built with  using Streamlit, FastAPI, and Google Gemini.")
