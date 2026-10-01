"""Lead generation scraper - command line entry point.

Examples:
  python main.py --source demo --format xlsx
  python main.py --source google --query "plumbers" --location "Atlanta, GA"
  python main.py --source yelp --query "hair salons" --location "Atlanta, GA"
  python main.py --source directory --config configs/my_directory.json
  python main.py --source google yelp --query "roofers" --location "Marietta, GA" --format xlsx
"""
import argparse

from dotenv import load_dotenv

from scraper.clean import clean_leads
from scraper.export import build_summary, export, print_summary
from scraper.sources import directory, google_places, yelp


def main():
    parser = argparse.ArgumentParser(description="Collect business leads and export a clean list.")
    parser.add_argument("--source", nargs="+", required=True,
                        choices=["google", "yelp", "directory", "demo"],
                        help="one or more sources to pull from")
    parser.add_argument("--query", help='type of business, e.g. "plumbers"')
    parser.add_argument("--location", help='city/area, e.g. "Atlanta, GA"')
    parser.add_argument("--config", help="JSON config for --source directory")
    parser.add_argument("--max-pages", type=int, default=5, help="page limit per source")
    parser.add_argument("--format", default="csv", choices=["csv", "xlsx", "json"])
    parser.add_argument("--out", default="output", help="folder for the export")
    args = parser.parse_args()

    load_dotenv()  # reads API keys from the .env file
    raw = []

    for source in args.source:
        print(f"\nCollecting from {source}...")
        if source in ("google", "yelp") and not (args.query and args.location):
            parser.error(f"--source {source} needs --query and --location")

        if source == "google":
            raw += google_places.search(args.query, args.location, min(args.max_pages, 3))
        elif source == "yelp":
            raw += yelp.search(args.query, args.location, args.max_pages)
        elif source == "directory":
            if not args.config:
                parser.error("--source directory needs --config")
            raw += directory.scrape(args.config, args.max_pages)
        elif source == "demo":
            raw += directory.scrape("configs/demo.json", args.max_pages)

    if not raw:
        print("No leads found.")
        return

    df, dupes = clean_leads(raw)
    summary = build_summary(df, dupes)
    name = (args.query or "leads").replace(" ", "_").lower()
    path = export(df, summary, args.format, args.out, name)
    print_summary(summary, path)


if __name__ == "__main__":
    main()
