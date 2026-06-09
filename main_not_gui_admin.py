import pickle
def play():
    choice = input("1. 종목추가\n2. 종목삭제\n3. 보유자금 설정\n: ")

    if choice == "1":
        stock_name = input("종목명: ").strip()

        if stock_name == "":
            print("종목명을 입력해주세요.")
            return
            
        with open("stock.txt", "a", encoding="utf-8") as f:
            f.write(stock_name + "\n")

        print(f"{stock_name} 종목이 추가되었습니다.")
    
    elif choice == "2":
        target = input()
        with open("stock.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open("stock.txt", "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip() != target:
                    f.write(line)

    elif choice == "3":
        with open("initial_money.pkl", "wb") as f:
            pickle.dump(int(input("초기 금액: ")),f)