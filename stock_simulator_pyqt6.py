# -*- coding: utf-8 -*-
"""
Stock Simulator - PyQt6 only version

기능 요약
- 시작 화면: 사용자가 제공한 Qt Designer XML 구조를 PyQt6 코드로 재현
- 게임 화면: 종목 선택, 매수, 매도, 포트폴리오, 총자산, 수익률, 최고기록
- 뉴스 시스템: 오늘 공개된 뉴스가 다음 날 가격 변동률에 반영됨
- 그래프: PyQt6 QPainter로 직접 주가 그래프를 그림
- 관리자 모드: 종목 추가/삭제, 보유 금액 증감
- 파일 연동: stock.txt, max.txt 자동 생성 및 사용

필요 패키지
    pip install PyQt6

실행
    python stock_simulator_pyqt6.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


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


# ============================================
# 파일 유틸
# ============================================

def ensure_data_files() -> None:
    """stock.txt, max.txt, stock_prices.json이 없으면 자동 생성한다."""
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
    """
    기존 콘솔 관리자 코드와 호환되도록 stock.txt에서는 종목명만 읽는다.
    공백 줄, 기본 종목, 중복 종목은 제외한다.
    """
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
    """stock.txt에는 추가 종목 이름만 한 줄씩 저장한다."""
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
    """
    PyQt6 관리자 모드에서 지정한 추가 종목 가격을 별도 JSON에 저장한다.
    stock.txt는 기존 콘솔 코드와 호환되도록 종목명만 보관한다.
    """
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


def format_money(value: float) -> str:
    return f"{value:,.0f}원"


# ============================================
# 주식 / 플레이어 모델
# ============================================

class Stock:
    def __init__(self, name: str, price: int):
        self.name = name
        self.price = int(price)
        self.start_price = int(price)
        self.history: List[int] = [int(price)]
        self.change = 100
        self.decide_change()

    def decide_change(self) -> None:
        """다음 날 반영될 가격 변동률을 결정한다. 70~130% 범위."""
        self.change = random.randint(70, 130)

    def update_price(self) -> Tuple[int, int]:
        """미리 결정된 변동률을 가격에 반영한다."""
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
        # {종목명: {"quantity": int, "buy_price": float}}
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
        ensure_data_files()
        self.extra_prices = load_extra_stock_prices()
        self.extra_names = load_extra_stock_names()
        self.stock_market: Dict[str, Stock] = self._create_initial_market()
        self.player = Player(INITIAL_MONEY)
        self.day = 1
        self.max_money = load_max_money()
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
            save_max_money(self.max_money)
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
            save_extra_stock_names(self.extra_names)
            save_extra_stock_prices(self.extra_prices)

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
            save_extra_stock_names(self.extra_names)

        if name in self.extra_prices:
            del self.extra_prices[name]
            save_extra_stock_prices(self.extra_prices)

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
        """
        현재 DAY의 뉴스에 해당하는 변동률을 가격에 반영하고,
        상장폐지 종목을 제거한 뒤 다음 DAY 뉴스 변동률을 새로 결정한다.
        """
        logs: List[str] = []
        delisted: List[str] = []

        for stock in list(self.stock_market.values()):
            old_price, new_price = stock.update_price()
            if new_price > old_price:
                direction = "상승"
            elif new_price < old_price:
                direction = "하락"
            else:
                direction = "보합"
            logs.append(
                f"{stock.name}: {old_price:,}원 → {new_price:,}원 "
                f"({direction}, {stock.change}%)"
            )

        for name, stock in list(self.stock_market.items()):
            if stock.is_delisted():
                delisted.append(name)
                del self.stock_market[name]
                if name in self.player.portfolio:
                    del self.player.portfolio[name]
                if name in self.extra_names:
                    self.extra_names.remove(name)
                    save_extra_stock_names(self.extra_names)
                if name in self.extra_prices:
                    del self.extra_prices[name]
                    save_extra_stock_prices(self.extra_prices)

        self.day += 1

        for stock in self.stock_market.values():
            stock.decide_change()

        if self.current_stock not in self.stock_market:
            self.current_stock = next(iter(self.stock_market), None)

        self.update_high_score()
        return logs, delisted


# ============================================
# PyQt6 그래프 위젯
# ============================================

class StockChart(QWidget):
    """PyQt6 QPainter만 사용해서 선택 종목의 주가 기록을 그리는 위젯."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.stock: Optional[Stock] = None
        self.setMinimumSize(640, 360)

    def draw_stock(self, stock: Optional[Stock]) -> None:
        self.stock = stock
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt method name
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        if self.stock is None:
            painter.setPen(QPen(QColor("#666666")))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "표시할 종목이 없습니다",
            )
            return

        history = self.stock.history
        rect = self.rect()
        margin_left = 82
        margin_top = 56
        margin_right = 32
        margin_bottom = 62

        chart = QRectF(
            margin_left,
            margin_top,
            max(10, rect.width() - margin_left - margin_right),
            max(10, rect.height() - margin_top - margin_bottom),
        )

        self._draw_title(painter, chart)
        self._draw_grid_and_axes(painter, chart, history)
        self._draw_line(painter, chart, history)
        self._draw_axis_names(painter, chart)

    def _price_bounds(self, history: List[int]) -> Tuple[float, float]:
        low = float(min(history))
        high = float(max(history))
        if low == high:
            padding = max(1000.0, high * 0.1)
        else:
            padding = (high - low) * 0.12
        return max(0.0, low - padding), high + padding

    def _draw_title(self, painter: QPainter, chart: QRectF) -> None:
        painter.setPen(QPen(QColor("#222222")))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(
            QRectF(0, 12, self.width(), 32),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.stock.name} 주가 그래프",
        )
        normal_font = QFont()
        normal_font.setPointSize(9)
        painter.setFont(normal_font)

    def _draw_grid_and_axes(self, painter: QPainter, chart: QRectF, history: List[int]) -> None:
        lower, upper = self._price_bounds(history)
        price_range = max(1.0, upper - lower)

        grid_pen = QPen(QColor("#E5E5E5"))
        axis_pen = QPen(QColor("#333333"))
        text_pen = QPen(QColor("#555555"))

        painter.setFont(QFont("", 8))

        # 가로 격자와 가격 라벨
        painter.setPen(grid_pen)
        for i in range(6):
            y = chart.bottom() - chart.height() * i / 5
            painter.drawLine(QPointF(chart.left(), y), QPointF(chart.right(), y))

            price = lower + price_range * i / 5
            painter.setPen(text_pen)
            painter.drawText(
                QRectF(0, y - 10, chart.left() - 8, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{price:,.0f}",
            )
            painter.setPen(grid_pen)

        # 세로 격자와 DAY 라벨
        n = len(history)
        label_count = min(6, n)
        if label_count <= 1:
            indices = [0]
        else:
            indices = sorted({round(i * (n - 1) / (label_count - 1)) for i in range(label_count)})

        for index in indices:
            x = self._x_for_index(chart, index, n)
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(x, chart.top()), QPointF(x, chart.bottom()))
            painter.setPen(text_pen)
            painter.drawText(
                QRectF(x - 24, chart.bottom() + 8, 48, 20),
                Qt.AlignmentFlag.AlignCenter,
                str(index + 1),
            )

        # 축
        painter.setPen(axis_pen)
        painter.drawLine(QPointF(chart.left(), chart.top()), QPointF(chart.left(), chart.bottom()))
        painter.drawLine(QPointF(chart.left(), chart.bottom()), QPointF(chart.right(), chart.bottom()))

    def _draw_line(self, painter: QPainter, chart: QRectF, history: List[int]) -> None:
        lower, upper = self._price_bounds(history)
        price_range = max(1.0, upper - lower)
        n = len(history)

        points = []
        for index, price in enumerate(history):
            x = self._x_for_index(chart, index, n)
            y = chart.bottom() - ((price - lower) / price_range) * chart.height()
            points.append(QPointF(x, y))

        line_pen = QPen(QColor("#3A7BFF"))
        line_pen.setWidth(3)
        painter.setPen(line_pen)

        if len(points) >= 2:
            painter.drawPolyline(QPolygonF(points))

        point_pen = QPen(QColor("#1F4FBF"))
        painter.setPen(point_pen)
        painter.setBrush(QBrush(QColor("#3A7BFF")))
        for point in points:
            painter.drawEllipse(point, 4.2, 4.2)

        # 마지막 가격 라벨
        if points:
            last_point = points[-1]
            painter.setPen(QPen(QColor("#222222")))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            label = f"{history[-1]:,}원"
            label_rect = QRectF(
                min(last_point.x() + 8, chart.right() - 88),
                max(chart.top(), last_point.y() - 14),
                88,
                24,
            )
            painter.drawRect(label_rect)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_axis_names(self, painter: QPainter, chart: QRectF) -> None:
        painter.setPen(QPen(QColor("#555555")))
        painter.setFont(QFont("", 9))
        painter.drawText(
            QRectF(chart.left(), chart.bottom() + 34, chart.width(), 22),
            Qt.AlignmentFlag.AlignCenter,
            "DAY",
        )
        painter.save()
        painter.translate(18, chart.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-70, -12, 140, 24),
            Qt.AlignmentFlag.AlignCenter,
            "가격",
        )
        painter.restore()

    def _x_for_index(self, chart: QRectF, index: int, count: int) -> float:
        if count <= 1:
            return chart.center().x()
        return chart.left() + chart.width() * index / (count - 1)


# ============================================
# 관리자 다이얼로그
# ============================================

class AdminDialog(QDialog):
    def __init__(
        self,
        state: GameState,
        parent: Optional[QWidget] = None,
        on_changed: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.state = state
        self.on_changed = on_changed
        self.setWindowTitle("관리자 모드")
        self.resize(460, 520)
        self._build_ui()
        self.refresh_stock_combo()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # 종목 추가
        add_group = QGroupBox("주식 종목 추가")
        add_layout = QFormLayout(add_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("예: 현대차")

        self.price_spin = QSpinBox()
        self.price_spin.setRange(1, 2_000_000_000)
        self.price_spin.setValue(EXTRA_STOCK_DEFAULT_PRICE)
        self.price_spin.setSingleStep(1_000)
        self.price_spin.setSuffix("원")

        self.add_button = QPushButton("종목 추가")
        self.add_button.clicked.connect(self.add_stock)

        add_layout.addRow("종목 이름", self.name_edit)
        add_layout.addRow("초기 가격", self.price_spin)
        add_layout.addRow(self.add_button)

        # 종목 삭제
        remove_group = QGroupBox("주식 종목 삭제")
        remove_layout = QFormLayout(remove_group)

        self.remove_combo = QComboBox()
        self.remove_button = QPushButton("선택 종목 삭제")
        self.remove_button.clicked.connect(self.remove_stock)

        remove_layout.addRow("종목 선택", self.remove_combo)
        remove_layout.addRow(self.remove_button)

        # 금액 조정
        money_group = QGroupBox("보유 금액 증감")
        money_layout = QFormLayout(money_group)

        self.money_spin = QSpinBox()
        self.money_spin.setRange(-2_000_000_000, 2_000_000_000)
        self.money_spin.setSingleStep(10_000)
        self.money_spin.setSuffix("원")

        self.money_button = QPushButton("금액 적용")
        self.money_button.clicked.connect(self.change_money)

        money_layout.addRow("변동 금액", self.money_spin)
        money_layout.addRow(self.money_button)

        info = QLabel(
            "※ stock.txt에는 추가 종목 이름만 저장합니다.\n"
            "※ 추가 종목 가격은 stock_prices.json에 저장합니다.\n"
            "※ 그래프는 PyQt6 QPainter로 표시합니다."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray;")

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(add_group)
        main_layout.addWidget(remove_group)
        main_layout.addWidget(money_group)
        main_layout.addWidget(info)
        main_layout.addStretch(1)
        main_layout.addWidget(close_button)

    def refresh_stock_combo(self) -> None:
        self.remove_combo.clear()
        self.remove_combo.addItems(list(self.state.stock_market.keys()))
        self.remove_button.setEnabled(self.remove_combo.count() > 0)

    def emit_changed(self) -> None:
        if callable(self.on_changed):
            self.on_changed()
        self.refresh_stock_combo()

    def add_stock(self) -> None:
        name = self.name_edit.text().strip()
        price = self.price_spin.value()
        ok, message = self.state.add_stock(name, price)

        if ok:
            QMessageBox.information(self, "완료", message)
            self.name_edit.clear()
            self.price_spin.setValue(EXTRA_STOCK_DEFAULT_PRICE)
            self.emit_changed()
        else:
            QMessageBox.warning(self, "오류", message)

    def remove_stock(self) -> None:
        name = self.remove_combo.currentText().strip()
        if not name:
            return

        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"{name} 종목을 삭제할까요?\n보유 중이면 포트폴리오에서도 제거됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, message = self.state.remove_stock(name)
        if ok:
            QMessageBox.information(self, "완료", message)
            self.emit_changed()
        else:
            QMessageBox.warning(self, "오류", message)

    def change_money(self) -> None:
        amount = self.money_spin.value()
        ok, message = self.state.change_money(amount)
        if ok:
            QMessageBox.information(self, "완료", message)
            self.money_spin.setValue(0)
            self.emit_changed()
        else:
            QMessageBox.warning(self, "오류", message)


# ============================================
# 게임 화면
# ============================================

class GameWindow(QMainWindow):
    def __init__(self, state: GameState, start_window: Optional[QWidget] = None):
        super().__init__()
        self.state = state
        self.start_window = start_window
        self.setWindowTitle("Stock Simulator - 게임")
        self.resize(1250, 760)
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        # 왼쪽 패널
        left_panel = QWidget()
        left_panel.setMinimumWidth(330)
        left_panel.setMaximumWidth(380)
        left_layout = QVBoxLayout(left_panel)

        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.money_label = QLabel()
        self.total_asset_label = QLabel()
        self.profit_rate_label = QLabel()
        self.max_label = QLabel()
        for label in [self.money_label, self.total_asset_label, self.profit_rate_label, self.max_label]:
            label.setStyleSheet("font-size: 14px;")

        self.stock_combo = QComboBox()
        self.stock_combo.currentTextChanged.connect(self.on_stock_changed)

        self.price_label = QLabel()
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.price_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px;")

        self.news_label = QLabel()
        self.news_label.setWordWrap(True)
        self.news_label.setStyleSheet("font-size: 13px; color: #555555;")

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1_000_000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setSuffix("주")

        buy_button = QPushButton("매수")
        buy_button.setMinimumHeight(36)
        buy_button.clicked.connect(self.buy_stock)

        sell_button = QPushButton("매도")
        sell_button.setMinimumHeight(36)
        sell_button.clicked.connect(self.sell_stock)

        next_day_button = QPushButton("다음 날")
        next_day_button.setMinimumHeight(40)
        next_day_button.setStyleSheet("font-weight: bold;")
        next_day_button.clicked.connect(self.next_day)

        news_button = QPushButton("뉴스 보기")
        news_button.clicked.connect(self.show_news_popup)

        admin_button = QPushButton("관리자 모드")
        admin_button.clicked.connect(self.open_admin_dialog)

        start_button = QPushButton("시작 화면으로")
        start_button.clicked.connect(self.back_to_start)

        self.portfolio_text = QTextEdit()
        self.portfolio_text.setReadOnly(True)
        self.portfolio_text.setMinimumHeight(210)

        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMinimumHeight(120)

        button_row = QHBoxLayout()
        button_row.addWidget(buy_button)
        button_row.addWidget(sell_button)

        left_layout.addWidget(self.day_label)
        left_layout.addSpacing(4)
        left_layout.addWidget(self.money_label)
        left_layout.addWidget(self.total_asset_label)
        left_layout.addWidget(self.profit_rate_label)
        left_layout.addWidget(self.max_label)
        left_layout.addSpacing(10)
        left_layout.addWidget(QLabel("종목 선택"))
        left_layout.addWidget(self.stock_combo)
        left_layout.addWidget(self.price_label)
        left_layout.addWidget(self.news_label)
        left_layout.addSpacing(8)
        left_layout.addWidget(QLabel("수량 입력"))
        left_layout.addWidget(self.quantity_spin)
        left_layout.addLayout(button_row)
        left_layout.addWidget(next_day_button)
        left_layout.addWidget(news_button)
        left_layout.addWidget(admin_button)
        left_layout.addWidget(start_button)
        left_layout.addSpacing(8)
        left_layout.addWidget(QLabel("포트폴리오"))
        left_layout.addWidget(self.portfolio_text, 1)
        left_layout.addWidget(QLabel("진행 기록"))
        left_layout.addWidget(self.event_log, 1)

        # 오른쪽 패널: 종목 현황 + PyQt6 직접 그래프
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.stock_table = QTableWidget(0, 4)
        self.stock_table.setHorizontalHeaderLabels(["종목", "현재가", "오늘의 뉴스", "보유 수량"])
        header = self.stock_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stock_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.stock_table.cellClicked.connect(self.on_table_clicked)

        self.graph = StockChart(self)

        splitter = QSplitter(Qt.Orientation.Vertical)
        table_box = QWidget()
        table_layout = QVBoxLayout(table_box)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_title = QLabel("시장 현황")
        table_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        table_layout.addWidget(table_title)
        table_layout.addWidget(self.stock_table)
        splitter.addWidget(table_box)
        splitter.addWidget(self.graph)
        splitter.setSizes([230, 500])

        right_layout.addWidget(splitter)

        root_layout.addWidget(left_panel)
        root_layout.addWidget(right_panel, 1)

    def current_stock(self) -> Optional[Stock]:
        name = self.state.current_stock
        if name is None:
            return None
        return self.state.stock_market.get(name)

    def refresh_stock_combo(self) -> None:
        self.stock_combo.blockSignals(True)
        self.stock_combo.clear()
        self.stock_combo.addItems(list(self.state.stock_market.keys()))

        if self.state.current_stock in self.state.stock_market:
            index = self.stock_combo.findText(self.state.current_stock)
            if index >= 0:
                self.stock_combo.setCurrentIndex(index)
        elif self.stock_combo.count() > 0:
            self.stock_combo.setCurrentIndex(0)
            self.state.current_stock = self.stock_combo.currentText()
        else:
            self.state.current_stock = None

        self.stock_combo.blockSignals(False)

    def refresh_table(self) -> None:
        self.stock_table.setRowCount(len(self.state.stock_market))

        for row, stock in enumerate(self.state.stock_market.values()):
            quantity = 0
            if stock.name in self.state.player.portfolio:
                quantity = int(self.state.player.portfolio[stock.name]["quantity"])

            values = [
                stock.name,
                format_money(stock.price),
                stock.news_text(),
                f"{quantity}주",
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in (1, 3):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                self.stock_table.setItem(row, col, item)

            if stock.name == self.state.current_stock:
                self.stock_table.selectRow(row)

    def refresh_portfolio(self) -> None:
        player = self.state.player
        lines = [f"보유 현금: {format_money(player.money)}", ""]

        if not player.portfolio:
            lines.append("보유 주식 없음")
        else:
            for stock_name, info in player.portfolio.items():
                stock = self.state.stock_market.get(stock_name)
                if stock is None:
                    continue

                quantity = int(info["quantity"])
                buy_price = float(info["buy_price"])
                value = stock.price * quantity
                profit = value - buy_price * quantity
                profit_rate = ((stock.price - buy_price) / buy_price) * 100 if buy_price else 0

                lines.extend([
                    f"종목: {stock_name}",
                    f"보유 수량: {quantity}주",
                    f"평균 매수가: {buy_price:,.0f}원",
                    f"현재가: {stock.price:,}원",
                    f"현재 가치: {value:,}원",
                    f"손익: {profit:,.0f}원 ({profit_rate:.2f}%)",
                    "",
                ])

        total_assets = player.calculate_total_assets(self.state.stock_market)
        profit_rate = player.calculate_profit_rate(self.state.stock_market, INITIAL_MONEY)
        lines.extend([
            "------------------------------",
            f"총 자산: {format_money(total_assets)}",
            f"전체 수익률: {profit_rate:.2f}%",
        ])
        self.portfolio_text.setPlainText("\n".join(lines))

    def refresh_summary_labels(self) -> None:
        total_assets = self.state.player.calculate_total_assets(self.state.stock_market)
        profit_rate = self.state.player.calculate_profit_rate(self.state.stock_market, INITIAL_MONEY)
        stock = self.current_stock()

        self.day_label.setText(f"DAY {self.state.day}")
        self.money_label.setText(f"보유 금액: {format_money(self.state.player.money)}")
        self.total_asset_label.setText(f"총 자산: {format_money(total_assets)}")
        self.profit_rate_label.setText(f"수익률: {profit_rate:.2f}%")
        self.max_label.setText(f"최고기록: {format_money(self.state.max_money)}")

        if stock is None:
            self.price_label.setText("종목 없음")
            self.news_label.setText("관리자 모드에서 종목을 추가하세요.")
        else:
            self.price_label.setText(f"{stock.name}\n현재 가격: {stock.price:,}원")
            self.news_label.setText(f"오늘의 뉴스: {stock.news_text()}")

    def refresh_all(self) -> None:
        self.refresh_stock_combo()
        self.refresh_summary_labels()
        self.refresh_portfolio()
        self.refresh_table()
        self.graph.draw_stock(self.current_stock())

    def on_stock_changed(self, name: str) -> None:
        if name in self.state.stock_market:
            self.state.current_stock = name
        self.refresh_summary_labels()
        self.refresh_table()
        self.graph.draw_stock(self.current_stock())

    def on_table_clicked(self, row: int, _column: int) -> None:
        item = self.stock_table.item(row, 0)
        if item is None:
            return
        name = item.text()
        index = self.stock_combo.findText(name)
        if index >= 0:
            self.stock_combo.setCurrentIndex(index)

    def buy_stock(self) -> None:
        stock = self.current_stock()
        if stock is None:
            QMessageBox.warning(self, "오류", "매수할 종목이 없습니다.")
            return

        quantity = self.quantity_spin.value()
        ok, message = self.state.player.buy_stock(stock, quantity)
        if ok:
            self.state.update_high_score()
            QMessageBox.information(self, "매수 완료", message)
            self.add_log(message)
            self.refresh_all()
        else:
            QMessageBox.warning(self, "실패", message)

    def sell_stock(self) -> None:
        stock = self.current_stock()
        if stock is None:
            QMessageBox.warning(self, "오류", "매도할 종목이 없습니다.")
            return

        quantity = self.quantity_spin.value()
        ok, message = self.state.player.sell_stock(stock, quantity)
        if ok:
            self.state.update_high_score()
            QMessageBox.information(self, "매도 완료", message)
            self.add_log(message)
            self.refresh_all()
        else:
            QMessageBox.warning(self, "실패", message)

    def next_day(self) -> None:
        if not self.state.stock_market:
            QMessageBox.warning(self, "오류", "진행할 종목이 없습니다. 관리자 모드에서 종목을 추가하세요.")
            return

        old_day = self.state.day
        logs, delisted = self.state.next_day()

        self.add_log(f"===== DAY {old_day} → DAY {self.state.day} =====")
        for log in logs:
            self.add_log(log)
        for name in delisted:
            self.add_log(f"[상장 폐지] {name} 종목이 상장 폐지되었습니다.")
            QMessageBox.warning(self, "상장 폐지", f"{name} 종목이 상장 폐지되었습니다.")

        self.refresh_all()

    def show_news_popup(self) -> None:
        if not self.state.stock_market:
            QMessageBox.information(self, "오늘의 신문", "표시할 뉴스가 없습니다.")
            return

        news = "\n".join(stock.news_text() for stock in self.state.stock_market.values())
        QMessageBox.information(self, "오늘의 신문", news)

    def open_admin_dialog(self) -> None:
        dialog = AdminDialog(self.state, self, on_changed=self.refresh_all)
        dialog.exec()
        self.refresh_all()

    def back_to_start(self) -> None:
        self.hide()
        if self.start_window is not None:
            self.start_window.show()

    def add_log(self, text: str) -> None:
        self.event_log.append(text)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt method name
        if self.start_window is not None:
            self.start_window.close()
        event.accept()


# ============================================
# 시작 화면: 사용자가 준 .ui XML 구조를 PyQt6 코드로 재현
# ============================================

class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.state = GameState()
        self.game_window: Optional[GameWindow] = None
        self.setWindowTitle("Stock Simulator")
        self.resize(520, 420)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 30, 40, 30)

        layout.addStretch(1)

        title_label = QLabel("STOCK SIMULATOR")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")

        desc_label = QLabel("뉴스와 가격 변동을 보고 매수와 매도를 결정하는 게임입니다")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px; color: gray;")
        desc_label.setWordWrap(True)

        start_button = QPushButton("게임 시작 →")
        start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        start_button.setMinimumHeight(48)
        start_button.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #3A7BFF; "
            "color: white; border-radius: 6px;"
        )
        start_button.clicked.connect(self.start_game)

        admin_button = QPushButton("관리자 모드")
        admin_button.setCursor(Qt.CursorShape.PointingHandCursor)
        admin_button.setMinimumHeight(42)
        admin_button.setStyleSheet(
            "font-size: 16px; padding: 8px; background-color: white; "
            "border: 1px solid #CCCCCC; border-radius: 6px;"
        )
        admin_button.clicked.connect(self.open_admin_dialog)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addSpacing(12)
        layout.addWidget(start_button)
        layout.addWidget(admin_button)
        layout.addStretch(1)

    def start_game(self) -> None:
        if self.game_window is None:
            self.game_window = GameWindow(self.state, start_window=self)
        else:
            self.game_window.refresh_all()

        self.game_window.show()
        self.hide()

    def open_admin_dialog(self) -> None:
        def refresh_game_if_open() -> None:
            if self.game_window is not None:
                self.game_window.refresh_all()

        dialog = AdminDialog(self.state, self, on_changed=refresh_game_if_open)
        dialog.exec()
        refresh_game_if_open()


# ============================================
# 프로그램 실행
# ============================================

def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = StartWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()