import json
import os

CONFIG_FILE = "settings.json"

PRIMARY_COLOR = "\033[38;2;218;165;32m"
INFO_COLOR = "\033[38;2;173;216;230m"
SUCCESS_COLOR = "\033[38;2;0;255;127m"
RESET = "\033[0m"
STAR = "✦"
ARROW = "➤"

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_title():
    clear()
    print(f"{PRIMARY_COLOR}{'═'*60}")
    print(f"{STAR*3}     Quotex VPS Client Settings     {STAR*3}")
    print(f"{'═'*60}{RESET}")

def print_input(prompt):
    return input(f"{INFO_COLOR}{ARROW} {prompt}:{RESET} ")

def print_success(msg):
    print(f"{SUCCESS_COLOR}✔ {msg}{RESET}")

def save_settings(settings):
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f, indent=4)
    print_success("Settings saved successfully!")

def load_settings():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE) as f:
        return json.load(f)

def get_user_settings():
    print_title()
    print("🔐 Please enter your Quotex login:\n")

    email = print_input("Quotex Email").strip()
    password = print_input("Quotex Password").strip()

    acc = ""
    while acc not in ["1", "2"]:
        acc = print_input("Choose account type (1=REAL, 2=PRACTICE)").strip()
    account_type = "REAL" if acc == "1" else "PRACTICE"

    try:
        amount = float(print_input("Fixed trade amount ($)").strip())
    except:
        amount = 1.0

    try:
        gale = int(print_input("Gale count (0-3)").strip())
        gale = max(0, min(gale, 3))
    except:
        gale = 0

    try:
        stop_profit = float(print_input("Stop Profit (0 = no limit)").strip())
        stop_profit = stop_profit if stop_profit > 0 else None
    except:
        stop_profit = None

    try:
        stop_loss = float(print_input("Stop Loss (0 = no limit)").strip())
        stop_loss = stop_loss if stop_loss > 0 else None
    except:
        stop_loss = None

    license_key = print_input("Enter your license key").strip()

    settings = {
        "email": email,
        "password": password,
        "account_type": account_type,
        "amount": amount,
        "gale": gale,
        "stop_profit": stop_profit,
        "stop_loss": stop_loss,
        "key": license_key
    }

    save_choice = print_input("Save settings for next time? (y/n)").lower()
    if save_choice == "y":
        save_settings(settings)

    return settings
