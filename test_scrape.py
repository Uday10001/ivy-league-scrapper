import os
import sys
import django
import logging

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivy_intel.settings')
django.setup()

logging.basicConfig(level=logging.DEBUG)

from scraper.logic import IvyScraper

if __name__ == '__main__':
    scraper = IvyScraper()
    print("Scraping Harvard:")
    result = scraper.scrape_one("Harvard")
    print("Harvard items:", result)
