# tripletex-deactivate-products

Small Python script that reads a list of product numbers from a CSV file and sets those products inactive in Tripletex via the API.

## CSV format

Semicolon-separated, with a header row. The product number is taken from the first column:

```
Produktnr.;Produktnavn
1000-0;"Example product"
ABC123;"Another product"
```

## Authentication

Either set your API tokens as environment variables (the script creates a session for you):

```powershell
$env:TRIPLETEX_CONSUMER_TOKEN = "..."
$env:TRIPLETEX_EMPLOYEE_TOKEN = "..."
```

or save a premade session token in a file and pass it with `--session-token-file`. Never commit that file.

## Usage

```powershell
pip install requests

# Dry run - shows what would change, changes nothing
python deactivate_products.py --csv products.csv

# Actually deactivate
python deactivate_products.py --csv products.csv --apply

# With a session token file
python deactivate_products.py --csv products.csv --session-token-file session_token.txt
```

Options:

| Option | Description |
| --- | --- |
| `--csv PATH` | CSV file (default `RB_products.csv`) |
| `--apply` | Actually deactivate. Without it the script only does a dry run. |
| `--session-token-file PATH` | Use a premade session token instead of the environment variables |
| `--base-url URL` | API base URL. Default `https://tripletex.no/v2`, test environment `https://api-test.tripletex.tech/v2` |

Only exact matches on product number are changed. If a product number matches more than one product, it is skipped.
