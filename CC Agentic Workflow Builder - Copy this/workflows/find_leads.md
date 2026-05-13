# Find Leads Workflow

## Objective
Generate a list of 20 qualified leads for an AI automation company. Target: small-to-medium HVAC companies, landscaping companies, and dentist offices in the US.

## Required Inputs
- `FIRECRAWL_API_KEY` set in `.env`
- Python packages: `firecrawl-py`, `python-dotenv`

## Steps

### Step 1: Search for Businesses
**Tool:** `tools/scrape_google_maps.py`
**What it does:** Uses Firecrawl's search endpoint to find ~10 businesses per industry (30 total candidates). Filters out directory sites (Yelp, Angi, etc.) and extracts company name, website URL, and phone number from search results.

```bash
python tools/scrape_google_maps.py
```

**Output:** `.tmp/raw_businesses.json`
**Verify:** File should contain entries across all 3 industries. Check the printed summary.

**Custom queries:** Pass a JSON string as the first argument to override defaults:
```bash
python tools/scrape_google_maps.py '{"HVAC": "HVAC repair companies in Texas", "Landscaping": "lawn care in Florida"}'
```

### Step 2: Extract Contact Emails
**Tool:** `tools/scrape_contact_email.py`
**What it does:** Scrapes each business website for email addresses and phone numbers. Tries the homepage first, then /contact, /contact-us, and /about pages. Filters out junk emails (noreply@, platform domains, etc.).

```bash
python tools/scrape_contact_email.py
```

**Output:** `.tmp/businesses_with_emails.json`
**Verify:** Check the summary for email/phone hit rates. Expect ~30-50% email success rate.

**⚠️ API CREDITS:** This step makes 1-4 Firecrawl scrape calls per business (up to ~120 total). Check with the user before re-running if it fails partway through.

### Step 3: Generate Final Lead List
**Tool:** `tools/generate_lead_list.py`
**What it does:** Deduplicates by domain, prioritizes leads with complete contact info (email + phone), balances across industries, and caps at 20 leads.

```bash
python tools/generate_lead_list.py
```

**Output:** `.tmp/leads.csv` with columns: Company Name, Industry, Email, Phone Number
**Verify:** Open the CSV, confirm ~20 rows with balanced industry distribution.

## Expected Output
A CSV file at `.tmp/leads.csv` containing 20 leads with:
- Company Name
- Industry (HVAC, Landscaping, or Dental)
- Email (if available)
- Phone Number (if available)

## Edge Cases & Troubleshooting

| Issue | Solution |
|-------|----------|
| Rate limiting from Firecrawl | Built-in retry with exponential backoff (3 retries). Wait and re-run if persistent. |
| Low email hit rate (<30%) | Re-run Step 1 with more specific queries (add city names) or increase the limit to 15 per industry. |
| No results for an industry | Adjust the search query — try variations like "HVAC repair" vs "heating and cooling". |
| `FIRECRAWL_API_KEY` missing | Add it to `.env` in the project root. |
| Mostly directory sites in results | The filter list in `scrape_google_maps.py` may need updating. Add new directory domains to `DIRECTORY_DOMAINS`. |
| Script fails mid-run on Step 2 | The output file won't exist. Fix the issue and re-run. Intermediate progress is not saved. |

## Search Queries (Defaults)
- HVAC: `"HVAC heating and cooling companies in United States phone number email contact"`
- Landscaping: `"landscaping lawn care companies in United States phone number email contact"`
- Dental: `"dentist dental office in United States phone number email contact"`

These can be customized by editing `DEFAULT_QUERIES` in `scrape_google_maps.py` or passing a JSON argument.

## Lessons Learned
- **dotenv override**: Must use `load_dotenv(override=True)` to ensure `.env` values take precedence over existing environment variables
- **Image file false positives**: Email regex can match image filenames like `logo@3x.webp`. Filter now includes `.webp` extension
- **Company name quality**: When search result titles are generic ("Contact Us"), the tool falls back to domain names which can be ugly ("Wholesaleheating"). Manual cleanup of the CSV may be needed for best results
- **Directory filtering**: Added `deltadentalia.com` and `dentalpracticelist.com` to the filter list — insurance/aggregator sites were appearing as dental leads
- **PDF URLs**: Search results can include PDF links (e.g., contractor lists). These are now filtered out
- **Geographic clustering**: Firecrawl search tends to cluster results geographically (e.g., all HVAC in Omaha, all dental in Iowa). To get more geographic diversity, use city-specific queries
