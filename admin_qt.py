import os
import pickle
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6 import uic

class AdminWindow(QWidget):
    def __init__(self, start_window=None):
        super().__init__()
        # admin_mode.ui 파일 로드
        uic.loadUi('admin_mode.ui', self)
        
        # 시작 창으로 돌아가기 위해 참조 저장
        self.start_window = start_window
        
        # 데이터 파일 경로 설정
        self.stock_file = "stock.txt"
        self.money_file = "initial_money.pkl"
        
        # 버튼 클릭 이벤트 연결
        self.btn_back.clicked.connect(self.go_back)
        self.btn_add_item.clicked.connect(self.add_item)
        self.btn_delete_item.clicked.connect(self.delete_item)
        self.btn_apply_money.clicked.connect(self.apply_money)
        
        # 창이 켜질 때 기존 데이터(종목, 돈)를 화면에 불러오기
        self.load_data()

    def load_data(self):
        # 1. 종목 목록 로드
        self.list_items.clear()
        self.combo_delete_item.clear()
        
        if os.path.exists(self.stock_file):
            with open(self.stock_file, "r", encoding="utf-8") as f:
                # 빈 줄을 제외하고 읽어오기
                stocks = [line.strip() for line in f.readlines() if line.strip()]
                stocks.append()
                self.list_items.addItems(stocks)
                self.combo_delete_item.addItems(stocks)

        # 2. 보유 금액 로드
        current_money = 1000000  # 파일이 없을 경우 기본값
        if os.path.exists(self.money_file):
            try:
                with open(self.money_file, "rb") as f:
                    current_money = pickle.load(f)
            except Exception:
                pass
        
        # 화면의 라벨 텍스트 업데이트 (천 단위 쉼표 추가)
        self.label_current_money.setText(f"현재 보유 금액: {current_money:,}원")
        self.current_money = current_money

    def add_item(self):
        # UI에서 종목 이름 가져오기
        stock_name = self.input_item_name.text().strip()
        
        if not stock_name:
            QMessageBox.warning(self, "경고", "종목 이름을 입력하세요.")
            return
            
        # 기존 로직대로 파일에 종목명 추가
        with open(self.stock_file, "a", encoding="utf-8") as f:
            f.write(f"{stock_name}\n")
            
        # 입력창 초기화 및 화면 갱신
        self.input_item_name.clear()
        self.input_item_price.clear()  # 초기 가격은 UI에 있지만 원본 로직에 맞춰 텍스트만 지움
        self.load_data()
        QMessageBox.information(self, "성공", f"'{stock_name}' 종목이 추가되었습니다.")

    def delete_item(self):
        # 콤보박스에서 선택된 항목 가져오기
        target = self.combo_delete_item.currentText()
        if not target:
            QMessageBox.warning(self, "경고", "삭제할 종목을 선택하세요.")
            return

        # 파일에서 해당 종목 삭제
        if os.path.exists(self.stock_file):
            with open(self.stock_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(self.stock_file, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.strip() != target:
                        f.write(line)
        
        self.load_data()
        QMessageBox.information(self, "성공", f"'{target}' 종목이 삭제되었습니다.")

    def apply_money(self):
        # 입력된 변동 금액 가져오기
        change_str = self.input_change_money.text().strip()
        try:
            change_amount = int(change_str)
        except ValueError:
            QMessageBox.warning(self, "경고", "올바른 금액(숫자)을 입력하세요. (예: 50000 또는 -50000)")
            return
            
        # 기존 금액에 변동 금액 반영 (+/- 연산)
        new_money = self.current_money + change_amount
        
        # pickle로 새로운 금액 저장
        with open(self.money_file, "wb") as f:
            pickle.dump(new_money, f)
            
        self.input_change_money.clear()
        self.load_data()
        QMessageBox.information(self, "성공", f"보유 금액이 {new_money:,}원으로 적용되었습니다.")

    def go_back(self):
        # 관리자 창을 닫고, 시작 창을 다시 엽니다.
        self.close()
        if self.start_window:
            self.start_window.show()