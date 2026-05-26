choice = input("1=plus 2=minus: ")

if choice == "1":
    with open("stock.txt", "a", encoding="utf-8") as f:
        f.write(f"{input()}\n")

elif choice == "2":
    target = input()
    with open("stock.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open("stock.txt", "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip() != target:
                f.write(line)