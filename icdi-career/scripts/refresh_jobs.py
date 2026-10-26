"""Download public Thailand job postings. No credentials; no fabricated listings.
Runs on GitHub Actions, independently of a browser being open.
"""
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMPANIES = ['BoschGroup', 'WesternDigital', 'MinorInternational', 'Dentsu', 'AccorHotel']
ROLES = json.loads((ROOT / 'data/roles.json').read_text())


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'ICDI-Career-Hub/1.0 public-posting-reader', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def categorize(title):
    return [i for i, role in enumerate(ROLES) if not (i == 21 and re.search(r'\bpeople\b|human resources', title, re.I)) and any((bool(re.search(r'\b' + re.escape(keyword) + r'\b', title, re.I)) if len(keyword) <= 3 and keyword.isascii() and keyword.isalpha() else keyword.lower() in title.lower()) for keyword in role[3])]


def level(title, experience=None):
    label = ((experience or {}).get('id', '') + ' ' + (experience or {}).get('label', '')).lower()
    if re.search(r'\b(senior|sr\.?|lead|head|director|manager|principal|supervisor)\b|\bstaff\s+(software|engineer|data)', title, re.I):
        return 'experienced'
    if re.search(r'\b(junior|jr\.?|graduate|entry|internship|intern|trainee|associate)\b', title, re.I) or 'entry_level' in label or 'internship' in label:
        return 'entry'
    return 'unspecified'


def company_jobs(company):
    jobs, offset, total = [], 0, 0
    try:
        while True:
            data = fetch(f'https://api.smartrecruiters.com/v1/companies/{company}/postings?country=th&limit=100&offset={offset}')
            postings = data['content']
            total = int(data.get('totalFound', 0))
            for item in postings:
                location = item.get('location') or {}
                if str(location.get('country', '')).lower() != 'th':
                    continue
                role_ids = categorize(item.get('name', ''))
                if not role_ids:
                    continue
                # Fetch documented postingUrl rather than guess an application URL.
                detail = fetch(f'https://api.smartrecruiters.com/v1/companies/{company}/postings/{item["id"]}')
                if detail.get('active') is False:
                    continue
                url = detail.get('postingUrl')
                if not url or urllib.parse.urlparse(url).scheme != 'https':
                    continue
                jobs.append({'id': f'{company}:{item["id"]}', 'title': item['name'],
                             'company': (item.get('company') or {}).get('name', company),
                             'company_id': company, 'posting_id': str(item['id']),
                             'location': ', '.join(dict.fromkeys(filter(None, [location.get('city'), location.get('region')]))),
                             'country': 'th', 'published_at': item.get('releasedDate'),
                             'url': url, 'employment_type': (item.get('typeOfEmployment') or {}).get('label', 'ดูที่ต้นทาง'),
                             'level': level(item['name'], item.get('experienceLevel')),
                             'role_ids': role_ids, 'source': 'SmartRecruiters',
                             'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat()})
                time.sleep(0.2)
            offset += 100
            if offset >= total or not postings or offset >= 2000:
                break
            time.sleep(0.3)
        return {'company': company, 'status': 'ok', 'count': len(jobs), 'jobs': jobs, 'truncated': offset < total}
    except Exception as exc:
        return {'company': company, 'status': 'error', 'message': str(exc), 'jobs': []}


def greenhouse_jobs(board, company):
    try:
        data = fetch(f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs')
        jobs = []
        for item in data['jobs']:
            location = (item.get('location') or {}).get('name', '')
            ids = categorize(item.get('title', ''))
            if not re.search(r'\bthailand\b', location, re.I) or not ids:
                continue
            url = item.get('absolute_url', '')
            if urllib.parse.urlparse(url).scheme != 'https':
                continue
            jobs.append({'id': f'greenhouse:{board}:{item["id"]}', 'title': item['title'],
                         'company': company, 'company_id': f'greenhouse:{board}', 'posting_id': str(item['id']),
                         'location': location, 'country': 'th', 'published_at': item.get('updated_at'),
                         'url': url, 'employment_type': 'ดูที่ต้นทาง', 'level': level(item['title']),
                         'role_ids': ids, 'source': 'Greenhouse',
                         'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat()})
        return {'company': f'greenhouse:{board}', 'status': 'ok', 'count': len(jobs), 'jobs': jobs}
    except Exception as exc:
        return {'company': f'greenhouse:{board}', 'status': 'error', 'message': str(exc), 'jobs': []}


def main():
    target = ROOT / 'data/jobs.json'
    previous = json.loads(target.read_text()) if target.exists() else {'jobs': []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(company_jobs, COMPANIES))
    for board, name in [('agoda', 'Agoda'), ('sertis', 'Sertis'), ('acommerce', 'aCommerce')]:
        results.append(greenhouse_jobs(board, name))
    succeeded = {r['company'] for r in results if r['status'] == 'ok'}
    # Keep the last snapshot on source failure, but surface the error and original retrieval time.
    jobs = [j for j in previous.get('jobs', []) if j['company_id'] not in succeeded]
    jobs.extend(j for r in results for j in r.pop('jobs'))
    jobs = list({j['id']: j for j in jobs}.values())
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    output = {'updated_at': now if succeeded else previous.get('updated_at'), 'attempted_at': now,
              'jobs': jobs, 'sources': results}
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'total_jobs': len(jobs), 'sources': results}, ensure_ascii=False))
    if not succeeded:
        raise SystemExit('All job sources failed; retained previous snapshot.')


if __name__ == '__main__':
    main()
