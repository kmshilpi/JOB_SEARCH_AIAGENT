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
        Score a list of jobs, extract correct company names, and specific locations using Gemini.
        """
        if not self.api_key or not jobs:
            # Bypass AI filtering if key is missing or no jobs
            for job in jobs:
                job["score"] = "N/A (AI Disabled)"
            return jobs

        # Prepare jobs for AI processing
        prepared_jobs = []
        for i, job in enumerate(jobs):
            prepared_jobs.append({
                "index": i,
                "title": job.get("title", ""),
                "url": job.get("link", ""),
                "snippet": job.get("description", "")[:250],
                "current_company": job.get("company", ""),
                "current_location": job.get("location", "")
            })

        prompt = f"""
        Act as a professional recruiter. Rank the following job listings and extract the correct company name and SPECIFIC location for each.
        
        Candidate Profile:
        - Desired Role: {user_profile['role']}
        - Skills: {', '.join(user_profile['skills'])}
        - Experience: {user_profile['experience']} years
        
        Jobs to Process:
        {json.dumps(prepared_jobs, indent=2)}
        
        For each job index:
        1. **Extract Company Name**: Identify the actual company hiring. Look at title, snippet, and URL path. Use a specific name, not generic site names.
        2. **Extract Specific Location**: Identify the city (e.g., Gurgaon, Noida, Bangalore, Delhi, Pune, Mumbai, Remote). 
           - Look at the TITLE, SNIPPET, and URL.
           - If it just says "India", try to find a more specific city. 
           - If definitely not found, use "{user_profile.get('location') if user_profile.get('location') else 'Remote/India'}".
        3. **Score**: 0-100 based on relevance.
        
        Return the result as a raw JSON list of objects:
        [
          {{"index": 0, "company": "Exact Company", "location": "Specific City", "score": 85}},
          ...
        ]
        Do not include any text other than the JSON list.
        """
        
        try:
            logger.info("Scoring jobs and extracting details with AI...")
            response = self.client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            result_text = response.text.strip()
            
            # Clean up potential markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[-1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[-1].split("```")[0]
                
            ai_results = json.loads(result_text)
            
            # Create a map for easy lookup
            results_map = {res["index"]: res for res in ai_results}
            
            # Update jobs with AI results
            scored_jobs = []
            for i, job in enumerate(jobs):
                ai_res = results_map.get(i, {})
                score = ai_res.get("score", 0)
                company = ai_res.get("company", job.get("company"))
                location = ai_res.get("location", job.get("location"))
                
                # Validation to avoid generic fallbacks
                if not company or "Generic" in company or "Unspecified" in company:
                     company = job.get("company")
                if not location or location.lower() == "india":
                     location = job.get("location")
                
                job["score"] = f"{score}%"
                job["company"] = company
                job["location"] = location
                scored_jobs.append(job)
                
            # Sort by score descending
            scored_jobs.sort(key=lambda x: int(x["score"].replace("%", "") if "%" in x["score"] else 0), reverse=True)
            return scored_jobs
            
        except Exception as e:
            logger.error(f"Error scoring jobs with AI: {e}")
            # Fallback
            for job in jobs:
                if "score" not in job:
                    job["score"] = "Error"
            return jobs

    def extract_params(self, user_message: str) -> Dict:
        """
        Extract job search parameters from a user's natural language message.
        """
        if not self.api_key:
            return {}

        prompt = f"""
        Extract job search parameters from the following user message:
        "{user_message}"
        
        Return the result as a raw JSON object with the following keys:
        - role (string, default "Software Engineer")
        - skills (list of strings, default ["Python"])
        - experience (integer, default 2)
        - location (string, default "India")
        
        Example Output:
        {{
          "role": "Data Scientist",
          "skills": ["Python", "TensorFlow", "Pandas"],
          "experience": 3,
          "location": "Bangalore"
        }}
        
        Do not include any text other than the JSON object.
        """
        
        try:
            logger.info(f"Extracting parameters from message: {user_message}")
            response = self.client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            params_text = response.text.strip()
            
            # Clean up potential markdown code blocks
            if "```json" in params_text:
                params_text = params_text.split("```json")[-1].split("```")[0]
            elif "```" in params_text:
                params_text = params_text.split("```")[-1].split("```")[0]
                
            params = json.loads(params_text)
            return params
            
        except Exception as e:
            logger.error(f"Error extracting params with AI: {e}")
            return {
                "role": "Software Engineer",
                "skills": ["Python"],
                "experience": 2,
                "location": "India"
            }

    def extract_from_resume_text(self, resume_text: str) -> Dict:
        """
        Extract job search parameters from a long resume text using AI.
        """
        if not self.api_key:
            return {}

        prompt = f"""
        Act as an Expert Technical Recruiter with 20 years of experience. Your task is to analyze the provided resume text and extract precise search parameters to find the candidate's next PERFECT job.
        
        Resume Content:
        {resume_text[:8000]}
        
        CRITICAL INSTRUCTIONS:
        1. **role**: Extract the most specific and senior job title. For example, if they are a "Senior Python Developer", use that, NOT just "Software Engineer".
        2. **skills**: Extract ALL technical skills, languages, frameworks, and tools. Prioritize the ones most relevant to their recent experience. Return at least 10 skills if available.
        3. **experience**: Precisely calculate total years of professional experience. Look at the start and end dates of all roles. Round to the nearest whole number.
        4. **location**: Identify the current city or target city mentioned. Default to "India" only if absolutely no city is found.
        
        OUTPUT FORMAT (Raw JSON only):
        {{
          "role": "Specific Senior Title",
          "skills": ["Skill1", "Skill2", "Skill3", "Skill4", "Skill5", "Skill6", "Skill7", "Skill8", "Skill9", "Skill10"],
          "experience": 8,
          "location": "City Name"
        }}
        
        Return ONLY the JSON object. No preamble, no explanation.
        """
        
        try:
            logger.info("Extracting parameters from resume text with AI (1.5-flash)...")
            response = self.client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            params_text = response.text.strip()
            
            # Clean up potential markdown code blocks
            if "```json" in params_text:
                params_text = params_text.split("```json")[-1].split("```")[0]
            elif "```" in params_text:
                params_text = params_text.split("```")[-1].split("```")[0]
                
            params = json.loads(params_text)
            return params
            
        except Exception as e:
            logger.error(f"Error extracting params from resume: {e}")
            return {
                "role": "",
                "skills": [],
                "experience": 0,
                "location": "India"
            }
