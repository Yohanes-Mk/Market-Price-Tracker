"""Plot Parker Clay product prices from the SQLite database.

This script reads products from `market_prices.db` and either plots the
average price per scrape date or, if only one scrape exists, plots the
individual product prices. The resulting figure is saved as
`price_plot.png`.
"""

import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

# Use a non-interactive backend so the script can run in headless
# environments and still produce an image file.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa:E402  # isort:skip

DB_NAME = "market_prices.db"
OUTPUT_FIG = "price_plot.png"


def fetch_rows():
    """Return all rows from the products table or an empty list if unavailable."""
    db_path = Path(DB_NAME)
    if not db_path.exists():
        print(f"Database not found: {DB_NAME}")
        return []

    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.execute(
            "SELECT product_name, price, scraped_at FROM products"
        )
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        print(f"Failed to read products: {exc}")
        rows = []
    finally:
        conn.close()
    return rows


def plot_prices(rows):
    """Create and save a plot from product rows."""
    if not rows:
        print("No products to plot.")
        return

    # Group prices by scrape date (YYYY-MM-DD)
    grouped = defaultdict(list)
    for name, price, scraped_at in rows:
        date_str = scraped_at.split(" ")[0]
        grouped[date_str].append(price)

    if len(grouped) > 1:
        # Multiple scrape dates -> line plot of average price over time
        dates = sorted(grouped, key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
        averages = [sum(grouped[d]) / len(grouped[d]) for d in dates]

        plt.figure(figsize=(8, 4))
        plt.plot(dates, averages, marker="o")
        plt.xlabel("Scrape Date")
        plt.ylabel("Average Price (USD)")
        plt.title("Average Parker Clay Product Price Over Time")
        plt.xticks(rotation=45)
    else:
        # Only one scrape date -> scatter plot of individual products
        names = [name for name, *_ in rows]
        prices = [price for _, price, _ in rows]

        plt.figure(figsize=(10, 5))
        plt.scatter(names, prices)
        plt.xlabel("Product")
        plt.ylabel("Price (USD)")
        plt.title("Parker Clay Product Prices")
        plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(OUTPUT_FIG)
    print(f"Plot saved to {OUTPUT_FIG}")


if __name__ == "__main__":
    plot_prices(fetch_rows())
