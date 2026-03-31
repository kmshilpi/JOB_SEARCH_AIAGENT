from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from backend.scraper import TavilyJobScraper
from backend.ai_filter import AIFilter
import logging

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

class SearchResult(BaseModel):
    jobs: List[JobResponse]

# Initialize components
# Use TAVILY_API_KEY from environment
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_KEY:
    logger.error("TAVILY_API_KEY not found in environment variables.")
    raise HTTPException(status_code=500, detail="Tavily API key is required.")
    
scraper = TavilyJobScraper(api_key=TAVILY_KEY)
# Use GEMINI_API_KEY from environment
ai_filter = AIFilter()

# Simple In-memory Cache for demonstration
# Key: (role, tuple(skills), experience, location)
# Value: List of scored jobs
_cache = {}

@app.post("/search-jobs", response_model=SearchResult)
async def search_jobs(request: JobSearchRequest):
    """
    Search for jobs on Naukri and rank them using AI.
    """
    cache_key = (request.role, tuple(sorted(request.skills)), request.experience, request.location)
    
    if cache_key in _cache:
        logger.info("Returning results from cache.")
        return {"jobs": _cache[cache_key]}

    try:
        # 1. Fetch jobs from Naukri
        jobs = scraper.fetch_jobs(
            role=request.role, 
            skills=request.skills, 
            experience=request.experience, 
            location=request.location
        )
        
        if not jobs:
            return {"jobs": []}

        # 2. Score jobs with AI
        user_profile = {
            "role": request.role,
            "skills": request.skills,
            "experience": request.experience
        }
        scored_jobs = ai_filter.score_jobs(user_profile, jobs)

        # 3. Cache and return
        # Limit to top 20 as per requirement
        final_jobs = scored_jobs[:20]
        _cache[cache_key] = final_jobs
        
        return {"jobs": final_jobs}

    except Exception as e:
        logger.error(f"Search jobs failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during the job search.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
