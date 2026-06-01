import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6 import uic
import main_not_gui
import main_not_gui_admin

class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        # UI 파일 연동 (start.ui 파일이 같은 폴더에 있어야 합니다)
        uic.loadUi('start.ui', self)
        
        # 버튼 클릭 이벤트 연결
        self.startButton.clicked.connect(self.play_normal_mode)
        self.adminButton.clicked.connect(self.play_admin_mode)
        
    def play_normal_mode(self):
        # 일반 모드 실행
        self.hide()  # 게임 실행 시 시작 화면을 잠시 숨깁니다
        main_not_gui.play()
        self.show()  # 게임이 종료되면 다시 시작 화면을 띄웁니다

    def play_admin_mode(self):
        # 관리자 모드 실행
        self.hide()
        main_not_gui_admin.play()
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    # PyQt6에서는 exec_() 대신 exec()를 사용합니다.
    sys.exit(app.exec())