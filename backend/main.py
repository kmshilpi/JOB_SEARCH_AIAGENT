from fastapi import FastAPI, HTTPException, File, UploadFile
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
