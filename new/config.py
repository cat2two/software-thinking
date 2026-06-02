# -*- coding: utf-8 -*-
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STOCK_FILE = BASE_DIR / "stock.txt"
MAX_FILE = BASE_DIR / "max.txt"
PRICE_FILE = BASE_DIR / "stock_prices.json"

INITIAL_MONEY = 1_000_000
EXTRA_STOCK_DEFAULT_PRICE = 5_000

DEFAULT_STOCKS = {
    "삼성전자": 70_000,
    "테슬라": 250_000,
    "애플": 180_000,
}

def format_money(value: float) -> str:
    return f"{value:,.0f}원"