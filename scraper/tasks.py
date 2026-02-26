from celery import shared_task
from .logic import IvyScraper


@shared_task
def run_ivy_scrape():
    scraper = IvyScraper()
    results = scraper.scrape_all()
    summary = ", ".join(f"{uni}: {n} new" for uni, n in results.items())
    return f"Scraped — {summary}"


@shared_task
def run_scrape_university(university):
    scraper = IvyScraper()
    n = scraper.scrape_one(university)
    return f"Scraped {n} new items from {university}"
