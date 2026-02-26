# Ivy League Scrapper

A Django-based web scraper that aggregates **research and event news** from Ivy League university websites into a single, searchable interface.

---

## Features

- Scrapes news feeds from Ivy League university websites
- Categorizes articles into **Research** and **Events**
- Clean web interface to browse and search scraped content
- Dockerized for easy setup and deployment

---

##  Project Structure

```
ivy-league-scrapper/
├── ivy_intel/          # Django app: data models, views, templates
├── scraper/            # Scraping logic and spiders
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image definition
└── docker-compose.yml  # Multi-container orchestration
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- Docker & Docker Compose (optional but recommended)

---

### Option 1: Run with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Uday10001/ivy-league-scrapper.git
cd ivy-league-scrapper

# Build and start the containers
docker-compose up --build
```

The app will be available at `http://localhost:8000`.

---

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/Uday10001/ivy-league-scrapper.git
cd ivy-league-scrapper

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run the development server
python manage.py runserver
```

The app will be available at `http://localhost:8000`.

---

## 🕷️ Running the Scraper

To manually trigger a scrape, run the appropriate Django management command:

```bash
python manage.py scrape
```

> **Note:** Check the `scraper/` directory for available scrapers and their target universities.

---

##  Supported Universities

The scraper targets news and events feeds from the 8 Ivy League institutions:

- Harvard University
- Yale University
- Princeton University
- Columbia University
- University of Pennsylvania
- Brown University
- Dartmouth College
- Cornell University

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django (Python) |
| Scraping | BeautifulSoup / Requests |
| Frontend | HTML / Django Templates |
| Deployment | Docker, Docker Compose |

