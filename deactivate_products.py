"""Set the products listed in RB_products.csv inactive in Tripletex.

Usage:
    set TRIPLETEX_CONSUMER_TOKEN=...
    set TRIPLETEX_EMPLOYEE_TOKEN=...
    python deactivate_products.py              # dry run, only shows what would change
    python deactivate_products.py --apply      # actually deactivates

Or with a premade session token saved in a file (no environment variables needed):
    python deactivate_products.py --session-token-file session_token.txt

Optional:
    --csv PATH          CSV file (default RB_products.csv, ';'-separated, product number in first column)
    --base-url URL      default https://tripletex.no/v2 (test: https://api-test.tripletex.tech/v2)
"""
import argparse
import csv
import datetime
import os
import sys

import requests


def read_product_numbers(path):
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(path, newline="", encoding=encoding) as f:
                rows = list(csv.reader(f, delimiter=";"))
            break
        except UnicodeDecodeError:
            continue
    # Skip header row, keep first column
    return [row[0].strip() for row in rows[1:] if row and row[0].strip()]


def create_session(base_url, consumer_token, employee_token):
    expiration = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    r = requests.put(
        f"{base_url}/token/session/:create",
        params={
            "consumerToken": consumer_token,
            "employeeToken": employee_token,
            "expirationDate": expiration,
        },
    )
    r.raise_for_status()
    return session_from_token(r.json()["value"]["token"])


def session_from_token(token):
    session = requests.Session()
    session.auth = ("0", token)
    return session


def read_session_token(path):
    with open(path, encoding="utf-8-sig") as f:
        token = f.read().strip()
    if not token:
        sys.exit(f"Session token file {path} is empty.")
    return token


def find_product(session, base_url, number):
    r = session.get(
        f"{base_url}/product",
        params={"productNumber": number, "fields": "id,version,number,name,isInactive"},
    )
    r.raise_for_status()
    # Only accept an exact match on product number
    matches = [p for p in r.json()["values"] if p.get("number") == number]
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default="RB_products.csv")
    parser.add_argument("--base-url", default="https://tripletex.no/v2")
    parser.add_argument("--apply", action="store_true", help="Actually deactivate (default is dry run)")
    parser.add_argument("--session-token-file", help="File containing a premade session token")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    if args.session_token_file:
        session = session_from_token(read_session_token(args.session_token_file))
    else:
        consumer_token = os.environ.get("TRIPLETEX_CONSUMER_TOKEN")
        employee_token = os.environ.get("TRIPLETEX_EMPLOYEE_TOKEN")
        if not consumer_token or not employee_token:
            sys.exit(
                "Set TRIPLETEX_CONSUMER_TOKEN and TRIPLETEX_EMPLOYEE_TOKEN environment variables, "
                "or use --session-token-file."
            )
        session = create_session(base_url, consumer_token, employee_token)

    numbers = read_product_numbers(args.csv)
    print(f"Read {len(numbers)} product numbers from {args.csv}")
    if not args.apply:
        print("DRY RUN - nothing will be changed. Use --apply to deactivate.\n")

    deactivated, already_inactive, not_found, failed = [], [], [], []
    for number in numbers:
        matches = find_product(session, base_url, number)
        if not matches:
            print(f"NOT FOUND   {number}")
            not_found.append(number)
            continue
        if len(matches) > 1:
            print(f"AMBIGUOUS   {number} ({len(matches)} matches) - skipped")
            failed.append(number)
            continue

        product = matches[0]
        label = f"{number} - {product.get('name')}"
        if product.get("isInactive"):
            print(f"ALREADY OFF {label}")
            already_inactive.append(number)
            continue

        if not args.apply:
            print(f"WOULD SET   {label} inactive")
            deactivated.append(number)
            continue

        r = session.put(
            f"{base_url}/product/{product['id']}",
            json={"id": product["id"], "version": product["version"], "isInactive": True},
        )
        if r.ok:
            print(f"DEACTIVATED {label}")
            deactivated.append(number)
        else:
            print(f"FAILED      {label}: {r.status_code} {r.text}")
            failed.append(number)

    print(
        f"\n{'Would deactivate' if not args.apply else 'Deactivated'}: {len(deactivated)}, "
        f"already inactive: {len(already_inactive)}, not found: {len(not_found)}, failed/skipped: {len(failed)}"
    )


if __name__ == "__main__":
    main()
