import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6 import uic
import main_not_gui
# 새로 만든 관리자 클래스 임포트
from admin_qt import AdminWindow 

class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('start.ui', self)
        
        self.startButton.clicked.connect(self.play_normal_mode)
        self.adminButton.clicked.connect(self.play_admin_mode)
        
    def play_normal_mode(self):
        self.hide()
        main_not_gui.play()
        self.show()

    def play_admin_mode(self):
        self.hide()
        # 관리자 창 객체를 생성하고 현재 창(self)을 넘겨주어 나중에 돌아올 수 있게 합니다.
        self.admin_window = AdminWindow(start_window=self)
        self.admin_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    sys.exit(app.exec())