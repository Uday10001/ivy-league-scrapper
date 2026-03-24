import requests
import urllib3
urllib3.disable_warnings()

urls = [
    'https://www.princeton.edu/feed',
    'https://news.columbia.edu/rss.xml',
    'https://www.brown.edu/news/feed',
    'https://news.dartmouth.edu/feed',
    'https://home.dartmouth.edu/news/feed',
]
with open('rss_status2.txt', 'w') as f:
    for u in urls:
        try:
            r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'Accept': 'application/rss+xml, application/xml'}, timeout=5, verify=False)
            f.write(f'{u}: {r.status_code}\n')
        except Exception as e:
            f.write(f'{u}: ERROR {e}\n')
