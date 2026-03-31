# AI Job Finder

A simple, minimal AI-powered job finder that fetches relevant listings from Naukri.com and ranks them based on your profile using LLM (Gemini).

## Folder Structure
```
ai_job_finder/
├── backend/
│   ├── main.py        # FastAPI Server
│   ├── scraper.py     # Naukri Scraper
│   ├── ai_filter.py   # AI Scoring Logic
│   └── __init__.py
├── frontend/
│   └── app.py         # Streamlit UI
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (Optional but recommended for AI ranking)
- [Tavily API Key](https://tavily.com/) (Required for job searching)

### 2. Installation
Navigate to the project directory and install dependencies:
```bash
cd ai_job_finder
pip install -r requirements.txt
```

### 3. Environment Setup
Set your API keys:
```bash
export GEMINI_API_KEY="your_gemini_key"
export TAVILY_API_KEY="your_tavily_key"
```

### 4. Running the Application

**Step 1: Start the Backend Server**
```bash
# From the project root
python3 -m backend.main  # Runs on http://localhost:8000
```

**Step 2: Start the Frontend UI (in a new terminal)**
```bash
cd frontend
streamlit run app.py
```

## How it Works
1. **Scraping**: Fetches live jobs from Naukri.com using their internal JSON search API.
2. **AI Ranking**: Uses Gemini LLM to analyze job titles and descriptions against your provided role, skills, and experience.
3. **Caching**: Results are cached in-memory to avoid redundant API calls and save tokens.

## Example Input
- **Job Role**: Backend Developer
- **Skills**: Python, FastAPI, PostgreSQL
- **Experience**: 3 years

## Example Output
A table of jobs with a "Match Score" (e.g., 90%, 75%) and direct links to apply.
