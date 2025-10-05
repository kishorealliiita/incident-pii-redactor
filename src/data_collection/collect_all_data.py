#!/usr/bin/env python3
"""
Batch data collection script for all platforms
Collects incident data from multiple platforms in one run

Usage:
    python collect_all_data.py --platforms incidentio firehydrant rootly --days-back 7
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.settings import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Import all collection modules
from collect_incidentio_data import IncidentIOCollector
from collect_firehydrant_data import FireHydrantCollector  
from collect_rootly_data import RootlyCollector
from collect_blameless_data import BlamelessCollector
from collect_pagerduty_data import PagerDutyCollector
from collect_bigpanda_data import BigPandaCollector

class BatchCollector:
    """Collects data from multiple platforms in batch"""
    
    def __init__(self):
        self.collectors = {
            "incidentio": IncidentIOCollector,
            "firehydrant": FireHydrantCollector,
            "rootly": RootlyCollector,
            "blameless": BlamelessCollector,
            "pagerduty": PagerDutyCollector,
            "bigpanda": BigPandaCollector,
        }
        
    def get_env_config(self, platform: str) -> Dict[str, str]:
        """Get configuration from environment variables"""
        config_mappings = {
            "incidentio": {
                "api_key": os.getenv("INCIDENT_IO_API_KEY"),
                "workspace_id": os.getenv("INCIDENT_IO_WORKSPACE_ID")
            },
            "firehydrant": {
                "api_key": os.getenv("FIREHYDRANT_API_KEY"),
                "org_id": os.getenv("FIREHYDRANT_ORG_ID")
            },
            "rootly": {
                "api_key": os.getenv("ROOTLY_API_KEY"),
                "org_id": os.getenv("ROOTLY_ORG_ID")
            },
            "blameless": {
                "api_key": os.getenv("BLAMELESS_API_KEY"),
                "workspace_id": os.getenv("BLAMELESS_WORKSPACE_ID")
            },
            "pagerduty": {
                "api_token": os.getenv("PAGERDUTY_API_TOKEN")
            },
            "bigpanda": {
                "api_token": os.getenv("BIGPANDA_API_TOKEN"),
                "org_id": os.getenv("BIGPANDA_ORG_ID")
            }
        }
        
        return config_mappings.get(platform, {})
    
    def collect_from_platform(self, platform: str, config: Dict[str, str], 
                             args: argparse.Namespace) -> bool:
        """Collect data from a single platform"""
        try:
            collector_class = self.collectors[platform]
            
            # Filter out None values from config
            config = {k: v for k, v in config.items() if v is not None}
            
            if not config:
                logger.error(f"No configuration found for {platform}. Check environment variables.")
                return False
                
            # Initialize collector with platform-specific parameters
            if platform == "incidentio":
                collector = collector_class(
                    api_key=config["api_key"],
                    workspace_id=config["workspace_id"]
                )
                results = self._collect_incidentio_data(collector, args)
                
            elif platform == "firehydrant":
                collector = collector_class(
                    api_key=config["api_key"],
                    org_id=config["org_id"]
                )
                results = self._collect_firehydrant_data(collector, args)
                
            elif platform == "rootly":
                collector = collector_class(
                    api_key=config["api_key"],
                    org_id=config["org_id"],
                    use_graphql=args.use_graphql
                )
                results = self._collect_rootly_data(collector, args)
                
            elif platform == "blameless":
                collector = collector_class(
                    api_key=config["api_key"],
                    workspace_id=config["workspace_id"]
                )
                results = self._collect_blameless_data(collector, args)
                
            elif platform == "pagerduty":
                collector = collector_class(api_token=config["api_token"])
                results = self._collect_pagerduty_data(collector, args)
                
            elif platform == "bigpanda":
                collector = collector_class(
                    api_token=config["api_token"],
                    org_id=config["org_id"]
                )
                results = self._collect_bigpanda_data(collector, args)
                
            logger.info(f"Successfully collected data from {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Error collecting from {platform}: {e}")
            return False
    
    def _collect_incidentio_data(self, collector, args):
        """Collect Incident.io data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
        if incidents:
            self._save_to_jsonl(incidents, f"{args.output_dir}/incidentio_incidents_{timestamp}.jsonl")
        
        postmortems = collector.fetch_postmortems(limit=args.limit)
        if postmortems:
            self._save_to_jsonl(postmortems, f"{args.output_dir}/incidentio_postmortems_{timestamp}.jsonl")
    
    def _collect_firehydrant_data(self, collector, args):
        """Collect FireHydrant data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
        if incidents:
            self._save_to_jsonl(incidents, f"{args.output_dir}/firehydrant_incidents_{timestamp}.jsonl")
        
        retrospectives = collector.fetch_retrospectives(limit=args.limit)
        if retrospectives:
            self._save_to_jsonl(retrospectives, f"{args.output_dir}/firehydrant_retrospectives_{timestamp}.jsonl")
    
    def _collect_rootly_data(self, collector, args):
        """Collect Rootly data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if args.use_graphql:
            incidents = collector.fetch_incidents_graphql(limit=args.limit, days_back=args.days_back)
        else:
            incidents = collector.fetch_incidents_rest(limit=args.limit, days_back=args.days_back)
        
        if incidents:
            self._save_to_jsonl(incidents, f"{args.output_dir}/rootly_incidents_{timestamp}.jsonl")
        
        retrospectives = collector.fetch_retrospectives()
        if retrospectives:
            self._save_to_jsonl(retrospectives, f"{args.output_dir}/rootly_retrospectives_{timestamp}.jsonl")
    
    def _collect_blameless_data(self, collector, args):
        """Collect Blameless data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
        if incidents:
            self._save_to_jsonl(incidents, f"{args.output_dir}/blameless_incidents_{timestamp}.jsonl")
        
        post_mortems = collector.fetch_post_mortems(limit=args.limit)
        if post_mortems:
            self._save_to_jsonl(post_mortems, f"{args.output_dir}/blameless_postmortems_{timestamp}.jsonl")
    
    def _collect_pagerduty_data(self, collector, args):
        """Collect PagerDuty data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
        if incidents:
            self._save_to_jsonl(incidents, f"{args.output_dir}/pagerduty_incidents_{timestamp}.jsonl")
    
    def _collect_bigpanda_data(self, collector, args):
        """Collect BigPanda data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        incidents = collector.fetch_incidents(limit=args.limit, days_back=args.days_back)
        if incidents:
            self._save_to_jsonl(incidents, f"{args.output_dir}/bigpanda_incidents_{timestamp}.jsonl")
        
        alerts = collector.fetch_alerts(limit=args.limit, days_back=args.days_back)
        if alerts:
            self._save_to_jsonl(alerts, f"{args.output_dir}/bigpanda_alerts_{timestamp}.jsonl")
    
    @staticmethod
    def _save_to_jsonl(data, filename):
        """Save data to JSONL file"""
        import json
        
        with open(filename, 'w') as f:
            for item in data:
                json.dump(item, f)
                f.write('\n')
        
        logger.info(f"Saved {len(data)} records to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Batch collect incident data from multiple platforms")
    parser.add_argument("--platforms", nargs="+", 
                       choices=["incidentio", "firehydrant", "rootly", "blameless", "pagerduty", "bigpanda"],
                       required=True, help="Platforms to collect from")
    parser.add_argument("--output-dir", default="./data/raw", help="Output directory")
    parser.add_argument("--limit", type=int, default=50, help="Max records per platform")
    parser.add_argument("--days-back", type=int, default=7, help="Days of data to fetch")
    parser.add_argument("--use-graphql", action="store_true", help="Use GraphQL for Rootly")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize batch collector
    batch_collector = BatchCollector()
    
    # Collect from each platform
    successful_platforms = []
    failed_platforms = []
    
    for platform in args.platforms:
        logger.info(f"Collecting data from {platform}...")
        
        config = batch_collector.get_env_config(platform)
        success = batch_collector.collect_from_platform(platform, config, args)
        
        if success:
            successful_platforms.append(platform)
        else:
            failed_platforms.append(platform)
    
    # Summary
    logger.info(f"Collection complete:")
    logger.info(f"  Successful: {successful_platforms}")
    if failed_platforms:
        logger.error(f"  Failed: {failed_platforms}")
        sys.exit(1)
    
    logger.info(f"Data saved to {args.output_dir}")

if __name__ == "__main__":
    main()
