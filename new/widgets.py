# -*- coding: utf-8 -*-
from typing import Optional, List, Tuple, Callable
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QSpinBox, QPushButton, QComboBox, QLabel, QMessageBox
from config import EXTRA_STOCK_DEFAULT_PRICE, format_money
from models import Stock, GameState

class StockChart(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.stock: Optional[Stock] = None
        self.setMinimumSize(640, 360)

    def draw_stock(self, stock: Optional[Stock]) -> None:
        self.stock = stock
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        if self.stock is None:
            painter.setPen(QPen(QColor("#666666")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "표시할 종목이 없습니다")
            return

        history = self.stock.history
        rect = self.rect()
        margin_left, margin_top, margin_right, margin_bottom = 82, 56, 32, 62

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
        low, high = float(min(history)), float(max(history))
        padding = max(1000.0, high * 0.1) if low == high else (high - low) * 0.12
        return max(0.0, low - padding), high + padding

    def _draw_title(self, painter: QPainter, chart: QRectF) -> None:
        painter.setPen(QPen(QColor("#222222")))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(QRectF(0, 12, self.width(), 32), Qt.AlignmentFlag.AlignCenter, f"{self.stock.name} 주가 그래프")
        painter.setFont(QFont("", 9))

    def _draw_grid_and_axes(self, painter: QPainter, chart: QRectF, history: List[int]) -> None:
        lower, upper = self._price_bounds(history)
        price_range = max(1.0, upper - lower)
        grid_pen, axis_pen, text_pen = QPen(QColor("#E5E5E5")), QPen(QColor("#333333")), QPen(QColor("#555555"))
        painter.setFont(QFont("", 8))

        # 가로 격자 및 라벨
        for i in range(6):
            y = chart.bottom() - chart.height() * i / 5
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(chart.left(), y), QPointF(chart.right(), y))
            price = lower + price_range * i / 5
            painter.setPen(text_pen)
            painter.drawText(QRectF(0, y - 10, chart.left() - 8, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{price:,.0f}")

        # 세로 격자 및 라벨
        n = len(history)
        label_count = min(6, n)
        indices = [0] if label_count <= 1 else sorted({round(i * (n - 1) / (label_count - 1)) for i in range(label_count)})

        for index in indices:
            x = self._x_for_index(chart, index, n)
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(x, chart.top()), QPointF(x, chart.bottom()))
            painter.setPen(text_pen)
            painter.drawText(QRectF(x - 24, chart.bottom() + 8, 48, 20), Qt.AlignmentFlag.AlignCenter, str(index + 1))

        painter.setPen(axis_pen)
        painter.drawLine(QPointF(chart.left(), chart.top()), QPointF(chart.left(), chart.bottom()))
        painter.drawLine(QPointF(chart.left(), chart.bottom()), QPointF(chart.right(), chart.bottom()))

    def _draw_line(self, painter: QPainter, chart: QRectF, history: List[int]) -> None:
        lower, upper = self._price_bounds(history)
        price_range = max(1.0, upper - lower)
        n = len(history)

        points = [QPointF(self._x_for_index(chart, idx, n), chart.bottom() - ((p - lower) / price_range) * chart.height()) for idx, p in enumerate(history)]

        line_pen = QPen(QColor("#3A7BFF"))
        line_pen.setWidth(3)
        painter.setPen(line_pen)
        if len(points) >= 2:
            painter.drawPolyline(QPolygonF(points))

        painter.setPen(QPen(QColor("#1F4FBF")))
        painter.setBrush(QBrush(QColor("#3A7BFF")))
        for pt in points:
            painter.drawEllipse(pt, 4.2, 4.2)

        if points:
            last_pt = points[-1]
            painter.setPen(QPen(QColor("#222222")))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            label_rect = QRectF(min(last_pt.x() + 8, chart.right() - 88), max(chart.top(), last_pt.y() - 14), 88, 24)
            painter.drawRect(label_rect)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, f"{history[-1]:,}원")

    def _draw_axis_names(self, painter: QPainter, chart: QRectF) -> None:
        painter.setPen(QPen(QColor("#555555")))
        painter.setFont(QFont("", 9))
        painter.drawText(QRectF(chart.left(), chart.bottom() + 34, chart.width(), 22), Qt.AlignmentFlag.AlignCenter, "DAY")
        painter.save()
        painter.translate(18, chart.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-70, -12, 140, 24), Qt.AlignmentFlag.AlignCenter, "가격")
        painter.restore()

    def _x_for_index(self, chart: QRectF, index: int, count: int) -> float:
        return chart.left() + chart.width() * index / (count - 1) if count > 1 else chart.center().x()


class AdminDialog(QDialog):
    def __init__(self, state: GameState, parent: Optional[QWidget] = None, on_changed: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.state = state
        self.on_changed = on_changed
        self.setWindowTitle("관리자 모드")
        self.resize(460, 520)
        self._build_ui()
        self.refresh_stock_combo()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

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

        remove_group = QGroupBox("주식 종목 삭제")
        remove_layout = QFormLayout(remove_group)
        self.remove_combo = QComboBox()
        self.remove_button = QPushButton("선택 종목 삭제")
        self.remove_button.clicked.connect(self.remove_stock)
        remove_layout.addRow("종목 선택", self.remove_combo)
        remove_layout.addRow(self.remove_button)

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

        info = QLabel("※ stock.txt에는 추가 종목 이름만 저장합니다.\n※ 추가 종목 가격은 stock_prices.json에 저장합니다.")
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
        name, price = self.name_edit.text().strip(), self.price_spin.value()
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
        if not name or QMessageBox.question(self, "삭제 확인", f"{name} 종목을 삭제할까요?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
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