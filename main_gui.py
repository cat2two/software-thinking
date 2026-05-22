# ============================================
# 주식 시뮬레이터
# GUI + 그래프 + 관리자 모드
# ============================================

import random
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# ============================================
# 주식 클래스
# ============================================

class Stock:

    def __init__(self, name, price):

        self.name = name
        self.price = price

        # 최초 가격 저장
        self.initial_price = price

        # 주가 기록 저장
        self.history = [price]

    # ========================================
    # 주가 변동
    # ========================================

    def update_price(self):

        change = random.randint(-5000, 5000)

        self.price += change

        # 최소 가격 제한
        if self.price < 1000:
            self.price = 1000

        self.history.append(self.price)


# ============================================
# 플레이어 클래스
# ============================================

class Player:

    def __init__(self, money):

        self.money = money

        # 보유 주식
        self.portfolio = {}

    # ========================================
    # 매수
    # ========================================

    def buy_stock(self, stock, quantity):

        total_price = stock.price * quantity

        # 돈 부족
        if total_price > self.money:
            return False

        # 돈 차감
        self.money -= total_price

        # 이미 보유 중
        if stock.name in self.portfolio:

            current_quantity = self.portfolio[stock.name]["quantity"]

            self.portfolio[stock.name]["quantity"] = (
                current_quantity + quantity
            )

        # 처음 구매
        else:

            self.portfolio[stock.name] = {
                "quantity": quantity
            }

        return True

    # ========================================
    # 매도
    # ========================================

    def sell_stock(self, stock, quantity):

        # 보유 여부 확인
        if stock.name not in self.portfolio:
            return False

        current_quantity = self.portfolio[stock.name]["quantity"]

        # 수량 부족
        if quantity > current_quantity:
            return False

        # 판매 금액
        total_price = stock.price * quantity

        # 돈 증가
        self.money += total_price

        # 수량 감소
        self.portfolio[stock.name]["quantity"] -= quantity

        # 0주면 삭제
        if self.portfolio[stock.name]["quantity"] == 0:

            del self.portfolio[stock.name]

        return True


# ============================================
# GUI 클래스
# ============================================

class StockSimulatorGUI:

    def __init__(self, root):

        self.root = root

        self.root.title("주식 시뮬레이터")

        self.root.geometry("1200x700")

        # ====================================
        # 주식 시장 생성
        # ====================================

        self.stock_market = {

            "삼성전자": Stock("삼성전자", 70000),
            "테슬라": Stock("테슬라", 250000),
            "애플": Stock("애플", 180000)

        }

        # ====================================
        # 플레이어 생성
        # ====================================

        self.player = Player(1000000)

        # 현재 선택 종목
        self.current_stock = "삼성전자"

        # 날짜
        self.day = 1

        self.create_widgets()

        self.update_display()

        self.draw_graph()

    # ========================================
    # 위젯 생성
    # ========================================

    def create_widgets(self):

        # 왼쪽 프레임
        left_frame = tk.Frame(self.root)

        left_frame.pack(
            side=tk.LEFT,
            fill=tk.Y,
            padx=10,
            pady=10
        )

        # 오른쪽 프레임
        right_frame = tk.Frame(self.root)

        right_frame.pack(
            side=tk.RIGHT,
            fill=tk.BOTH,
            expand=True
        )

        # ====================================
        # 정보 라벨
        # ====================================

        self.money_label = tk.Label(
            left_frame,
            text="",
            font=("Arial", 14)
        )

        self.money_label.pack(pady=10)

        self.day_label = tk.Label(
            left_frame,
            text="",
            font=("Arial", 14)
        )

        self.day_label.pack(pady=10)

        # ====================================
        # 종목 선택
        # ====================================

        tk.Label(
            left_frame,
            text="종목 선택",
            font=("Arial", 13, "bold")
        ).pack(pady=5)

        self.stock_combo = ttk.Combobox(
            left_frame,
            values=list(self.stock_market.keys()),
            state="readonly"
        )

        self.stock_combo.current(0)

        self.stock_combo.pack(pady=5)

        self.stock_combo.bind(
            "<<ComboboxSelected>>",
            self.change_stock
        )

        # ====================================
        # 현재 가격
        # ====================================

        self.price_label = tk.Label(
            left_frame,
            text="",
            font=("Arial", 15, "bold")
        )

        self.price_label.pack(pady=20)

        # ====================================
        # 수량 입력
        # ====================================

        tk.Label(left_frame, text="수량 입력").pack()

        self.amount_entry = tk.Entry(left_frame)

        self.amount_entry.pack(pady=5)

        # ====================================
        # 버튼들
        # ====================================

        buy_button = tk.Button(
            left_frame,
            text="매수",
            width=15,
            height=2,
            command=self.buy_stock
        )

        buy_button.pack(pady=5)

        sell_button = tk.Button(
            left_frame,
            text="매도",
            width=15,
            height=2,
            command=self.sell_stock
        )

        sell_button.pack(pady=5)

        next_day_button = tk.Button(
            left_frame,
            text="다음 날",
            width=15,
            height=2,
            command=self.next_day
        )

        next_day_button.pack(pady=10)

        admin_button = tk.Button(
            left_frame,
            text="관리자 모드",
            width=15,
            height=2,
            command=self.admin_mode
        )

        admin_button.pack(pady=10)

        # ====================================
        # 포트폴리오
        # ====================================

        tk.Label(
            left_frame,
            text="포트폴리오",
            font=("Arial", 13, "bold")
        ).pack(pady=5)

        self.portfolio_text = tk.Text(
            left_frame,
            width=30,
            height=15
        )

        self.portfolio_text.pack(pady=5)

        # ====================================
        # 그래프
        # ====================================

        self.figure = Figure(figsize=(7, 5), dpi=100)

        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=right_frame
        )

        self.canvas.get_tk_widget().pack(
            fill=tk.BOTH,
            expand=True
        )

    # ========================================
    # 화면 업데이트
    # ========================================

    def update_display(self):

        if self.current_stock not in self.stock_market:

            if len(self.stock_market) == 0:
                return

            self.current_stock = list(
                self.stock_market.keys()
            )[0]

        stock = self.stock_market[self.current_stock]

        self.money_label.config(
            text=f"보유 금액: {self.player.money:,}원"
        )

        self.day_label.config(
            text=f"DAY: {self.day}"
        )

        self.price_label.config(
            text=f"{stock.name}\n현재 가격: {stock.price:,}원"
        )

        # 포트폴리오 출력
        self.portfolio_text.delete("1.0", tk.END)

        total_assets = self.player.money

        for stock_name, info in self.player.portfolio.items():

            quantity = info["quantity"]

            current_price = self.stock_market[stock_name].price

            value = current_price * quantity

            total_assets += value

            self.portfolio_text.insert(
                tk.END,
                f"{stock_name}\n"
                f"보유 수량: {quantity}주\n"
                f"현재 가치: {value:,}원\n\n"
            )

        self.portfolio_text.insert(
            tk.END,
            f"\n총 자산: {total_assets:,}원"
        )

    # ========================================
    # 그래프
    # ========================================

    def draw_graph(self):

        if self.current_stock not in self.stock_market:
            return

        stock = self.stock_market[self.current_stock]

        self.ax.clear()

        self.ax.plot(
            stock.history,
            marker='o',
            linewidth=2,
            label=stock.name
        )

        self.ax.set_title(f"{stock.name} 주가 그래프")
        self.ax.set_xlabel("DAY")
        self.ax.set_ylabel("가격")

        self.ax.grid()
        self.ax.legend()

        self.canvas.draw()

    # ========================================
    # 종목 변경
    # ========================================

    def change_stock(self, event):

        self.current_stock = self.stock_combo.get()

        self.update_display()

        self.draw_graph()

    # ========================================
    # 매수
    # ========================================

    def buy_stock(self):

        stock = self.stock_market[self.current_stock]

        try:

            quantity = int(self.amount_entry.get())

            if quantity <= 0:
                raise ValueError

        except:

            messagebox.showerror(
                "오류",
                "올바른 수량을 입력하세요"
            )

            return

        success = self.player.buy_stock(
            stock,
            quantity
        )

        if success:

            messagebox.showinfo(
                "매수 완료",
                f"{stock.name} {quantity}주 구매 완료"
            )

        else:

            messagebox.showerror(
                "실패",
                "돈이 부족합니다"
            )

        self.update_display()

    # ========================================
    # 매도
    # ========================================

    def sell_stock(self):

        stock = self.stock_market[self.current_stock]

        try:

            quantity = int(self.amount_entry.get())

            if quantity <= 0:
                raise ValueError

        except:

            messagebox.showerror(
                "오류",
                "올바른 수량을 입력하세요"
            )

            return

        success = self.player.sell_stock(
            stock,
            quantity
        )

        if success:

            messagebox.showinfo(
                "매도 완료",
                f"{stock.name} {quantity}주 판매 완료"
            )

        else:

            messagebox.showerror(
                "실패",
                "보유 주식이 부족합니다"
            )

        self.update_display()

    # ========================================
    # 상장 폐지 체크
    # ========================================

    def check_delisting(self):

        remove_list = []

        for stock_name, stock in self.stock_market.items():

            if stock.price <= stock.initial_price / 10:

                remove_list.append(stock_name)

        for stock_name in remove_list:

            del self.stock_market[stock_name]

            if stock_name in self.player.portfolio:

                del self.player.portfolio[stock_name]

            messagebox.showwarning(
                "상장 폐지",
                f"{stock_name} 종목이 상장 폐지되었습니다."
            )

        self.stock_combo["values"] = list(
            self.stock_market.keys()
        )

    # ========================================
    # 다음 날
    # ========================================

    def next_day(self):

        self.day += 1

        for stock in self.stock_market.values():

            stock.update_price()

        self.check_delisting()

        self.update_display()

        self.draw_graph()

    # ========================================
    # 관리자 모드
    # ========================================

    def admin_mode(self):

        admin_window = tk.Toplevel(self.root)

        admin_window.title("관리자 모드")

        admin_window.geometry("400x600")

        # ====================================
        # 종목 추가
        # ====================================

        tk.Label(
            admin_window,
            text="주식 종목 추가",
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        tk.Label(admin_window, text="종목 이름").pack()

        name_entry = tk.Entry(admin_window)

        name_entry.pack()

        tk.Label(admin_window, text="초기 가격").pack()

        price_entry = tk.Entry(admin_window)

        price_entry.pack()

        def add_stock():

            name = name_entry.get()

            try:

                price = int(price_entry.get())

            except:

                messagebox.showerror(
                    "오류",
                    "가격은 숫자만 입력"
                )

                return

            if name in self.stock_market:

                messagebox.showerror(
                    "오류",
                    "이미 존재하는 종목"
                )

                return

            self.stock_market[name] = Stock(
                name,
                price
            )

            self.stock_combo["values"] = list(
                self.stock_market.keys()
            )

            messagebox.showinfo(
                "완료",
                f"{name} 종목 추가 완료"
            )

        tk.Button(
            admin_window,
            text="종목 추가",
            command=add_stock
        ).pack(pady=10)

        # ====================================
        # 보유 금액 증감
        # ====================================

        tk.Label(
            admin_window,
            text="보유 금액 증감",
            font=("Arial", 12, "bold")
        ).pack(pady=20)

        tk.Label(
            admin_window,
            text="변동 금액 (+/- 가능)"
        ).pack()

        money_entry = tk.Entry(admin_window)

        money_entry.pack()

        def change_money():

            try:

                amount = int(money_entry.get())

            except:

                messagebox.showerror(
                    "오류",
                    "숫자만 입력"
                )

                return

            # 금액 증가/감소
            self.player.money += amount

            self.update_display()

            if amount >= 0:

                messagebox.showinfo(
                    "완료",
                    f"{amount:,}원 추가 완료"
                )

            else:

                messagebox.showinfo(
                    "완료",
                    f"{abs(amount):,}원 차감 완료"
                )

        tk.Button(
            admin_window,
            text="금액 적용",
            command=change_money
        ).pack(pady=10)


# ============================================
# 프로그램 실행
# ============================================

root = tk.Tk()

app = StockSimulatorGUI(root)

root.mainloop()