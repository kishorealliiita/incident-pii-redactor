#!/usr/bin/env python3
"""
Data collection script for Blameless
Fetches incidents, timeline events, and analysis data from Blameless GraphQL API

API Documentation: Blameless GraphQL API
Requires: BLAMELESS_API_KEY
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

class BlamelessCollector:
    """Collects data from Blameless GraphQL API"""
    
    def __init__(self, api_key: str, workspace_id: str):
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.base_url = "https://api.blameless.com/graphql"  # Update with actual endpoint
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def fetch_incidents(self, limit: int = 100, days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch incidents with timeline events and analysis"""
        query = """
        query GetIncidents($workspaceId: ID!, $limit: Int, $createdAtGte: ISO8601DateTime, $createdAtLte: ISO8601DateTime) {
          incidents(
            workspaceId: $workspaceId
            limit: $limit
            createdAt: { gte: $createdAtGte, lte: $createdAtLte }
          ) {
            id
            title
            description
            status
            severity
            createdAt
            updatedAt
            resolvedAt
            
            # Assignee and team information
            assignee {
              id
              name
              email
            }
            team {
              id
              name
            }
            
            # Timeline events with full context
            timelineEvents {
              id
              type
              title
              description
              createdAt
              author {
                id
                name
                email
              }
              metadata
            }
            
            # Analysis data
            analysis {
              id
              rootCause
              contributingFactors
              lessonsLearned
              actionsTaken
              recommendations
              createdAt
              authors {
                id
                name
                email
              }
            }
            
            # Post-mortem data
            postMortem {
              id
              title
              summary
              detailedAnalysis
              recommendations
              actionItems {
                id
                title
                description
                assignee {
                  id
                  name
                  email
                }
                status
                dueDate
              }
              createdAt
              updatedAt
            }
            
            # Custom fields and tags
            customFields {
              id
              name
              value
              type
            }
            tags {
              id
              name
              color
            }
            
            # Metrics and KPIs
            metrics {
              incidentId
              mttr
              mtbf
              impactScore
              cost
            }
          }
        }
        """
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        variables = {
            "workspaceId": self.workspace_id,
            "limit": limit,
            "createdAtGte": start_date.isoformat(),
            "createdAtLte": end_date.isoformat()
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
                
            incidents = data.get("data", {}).get("incidents", [])
            
            logger.info(f"Fetched {len(incidents)} incidents from Blameless")
            return incidents
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error with GraphQL request: {e}")
            return []
    
    def fetch_post_mortems(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch standalone post-mortems"""
        query = """
        query GetPostMortems($workspaceId: ID!, $limit: Int) {
          postMortems(workspaceId: $workspaceId, limit: $limit) {
            id
            title
            summary
            incident {
              id
              title
              description
              status
            }
            
            # Detailed sections
            detailedAnalysis {
              whatHappened
              timeline
              rootCause
              contributingFactors
              impact
            }
            
            # Action items and recommendations
            actionItems {
              id
              title
              description
              priority
              status
              assignee {
                id
                name
                email
              }
              dueDate
              createdAt
              updatedAt
            }
            
            recommendations {
              id
              category
              title
              description
              priority
              status
            }
            
            # Authors and approval
            authors {
              id
              name
              email
            }
            
            # Review and approval workflow
            reviews {
              id
              reviewer {
                id
                name
                email
              }
              status
              comments
              createdAt
            }
            
            # Metadata
            tags {
              id
              name
            }
            
            createdAt
            updatedAt
            publishedAt
            
            # Metrics
            metrics {
              timeToComplete
              reviewCount
              actionItemCount
            }
          }
        }
        """
        
        variables = {
            "workspaceId": self.workspace_id,
            "limit": limit
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
                
            post_mortems = data.get("data", {}).get("postMortems", [])
            
            logger.info(f"Fetched {len(post_mortems)} post-mortems from Blameless")
            return post_mortems
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching post-mortems: {e}")
            return []
    
    def fetch_incident_analysis(self, incident_id: str) -> Dict[str, Any]:
        """Fetch detailed analysis for a specific incident"""
        query = """
        query GetIncidentAnalysis($incidentId: ID!) {
          incident(id: $incidentId) {
            id
            title
            
            analysis {
              rootCause
              contributingFactors
              impactAssessment
              timelineAnalysis
              
              # Human factors
              humanFactors {
                category
                description
                severity
              }
              
              # Process issues
              processIssues {
                category
                description
                recommendations
              }
              
              # Technical analysis
              technicalFactors {
                category
                description
                remediation
              }
              
              # Recommendations
              recommendations {
                id
                category
                title
                description
                priority
                effort
                impact
              }
            }
            
            # Timeline with analysis context
            detailedTimeline {
              id
              timestamp
              event
              category
              impact
              analysis
              actors {
                id
                name
                role
              }
            }
          }
        }
        """
        
        variables = {
            "incidentId": incident_id
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return {}
                
            incident = data.get("data", {}).get("incident", {})
            
            logger.info(f"Fetched detailed analysis for incident {incident_id}")
            return incident
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching incident analysis: {e}")
            return {}

def save_to_jsonl(data: List[Dict[str, Any]], filename: str) -> None:
    """Save data to JSONL file"""
    with open(filename, 'w') as f:
        for item in data:
            json.dump(item, f)
            f.write('\n')
    
    logger.info(f"Saved {len(data)} records to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Collect Blameless data")
    parser.add_argument("--api-key", required=True, help="Blameless API key")
    parser.add_argument("--workspace-id", required=True, help="Blameless workspace ID")
    parser.add_argument("--output-dir", default="./data/raw", help="Output directory")
    parser.add_argument("--limit", type=int, default=100, help="Max records to fetch")
    parser.add_argument("--days-back", type=int, default=30, help="Days of data to fetch")
    parser.add_argument("--include-analysis", action="store_true", help="Include detailed analysis")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize collector
    collector = BlamelessCollector(args.api_key, args.workspace_id)
    
    # Collect data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Fetch incidents
    logger.info("Fetching incidents...")
    incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
    
    if incidents:
        save_to_jsonl(incidents, f"{args.output_dir}/blameless_incidents_{timestamp}.jsonl")
    
    # Fetch post-mortems
    logger.info("Fetching post-mortems...")
    post_mortems = collector.fetch_post_mortems(limit=args.limit)
    
    if post_mortems:
        save_to_jsonl(post_mortems, f"{args.output_dir}/blameless_postmortems_{timestamp}.jsonl")
    
    # Fetch detailed analysis for first few incidents if requested
    if args.include_analysis and incidents:
        logger.info("Fetching detailed analysis...")
        detailed_incidents = []
        
        for incident in incidents[:5]:  # Limit to avoid excessive API calls
            incident_id = incident.get("id")
            detailed = collector.fetch_incident_analysis(incident_id)
            if detailed:
                detailed_incidents.append(detailed)
        
        if detailed_incidents:
            save_to_jsonl(detailed_incidents, f"{args.output_dir}/blameless_detailed_analysis_{timestamp}.jsonl")

if __name__ == "__main__":
    main()
