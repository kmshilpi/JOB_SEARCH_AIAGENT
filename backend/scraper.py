import os
import requests
import json
import logging
from tavily import TavilyClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TavilyJobScraper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
        else:
            logger.warning("TAVILY_API_KEY not found. Job fetching will fail.")

    def fetch_jobs(self, role, skills, experience, location=None):
        """
        Fetch jobs from Naukri.com using Tavily Search API.
        """
        if not self.api_key:
            return []

        # Construct a search query focused on Naukri.com
        query = f'site:naukri.com "{role}" {" ".join(skills)} {experience} years experience'
        if location:
            query += f" in {location}"

        try:
            logger.info(f"Searching for jobs with Tavily: {query}")
            # Use search method to get results
            response = self.client.search(query=query, search_depth="basic", max_results=20)
            
            jobs = []
            results = response.get("results", [])
            
            for res in results:
                title = res.get("title", "")
                url = res.get("url", "")
                snippet = res.get("content", "")
                
                # Simple extraction of company name from title if possible (Naukri titles often follow 'Title at Company')
                company = "Naukri Listing"
                if " at " in title:
                    company = title.split(" at ")[-1].split(" - ")[0].strip()
                elif " | " in title:
                    company = title.split(" | ")[-1].strip()
                
                # Cleanup title (remove site suffix)
                clean_title = title.split(" - naukri.com")[0].split(" | ")[0].strip()
                
                jobs.append({
                    "title": clean_title,
                    "company": company,
                    "location": location if location else "India",
                    "link": url,
                    "description": snippet
                })
            
            logger.info(f"Successfully fetched {len(jobs)} jobs via Tavily.")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs via Tavily: {e}")
            return []

if __name__ == "__main__":
    # Test with environment variable
    scraper = TavilyJobScraper()
    test_jobs = scraper.fetch_jobs("Data Engineer", ["Python", "SQL"], 2)
    print(json.dumps(test_jobs[:2], indent=2))
