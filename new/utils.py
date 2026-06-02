# -*- coding: utf-8 -*-
import json
from typing import List, Dict
from config import STOCK_FILE, MAX_FILE, PRICE_FILE, INITIAL_MONEY, DEFAULT_STOCKS

def ensure_data_files() -> None:
    """필수 데이터 파일이 없으면 자동 생성한다."""
    if not STOCK_FILE.exists():
        STOCK_FILE.write_text("", encoding="utf-8")

    if not MAX_FILE.exists():
        MAX_FILE.write_text(str(INITIAL_MONEY), encoding="utf-8")

    if not PRICE_FILE.exists():
        PRICE_FILE.write_text("{}", encoding="utf-8")


def load_max_money() -> int:
    ensure_data_files()
    try:
        value = int(MAX_FILE.read_text(encoding="utf-8").strip() or INITIAL_MONEY)
        return max(value, INITIAL_MONEY)
    except ValueError:
        MAX_FILE.write_text(str(INITIAL_MONEY), encoding="utf-8")
        return INITIAL_MONEY


def save_max_money(value: int) -> None:
    MAX_FILE.write_text(str(int(value)), encoding="utf-8")


def load_extra_stock_names() -> List[str]:
    ensure_data_files()
    names: List[str] = []
    seen = set()

    for raw_line in STOCK_FILE.read_text(encoding="utf-8").splitlines():
        name = raw_line.strip()
        if not name or name in DEFAULT_STOCKS or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def save_extra_stock_names(names: List[str]) -> None:
    unique_names: List[str] = []
    seen = set()

    for name in names:
        cleaned = name.strip()
        if not cleaned or cleaned in DEFAULT_STOCKS or cleaned in seen:
            continue
        seen.add(cleaned)
        unique_names.append(cleaned)

    text = "\n".join(unique_names)
    STOCK_FILE.write_text(text + ("\n" if text else ""), encoding="utf-8")


def load_extra_stock_prices() -> Dict[str, int]:
    ensure_data_files()
    try:
        data = json.loads(PRICE_FILE.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        data = {}

    prices: Dict[str, int] = {}
    for name, price in data.items():
        try:
            prices[str(name)] = max(1, int(price))
        except (TypeError, ValueError):
            continue
    return prices


def save_extra_stock_prices(prices: Dict[str, int]) -> None:
    clean_prices = {}
    for name, price in prices.items():
        try:
            numeric_price = int(price)
        except (TypeError, ValueError):
            continue
        if name and numeric_price > 0:
            clean_prices[name] = numeric_price

    PRICE_FILE.write_text(
        json.dumps(clean_prices, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )