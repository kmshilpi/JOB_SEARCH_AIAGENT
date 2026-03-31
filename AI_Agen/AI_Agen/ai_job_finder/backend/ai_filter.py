import os
from google import genai
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIFilter:
    def __init__(self, api_key: str = None):
        # Use provided key or fallback to env
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. AI filtering will be bypassed.")
        else:
            self.client = genai.Client(api_key=self.api_key)

    def score_jobs(self, user_profile: Dict, jobs: List[Dict]) -> List[Dict]:
        """
        Score a list of jobs based on user profile using Gemini.
        """
        if not self.api_key or not jobs:
            # Bypass AI filtering if key is missing or no jobs
            for job in jobs:
                job["score"] = "N/A (AI Disabled)"
            return jobs

        # To save tokens and time, we'll process jobs in one go or batches
        # For simplicity, we'll ask the AI to return scores for each job index
        
        prompt = f"""
        Act as a professional recruiter. Rank the following job listings based on their relevance to a candidate's profile.
        
        Candidate Profile:
        - Desired Role: {user_profile['role']}
        - Skills: {', '.join(user_profile['skills'])}
        - Experience: {user_profile['experience']} years
        
        Jobs to Rank:
        {json.dumps([{i: j['title'] + " at " + j['company']} for i, j in enumerate(jobs)], indent=2)}
        
        For each job index, provide a score from 0-100 based on:
        1. Skill match (50%)
        2. Role similarity (30%)
        3. Experience match (20%)
        
        Return the result as a raw JSON list of scores in the exact same order as the input jobs.
        Example: [85, 40, 92, ...]
        Do not include any text other than the JSON list.
        """
        
        try:
            logger.info("Scoring jobs with AI...")
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            scores_text = response.text.strip()
            
            # Clean up potential markdown code blocks
            if "```json" in scores_text:
                scores_text = scores_text.split("```json")[-1].split("```")[0]
            elif "```" in scores_text:
                scores_text = scores_text.split("```")[-1].split("```")[0]
                
            scores = json.loads(scores_text)
            
            # Match scores to jobs
            scored_jobs = []
            for i, job in enumerate(jobs):
                score = scores[i] if i < len(scores) else 0
                job["score"] = f"{score}%"
                scored_jobs.append(job)
                
            # Sort by score descending
            scored_jobs.sort(key=lambda x: int(x["score"].replace("%", "") if "%" in x["score"] else 0), reverse=True)
            return scored_jobs
            
        except Exception as e:
            logger.error(f"Error scoring jobs with AI: {e}")
            # Fallback to original order
            for job in jobs:
                job["score"] = "Error"
            return jobs
