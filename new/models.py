# -*- coding: utf-8 -*-
import random
from typing import Dict, List, Tuple, Optional
from config import INITIAL_MONEY, DEFAULT_STOCKS, EXTRA_STOCK_DEFAULT_PRICE, format_money
import utils

class Stock:
    def __init__(self, name: str, price: int):
        self.name = name
        self.price = int(price)
        self.start_price = int(price)
        self.history: List[int] = [int(price)]
        self.change = 100
        self.decide_change()

    def decide_change(self) -> None:
        self.change = random.randint(70, 130)

    def update_price(self) -> Tuple[int, int]:
        old_price = self.price
        self.price = max(1, int(self.price * self.change / 100))
        self.history.append(self.price)
        return old_price, self.price

    def is_delisted(self) -> bool:
        return self.price < self.start_price / 10

    def news_text(self) -> str:
        if self.change < 85:
            return f"{self.name} 대표이사 사임"
        if self.change < 100:
            return f"{self.name}에서 화재 발생"
        if self.change < 115:
            return f"{self.name}에서 약간의 호재"
        return f"{self.name}에서 신기술 개발"


class Player:
    def __init__(self, money: int):
        self.money = int(money)
        self.portfolio: Dict[str, Dict[str, float]] = {}

    def buy_stock(self, stock: Stock, quantity: int) -> Tuple[bool, str]:
        if quantity <= 0:
            return False, "올바른 수량을 입력하세요."

        total_price = stock.price * quantity
        if total_price > self.money:
            return False, "돈이 부족합니다."

        self.money -= total_price

        if stock.name in self.portfolio:
            current_quantity = int(self.portfolio[stock.name]["quantity"])
            current_buy_price = float(self.portfolio[stock.name]["buy_price"])
            new_quantity = current_quantity + quantity
            average_price = (
                (current_quantity * current_buy_price) + (quantity * stock.price)
            ) / new_quantity
            self.portfolio[stock.name]["quantity"] = new_quantity
            self.portfolio[stock.name]["buy_price"] = average_price
        else:
            self.portfolio[stock.name] = {
                "quantity": quantity,
                "buy_price": float(stock.price),
            }
        return True, f"{stock.name} {quantity}주 구매 완료"

    def sell_stock(self, stock: Stock, quantity: int) -> Tuple[bool, str]:
        if quantity <= 0:
            return False, "올바른 수량을 입력하세요."

        if stock.name not in self.portfolio:
            return False, "보유하지 않은 주식입니다."

        current_quantity = int(self.portfolio[stock.name]["quantity"])
        if quantity > current_quantity:
            return False, "보유 수량이 부족합니다."

        self.money += stock.price * quantity
        self.portfolio[stock.name]["quantity"] = current_quantity - quantity

        if self.portfolio[stock.name]["quantity"] == 0:
            del self.portfolio[stock.name]

        return True, f"{stock.name} {quantity}주 판매 완료"

    def calculate_total_assets(self, stock_market: Dict[str, Stock]) -> int:
        total_assets = self.money
        for stock_name, info in self.portfolio.items():
            if stock_name not in stock_market:
                continue
            quantity = int(info["quantity"])
            total_assets += quantity * stock_market[stock_name].price
        return int(total_assets)

    def calculate_profit_rate(self, stock_market: Dict[str, Stock], initial_money: int) -> float:
        current_assets = self.calculate_total_assets(stock_market)
        return ((current_assets - initial_money) / initial_money) * 100


class GameState:
    def __init__(self):
        utils.ensure_data_files()
        self.extra_prices = utils.load_extra_stock_prices()
        self.extra_names = utils.load_extra_stock_names()
        self.stock_market: Dict[str, Stock] = self._create_initial_market()
        self.player = Player(INITIAL_MONEY)
        self.day = 1
        self.max_money = utils.load_max_money()
        self.current_stock: Optional[str] = next(iter(self.stock_market), None)

    def _create_initial_market(self) -> Dict[str, Stock]:
        market: Dict[str, Stock] = {
            name: Stock(name, price) for name, price in DEFAULT_STOCKS.items()
        }
        for name in self.extra_names:
            price = self.extra_prices.get(name, EXTRA_STOCK_DEFAULT_PRICE)
            market[name] = Stock(name, price)
        return market

    def update_high_score(self) -> bool:
        total_assets = self.player.calculate_total_assets(self.stock_market)
        if total_assets > self.max_money:
            self.max_money = total_assets
            utils.save_max_money(self.max_money)
            return True
        return False

    def add_stock(self, name: str, price: int) -> Tuple[bool, str]:
        name = name.strip()
        if not name:
            return False, "종목 이름을 입력하세요."
        if name in self.stock_market:
            return False, "이미 존재하는 종목입니다."
        if price <= 0:
            return False, "가격은 1원 이상이어야 합니다."

        self.stock_market[name] = Stock(name, price)
        if name not in DEFAULT_STOCKS and name not in self.extra_names:
            self.extra_names.append(name)
            self.extra_prices[name] = int(price)
            utils.save_extra_stock_names(self.extra_names)
            utils.save_extra_stock_prices(self.extra_prices)

        if self.current_stock is None:
            self.current_stock = name
        return True, f"{name} 종목 추가 완료"

    def remove_stock(self, name: str) -> Tuple[bool, str]:
        if name not in self.stock_market:
            return False, "존재하지 않는 종목입니다."

        del self.stock_market[name]
        if name in self.player.portfolio:
            del self.player.portfolio[name]

        if name in self.extra_names:
            self.extra_names.remove(name)
            utils.save_extra_stock_names(self.extra_names)

        if name in self.extra_prices:
            del self.extra_prices[name]
            utils.save_extra_stock_prices(self.extra_prices)

        if self.current_stock == name:
            self.current_stock = next(iter(self.stock_market), None)
        return True, f"{name} 종목 삭제 완료"

    def change_money(self, amount: int) -> Tuple[bool, str]:
        if self.player.money + amount < 0:
            return False, "보유 금액은 0원보다 작아질 수 없습니다."

        self.player.money += amount
        self.update_high_score()

        if amount >= 0:
            return True, f"{format_money(amount)} 추가 완료"
        return True, f"{format_money(abs(amount))} 차감 완료"

    def next_day(self) -> Tuple[List[str], List[str]]:
        logs: List[str] = []
        delisted: List[str] = []

        for stock in list(self.stock_market.values()):
            old_price, new_price = stock.update_price()
            direction = "상승" if new_price > old_price else ("하락" if new_price < old_price else "보합")
            logs.append(f"{stock.name}: {old_price:,}원 → {new_price:,}원 ({direction}, {stock.change}%)")

        for name, stock in list(self.stock_market.items()):
            if stock.is_delisted():
                delisted.append(name)
                del self.stock_market[name]
                if name in self.player.portfolio:
                    del self.player.portfolio[name]
                if name in self.extra_names:
                    self.extra_names.remove(name)
                    utils.save_extra_stock_names(self.extra_names)
                if name in self.extra_prices:
                    del self.extra_prices[name]
                    utils.save_extra_stock_prices(self.extra_prices)

        self.day += 1
        for stock in self.stock_market.values():
            stock.decide_change()

        if self.current_stock not in self.stock_market:
            self.current_stock = next(iter(self.stock_market), None)

        self.update_high_score()
        return logs, delisted