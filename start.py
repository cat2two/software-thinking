# 시작 화면

import main_not_gui
import main_not_gui_admin



while True:

    print("""
    1. 일반 모드
    2. 관리자 모드
      """)

    behavior = input("입력:")
    
    if behavior == "1":
        main_not_gui.play()
    elif behavior == "2":
        main_not_gui_admin.play()
    else:
        print("다시")