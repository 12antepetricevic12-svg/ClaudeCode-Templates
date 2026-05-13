"""
Tool: Scrape Contact Emails from Business Websites
Reads raw_businesses.json, scrapes each website for email and phone,
outputs businesses_with_emails.json

NOTE: This is the most API-credit-intensive tool.
It makes 1-4 scrape calls per business.
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

INPUT_PATH = PROJECT_ROOT / ".tmp" / "raw_businesses.json"
OUTPUT_PATH = PROJECT_ROOT / ".tmp" / "businesses_with_emails.json"

# Platform/junk email domains to filter out
JUNK_DOMAINS = [
    "wix.com", "squarespace.com", "wordpress.com", "godaddy.com",
    "google.com", "example.com", "sentry.io", "cloudflare.com",
    "w3.org", "schema.org", "facebook.com", "twitter.com",
    "instagram.com", "linkedin.com", "youtube.com", "change.org",
    "sentry.wixpress.com", "weebly.com", "shopify.com",
]

# Email prefixes that are usually not useful for outreach
JUNK_PREFIXES = [
    "noreply", "no-reply", "donotreply", "mailer-daemon",
    "postmaster", "webmaster", "admin@localhost",
]

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


def is_valid_email(email: str) -> bool:
    """Check if an email is likely a real business contact email."""
    email_lower = email.lower()

    # Filter junk prefixes
    for prefix in JUNK_PREFIXES:
        if email_lower.startswith(prefix):
            return False

    # Filter junk domains
    domain = email_lower.split("@")[1] if "@" in email_lower else ""
    for junk in JUNK_DOMAINS:
        if junk in domain:
            return False

    # Filter obviously fake/placeholder emails
    if "example" in email_lower or "test@" in email_lower:
        return False

    # Filter image file extensions that regex might catch
    if email_lower.endswith((".png", ".jpg", ".gif", ".svg", ".jpeg", ".webp", ".bmp", ".ico")):
        return False

    return True


def extract_emails(text: str) -> list[str]:
    """Extract valid email addresses from text."""
    if not text:
        return []
    raw_emails = EMAIL_PATTERN.findall(text)
    return [e for e in raw_emails if is_valid_email(e)]


def extract_phone(text: str) -> str | None:
    """Extract a US phone number from text."""
    if not text:
        return None
    pattern = r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def scrape_with_retry(app: Firecrawl, url: str, max_retries: int = 3) -> str | None:
    """Scrape a URL with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            doc = app.scrape(
                url=url,
                formats=["markdown"],
                only_main_content=False,
                timeout=30000,
            )
            return doc.markdown or ""
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    Retry {attempt + 1}/{max_retries} in {wait}s: {error_msg}")
                time.sleep(wait)
            else:
                print(f"    Failed after {max_retries} attempts: {error_msg}")
                return None


def scrape_business_contact(app: Firecrawl, website: str) -> dict:
    """Scrape a business website for email and phone number."""
    base_url = website.rstrip("/")

    # Pages to try, in order of likelihood of having contact info
    pages = [
        base_url,
        base_url + "/contact",
        base_url + "/contact-us",
        base_url + "/about",
    ]

    all_emails = []
    phone = None

    for page_url in pages:
        markdown = scrape_with_retry(app, page_url)
        if markdown is None:
            continue

        # Extract emails
        emails = extract_emails(markdown)
        all_emails.extend(emails)

        # Extract phone if we don't have one yet
        if not phone:
            phone = extract_phone(markdown)

        # If we found at least one email, stop scraping more pages
        if all_emails:
            break

        time.sleep(0.5)  # Brief pause between page scrapes

    # Deduplicate emails, keep order
    seen = set()
    unique_emails = []
    for e in all_emails:
        if e.lower() not in seen:
            seen.add(e.lower())
            unique_emails.append(e)

    return {
        "email": unique_emails[0] if unique_emails else None,
        "all_emails": unique_emails,
        "phone": phone,
    }


def main():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not found in .env")
        sys.exit(1)

    if not INPUT_PATH.exists():
        print(f"ERROR: Input file not found: {INPUT_PATH}")
        print("Run scrape_google_maps.py first.")
        sys.exit(1)

    app = Firecrawl(api_key=api_key)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        businesses = json.load(f)

    print(f"Processing {len(businesses)} businesses...\n")

    for i, biz in enumerate(businesses, 1):
        website = biz.get("website")
        name = biz.get("name", "Unknown")
        print(f"[{i}/{len(businesses)}] {name} ({website})")

        if not website:
            print("  Skipped: no website")
            biz["email"] = None
            continue

        contact = scrape_business_contact(app, website)

        # Use scraped email, keep existing phone if scrape didn't find one
        biz["email"] = contact["email"]
        if contact["phone"] and not biz.get("phone"):
            biz["phone"] = contact["phone"]

        status = []
        if contact["email"]:
            status.append(f"email: {contact['email']}")
        if biz.get("phone"):
            status.append(f"phone: {biz['phone']}")
        print(f"  -> {', '.join(status) if status else 'no contact info found'}")

        time.sleep(0.5)  # Rate limiting between businesses

    # Save enriched results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(businesses, f, indent=2, ensure_ascii=False)

    # Summary
    with_email = sum(1 for b in businesses if b.get("email"))
    with_phone = sum(1 for b in businesses if b.get("phone"))
    print(f"\n{'='*50}")
    print(f"Results: {len(businesses)} businesses processed")
    print(f"  With email: {with_email}")
    print(f"  With phone: {with_phone}")
    print(f"  With both:  {sum(1 for b in businesses if b.get('email') and b.get('phone'))}")
    print(f"Output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
