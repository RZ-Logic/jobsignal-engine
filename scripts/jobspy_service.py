"""
JobSpy Scanner Service for JobSignal Engine
Runs as a Docker sidecar alongside n8n.
Called via HTTP Request node from Workflow 1d.

Endpoints:
  POST /scan    — Run a single JobSpy search query, return results as JSON
  POST /batch   — Run multiple queries in one call, return combined results
  GET  /health  — Health check

Port: 3457 (cv-renderer is on 3456)
"""

import json
import logging
import traceback
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def run_single_query(query):
    """
    Run a single JobSpy scrape_jobs() call.

    Expected query format:
    {
        "search_term": "AI engineer",
        "location": "Toronto, Canada",
        "sites": ["indeed", "linkedin"],
        "country_indeed": "Canada",
        "hours_old": 72,
        "results_wanted": 50,
        "source_tag": "AI Hunter",
        "description_format": "markdown"
    }
    """
    from jobspy import scrape_jobs

    search_term = query.get('search_term', '')
    location = query.get('location', '')
    sites = query.get('sites', ['indeed', 'linkedin'])
    country_indeed = query.get('country_indeed', 'Canada')
    hours_old = query.get('hours_old', 72)
    results_wanted = query.get('results_wanted', 50)
    description_format = query.get('description_format', 'markdown')
    is_remote = query.get('is_remote', None)
    job_type = query.get('job_type', None)

    # Validate
    if not search_term:
        return [], 'search_term is required'

    # Cap results_wanted to prevent runaway scrapes
    results_wanted = min(results_wanted, 100)

    logger.info(f"Scanning: '{search_term}' | location='{location}' | sites={sites} | "
                f"hours_old={hours_old} | results_wanted={results_wanted}")

    # Build kwargs — only include optional params if provided
    kwargs = {
        'site_name': sites,
        'search_term': search_term,
        'location': location,
        'results_wanted': results_wanted,
        'hours_old': hours_old,
        'country_indeed': country_indeed,
        'description_format': description_format,
    }
    if is_remote is not None:
        kwargs['is_remote'] = is_remote
    if job_type is not None:
        kwargs['job_type'] = job_type
    linkedin_fetch_description = query.get('linkedin_fetch_description', False)
    if linkedin_fetch_description:
        kwargs['linkedin_fetch_description'] = True

    jobs_df = scrape_jobs(**kwargs)

    if jobs_df is None or jobs_df.empty:
        logger.info(f"No results for '{search_term}'")
        return [], None

    # Convert DataFrame to list of dicts
    # Replace NaN/NaT with None for clean JSON serialization
    jobs_df = jobs_df.where(jobs_df.notnull(), None)

    results = []
    for _, row in jobs_df.iterrows():
        job = {
            'title': row.get('title'),
            'company': row.get('company'),
            'location': _build_location_string(row),
            'job_url': row.get('job_url'),
            'job_url_direct': row.get('job_url_direct'),
            'description': row.get('description'),
            'site': row.get('site'),
            'date_posted': str(row.get('date_posted')) if row.get('date_posted') else None,
            'job_type': row.get('job_type'),
            'is_remote': row.get('is_remote'),
            'salary_min': _safe_number(row.get('min_amount')),
            'salary_max': _safe_number(row.get('max_amount')),
            'salary_interval': row.get('interval'),
            'salary_currency': row.get('currency'),
            'company_url': row.get('company_url'),
        }
        results.append(job)

    logger.info(f"Found {len(results)} jobs for '{search_term}'")
    return results, None


def _build_location_string(row):
    """Build a clean location string from city/state/country fields."""
    parts = []
    city = row.get('city')
    state = row.get('state')
    country = row.get('country')
    if city and str(city) != 'None':
        parts.append(str(city))
    if state and str(state) != 'None':
        parts.append(str(state))
    if country and str(country) != 'None':
        parts.append(str(country))
    return ', '.join(parts) if parts else (row.get('location') or 'Not specified')


def _safe_number(val):
    """Convert to float or return None."""
    if val is None:
        return None
    try:
        f = float(val)
        if f != f:  # NaN check
            return None
        return f
    except (ValueError, TypeError):
        return None


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'jobspy-scanner', 'port': 3457})


@app.route('/scan', methods=['POST'])
def scan():
    """
    Run a single search query.

    Request body (JSON):
    {
        "search_term": "AI engineer",
        "location": "Toronto, Canada",
        "sites": ["indeed", "linkedin"],
        "country_indeed": "Canada",
        "hours_old": 72,
        "results_wanted": 50,
        "source_tag": "AI Hunter"
    }

    Response (JSON):
    {
        "success": true,
        "count": 23,
        "source_tag": "AI Hunter",
        "search_term": "AI engineer",
        "jobs": [ ... ]
    }
    """
    try:
        query = request.get_json(force=True)
        if not query:
            return jsonify({'success': False, 'error': 'No JSON body provided'}), 400

        results, error = run_single_query(query)

        if error:
            return jsonify({'success': False, 'error': error}), 400

        return jsonify({
            'success': True,
            'count': len(results),
            'source_tag': query.get('source_tag', ''),
            'search_term': query.get('search_term', ''),
            'jobs': results
        })

    except Exception as e:
        logger.error(f"Scan failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/batch', methods=['POST'])
def batch():
    """
    Run multiple search queries in one call.
    Useful when n8n wants to fire all Search Queries at once
    instead of looping.

    Request body (JSON):
    {
        "queries": [
            { "search_term": "AI engineer", "location": "Toronto", ... },
            { "search_term": "automation engineer", "location": "Remote", ... }
        ]
    }

    Response (JSON):
    {
        "success": true,
        "total_count": 47,
        "query_results": [
            { "search_term": "AI engineer", "source_tag": "...", "count": 23, "jobs": [...] },
            { "search_term": "automation engineer", "source_tag": "...", "count": 24, "jobs": [...] }
        ]
    }
    """
    try:
        body = request.get_json(force=True)
        if not body or 'queries' not in body:
            return jsonify({'success': False, 'error': 'Request must contain "queries" array'}), 400

        queries = body['queries']
        if not isinstance(queries, list) or len(queries) == 0:
            return jsonify({'success': False, 'error': '"queries" must be a non-empty array'}), 400

        # Safety brake: cap at 10 queries per batch
        if len(queries) > 10:
            return jsonify({
                'success': False,
                'error': f'Too many queries ({len(queries)}). Max 10 per batch.'
            }), 400

        query_results = []
        total_count = 0

        for i, query in enumerate(queries):
            logger.info(f"Batch query {i+1}/{len(queries)}: '{query.get('search_term', '?')}'")
            try:
                results, error = run_single_query(query)
                if error:
                    query_results.append({
                        'search_term': query.get('search_term', ''),
                        'source_tag': query.get('source_tag', ''),
                        'count': 0,
                        'error': error,
                        'jobs': []
                    })
                else:
                    total_count += len(results)
                    query_results.append({
                        'search_term': query.get('search_term', ''),
                        'source_tag': query.get('source_tag', ''),
                        'count': len(results),
                        'jobs': results
                    })
            except Exception as e:
                logger.error(f"Query {i+1} failed: {e}")
                query_results.append({
                    'search_term': query.get('search_term', ''),
                    'source_tag': query.get('source_tag', ''),
                    'count': 0,
                    'error': str(e),
                    'jobs': []
                })

        return jsonify({
            'success': True,
            'total_count': total_count,
            'queries_run': len(queries),
            'query_results': query_results
        })

    except Exception as e:
        logger.error(f"Batch scan failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


if __name__ == '__main__':
    logger.info("JobSpy Scanner Service starting on port 3457...")
    app.run(host='0.0.0.0', port=3457)
