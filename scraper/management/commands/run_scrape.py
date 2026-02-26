from django.core.management.base import BaseCommand
from scraper.logic import IvyScraper, SOURCES


class Command(BaseCommand):
    help = 'Scrape Ivy League universities (RSS-first, then HTML fallback)'

    def add_arguments(self, parser):
        parser.add_argument('--university', '-u', type=str, default='',
            help=f'One of: {", ".join(SOURCES.keys())}. Omit for all.')

    def handle(self, *args, **options):
        scraper = IvyScraper()
        uni = options['university'].strip()
        self.stdout.write(self.style.WARNING('─── IvyIntel Scrape ───'))
        if uni:
            n = scraper.scrape_one(uni)
            self.stdout.write(self.style.SUCCESS(f'{uni}: {n} new items'))
        else:
            for name, n in scraper.scrape_all().items():
                fn = self.style.SUCCESS if n > 0 else self.style.WARNING
                self.stdout.write(fn(f'  {name}: {n} new'))
        self.stdout.write(self.style.SUCCESS('─── Done ───'))
