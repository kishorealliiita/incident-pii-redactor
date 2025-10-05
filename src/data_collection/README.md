# Data Collection Scripts

This directory contains dedicated data collection scripts for various incident management platforms. Each script collects real incident data via their respective APIs and saves them as JSONL files for testing the PII redaction pipeline.

## Platform Coverage

| Platform | Script | API Documentation | Status |
|----------|--------|-------------------|---------|
| Incident.io | `collect_incidentio_data.py` | https://api.incident.io | ✅ Complete |
| FireHydrant | `collect_firehydrant_data.py` | https://api.firehydrant.io/v1 | ✅ Complete |
| Rootly | `collect_rootly_data.py` | https://docs.google.com/doc/api | ✅ Complete (REST + GraphQL) |
| Blameless | `collect_blameless_data.py` | GraphQL API | ✅ Complete |
| PagerDuty | `collect_pagerduty_data.py` | https://developer.pagerduty.com/api-reference/ | ✅ Complete |
| BigPanda | `collect_bigpanda_data.py` | REST API | ✅ Complete |

## Prerequisites

### API Credentials

You'll need API credentials for each platform you want to collect data from:

#### Incident.io
- `INCIDENT_IO_API_KEY`: Your Incident.io API key
- `INCIDENT_IO_WORKSPACE_ID`: Your workspace ID

#### FireHydrant
- `FIREHYDRANT_API_KEY`: Your FireHydrant API key
- `FIREHYDRANT_ORG_ID`: Your organization ID

#### Rootly
- `ROOTLY_API_KEY`: Your Rootly API key
- `ROOTLY_ORG_ID`: Your organization ID

#### Blameless
- `BLAMELESS_API_KEY`: Your Blameless API key
- `BLAMELESS_WORKSPACE_ID`: Your workspace ID

#### PagerDuty
- `PAGERDUTY_API_TOKEN`: Your PagerDuty API token

#### BigPanda
- `BIGPANDA_API_TOKEN`: Your BigPanda API token
- `BIGPANDA_ORG_ID`: Your organization ID

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install the data collection scripts
pip install -e .
```

## Usage Examples

### Incident.io
```bash
python scripts/data_collection/collect_incidentio_data.py \
  --api-key YOUR_INCIDENT_IO_API_KEY \
  --workspace-id YOUR_WORKSPACE_ID \
  --output-dir ./data/raw \
  --limit 50 \
  --days-back 7 \
  --include-timeline
```

### FireHydrant
```bash
python scripts/data_collection/collect_firehydrant_data.py \
  --api-key YOUR_FIREHYDRANT_API_KEY \
  --org-id YOUR_ORG_ID \
  --output-dir ./data/raw \
  --limit 50 \
  --days-back 7 \
  --include-full-data
```

### Rootly (GraphQL)
```bash
python scripts/data_collection/collect_rootly_data.py \
  --api-key YOUR_ROOTLY_API_KEY \
  --org-id YOUR_ORG_ID \
  --use-graphql \
  --output-dir ./data/raw \
  --limit 50 \
  --days-back 7 \
  --include-tasks
```

### Blameless
```bash
python scripts/data_collection/collect_blameless_data.py \
  --api-key YOUR_BLAMELESS_API_KEY \
  --workspace-id YOUR_WORKSPACE_ID \
  --output-dir ./data/raw \
  --limit 50 \
  --days-back 7 \
  --include-analysis
```

### PagerDuty
```bash
python scripts/data_collection/collect_pagerduty_data.py \
  --api-token YOUR_PAGERDUTY_API_TOKEN \
  --output-dir ./data/raw \
  --limit 50 \
  --days-back 7 \
  --include-full-data \
  --include-reference-data
```

### BigPanda
```bash
python scripts/data_collection/collect_bigpanda_data.py \
  --api-token YOUR_BIGPANDA_API_TOKEN \
  --org-id YOUR_ORG_ID \
  --output-dir ./data/raw \
  --limit 50 \
  --days-back 7 \
  --include-events \
  --fetch-alerts
```

## Output Format

All scripts output JSONL files (one JSON object per line) with the following naming convention:
```
{platform}_{data_type}_{timestamp}.jsonl
```

Examples:
- `incidentio_incidents_20241215_143022.jsonl`
- `firehydrant_retrospectives_20241215_143022.jsonl`
- `rootly_incidents_20241215_143022.jsonl`

## Data Schemas

Each platform has its unique data structure, but all data includes:

### Common Fields Across Platforms
- `id`: Unique identifier
- `title`: Incident summary/title
- `description`: Detailed incident description
- `status`: Current status
- `severity`: Impact level
- `created_at`: Incident creation timestamp
- `updated_at`: Last modification timestamp
- `assignee`: Primary responder information
- `custom_fields`: Platform-specific additional data

### Platform-Specific Features

#### Incident.io
- `timeline_events`: Real-time incident updates
- `post_mortems`: Structured retrospective data
- Clean schema optimized for integrations

#### FireHydrant
- `follow_ups`: Action items and next steps
- `retrospectives`: Automated postmortem data
- Nested retrospective information within incidents

#### Rootly
- `learned_lessons`: Structured learning outcomes
- `follow_ups`: Trackable action items
- Both REST and GraphQL endpoints supported

#### Blameless
- `analysis.spellable_root_cause`: Detailed root cause analysis
- Action items with assignees and due dates
- Comprehensive post-mortem structure

#### PagerDuty
- `notes`: Manual annotations during incidents
- `log_entries`: Status update timeline
- `alerts`: Alert correlation data
- Strong focus on alert management

#### BigPanda
- Alert correlation and event grouping
- Correlation events for pattern analysis
- Focus on infrastructure event correlation

## Batch Collection Script

Use the batch collection script to gather data from multiple platforms at once:

```bash
python scripts/data_collection/collect_all_data.py \
  --days-back 30 \
  --output-dir ./data/raw \
  --platforms incidentio firehydrant rootly
```

## Best Practices

1. **Start Small**: Begin with `--limit 10` and `--days-back 7` to test API access
2. **Rate Limiting**: Scripts include built-in rate limiting and error handling
3. **Data Privacy**: All collected data contains real operational information - handle securely
4. **Incremental Collection**: Use timestamp filtering to collect only new data
5. **Storage**: Consider archiving old JSONL files to manage disk usage

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: HTTP 401 Unauthorized
```
- Verify your API credentials are correct
- Check if your API key is active and has proper permissions
- Ensure workspace/organization ID matches your account

#### Rate Limiting
```
Error: HTTP 429 Too Many Requests
```
- Scripts automatically handle rate limiting
- Reduce `--limit` or increase collection intervals
- Check platform-specific rate limits in their documentation

#### Missing Data
```
Warning: No incidents found in date range
```
- Verify the date range spans active incidents
- Check if your account has access to the requested data
- Some platforms require specific incident states (e.g., "resolved")

#### API Changes
```
Error: HTTP 404 Not Found
```
- Platform APIs may have changed endpoints or authentication
- Check the platform's API documentation for updates
- Some platforms are still developing their APIs

### Getting Help

1. Check platform-specific API documentation
2. Verify credentials and permissions with platform support
3. Test with minimal parameters first (`--limit 1`)
4. Review error logs for specific troubleshooting information
