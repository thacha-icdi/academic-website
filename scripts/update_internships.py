"""Collect public employer feeds. No credentials, paid API, or personal data."""
import concurrent.futures
import datetime as dt
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).parent.name == 'scripts' else Path(__file__).parent
OUTPUT = ROOT / 'icdi-internship/data/internships.json'
SOURCES = [
    ('sertis', 'Sertis', 'greenhouse'),
    ('agoda', 'Agoda', 'greenhouse'),
    ('BoschGroup', 'Bosch Group', 'smartrecruiters'),
    ('MinorInternational', 'Minor International', 'smartrecruiters'),
    ('AccorHotel', 'Accor', 'smartrecruiters'),
    ('oocahq', 'OOCA', 'workable'),
    ('cloudcommerce', 'CloudCommerce', 'breezy'),
    ('dsgpay', 'DSGPay', 'employer_html'),
    ('https://mercil.co.th/careers/ux-ui-designer-internship', 'MERCIL', 'jobposting'),
    ('https://sales-mind.ai/en/careers/ai-business-analyst-intern', 'SalesMind AI', 'jobposting'),
]
PROVINCES = {
    'bangkok': 'กรุงเทพมหานคร', 'bangkok metropolis': 'กรุงเทพมหานคร',
    'rayong': 'ระยอง', 'phuket': 'ภูเก็ต', 'chiang mai': 'เชียงใหม่',
    'chon buri': 'ชลบุรี', 'chonburi': 'ชลบุรี', 'samut prakan': 'สมุทรปราการ',
    'pathum thani': 'ปทุมธานี', 'nonthaburi': 'นนทบุรี', 'surat thani': 'สุราษฎร์ธานี',
    'prachuap khiri khan': 'ประจวบคีรีขันธ์', 'phetchaburi': 'เพชรบุรี',
    'nakhon ratchasima': 'นครราชสีมา', 'krabi': 'กระบี่', 'phang nga': 'พังงา',
    'chiang rai': 'เชียงราย', 'lamphun': 'ลำพูน', 'lampang': 'ลำปาง',
    'khon kaen': 'ขอนแก่น', 'udon thani': 'อุดรธานี', 'songkhla': 'สงขลา',
    'nakhon pathom': 'นครปฐม', 'phra nakhon si ayutthaya': 'พระนครศรีอยุธยา',
    'saraburi': 'สระบุรี', 'prachin buri': 'ปราจีนบุรี', 'trat': 'ตราด',
    'ko samui': 'สุราษฎร์ธานี', 'koh samui': 'สุราษฎร์ธานี', 'hua hin': 'ประจวบคีรีขันธ์',
    'pattaya': 'ชลบุรี', 'khao lak': 'พังงา', 'hat yai': 'สงขลา',
}

def plain(value):
    value = html.unescape(html.unescape(str(value or '')))
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', value)).strip()

def is_internship(title, employment=''):
    # Management/graduate trainee is not automatically a student internship.
    return bool(re.search(r'\b(?:intern|internship|internships)\b|ฝึกงาน|สหกิจศึกษา', title, re.I)
                or str(employment).lower() in ('intern', 'internship'))

def province_for(location, region=''):
    for candidate in (region, location):
        candidate = plain(candidate).lower().strip()
        if candidate in PROVINCES:
            return PROVINCES[candidate]
        for english, thai in sorted(PROVINCES.items(), key=lambda x: -len(x[0])):
            if thai in candidate or re.search(r'\b' + re.escape(english) + r'\b', candidate):
                return thai
    return ''

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'ICDI-Internship-Feed/1.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def fetch_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'ICDI-Internship-Feed/1.0'})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read().decode('utf-8')

def jobpostings_from_html(page):
    postings = []
    def walk(value):
        if isinstance(value, dict):
            if value.get('@type') == 'JobPosting':
                postings.append(value)
            else:
                for child in value.values():
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    for script in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try:
            walk(json.loads(script))
        except ValueError:
            continue
    return postings

def normalize(source, row, checked_at):
    slug, company, kind = source
    if kind == 'greenhouse':
        title = plain(row.get('title'))
        location = plain(row.get('location', {}).get('name'))
        # Only declared job location counts, never the company's global description.
        if not re.search(r'\bThailand\b|ประเทศไทย', location, re.I):
            return None
        employment = ''
        region = ''
        url = row.get('absolute_url', '')
        deadline = row.get('application_deadline')
    elif kind == 'smartrecruiters':
        loc = row.get('location') or {}
        if str(loc.get('country', '')).lower() != 'th':
            return None
        title = plain(row.get('name'))
        location = plain(loc.get('fullLocation') or ', '.join(filter(None, [loc.get('city'), loc.get('region'), 'Thailand'])))
        region = loc.get('region', '')
        employment = (row.get('typeOfEmployment') or {}).get('label', '')
        url = row.get('postingUrl') or 'https://jobs.smartrecruiters.com/' + slug + '/' + str(row.get('id', ''))
        deadline = None
    elif kind == 'workable':
        if str(row.get('country', '')).lower() != 'thailand':
            return None
        title = plain(row.get('title'))
        location = ', '.join(filter(None, [row.get('city'), row.get('state'), row.get('country')]))
        region = row.get('state', '')
        employment = row.get('experience', '')
        url = row.get('url', '')
        deadline = None
        row = {**row, 'id': row.get('shortcode')}
    elif kind == 'breezy':
        loc = row.get('location') or {}
        if str((loc.get('country') or {}).get('id', '')).upper() != 'TH':
            return None
        title = plain(row.get('name'))
        location = plain(loc.get('name') or (loc.get('city', '') + ', Thailand'))
        region = loc.get('city', '')
        employment = 'Internship' if row.get('department') == 'Internship' else ''
        url = row.get('url', '')
        deadline = None
    elif kind == 'employer_html':
        title = plain(row.get('title'))
        location = plain(row.get('location'))
        if not re.search(r'Chiang Mai,\s*Thailand', location, re.I):
            return None
        region = 'Chiang Mai'
        employment = ''
        url = row.get('url', '')
        deadline = None
    elif kind == 'jobposting':
        title = plain(row.get('title'))
        loc = row.get('jobLocation') or {}
        if isinstance(loc, list):
            loc = next((item for item in loc if (item.get('address') or {}).get('addressCountry') in ('TH', 'Thailand')), {})
        address = loc.get('address') or {}
        country = address.get('addressCountry') or ''
        if isinstance(country, dict):
            country = country.get('name', '')
        locality = plain(address.get('addressLocality'))
        if str(country).lower() not in ('th', 'thailand'):
            if country or not re.search(r'\bBangkok\b|\bChiang Mai\b', locality, re.I):
                return None
        location = ', '.join(filter(None, [locality, address.get('addressRegion'), 'Thailand']))
        region = address.get('addressRegion', '')
        employment = row.get('employmentType', '')
        if isinstance(employment, list):
            employment = 'Internship' if any(str(t).lower() in ('intern', 'internship') for t in employment) else ''
        url = row.get('url') or slug
        deadline = row.get('validThrough')
        row = {**row, 'id': row.get('@id') or url}
    else:
        return None
    if not is_internship(title, employment):
        return None
    years = [int(y) for y in re.findall(r'\b20\d{2}\b', title)]
    if years and max(years) < int(checked_at[:4]):
        return None
    if not url.startswith('https://') or not row.get('id'):
        return None
    if deadline and str(deadline)[:10] < checked_at[:10]:
        return None
    return {
        'id': kind + ':' + slug + ':' + str(row['id']), 'title': title, 'company': company,
        'location': location, 'province': province_for(location, region), 'country': 'TH',
        'url': url, 'source': company + ' — ประกาศรับสมัครของบริษัท',
        'source_id': slug, 'checked_at': checked_at,
        'deadline': deadline, 'start_date': None, 'end_date': None,
        'employment_type': employment or 'Internship',
        'discovery_only': kind in ('workable', 'breezy', 'employer_html', 'jobposting'),
    }

def collect_source(source, checked_at):
    slug, company, kind = source
    if kind == 'greenhouse':
        payload = fetch_json('https://boards-api.greenhouse.io/v1/boards/' + slug + '/jobs')
        if not isinstance(payload.get('jobs'), list):
            raise ValueError('Invalid Greenhouse response')
        rows = payload['jobs']
    elif kind == 'workable':
        payload = fetch_json('https://apply.workable.com/api/v1/widget/accounts/' + slug)
        if not isinstance(payload.get('jobs'), list):
            raise ValueError('Invalid Workable response')
        rows = payload['jobs']
    elif kind == 'breezy':
        rows = fetch_json('https://' + slug + '.breezy.hr/json')
        if not isinstance(rows, list):
            raise ValueError('Invalid Breezy response')
    elif kind == 'employer_html':
        index = fetch_html('https://www.dsgpay.com/internship')
        links = set(re.findall(r'href=[\"\x27]((?:https://www\.dsgpay\.com)?/jobs/[^\"\x27?#]+)', index))
        if not links:
            raise ValueError('No employer job links in internship index')
        rows = []
        for link in sorted(links):
            url = urllib.parse.urljoin('https://www.dsgpay.com', link)
            page = fetch_html(url)
            headings = re.findall(r'<h1[^>]*>(.*?)</h1>', page, re.S | re.I)
            title = plain(headings[0]) if headings else ''
            if not is_internship(title) or title.lower() == 'internship opportunities':
                continue
            if not re.search(r'Chiang Mai,\s*Thailand', plain(page), re.I):
                continue
            if re.search(r'position (?:is )?filled|no longer accepting applications|job (?:has )?expired', plain(page), re.I):
                continue
            rows.append({'id': url.rsplit('/', 1)[-1], 'title': title,
                         'location': 'Chiang Mai, Thailand', 'url': url})
    elif kind == 'jobposting':
        rows = jobpostings_from_html(fetch_html(slug))
        if not rows:
            raise ValueError('No structured JobPosting on employer page')
    else:
        rows = []
        # Fetch all Thai postings; keyword searches can also match "international".
        for offset in range(0, 2000, 100):
            query = urllib.parse.urlencode({'country': 'th', 'limit': 100, 'offset': offset})
            payload = fetch_json('https://api.smartrecruiters.com/v1/companies/' + slug + '/postings?' + query)
            if not isinstance(payload.get('content'), list):
                raise ValueError('Invalid SmartRecruiters response')
            page = payload['content']
            rows.extend(page)
            if not page or offset + len(page) >= int(payload.get('totalFound', 0)):
                break
        else:
            raise ValueError('Feed pagination limit exceeded')
    jobs = [j for row in rows if (j := normalize(source, row, checked_at))]
    return {'id': slug, 'company': company, 'status': 'ok', 'checked_at': checked_at,
            'count': len(jobs)}, jobs

def reviewed_jobs(records, checked_at):
    """Human-reviewed employer pages expire; scheduled runs never renew their dates."""
    result = []
    now = dt.datetime.fromisoformat(checked_at)
    for record in records:
        try:
            age = now - dt.datetime.fromisoformat(record['checked_at'])
            if not dt.timedelta(0) <= age < dt.timedelta(days=7):
                continue
            if record.get('country') != 'TH' or not is_internship(record.get('title', '')):
                continue
            if not record.get('url', '').startswith('https://'):
                continue
            result.append({**record, 'discovery_only': True})
        except (KeyError, ValueError, TypeError):
            continue
    return result

def main():
    checked_at = dt.datetime.now(dt.timezone.utc).isoformat()
    jobs, statuses = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(collect_source, source, checked_at): source for source in SOURCES}
        for future in concurrent.futures.as_completed(futures):
            source = futures[future]
            try:
                status, found = future.result()
                statuses.append(status)
                jobs.extend(found)
                print(source[1], len(found), 'internships')
            except Exception as error:
                # Do not silently retain possibly closed jobs from a failed source.
                statuses.append({'id': source[0], 'company': source[1], 'status': 'unavailable',
                                 'checked_at': checked_at, 'count': 0})
                print(source[1], 'unavailable:', type(error).__name__, file=sys.stderr)
    if not any(s['status'] == 'ok' for s in statuses):
        raise RuntimeError('Every source failed; keep previous snapshot, frontend hides snapshots older than seven days')
    reviewed_path = ROOT / 'icdi-internship/data/reviewed-sources.json'
    if reviewed_path.exists():
        reviewed = reviewed_jobs(json.loads(reviewed_path.read_text(encoding='utf-8')), checked_at)
        jobs.extend(reviewed)
        statuses.append({'id': 'reviewed-employer-pages', 'company': 'Additional reviewed employer pages',
                         'status': 'ok' if reviewed else 'unavailable',
                         'checked_at': max((j['checked_at'] for j in reviewed), default=None),
                         'count': len(reviewed)})
    unique = {j['url']: j for j in jobs}
    result = {'schema_version': 1, 'generated_at': checked_at,
              'sources': sorted(statuses, key=lambda x: x['company']),
              'jobs': sorted(unique.values(), key=lambda x: (x['company'], x['title']))}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix('.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(OUTPUT)
    print('Saved', len(unique), 'internships to', OUTPUT)

if __name__ == '__main__':
    main()
