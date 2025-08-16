"""Scrape Parker Clay leather bag products and store in SQLite.

This script fetches product names, prices, and URLs from the Parker Clay
leather bag collection and saves them into a SQLite database while avoiding
duplicate entries.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://www.parkerclay.com"
COLLECTION_URL = f"{BASE_URL}/collections/leather-bags"
DB_NAME = "market_prices.db"


def fetch_products() -> List[Dict[str, str]]:
    """Fetch product data from Parker Clay leather bag collection.

    Returns a list of dictionaries each containing product_name, price, and product_url.
    If the request fails, an empty list is returned.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(COLLECTION_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network failures
        print(f"Failed to fetch products: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    products = []

    # Products are contained within <div> elements with a 'product-grid-item' class (Shopify structure)
    for product_div in soup.select("div.product-grid-item"):
        # Extract product name
        name_tag = product_div.select_one("p.product-card__title")
        if not name_tag:
            continue
        product_name = name_tag.get_text(strip=True)

        # Extract product URL
        link_tag = product_div.find("a", href=True)
        product_url = f"{BASE_URL}{link_tag['href']}" if link_tag else None

        # Extract price; Shopify often stores price in span with class 'price-item--regular'
        price_tag = product_div.select_one("span.price-item--regular")
        if not price_tag:
            continue
        raw_price = price_tag.get_text(strip=True)
        # Remove currency symbols and commas to convert to float
        price = float(raw_price.replace("$", "").replace(",", ""))

        products.append(
            {
                "product_name": product_name,
                "price": price,
                "product_url": product_url,
            }
        )

    return products


def init_db(conn: sqlite3.Connection) -> None:
    """Create the products table if it does not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT DEFAULT 'Parker Clay',
            product_name TEXT,
            price REAL,
            product_url TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def product_exists(conn: sqlite3.Connection, name: str, price: float) -> bool:
    """Check if a product with the same name and price already exists."""
    cursor = conn.execute(
        "SELECT 1 FROM products WHERE product_name = ? AND price = ? LIMIT 1",
        (name, price),
    )
    return cursor.fetchone() is not None


def save_products(products: List[Dict[str, str]]) -> None:
    """Insert products into the database, avoiding duplicates."""
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)

    for item in products:
        name = item["product_name"]
        price = item["price"]
        url = item["product_url"]

        if product_exists(conn, name, price):
            print(f"Skipping duplicate: {name} - ${price}")
            continue

        conn.execute(
            "INSERT INTO products (product_name, price, product_url) VALUES (?, ?, ?)",
            (name, price, url),
        )
        print(f"Inserted: {name} - ${price}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    products = fetch_products()
    if not products:
        print("No products fetched.")
    else:
        save_products(products)
        print(f"Saved {len(products)} products to {DB_NAME}.")
