# 시작 화면

import main_not_gui
import main_not_gui_admin

print("""
1. api 안 쓴 모드
2. api 쓴 모드
3. 관리자 모드
      """)

while True:
    behavior = input("입력")
    
    if behavior == "1":
        main_not_gui.play()
    elif behavior == "2":
        pass
    elif behavior == "3":
        pass
    else:
        print("다시")