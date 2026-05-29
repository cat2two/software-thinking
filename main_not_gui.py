# ============================================
# 주식 시뮬레이터
# ============================================

import random
import pickle

# 삭제 리스트
delete_list = []

# ============================================
# 주식 클래스
# ============================================

class Stock:

    def __init__(self, name, price):

        self.name = name
        self.price = price
        self.start_price = price

    def change_decision(self):
        self.change = random.randint(70, 130)

    # 주가 변동
    def update_price(self):

        self.price = int(self.price * self.change/100)

        if self.price < self.start_price / 10:
            delete_list.append(self.name)
# ============================================
# 플레이어 클래스
# ============================================

class Player:

    def __init__(self, money):

        self.money = money

        # 보유 주식 정보 저장
        self.portfolio = {}

    # ========================================
    # 매수 기능
    # ========================================

    def buy_stock(self, stock, quantity):

        total_price = stock.price * quantity

        # 돈 부족
        if total_price > self.money:

            print("\n[실패] 돈이 부족합니다.")
            return

        # 돈 차감
        self.money -= total_price

        # 이미 보유 중인 경우
        if stock.name in self.portfolio:

            current_quantity = self.portfolio[stock.name]["quantity"]
            current_buy_price = self.portfolio[stock.name]["buy_price"]

            # 평균 매수가 계산
            new_quantity = current_quantity + quantity

            average_price = (
                (current_quantity * current_buy_price)
                + (quantity * stock.price)
            ) / new_quantity

            self.portfolio[stock.name]["quantity"] = new_quantity
            self.portfolio[stock.name]["buy_price"] = average_price

        # 처음 구매하는 경우
        else:

            self.portfolio[stock.name] = {
                "quantity": quantity,
                "buy_price": stock.price
            }

        print(f"\n[매수 완료] {stock.name} {quantity}주 구매")

    # ========================================
    # 매도 기능
    # ========================================

    def sell_stock(self, stock, quantity):

        # 보유 여부 확인
        if stock.name not in self.portfolio:

            print("\n[실패] 보유하지 않은 주식입니다.")
            return

        current_quantity = self.portfolio[stock.name]["quantity"]

        # 수량 부족
        if quantity > current_quantity:

            print("\n[실패] 보유 수량이 부족합니다.")
            return

        # 판매 금액
        total_price = stock.price * quantity

        # 돈 증가
        self.money += total_price

        # 수량 감소
        self.portfolio[stock.name]["quantity"] -= quantity

        # 0주면 삭제
        if self.portfolio[stock.name]["quantity"] == 0:
            del self.portfolio[stock.name]

        print(f"\n[매도 완료] {stock.name} {quantity}주 판매")

    # ========================================
    # 총 자산 계산
    # ========================================

    def calculate_total_assets(self, stock_market):

        total_assets = self.money

        for stock_name, info in self.portfolio.items():

            quantity = info["quantity"]

            current_price = stock_market[stock_name].price

            total_assets += quantity * current_price

        return total_assets

    # ========================================
    # 수익률 계산
    # ========================================

    def calculate_profit_rate(self, stock_market, initial_money):

        current_assets = self.calculate_total_assets(stock_market)

        profit_rate = (
            (current_assets - initial_money)
            / initial_money
        ) * 100

        return profit_rate

    # ========================================
    # 포트폴리오 출력
    # ========================================

    def show_portfolio(self, stock_market):

        print("\n========== 포트폴리오 ==========")

        print(f"보유 현금: {self.money:,}원")

        # 보유 주식이 없는 경우
        if not self.portfolio:

            print("보유 주식 없음")

        else:

            for stock_name, info in self.portfolio.items():

                quantity = info["quantity"]

                buy_price = info["buy_price"]

                current_price = stock_market[stock_name].price

                total_value = current_price * quantity

                print(f"\n종목: {stock_name}")
                print(f"보유 수량: {quantity}주")
                print(f"평균 매수가: {buy_price:,.0f}원")
                print(f"현재가: {current_price:,}원")
                print(f"현재 매도 시 예상 금액: {total_value:,}원")

def play():
    
    # 최고기록 가져오기
    with open("max.txt", "r") as f:
        max_money = int(f.read())

    # ============================================
    # 주식 시장 생성
    # ============================================

    stock_market = {

        "삼성전자": Stock("삼성전자", 70000),
        "테슬라": Stock("테슬라", 250000),
        "애플": Stock("애플", 180000)

    }

    with open("stock.txt", "r", encoding="utf-8") as f:
        stock_extra_text = f.read()
        stock_extra = list(stock_extra_text.split())

    for stock_name in stock_extra:
        stock_market[stock_name] = Stock(f"{stock_name}", 5000)

    # ============================================
    # 플레이어 생성
    # ============================================
    with open("initial_money.pkl", "rb") as f:
        INITIAL_MONEY = pickle.load(f)

    player = Player(INITIAL_MONEY)

    # ============================================
    # 턴 시스템
    # ============================================

    day = 1

    # ============================================
    # 메인 게임 루프
    # ============================================

    # 변동 값이 변동되었는가
    change_change = False

    while True:

        print("\n================================")
        print(f"주식 시뮬레이터 - DAY {day}")
        print("================================")

        # 현재 주가 출력
        print("\n[현재 주가]")

        for stock in stock_market.values():

            print(f"{stock.name}: {stock.price:,}원")
            # 변동 폭 결정
            if not change_change:
                stock.change_decision()
        else:
            change_change = True
        
        # 현재 자산 출력
        print(f"\n현재 보유 자산: {player.money:,.0f}원")

        # 메뉴 출력
        print("\n1. 매수")
        print("2. 매도")
        print("3. 포트폴리오 확인")
        print("4. 다음 날")
        print("5. 뉴스 보기")
        print("6. 종료")

        choice = input("\n메뉴 선택: ")

        # ========================================
        # 매수
        # ========================================

        if choice == "1":

            stock_name = input("종목 이름 입력: ")

            if stock_name not in stock_market:

                print("존재하지 않는 종목입니다.")
                continue

            quantity = int(input("구매 수량 입력: "))

            player.buy_stock(
                stock_market[stock_name],
                quantity
            )

        # ========================================
        # 매도
        # ========================================

        elif choice == "2":

            stock_name = input("종목 이름 입력: ")

            if stock_name not in stock_market:

                print("존재하지 않는 종목입니다.")
                continue

            quantity = int(input("판매 수량 입력: "))

            player.sell_stock(
                stock_market[stock_name],
                quantity
            )

            with open("max.txt", "w") as f:
                if max_money < player.money:
                    max_money = player.money
                    f.write(str(max_money))

        # ========================================
        # 포트폴리오 확인
        # ========================================

        elif choice == "3":

            player.show_portfolio(stock_market)

            total_assets = player.calculate_total_assets(
                stock_market
            )

            profit_rate = player.calculate_profit_rate(
                stock_market,
                INITIAL_MONEY
            )

            print(f"\n총 자산: {total_assets:,.0f}원")
            print(f"수익률: {profit_rate:.2f}%")
            print(f"최고기록: {max_money:,.0f}원")

        # ========================================
        # 다음 날 진행
        # ========================================

        elif choice == "4":

            print(f"\n===== DAY {day} → DAY {day + 1} =====")

            # 모든 주식 가격 변동
            for stock in stock_market.values():

                old_price = stock.price

                stock.update_price()

                print(
                    f"{stock.name}: "
                    f"{old_price:,}원 → "
                    f"{stock.price:,}원"
                )
            for i in delete_list:
                if i in stock_market:
                    print(f"\n{i} 종목이 상장 폐지되었습니다.")
                    del stock_market[i]
                delete_list.clear()

            # 변동 값이 변동되지 않음
            change_change = False

            # 현재 자산 출력
            print(f"\n현재 보유 자산: {player.money:,.0f}원")

            # 날짜 증가
            day += 1
        
        # ========================================
        # 뉴스 보기
        # ========================================

        elif choice == "5":

            print("\n오늘의 신문")
            for i in stock_market.values():
                if i.change < 85:
                    print(f"{i.name} 대표이사 사임")
                elif i.change < 100:
                    print(f"{i.name}에서 화재 발생")
                elif i.change < 115:
                    print(f"{i.name}에서 약간의 호재")
                else:
                    print(f"{i.name}에서 신기술 개발")

        # ========================================
        # 프로그램 종료
        # ========================================

        elif choice == "6":

            print("\n프로그램 종료")
            break

        # ========================================
        # 잘못된 입력
        # ========================================

        else:

            print("\n올바른 메뉴를 선택하세요.")