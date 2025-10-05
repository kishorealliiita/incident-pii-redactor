#!/usr/bin/env python3
"""
Data collection script for FireHydrant
Fetches incidents, retrospectives, and related data from FireHydrant API
Generates JSONL files for testing the PII redaction pipeline

API Documentation: https://api.firehydrant.io
Requires: FIREHYDRANT_API_KEY, FIREHYDRANT_ORG_ID
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.settings import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

class FireHydrantCollector:
    """Collects data from FireHydrant API"""
    
    def __init__(self, api_key: str, org_id: str):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = "https://api.firehydrant.io"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def fetch_incidents(self, limit: int = 100, days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch incidents with optional date filtering"""
        url = f"{self.base_url}/v1/incidents"
        
        # Calculate date filter
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "limit": limit,
            "organization_id": self.org_id,
            "created_at_start": start_date.isoformat(),
            "created_at_end": end_date.isoformat()
        }
        
        all_incidents = []
        page_token = None
        
        while True:
            if page_token:
                params["starting_after"] = page_token
                
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                incidents = data.get("data", [])
                all_incidents.extend(incidents)
                
                logger.info(f"Fetched {len(incidents)} incidents (total: {len(all_incidents)})")
                
                # Check pagination
                has_more = data.get("has_more", False)
                if not has_more:
                    break
                    
                # Update page token for next request
                if incidents:
                    page_token = incidents[-1].get("id")
                else:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching incidents: {e}")
                break
                
        logger.info(f"Total incidents fetched: {len(all_incidents)}")
        return all_incidents
    
    def fetch_retrospectives(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch retrospectives"""
        url = f"{self.base_url}/v1/retrospectives"
        
        params = {
            "limit": limit,
            "organization_id": self.org_id
        }
        
        all_retrospectives = []
        page_token = None
        
        while True:
            if page_token:
                params["starting_after"] = page_token
                
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                retrospectives = data.get("data", [])
                all_retrospectives.extend(retrospectives)
                
                logger.info(f"Fetched {len(retrospectives)} retrospectives (total: {len(all_retrospectives)})")
                
                has_more = data.get("has_more", False)
                if not has_more:
                    break
                    
                if retrospectives:
                    page_token = retrospectives[-1].get("id")
                else:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching retrospectives: {e}")
                break
                
        return all_retrospectives
    
    def fetch_incident_tasks(self, incident_id: str) -> List[Dict[str, Any]]:
        """Fetch tasks for a specific incident"""
        url = f"{self.base_url}/v1/incidents/{incident_id}/tasks"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            tasks = data.get("data", [])
            
            logger.info(f"Fetched {len(tasks)} tasks for incident {incident_id}")
            return tasks
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching tasks for incident {incident_id}: {e}")
            return []
    
    def fetch_follow_ups(self, incident_id: str) -> List[Dict[str, Any]]:
        """Fetch follow-ups for a specific incident"""
        url = f"{self.base_url}/v1/incidents/{incident_id}/follow_ups"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            follow_ups = data.get("data", [])
            
            logger.info(f"Fetched {len(follow_ups)} follow-ups for incident {incident_id}")
            return follow_ups
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching follow-ups for incident {incident_id}: {e}")
            return []
    
    def enrich_incidents(self, incidents: List[Dict[str, Any]], include_full_data: bool = True) -> List[Dict[str, Any]]:
        """Enrich incidents with tasks, follow-ups, and other related data"""
        enriched_incidents = []
        
        for incident in incidents:
            incident_id = incident.get("id")
            
            enriched_incident = incident.copy()
            
            if include_full_data:
                # Add tasks and follow-ups
                tasks = self.fetch_incident_tasks(incident_id)
                follow_ups = self.fetch_follow_ups(incident_id)
                
                enriched_incident["tasks"] = tasks
                enriched_incident["follow_ups"] = follow_ups
                
            enriched_incidents.append(enriched_incident)
            
        return enriched_incidents

def save_to_jsonl(data: List[Dict[str, Any]], filename: str) -> None:
    """Save data to JSONL file"""
    with open(filename, 'w') as f:
        for item in data:
            json.dump(item, f)
            f.write('\n')
    
    logger.info(f"Saved {len(data)} records to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Collect FireHydrant data")
    parser.add_argument("--api-key", required=True, help="FireHydrant API key")
    parser.add_argument("--org-id", required=True, help="FireHydrant organization ID")
    parser.add_argument("--output-dir", default="./data/raw", help="Output directory")
    parser.add_argument("--limit", type=int, default=100, help="Max records to fetch")
    parser.add_argument("--days-back", type=int, default=30, help="Days of data to fetch")
    parser.add_argument("--include-full-data", action="store_true", help="Include tasks and follow-ups")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize collector
    collector = FireHydrantCollector(args.api_key, args.org_id)
    
    # Collect data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Fetch incidents
    logger.info("Fetching incidents...")
    incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
    
    if incidents:
        if args.include_full_data:
            incidents = collector.enrich_incidents(incidents, include_full_data=True)
        
        save_to_jsonl(incidents, f"{args.output_dir}/firehydrant_incidents_{timestamp}.jsonl")
    
    # Fetch retrospectives
    logger.info("Fetching retrospectives...")
    retrospectives = collector.fetch_retrospectives(limit=args.limit)
    
    if retrospectives:
        save_to_jsonl(retrospectives, f"{args.output_dir}/firehydrant_retrospectives_{timestamp}.jsonl")

if __name__ == "__main__":
    main()
