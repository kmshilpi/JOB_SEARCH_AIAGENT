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
        Fetch jobs from Naukri.com, LinkedIn, and Indeed by performing separate searches.
        """
        if not self.api_key:
            return []

        sources_configs = [
            {"name": "Naukri", "site": "site:naukri.com"},
            {"name": "LinkedIn", "site": "site:linkedin.com/jobs"},
            {"name": "Indeed", "site": "site:indeed.com"}
        ]
        
        all_jobs = []
        
        for config in sources_configs:
            query = f'{config["site"]} "{role}" {" ".join(skills)} {experience} years experience'
            if location:
                query += f" in {location}"
            
            try:
                logger.info(f"Searching {config['name']} via Tavily: {query}")
                # Fetch up to 10-15 results per source to get a good mix
                response = self.client.search(query=query, search_depth="basic", max_results=15)
                results = response.get("results", [])
                
                for res in results:
                    title = res.get("title", "")
                    url = res.get("url", "")
                    snippet = res.get("content", "")
                    
                    # Double check if the URL actually belongs to the intended site
                    if config["site"].split("site:")[1] not in url:
                        continue
                        
                    source = config["name"]
                    company = f"{source} Listing"
                    
                    # Refined extraction of company name
                    if " at " in title:
                        parts = title.split(" at ")
                        company = parts[-1].split(" - ")[0].split(" | ")[0].strip()
                    elif " | " in title:
                        company = title.split(" | ")[-1].strip()
                    elif " - " in title:
                        parts = title.split(" - ")
                        if len(parts) > 1:
                             company = parts[1].strip()

                    # Cleanup title
                    clean_title = title
                    for suffix in [" - naukri.com", " | LinkedIn", " - Indeed", "Jobs | LinkedIn"]:
                        clean_title = clean_title.replace(suffix, "")
                    clean_title = clean_title.split(" - ")[0].split(" | ")[0].strip()
                    
                    all_jobs.append({
                        "title": clean_title,
                        "company": company,
                        "location": location if location else "India",
                        "link": url,
                        "description": snippet,
                        "source": source
                    })
            except Exception as e:
                logger.error(f"Error searching {config['name']} via Tavily: {e}")

        logger.info(f"Successfully fetched {len(all_jobs)} jobs total from multiple sources.")
        return all_jobs

if __name__ == "__main__":
    # Test with environment variable
    scraper = TavilyJobScraper()
    test_jobs = scraper.fetch_jobs("Data Engineer", ["Python", "SQL"], 2)
    print(json.dumps(test_jobs[:2], indent=2))
