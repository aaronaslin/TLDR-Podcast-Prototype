#!/usr/bin/env python3
"""
Main entrypoint for Email-to-Podcast pipeline.
"""
import argparse
import logging
import sys
from datetime import date

from src.config.settings import Settings
from src.core.pipeline import run_pipeline


def main():
    """Main execution flow for email-to-podcast conversion."""
    parser = argparse.ArgumentParser(description="Run the Email-to-Podcast pipeline")
    parser.add_argument(
        "--date",
        dest="target_date",
        help="Target digest date in YYYY-MM-DD (matches email Date header within that day)",
    )
    args = parser.parse_args()

    parsed_target_date: date | None = None
    if args.target_date:
        try:
            parsed_target_date = date.fromisoformat(args.target_date)
        except ValueError:
            print("✗ Invalid --date format. Use YYYY-MM-DD")
            sys.exit(2)

    settings = Settings.load()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    print("=" * 50)
    print("Email to Podcast Pipeline")
    print("=" * 50)

    try:
        feed_url = run_pipeline(target_date=parsed_target_date)
        print("\n" + "=" * 50)
        print("✓ Pipeline completed successfully!")
        print("=" * 50)
        print(f"\nSubscribe to your podcast at: {feed_url}")
    except ValueError as e:
        print(f"✗ Pipeline error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
