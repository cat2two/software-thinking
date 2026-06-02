# -*- coding: utf-8 -*-
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QTextEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QMessageBox)
from config import INITIAL_MONEY, format_money
from models import GameState, Stock
from widgets import StockChart, AdminDialog

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

        left_panel = QWidget()
        left_panel.setMinimumWidth(330)
        left_panel.setMaximumWidth(380)
        left_layout = QVBoxLayout(left_panel)

        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.money_label, self.total_asset_label, self.profit_rate_label, self.max_label = QLabel(), QLabel(), QLabel(), QLabel()
        for lbl in [self.money_label, self.total_asset_label, self.profit_rate_label, self.max_label]:
            lbl.setStyleSheet("font-size: 14px;")

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

        buy_btn, sell_btn, next_btn = QPushButton("매수"), QPushButton("매도"), QPushButton("다음 날")
        buy_btn.clicked.connect(self.buy_stock)
        sell_btn.clicked.connect(self.sell_stock)
        next_btn.clicked.connect(self.next_day)
        next_btn.setStyleSheet("font-weight: bold;")

        news_btn = QPushButton("뉴스 보기")
        news_btn.clicked.connect(self.show_news_popup)

        admin_btn = QPushButton("관리자 모드")
        admin_btn.clicked.connect(self.open_admin_dialog)

        start_btn = QPushButton("시작 화면으로")
        start_btn.clicked.connect(self.back_to_start)

        self.portfolio_text, self.event_log = QTextEdit(), QTextEdit()
        self.portfolio_text.setReadOnly(True)
        self.event_log.setReadOnly(True)

        btn_row = QHBoxLayout()
        btn_row.addWidget(buy_btn)
        btn_row.addWidget(sell_btn)

        left_layout.addWidget(self.day_label)
        left_layout.addWidget(self.money_label)
        left_layout.addWidget(self.total_asset_label)
        left_layout.addWidget(self.profit_rate_label)
        left_layout.addWidget(self.max_label)
        left_layout.addWidget(QLabel("종목 선택"))
        left_layout.addWidget(self.stock_combo)
        left_layout.addWidget(self.price_label)
        left_layout.addWidget(self.news_label)
        left_layout.addWidget(QLabel("수량 입력"))
        left_layout.addWidget(self.quantity_spin)
        left_layout.addLayout(btn_row)
        left_layout.addWidget(next_btn)
        left_layout.addWidget(news_btn)
        left_layout.addWidget(admin_btn)
        left_layout.addWidget(start_btn)
        left_layout.addWidget(QLabel("포트폴리오"))
        left_layout.addWidget(self.portfolio_text, 1)
        left_layout.addWidget(QLabel("진행 기록"))
        left_layout.addWidget(self.event_log, 1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.stock_table = QTableWidget(0, 4)
        self.stock_table.setHorizontalHeaderLabels(["종목", "현재가", "오늘의 뉴스", "보유 수량"])
        self.stock_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stock_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.stock_table.cellClicked.connect(self.on_table_clicked)

        self.graph = StockChart(self)

        splitter = QSplitter(Qt.Orientation.Vertical)
        table_box = QWidget()
        table_layout = QVBoxLayout(table_box)
        table_layout.addWidget(QLabel("시장 현황"))
        table_layout.addWidget(self.stock_table)
        splitter.addWidget(table_box)
        splitter.addWidget(self.graph)
        splitter.setSizes([230, 500])

        right_layout.addWidget(splitter)
        root_layout.addWidget(left_panel)
        root_layout.addWidget(right_panel, 1)

    def current_stock(self) -> Optional[Stock]:
        return self.state.stock_market.get(self.state.current_stock) if self.state.current_stock else None

    def refresh_stock_combo(self) -> None:
        self.stock_combo.blockSignals(True)
        self.stock_combo.clear()
        self.stock_combo.addItems(list(self.state.stock_market.keys()))

        if self.state.current_stock in self.state.stock_market:
            self.stock_combo.setCurrentText(self.state.current_stock)
        elif self.stock_combo.count() > 0:
            self.stock_combo.setCurrentIndex(0)
            self.state.current_stock = self.stock_combo.currentText()
        else:
            self.state.current_stock = None
        self.stock_combo.blockSignals(False)

    def refresh_table(self) -> None:
        self.stock_table.setRowCount(len(self.state.stock_market))
        for row, stock in enumerate(self.state.stock_market.values()):
            quantity = int(self.state.player.portfolio.get(stock.name, {}).get("quantity", 0))
            values = [stock.name, format_money(stock.price), stock.news_text(), f"{quantity}주"]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment((Qt.AlignmentFlag.AlignRight if col in (1, 3) else Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter)
                self.stock_table.setItem(row, col, item)
            if stock.name == self.state.current_stock:
                self.stock_table.selectRow(row)

    def refresh_portfolio(self) -> None:
        player = self.state.player
        lines = [f"보유 현금: {format_money(player.money)}", ""]
        if not player.portfolio:
            lines.append("보유 주식 없음")
        else:
            for name, info in player.portfolio.items():
                stock = self.state.stock_market.get(name)
                if not stock: continue
                qty, buy_p = int(info["quantity"]), float(info["buy_price"])
                val = stock.price * qty
                profit = val - buy_p * qty
                rate = ((stock.price - buy_p) / buy_p) * 100 if buy_p else 0
                lines.extend([f"종목: {name}", f"보유 수량: {qty}주", f"평균 매수가: {buy_p:,.0f}원", f"현재가: {stock.price:,}원", f"현재 가치: {val:,}원", f"손익: {profit:,.0f}원 ({rate:.2f}%)", ""])

        total_assets = player.calculate_total_assets(self.state.stock_market)
        profit_rate = player.calculate_profit_rate(self.state.stock_market, INITIAL_MONEY)
        lines.extend(["------------------------------", f"총 자산: {format_money(total_assets)}", f"전체 수익률: {profit_rate:.2f}%"])
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

    def on_table_clicked(self, row: int, _col: int) -> None:
        item = self.stock_table.item(row, 0)
        if item and self.stock_combo.findText(item.text()) >= 0:
            self.stock_combo.setCurrentText(item.text())

    def buy_stock(self) -> None:
        stock = self.current_stock()
        if not stock: return
        ok, msg = self.state.player.buy_stock(stock, self.quantity_spin.value())
        if ok:
            self.state.update_high_score()
            QMessageBox.information(self, "매수 완료", msg)
            self.add_log(msg)
            self.refresh_all()
        else:
            QMessageBox.warning(self, "실패", msg)

    def sell_stock(self) -> None:
        stock = self.current_stock()
        if not stock: return
        ok, msg = self.state.player.sell_stock(stock, self.quantity_spin.value())
        if ok:
            self.state.update_high_score()
            QMessageBox.information(self, "매도 완료", msg)
            self.add_log(msg)
            self.refresh_all()
        else:
            QMessageBox.warning(self, "실패", msg)

    def next_day(self) -> None:
        if not self.state.stock_market: return
        old_day = self.state.day
        logs, delisted = self.state.next_day()
        self.add_log(f"===== DAY {old_day} → DAY {self.state.day} =====")
        for log in logs: self.add_log(log)
        for name in delisted:
            self.add_log(f"[상장 폐지] {name} 종목이 상장 폐지되었습니다.")
            QMessageBox.warning(self, "상장 폐지", f"{name} 종목이 상장 폐지되었습니다.")
        self.refresh_all()

    def show_news_popup(self) -> None:
        news = "\n".join(s.news_text() for s in self.state.stock_market.values()) if self.state.stock_market else "표시할 뉴스가 없습니다."
        QMessageBox.information(self, "오늘의 신문", news)

    def open_admin_dialog(self) -> None:
        AdminDialog(self.state, self, on_changed=self.refresh_all).exec()
        self.refresh_all()

    def back_to_start(self) -> None:
        self.hide()
        if self.start_window: self.start_window.show()

    def add_log(self, text: str) -> None:
        self.event_log.append(text)

    def closeEvent(self, event) -> None:
        if self.start_window: self.start_window.close()
        event.accept()


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
        layout.setContentsMargins(40, 30, 40, 30)
        layout.addStretch(1)

        title = QLabel("STOCK SIMULATOR")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")

        desc = QLabel("뉴스와 가격 변동을 보고 매수와 매도를 결정하는 게임입니다")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: gray;")

        start_btn = QPushButton("게임 시작 →")
        start_btn.setMinimumHeight(48)
        start_btn.setStyleSheet("font-size: 18px; background-color: #3A7BFF; color: white; border-radius: 6px;")
        start_btn.clicked.connect(self.start_game)

        admin_btn = QPushButton("관리자 모드")
        admin_btn.setMinimumHeight(42)
        admin_btn.setStyleSheet("font-size: 16px; background-color: white; border: 1px solid #CCCCCC; border-radius: 6px;")
        admin_btn.clicked.connect(self.open_admin_dialog)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(12)
        layout.addWidget(start_btn)
        layout.addWidget(admin_btn)
        layout.addStretch(1)

    def start_game(self) -> None:
        if self.game_window is None:
            self.game_window = GameWindow(self.state, start_window=self)
        else:
            self.game_window.refresh_all()
        self.game_window.show()
        self.hide()

    def open_admin_dialog(self) -> None:
        fn = lambda: self.game_window.refresh_all() if self.game_window else None
        AdminDialog(self.state, self, on_changed=fn).exec()
        fn()