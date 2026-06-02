# -*- coding: utf-8 -*-
"""
Stock Simulator - PyQt6 구조화 버전
실행: python stock_simulator_pyqt6.py
"""
import sys
from PyQt6.QtWidgets import QApplication
from windows import StartWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = StartWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()