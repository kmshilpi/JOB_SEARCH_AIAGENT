from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import io
from dotenv import load_dotenv
from .scraper import TavilyJobScraper
from .ai_filter import AIFilter
import logging
import pypdf
import docx

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Job Finder API")

# ─── CORS Middleware ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI Job Finder API is running"}

# Models for input/output
class JobSearchRequest(BaseModel):
    role: str
    skills: List[str]
    experience: int
    location: Optional[str] = None

class JobResponse(BaseModel):
    title: str
    company: str
    location: str
    link: str
    score: str
    source: str

class SearchResult(BaseModel):
    jobs: List[JobResponse]

class ExtractionRequest(BaseModel):
    message: str

# Instances
scraper = TavilyJobScraper()
ai_filter = AIFilter()

# Simple In-memory Cache for demonstration
# Key: (role, tuple(skills), experience, location)
# Value: List of scored jobs
_cache = {}

@app.post("/search-jobs", response_model=SearchResult)
async def search_jobs(request: JobSearchRequest):
    """
    Search for jobs across multiple platforms and rank them using AI.
    """
    try:
        # Create a unique cache key
        cache_key = (request.role, tuple(sorted(request.skills)), request.experience, request.location)
        
        if cache_key in _cache:
            logger.info(f"Returning cached results for: {request.role}")
            return {"jobs": _cache[cache_key]}

        # 1. Fetch raw jobs from scraper
        raw_jobs = scraper.fetch_jobs(
            role=request.role,
            skills=request.skills,
            experience=request.experience,
            location=request.location
        )
        
        if not raw_jobs:
            return {"jobs": []}

        # 2. Score and refine jobs using AI
        user_profile = {
            "role": request.role,
            "skills": request.skills,
            "experience": request.experience,
            "location": request.location
        }
        scored_jobs = ai_filter.score_jobs(user_profile, raw_jobs)
        
        # 3. Cache and return results
        _cache[cache_key] = scored_jobs
        return {"jobs": scored_jobs}
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-params")
async def extract_params(request: ExtractionRequest):
    """
    Extract job search parameters from a natural language message.
    """
    try:
        params = ai_filter.extract_params(request.message)
        return params
    except Exception as e:
        logger.error(f"Parameter extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract parameters from message.")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

@app.post("/extract-from-resume")
async def extract_from_resume(file: UploadFile = File(...)):
    """
    Extract job search parameters from an uploaded resume (PDF/DOCX).
    """
    try:
        content = await file.read()
        filename = file.filename.lower()
        
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(content)
        elif filename.endswith(".docx"):
            text = extract_text_from_docx(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or DOCX.")
            
        logger.info(f"Extracted {len(text)} characters from {filename}")
        if len(text) < 100:
            logger.warning(f"Very little text extracted from {filename}. Content might be an image or complex layout.")
            logger.debug(f"Sample: {text[:200]}")
            
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the file. It might be a scanned image or empty.")
            
        params = ai_filter.extract_from_resume_text(text)
        return params
        
    except Exception as e:
        logger.error(f"Resume extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CareerAdvisorRequest(BaseModel):
    target_role: str
    current_skills: Optional[List[str]] = None


class MatchExplanationRequest(BaseModel):
    resume_text: str
    job_title: str
    job_snippet: str


@app.post("/career-advisor")
async def career_advisor(request: CareerAdvisorRequest):
    """
    AI Career Advisor: skill gap analysis + roadmap for any target role.
    """
    try:
        advice = ai_filter.get_career_advice(
            target_role=request.target_role,
            current_skills=request.current_skills
        )
        return advice
    except Exception as e:
        logger.error(f"Career advisor failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match-explanation")
async def match_explanation(request: MatchExplanationRequest):
    """
    AI Match Explanation: explain why a job matches a resume.
    """
    try:
        explanation = ai_filter.get_match_explanation(
            resume_text=request.resume_text,
            job_title=request.job_title,
            job_snippet=request.job_snippet
        )
        return explanation
    except Exception as e:
        logger.error(f"Match explanation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
