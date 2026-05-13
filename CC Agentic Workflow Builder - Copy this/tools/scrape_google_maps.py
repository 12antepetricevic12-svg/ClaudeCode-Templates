"""
Tool: Scrape Google Maps / Web Search for Business Listings
Uses Firecrawl's search endpoint to find businesses by industry.
Outputs raw business data to .tmp/raw_businesses.json
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from firecrawl import Firecrawl

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Default search queries per industry
DEFAULT_QUERIES = {
    "HVAC": "HVAC heating and cooling companies in United States phone number email contact",
    "Landscaping": "landscaping lawn care companies in United States phone number email contact",
    "Dental": "dentist dental office in United States phone number email contact",
}

OUTPUT_PATH = PROJECT_ROOT / ".tmp" / "raw_businesses.json"

# Domains that are directories/aggregators, not actual businesses
DIRECTORY_DOMAINS = [
    "yelp.com", "yellowpages.com", "angi.com", "angieslist.com",
    "bbb.org", "homeadvisor.com", "thumbtack.com", "facebook.com",
    "instagram.com", "twitter.com", "linkedin.com", "mapquest.com",
    "manta.com", "superpages.com", "citysearch.com", "foursquare.com",
    "google.com", "apple.com", "bing.com", "wikipedia.org",
    "nextdoor.com", "porch.com", "houzz.com", "zocdoc.com",
    "healthgrades.com", "vitals.com", "webmd.com",
    "deltadentalia.com", "dentalpracticelist.com", "dentistry.com",
    "squarespace.com", "static1.squarespace.com",
]


def is_directory_site(url: str) -> bool:
    """Check if a URL belongs to a directory/aggregator site."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in DIRECTORY_DOMAINS)


def extract_phone(text: str) -> str | None:
    """Extract a US phone number from text."""
    if not text:
        return None
    pattern = r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def name_from_domain(url: str) -> str:
    """Extract a readable name from a URL domain."""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        domain = domain.lower().replace("www.", "")
        # Remove TLD
        name = domain.split(".")[0]
        # Split camelCase and joined words using common business suffixes
        import re
        # Insert space before common suffixes
        for suffix in ["llc", "inc", "hvac", "dental", "landscaping", "heating", "cooling", "lawn", "care"]:
            pattern = re.compile(f"({suffix})", re.IGNORECASE)
            name = pattern.sub(r" \1", name)
        # Convert hyphens to spaces
        name = name.replace("-", " ")
        # Clean up multiple spaces
        name = re.sub(r"\s+", " ", name).strip()
        return name.title()
    except Exception:
        return "Unknown"


def clean_company_name(title: str, url: str = "") -> str:
    """Clean up a company name from a search result title."""
    if not title:
        return name_from_domain(url) if url else "Unknown"

    # Remove common suffixes like " - Home", " | Official Site", etc.
    separators = [" - ", " | ", " – ", " — ", " :: "]
    for sep in separators:
        if sep in title:
            title = title.split(sep)[0]

    cleaned = title.strip()

    # If the title is generic (like "Contact Us"), fall back to domain name
    generic_titles = ["contact us", "contact", "home", "about", "about us", "services"]
    if cleaned.lower() in generic_titles and url:
        return name_from_domain(url)

    return cleaned


def search_businesses(app: Firecrawl, query: str, industry: str, limit: int = 10) -> list[dict]:
    """Search for businesses using Firecrawl search endpoint."""
    print(f"  Searching: {query}")

    try:
        results = app.search(
            query=query,
            limit=limit,
            location="United States",
        )
    except Exception as e:
        print(f"  ERROR: Search failed - {e}")
        return []

    businesses = []
    if not results.web:
        print(f"  No web results returned")
        return []

    for result in results.web:
        url = getattr(result, "url", None)
        title = getattr(result, "title", None)
        description = getattr(result, "description", None)

        if not url:
            continue

        # Skip directory/aggregator sites and non-webpage URLs
        if is_directory_site(url):
            continue
        if url.lower().endswith(".pdf"):
            continue

        name = clean_company_name(title, url)
        phone = extract_phone(description or "")

        businesses.append({
            "name": name,
            "phone": phone,
            "website": url,
            "industry": industry,
            "description": description,
        })

    print(f"  Found {len(businesses)} businesses (filtered from {len(results.web)} results)")
    return businesses


def main():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not found in .env")
        sys.exit(1)

    app = Firecrawl(api_key=api_key)

    # Parse optional CLI args for custom queries
    queries = DEFAULT_QUERIES
    if len(sys.argv) > 1:
        try:
            queries = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print("WARNING: Could not parse custom queries, using defaults")

    all_businesses = []

    for industry, query in queries.items():
        print(f"\n[{industry}]")
        results = search_businesses(app, query, industry, limit=10)
        all_businesses.extend(results)
        time.sleep(1)  # Brief pause between searches

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_businesses, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Total businesses found: {len(all_businesses)}")
    print(f"  HVAC: {sum(1 for b in all_businesses if b['industry'] == 'HVAC')}")
    print(f"  Landscaping: {sum(1 for b in all_businesses if b['industry'] == 'Landscaping')}")
    print(f"  Dental: {sum(1 for b in all_businesses if b['industry'] == 'Dental')}")
    print(f"Output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
