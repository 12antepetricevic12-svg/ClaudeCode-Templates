"""
Tool: Generate Final Lead List
Reads businesses_with_emails.json, deduplicates, prioritizes,
and outputs a clean 20-lead CSV.

No external dependencies — uses Python stdlib only.
"""

import json
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / ".tmp" / "businesses_with_emails.json"
OUTPUT_PATH = PROJECT_ROOT / ".tmp" / "leads.csv"


def normalize_domain(url: str) -> str:
    """Normalize a URL to its base domain for deduplication."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url.lower().strip()


def deduplicate(businesses: list[dict]) -> list[dict]:
    """Remove duplicate businesses based on domain. Keep the most complete entry."""
    seen = {}
    for biz in businesses:
        domain = normalize_domain(biz.get("website", ""))
        if not domain:
            continue

        if domain not in seen:
            seen[domain] = biz
        else:
            # Keep the entry with more complete data
            existing = seen[domain]
            existing_score = bool(existing.get("email")) + bool(existing.get("phone"))
            new_score = bool(biz.get("email")) + bool(biz.get("phone"))
            if new_score > existing_score:
                seen[domain] = biz

    return list(seen.values())


def score_lead(biz: dict) -> int:
    """Score a lead for prioritization. Higher = better."""
    score = 0
    if biz.get("email"):
        score += 2
    if biz.get("phone"):
        score += 1
    return score


def select_leads(businesses: list[dict], target: int = 20) -> list[dict]:
    """Select up to target leads, balanced across industries, prioritizing completeness."""
    # Group by industry
    by_industry = {}
    for biz in businesses:
        industry = biz.get("industry", "Unknown")
        by_industry.setdefault(industry, []).append(biz)

    # Sort each group by score (best first)
    for industry in by_industry:
        by_industry[industry].sort(key=score_lead, reverse=True)

    # Round-robin selection to balance across industries
    selected = []
    industries = list(by_industry.keys())
    per_industry = max(1, target // len(industries)) if industries else target

    # First pass: take up to per_industry from each
    for industry in industries:
        candidates = by_industry[industry]
        selected.extend(candidates[:per_industry])

    # Second pass: fill remaining slots from any industry (best scores first)
    if len(selected) < target:
        remaining = []
        for industry in industries:
            remaining.extend(by_industry[industry][per_industry:])
        remaining.sort(key=score_lead, reverse=True)
        selected.extend(remaining[:target - len(selected)])

    return selected[:target]


def clean_name(name: str, url: str = "") -> str:
    """Clean up company name for display."""
    if not name or name.lower() in ["contact us", "contact", "home", "about", "about us", "services", "unknown"]:
        # Fall back to domain name
        if url:
            try:
                domain = urlparse(url).netloc.lower().replace("www.", "").split(".")[0]
                # Insert spaces before common suffixes
                for suffix in ["llc", "inc", "hvac", "dental", "landscaping", "heating", "cooling", "lawn", "care"]:
                    domain = re.sub(f"({suffix})", r" \1", domain, flags=re.IGNORECASE)
                domain = domain.replace("-", " ")
                domain = re.sub(r"\s+", " ", domain).strip()
                return domain.title()
            except Exception:
                pass
        return name or "Unknown"

    # Remove "[PDF]" prefix
    name = re.sub(r"^\[PDF\]\s*", "", name)
    # Truncate overly long names
    if len(name) > 50:
        name = name[:50].rsplit(" ", 1)[0]
    return name.strip()


def export_csv(leads: list[dict], output_path: Path):
    """Write leads to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Company Name", "Industry", "Email", "Phone Number"])
        for lead in leads:
            writer.writerow([
                clean_name(lead.get("name", ""), lead.get("website", "")),
                lead.get("industry", ""),
                lead.get("email", ""),
                lead.get("phone", ""),
            ])


def print_table(leads: list[dict]):
    """Print a formatted table of leads to stdout."""
    # Column widths
    name_w = max(len("Company Name"), max((len(l.get("name", "")) for l in leads), default=0))
    ind_w = max(len("Industry"), max((len(l.get("industry", "")) for l in leads), default=0))
    email_w = max(len("Email"), max((len(l.get("email", "") or "") for l in leads), default=0))
    phone_w = max(len("Phone"), max((len(l.get("phone", "") or "") for l in leads), default=0))

    # Cap widths for readability
    name_w = min(name_w, 35)
    email_w = min(email_w, 35)

    header = f"{'Company Name':<{name_w}}  {'Industry':<{ind_w}}  {'Email':<{email_w}}  {'Phone':<{phone_w}}"
    separator = "-" * len(header)

    print(f"\n{header}")
    print(separator)
    for lead in leads:
        name = clean_name(lead.get("name", ""), lead.get("website", ""))[:name_w]
        industry = lead.get("industry", "") or ""
        email = (lead.get("email", "") or "")[:email_w]
        phone = lead.get("phone", "") or ""
        print(f"{name:<{name_w}}  {industry:<{ind_w}}  {email:<{email_w}}  {phone:<{phone_w}}")


def main():
    if not INPUT_PATH.exists():
        print(f"ERROR: Input file not found: {INPUT_PATH}")
        print("Run scrape_contact_email.py first.")
        sys.exit(1)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        businesses = json.load(f)

    print(f"Loaded {len(businesses)} businesses")

    # Deduplicate
    unique = deduplicate(businesses)
    print(f"After dedup: {len(unique)} unique businesses")

    # Select top leads
    leads = select_leads(unique, target=20)
    print(f"Selected {len(leads)} leads")

    # Export
    export_csv(leads, OUTPUT_PATH)
    print(f"CSV saved to: {OUTPUT_PATH}")

    # Print table
    print_table(leads)

    # Summary
    with_email = sum(1 for l in leads if l.get("email"))
    with_phone = sum(1 for l in leads if l.get("phone"))
    with_both = sum(1 for l in leads if l.get("email") and l.get("phone"))
    print(f"\nSummary: {len(leads)} leads | {with_email} with email | {with_phone} with phone | {with_both} with both")


if __name__ == "__main__":
    main()
