import requests

urls = [
    'https://news.harvard.edu/gazette/feed',
    'https://news.mit.edu/rss/feed',
    'https://news.yale.edu/news-rss',
    'https://www.princeton.edu/feed',
    'https://news.columbia.edu/rss.xml',
    'https://news.cornell.edu/rss',
    'https://news.brown.edu/feed',
    'https://home.dartmouth.edu/feeds/news',
    'https://news.dartmouth.edu/rss/feed'
]
with open('rss_status.txt', 'w') as f:
    for u in urls:
        try:
            r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            f.write(f'{u}: {r.status_code}\n')
        except Exception as e:
            f.write(f'{u}: ERROR {e}\n')
