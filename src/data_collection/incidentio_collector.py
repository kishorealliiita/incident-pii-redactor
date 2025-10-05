#!/usr/bin/env python3
"""
Data collection script for Incident.io
Fetches incidents, post-mortems, and timeline events from the Incident.io API
Generates JSONL files for testing the PII redaction pipeline

API Documentation: https://api.incident.io
Requires: INCIDENT_IO_API_KEY, INCIDENT_IO_WORKSPACE_ID
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

class IncidentIOCollector:
    """Collects data from Incident.io API"""
    
    def __init__(self, api_key: str, workspace_id: str):
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.base_url = "https://api.incident.io"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def fetch_incidents(self, limit: int = 100, days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch incidents with optional date filtering"""
        url = f"{self.base_url}/v2/incidents"
        
        # Calculate date filter
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "limit": limit,
            "page_size": 50,  # API max
            "workspace_id": self.workspace_id,
            # Note: Incident.io handles date filtering differently - may need to adjust
        }
        
        all_incidents = []
        page_token = None
        
        while True:
            if page_token:
                params["page_token"] = page_token
                
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                incidents = data.get("incidents", [])
                all_incidents.extend(incidents)
                
                logger.info(f"Fetched {len(incidents)} incidents (total: {len(all_incidents)})")
                
                # Check if there are more pages
                page_info = data.get("pagination", {})
                page_token = page_info.get("page_token")
                if not page_token:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching incidents: {e}")
                break
                
        logger.info(f"Total incidents fetched: {len(all_incidents)}")
        return all_incidents
    
    def fetch_postmortems(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch post-mortems"""
        url = f"{self.base_url}/v2/post_mortems"
        
        params = {
            "limit": limit,
            "workspace_id": self.workspace_id
        }
        
        all_postmortems = []
        page_token = None
        
        while True:
            if page_token:
                params["page_token"] = page_token
                
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                postmortems = data.get("post_mortems", [])
                all_postmortems.extend(postmortems)
                
                logger.info(f"Fetched {len(postmortems)} post-mortems (total: {len(all_postmortems)})")
                
                page_info = data.get("pagination", {})
                page_token = page_info.get("page_token")
                if not page_token:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching post-mortems: {e}")
                break
                
        return all_postmortems
    
    def fetch_timeline_events(self, incident_id: str) -> List[Dict[str, Any]]:
        """Fetch timeline events for a specific incident"""
        url = f"{self.base_url}/v2/timeline_events"
        
        params = {
            "incident_id": incident_id,
            "workspace_id": self.workspace_id
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            events = data.get("timeline_events", [])
            
            logger.info(f"Fetched {len(events)} timeline events for incident {incident_id}")
            return events
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching timeline events for {incident_id}: {e}")
            return []
    
    def enrich_incidents_with_timeline(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich incidents with their timeline events"""
        enriched_incidents = []
        
        for incident in incidents:
            incident_id = incident.get("id")
            timeline_events = self.fetch_timeline_events(incident_id)
            
            enriched_incident = incident.copy()
            enriched_incident["timeline_events"] = timeline_events
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
    parser = argparse.ArgumentParser(description="Collect Incident.io data")
    parser.add_argument("--api-key", required=True, help="Incident.io API key")
    parser.add_argument("--workspace-id", required=True, help="Incident.io workspace ID")
    parser.add_argument("--output-dir", default="./data/raw", help="Output directory")
    parser.add_argument("--limit", type=int, default=100, help="Max records to fetch")
    parser.add_argument("--days-back", type=int, default=30, help="Days of data to fetch")
    parser.add_argument("--include-timeline", action="store_true", help="Include timeline events")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize collector
    collector = IncidentIOCollector(args.api_key, args.workspace_id)
    
    # Collect data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Fetch incidents
    logger.info("Fetching incidents...")
    incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
    
    if incidents:
        save_to_jsonl(incidents, f"{args.output_dir}/incidentio_incidents_{timestamp}.jsonl")
    
    # Fetch post-mortems
    logger<｜tool▁sep｜>info("Fetching postmortems...")
    postmortems = collector.fetch_postmortems(limit=args.limit)
    
    if postmortems:
        save_to_jsonl(postmortems, f"{args.output_dir}/incidentio_postmortems_{timestamp}.jsonl")
    
    # Enrich incidents with timeline if requested
    if args.include_timeline and incidents:
        logger.info("Enriching incidents with timeline events...")
        enriched_incidents = collector.enrich_incidents_with_timeline(incidents[:10])  # Limit for API calls
        save_to_jsonl(enriched_incidents, f"{args.output_dir}/incidentio_enriched_incidents_{timestamp}.jsonl")

if __name__ == "__main__":
    main()
