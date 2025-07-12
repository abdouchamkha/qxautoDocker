
import requests
import os
import json
from pathlib import Path
import time
import shutil
import pyfiglet
import asyncio
import datetime
import re
from colorama import init, Style, Fore, Back
from telethon import TelegramClient, events
from quotexapi.stable_api import Quotex
from pytz import timezone

# Initialize colorama
init(autoreset=True)

## ---------------------------- ##
##       Color Settings         ##
## ---------------------------- ##
PRIMARY_COLOR = "\033[38;2;218;165;32m"  # Gold
SECONDARY_COLOR = "\033[38;2;0;105;148m"  # Dark Blue
ASCII_COLOR = "\033[38;2;240;240;240m"  # Pure White
INFO_COLOR = "\033[38;2;173;216;230m"  # Light Blue
SUCCESS_COLOR = "\033[38;2;0;255;127m"  # Light Green
ERROR_COLOR = "\033[38;2;255;69;0m"  # Orange Red
WARNING_COLOR = "\033[38;2;255;215;0m"  # Light Gold
BORDER_COLOR = "\033[38;2;184;134;11m"  # Dark Gold
INPUT_COLOR = "\033[38;2;64;224;208m"  # Turquoise

## ---------------------------- ##
##      Decoration Settings     ##
## ---------------------------- ##
TOP_LEFT_CORNER = "╔"
TOP_RIGHT_CORNER = "╗"
BOTTOM_LEFT_CORNER = "╚"
BOTTOM_RIGHT_CORNER = "╝"
HORIZONTAL_LINE = "═"
VERTICAL_LINE = "║"
DIAMOND = "♦"
STAR = "✦"
HEART = "♥"
CLUB = "♣"
SPADE = "♠"
ARROW_UP = "↑"
ARROW_DOWN = "↓"

## ---------------------------- ##
##      App Configuration       ##
## ---------------------------- ##
API_ID = 25712604
API_HASH = '8c745804b912834996255dc41f92e1e4'
CHANNEL_ID = -1002526280469
BOT_TOKEN = '8175643752:AAFclZVqlIZX0nE-9al-W5UZP4BlHkMlDn4'
QUOTEX_EMAIL = ""
QUOTEX_PASSWORD = ""

## ---------------------------- ##
##      Global Variables        ##
## ---------------------------- ##
telegram_client = TelegramClient('session_name', API_ID, API_HASH)
quotex_client = None
trade_amount = None
last_trade_loss = False
current_trade_amount = None
last_message = None
gale_limit = 1
current_gale_count = 0

# Add profit/loss tracking variables
net_profit = 0
total_trades = 0
winning_trades = 0
losing_trades = 0
stop_profit = None
stop_loss = None
is_trading_active = True
session_start_time = None

# متغير لمنع التداخل بين الصفقات
is_trade_running = False

## ---------------------------- ##
##      File Path Settings      ##
## ---------------------------- ##
CONFIG_DIR = Path.home() / ".quotex_bot"
CONFIG_FILE = CONFIG_DIR / "config.json"


## ----------------------------- ##
##      File Management         ##
## ----------------------------- ##

def ensure_config_dir():
    """Create config directory if it doesn't exist"""
    try:
        CONFIG_DIR.mkdir(exist_ok=True, mode=0o700)
        return True
    except Exception as e:
        print_error(f"Failed to create config directory: {e}")
        return False


def save_login_data(email, password):
    """Save login data to file"""
    try:
        if not ensure_config_dir():
            return False

        data = {
            "email": email,
            "password": password,
            "saved_at": datetime.datetime.now().isoformat()
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)

        # Change file permissions for security
        os.chmod(CONFIG_FILE, 0o600)
        return True
    except Exception as e:
        print_error(f"Failed to save login data: {e}")
        return False


def load_login_data():
    """Load login data from file"""
    try:
        if not CONFIG_FILE.exists():
            return None

        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)

        # Verify required fields
        if "email" in data and "password" in data:
            return data
        return None
    except Exception as e:
        print_error(f"Failed to load login data: {e}")
        return None


def delete_login_data():
    """Delete saved login data"""
    try:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            return True
        return False
    except Exception as e:
        print_error(f"Failed to delete login data: {e}")
        return False


## ---------------------------- ##
##      Login Functions         ##
## ---------------------------- ##

async def get_login_credentials():
    """Get login credentials from user"""
    print_header("LOGIN")

    # Check for saved data
    saved_data = load_login_data()
    if saved_data:
        print(f"\n{INFO_COLOR}1. {PRIMARY_COLOR}Use saved account ({saved_data['email']})")
        print(f"{INFO_COLOR}2. {PRIMARY_COLOR}Enter new credentials")
        print(f"{INFO_COLOR}3. {PRIMARY_COLOR}Delete saved credentials\n")

        while True:
            print_input_prompt("Choose option (1-3)")
            choice = input().strip()

            if choice == "1":
                return saved_data["email"], saved_data["password"], True
            elif choice == "2":
                break
            elif choice == "3":
                if delete_login_data():
                    print_success("Saved credentials deleted successfully")
                else:
                    print_error("Failed to delete saved credentials")
                # Show menu again after deletion
                return await get_login_credentials()
            else:
                print_error("Invalid choice, please try again")

    # Get new credentials
    print(f"\n{INFO_COLOR}Please enter your login credentials:")

    while True:
        print_input_prompt("Quotex Email")
        email = input().strip()
        if "@" in email and "." in email:
            break
        print_error("Invalid email format")

    print_input_prompt("Quotex Password")
    password = input().strip()

    # Ask to save credentials
    print(f"\n{INFO_COLOR}Do you want to save these credentials?")
    print(f"{WARNING_COLOR}Warning: Data will be stored unencrypted on your device\n")
    print(f"{INFO_COLOR}1. {PRIMARY_COLOR}Yes, save credentials")
    print(f"{INFO_COLOR}2. {PRIMARY_COLOR}No, don't save\n")

    while True:
        print_input_prompt("Choose option (1 or 2)")
        save_choice = input().strip()
        if save_choice == "1":
            if save_login_data(email, password):
                print_success("Credentials saved successfully")
            else:
                print_error("Failed to save credentials")
            break
        elif save_choice == "2":
            break
        else:
            print_error("Invalid choice")

    return email, password, False


## ---------------------------- ##
##      Utility Functions       ##
## ---------------------------- ##

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_width():
    return shutil.get_terminal_size().columns


def print_line(line, side_margin, delay=0.05):
    print(" " * side_margin + line)
    time.sleep(delay)


def display_ascii_art():
    clear_screen()
    term_width = get_terminal_width()

    # Fixed width for the frame - adjusted to be more compact
    frame_width = 95  # Adjusted width to properly fit the ASCII art

    # Master V1 ASCII art
    venom_art = [
        "  __  __               _____   _______   ______   _____                __      __  __ ",
        " |  \\/  |     /\\      / ____| |__   __| |  ____| |  __ \\               \\ \\    / / /_ |",
        " | \\  / |    /  \\    | (___      | |    | |__    | |__) |    ______     \\ \\  / /   | |",
        " | |\\/| |   / /\\ \\    \\___ \\     | |    |  __|   |  _  /    |______|     \\ \\/ /    | |",
        " | |  | |  / ____ \\   ____) |    | |    | |____  | | \\ \\                  \\  /     | |",
        " |_|  |_| /_/    \\_\\ |_____/     |_|    |______| |_|  \\_\\                  \\/      |_|"
    ]

    # Calculate side margin to center the frame
    side_margin = (term_width - frame_width) // 2 if term_width > frame_width else 0

    # Border elements with corners - adjusted spacing
    top_border = f"{BORDER_COLOR}╔{'═' * (frame_width - 2)}╗"
    bottom_border = f"{BORDER_COLOR}╚{'═' * (frame_width - 2)}╝"
    empty_line = f"{BORDER_COLOR}║{' ' * (frame_width - 2)}║"

    # Print the frame
    print_line(top_border, side_margin, 0.05)
    print_line(empty_line, side_margin, 0.02)

    # Print top stars
    stars = "✦✦✦✦✦"
    star_line = f"{BORDER_COLOR}║{PRIMARY_COLOR}{stars.center(frame_width - 2)}{BORDER_COLOR}║"
    print_line(star_line, side_margin, 0.02)
    print_line(empty_line, side_margin, 0.02)

    # Print ASCII art with exact spacing
    art_padding = (frame_width - len(venom_art[0]) - 2) // 2  # Calculate padding for centering
    for line in venom_art:
        content = f"{BORDER_COLOR}║{' ' * art_padding}{PRIMARY_COLOR}{line}{' ' * (frame_width - len(line) - art_padding - 2)}{BORDER_COLOR}║"
        print_line(content, side_margin, 0.02)

    print_line(empty_line, side_margin, 0.02)

    # Print bottom stars
    print_line(star_line, side_margin, 0.02)
    print_line(empty_line, side_margin, 0.02)

    # Developer info with fixed spacing and borders
    info_lines = [
        f"✦ Developer: @TAKIHAMATA ✦",
        f"✦ Version:  v2.0 ✦",
        f"✦ Telegram: https://t.me/TAKIHAMATA ✦"
    ]

    for line in info_lines:
        content = f"{BORDER_COLOR}║{INFO_COLOR}{line.center(frame_width - 2)}{BORDER_COLOR}║"
        print_line(content, side_margin, 0.02)

    print_line(empty_line, side_margin, 0.02)
    print_line(bottom_border, side_margin, 0.05)

    # Loading animation outside the frame
    loading_text = f"{PRIMARY_COLOR}Initializing System"
    print(f"{' ' * side_margin}{loading_text}...", flush=True)
    print("\n")


def print_header(title):
    term_width = get_terminal_width()
    title_text = f" {title} "
    border_length = (term_width - len(title_text)) // 2
    print(
        f"{BORDER_COLOR}{HORIZONTAL_LINE * border_length}{SECONDARY_COLOR}{title_text}{BORDER_COLOR}{HORIZONTAL_LINE * border_length}")


def print_footer():
    term_width = get_terminal_width()
    print(f"{BORDER_COLOR}{HORIZONTAL_LINE * term_width}")


def print_success(message):
    print(f"\n{SUCCESS_COLOR}{STAR * 3} {message} {STAR * 3}\n")


def print_error(message):
    print(f"\n{ERROR_COLOR}{HEART * 3} {message} {HEART * 3}\n")


def print_warning(message):
    print(f"\n{WARNING_COLOR}{DIAMOND * 3} {message} {DIAMOND * 3}\n")


def print_info(message):
    print(f"\n{INFO_COLOR}{CLUB * 3} {message} {CLUB * 3}\n")


def print_input_prompt(prompt):
    print(f"{INPUT_COLOR}{prompt}: {Style.RESET_ALL}", end="")


## ---------------------------- ##
##      Core Functions          ##
## ---------------------------- ##

def correct_asset_name(asset_name):
    if "-OTCq" in asset_name:
        asset_name = asset_name.replace("-OTCq", "_otc")
    return asset_name


async def wait_for_new_minute():
    """Wait for the start of next minute"""
    now = datetime.datetime.now()
    seconds_to_wait = 60 - now.second - now.microsecond / 1000000
    await asyncio.sleep(seconds_to_wait)


async def connect_with_retries(client, retries=3):
    for attempt in range(retries):
        check_connect, message = await client.connect()
        if check_connect:
            return True
        print_error(f"Connection attempt {attempt + 1} failed: {message}")
        await asyncio.sleep(2)
    return False


async def select_account(client):
    print_header("ACCOUNT SELECTION")
    print(f"\n{INFO_COLOR}1. {PRIMARY_COLOR}Real Account")
    print(f"{INFO_COLOR}2. {PRIMARY_COLOR}Practice Account\n")

    while True:
        print_input_prompt("Enter your choice (1 or 2)")
        choice = input()
        if choice == "1":
            return "REAL"
        elif choice == "2":
            return "PRACTICE"
        else:
            print_error("Invalid choice. Please enter 1 or 2.")


async def set_trade_amount(balance):
    while True:
        try:
            print_header("TRADE AMOUNT SETUP")
            print(f"\n{INFO_COLOR}Current Balance: {PRIMARY_COLOR}{balance}")
            print_input_prompt("Enter the fixed trade amount")
            trade_amount = float(input())

            if trade_amount <= 0:
                print_error("Trade amount must be greater than 0.")
            elif trade_amount > balance:
                print_error("Trade amount cannot exceed your current balance.")
            else:
                print_success(f"Trade amount set to: {trade_amount}")
                return trade_amount
        except ValueError:
            print_error("Invalid input. Please enter a valid number.")


async def set_gale_limit(balance):
    global gale_limit
    while True:
        try:
            print_header("GALE SETTINGS")
            print(f"\n{INFO_COLOR}Set the maximum number of Gale trades (0-3):")
            print(f"{INFO_COLOR}0 = No Gale trades")
            print(f"{INFO_COLOR}1 = One Gale trade")
            print(f"{INFO_COLOR}2 = Two Gale trades")
            print(f"{INFO_COLOR}3 = Three Gale trades\n")
            print_input_prompt("Enter the number of Gale trades")
            gale_input = int(input())

            if 0 <= gale_input <= 3:
                gale_limit = gale_input
                print_success(f"Gale limit set to: {gale_limit}")
                return
            else:
                print_error("Please enter a number between 0 and 3.")
        except ValueError:
            print_error("Invalid input. Please enter a number.")


async def set_trading_limits():
    global stop_profit, stop_loss

    print_header("TRADING LIMITS SETUP")
    print(f"\n{INFO_COLOR}Set your trading limits for this session:")

    while True:
        try:
            print_input_prompt("Enter Stop Profit amount (or 0 for no limit)")
            stop_profit_input = float(input())
            if stop_profit_input >= 0:
                stop_profit = stop_profit_input if stop_profit_input > 0 else None
                break
            print_error("Please enter a positive number or 0")
        except ValueError:
            print_error("Invalid input. Please enter a number")

    while True:
        try:
            print_input_prompt("Enter Stop Loss amount (or 0 for no limit)")
            stop_loss_input = float(input())
            if stop_loss_input >= 0:
                stop_loss = stop_loss_input if stop_loss_input > 0 else None
                break
            print_error("Please enter a positive number or 0")
        except ValueError:
            print_error("Invalid input. Please enter a number")

    print_success(
        f"Trading limits set - Stop Profit: {'∞' if stop_profit is None else f'${stop_profit:.2f}'} | Stop Loss: {'∞' if stop_loss is None else f'${stop_loss:.2f}'}")


def check_trading_limits():
    global is_trading_active

    if not is_trading_active:
        return False

    if stop_profit is not None and net_profit >= stop_profit:
        print_success(f"🎯 Stop Profit reached! Net Profit: ${net_profit:.2f}")
        is_trading_active = False
        return False

    if stop_loss is not None and net_profit <= -stop_loss:
        print_error(f"⛔ Stop Loss reached! Net Loss: ${-net_profit:.2f}")
        is_trading_active = False
        return False

    return True


def update_trading_stats(won, profit_amount, is_gale=False):
    global net_profit, total_trades, winning_trades, losing_trades, session_start_time

    if is_gale:
        total_trades += 1
        if won:
            winning_trades += 1
            net_profit += profit_amount
        else:
            losing_trades += 1
            net_profit -= profit_amount
    else:
        total_trades += 1
        if won:
            winning_trades += 1
            net_profit += profit_amount
        else:
            losing_trades += 1
            net_profit -= profit_amount

    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

    print_header("TRADING STATISTICS")
    print(f"{INFO_COLOR}💰 Net Profit/Loss: {SUCCESS_COLOR if net_profit >= 0 else ERROR_COLOR}${net_profit:.2f}")
    print(f"{INFO_COLOR}📊 Total Trades: {total_trades}")
    print(f"{INFO_COLOR}📈 Win Rate: {SUCCESS_COLOR}{win_rate:.1f}%")
    print(f"{INFO_COLOR}✅ Winning Trades: {SUCCESS_COLOR}{winning_trades}")
    print(f"{INFO_COLOR}❌ Losing Trades: {ERROR_COLOR}{losing_trades}")

    # Add session duration
    if session_start_time is None:
        session_start_time = time.time()
    else:
        session_duration = time.time() - session_start_time
        hours = int(session_duration // 3600)
        minutes = int((session_duration % 3600) // 60)
        print(f"{INFO_COLOR}⏱️ Session Duration: {hours}h {minutes}m")


async def check_candle_result(asset_name, duration):
    """Check if the candle closed in our favor"""
    try:
        # Get candle data for the asset
        end_from_time = time.time()
        offset = 3600  # in seconds
        candles = await quotex_client.get_candles(asset_name, end_from_time, offset, duration)

        if not candles:
            print_error("Could not fetch candle data")
            return None

        # Get the current completed candle (last candle)
        current_candle = candles[-1]

        # Calculate if candle is bullish (CALL) or bearish (PUT)
        is_bullish = current_candle['close'] > current_candle['open']

        result = 'CALL' if is_bullish else 'PUT'
        return is_bullish

    except Exception as e:
        return None


async def execute_trade(amount, asset_name, direction, duration, balance, is_gale=False, gale_used=False, total_lost=0):
    global last_trade_loss, current_trade_amount, trade_amount, current_gale_count, is_trading_active

    try:
        if not check_trading_limits():
            print_warning("Trading stopped due to reaching profit/loss limits")
            return balance, 0, False

        # Wait for new minute only if it's not a Gale trade
        if not last_trade_loss:
            await wait_for_new_minute()
            current_gale_count = 0  # Reset gale count for new trade

        # Format trade info
        trade_type = f"GALE #{current_gale_count }" if last_trade_loss else "SIGNAL TRADE"
        direction_arrow = ARROW_UP if direction == 'call' else ARROW_DOWN

        print_header(f"{trade_type}")
        print(f"{WARNING_COLOR}{direction_arrow} {asset_name} | {direction.upper()} | {duration}s | Amount: ${amount}")
        print(f"{INFO_COLOR}💰 Balance: ${balance:.2f}")

        # Verify asset availability
        try:
            asset_name, asset_data = await quotex_client.get_available_asset(asset_name, force_open=True)
        except Exception as e:
            print_error("❌ Connection Error")
            print_error("Unable to connect to trading server")
            print_error("Please check your internet connection")
            return balance, 0, False

        if asset_data is None:
            print_error("❌ Asset Error")
            print_error(f"Unable to access {asset_name}")
            print_error("The asset may be temporarily unavailable")
            update_trading_stats(False, amount, is_gale=gale_used)
            return balance, 0, False

        if not asset_data[2]:
            print_error("❌ Market Closed")
            print_error(f"{asset_name} market is currently closed")
            print_error("Please wait for market hours or try a different asset")
            return balance, 0, False

        # Execute trade
        try:
            status, buy_info = await quotex_client.buy(amount, asset_name, direction, duration)
        except Exception as e:
            print_error("❌ Order Error")
            print_error("Failed to place trade order")
            print_error("Please try again in a few moments")
            return balance, 0, False

        if status:
            balance -= amount
            total_lost += amount

            # Wait for trade completion
            await asyncio.sleep(duration)

            # Verify trade result
            try:
                is_bullish = await check_candle_result(asset_name, duration)
            except Exception as e:
                print_error("❌ Verification Error")
                print_error("Unable to verify trade result")
                print_error("Please check your connection")
                return balance, 0, False

            if is_bullish is None:
                print_error("❌ Result Error")
                print_error("Unable to determine trade outcome")
                print_error("Please verify manually in your account")
                return balance, 0, False

            won = (direction == 'call' and is_bullish) or (direction == 'put' and not is_bullish)

            if won:
                profit = amount * 0.8  # 80% payout
                balance += amount + profit
                # الربح الصافي = الربح - مجموع الخسائر السابقة + مبلغ الصفقة الأخيرة
                net_result = profit - (total_lost - amount)
                print(f"✅ WIN | +${profit:.2f} | New Balance: ${balance:.2f}")
                last_trade_loss = False
                current_trade_amount = trade_amount
                current_gale_count = 0
                update_trading_stats(True, net_result, is_gale=gale_used)
                return balance, profit, True
            else:
                if current_gale_count < gale_limit:
                    print(f"❎ LOSS | -${amount:.2f} | New Balance: ${balance:.2f} | Starting Gale")
                    last_trade_loss = True
                    current_gale_count += 1
                    current_trade_amount = amount * 2
                    # مرر total_lost في الاستدعاء التالي
                    return await execute_trade(current_trade_amount, asset_name, direction, duration, balance,
                                               is_gale=True, gale_used=True, total_lost=total_lost)
                else:
                    print(f"❎ LOSS | -${amount:.2f} | New Balance: ${balance:.2f}")
                    if gale_limit > 0:
                        print_warning("⚠️ Maximum Gale trades reached - Starting new cycle")
                    last_trade_loss = False
                    current_trade_amount = trade_amount
                    current_gale_count = 0
                    # عند خسارة كل الجالي، مرر مجموع الخسارة
                    update_trading_stats(False, total_lost, is_gale=gale_used)
                    return balance, 0, False

        else:
            print_error("\n❌ Trade Failed")
            print_error("Unable to execute order\n")
            print_warning("Possible reasons:")
            print_warning("• Insufficient balance")
            print_warning("• Market volatility")
            print_warning("• Connection issues\n")
            return balance, 0, False

    except Exception as e:
        print_error("\n❌ System Error")
        print_error(f"Details: {str(e)}")
        print_error("Please check your connection and try again\n")
        return balance, 0, False


@telegram_client.on(events.NewMessage(chats=CHANNEL_ID))
async def handle_message(event):
    global last_trade_loss, last_message, is_trade_running

    # منع استقبال إشارة جديدة أثناء وجود صفقة قيد التنفيذ
    if is_trade_running:
        return
    is_trade_running = True

    message = event.message.message

    if message == last_message:
        is_trade_running = False
        return

    last_message = message

    # Filter out WebSocket messages

    if "SURESHOT" in message:
        print_header("TRADE RESULT")
        print_success("✅ Trade result: WIN")
        last_trade_loss = False
        current_gale_count = 0
        current_trade_amount = trade_amount
        is_trade_running = False
    elif "LOSS" in message:
        print_header("TRADE RESULT")
        print_error("❌ Trade result: LOSS")
        last_trade_loss = True
        await execute_trade_immediately()
        is_trade_running = False
    else:
        pair_pattern = r"([A-Z]{6}(?:-OTCq)?)"
        direction_pattern = r"(PUT|CALL)"
        duration_pattern = r"(M1|M5)"

        pair_match = re.search(pair_pattern, message)
        direction_match = re.search(direction_pattern, message)
        duration_match = re.search(duration_pattern, message)

        if pair_match and direction_match and duration_match:
            pair = pair_match.group(1)
            direction = direction_match.group(1).lower()
            duration = duration_match.group(1)

            pair = correct_asset_name(pair)

            if duration == "M1":
                duration_seconds = 60
            elif duration == "M5":
                duration_seconds = 300
            else:
                print_error("❌ Invalid Duration")
                print_error(f"Unsupported duration: {duration}")
                is_trade_running = False
                return

            print_header("NEW TRADE SIGNAL")
            print(f"{INFO_COLOR}📊 Pair: {pair}")
            print(f"{INFO_COLOR}📈 Direction: {SUCCESS_COLOR if direction == 'call' else ERROR_COLOR}{direction.upper()}")
            print(f"{INFO_COLOR}⏱️ Duration: {duration_seconds}s")

            balance = await quotex_client.get_balance()
            amount = trade_amount
            last_trade_loss = False
            current_gale_count = 0
            current_trade_amount = trade_amount
            balance, profit, success = await execute_trade(amount, pair, direction, duration_seconds, balance,
                                                           is_gale=False, gale_used=False, total_lost=0)

            if not success:
                pass  # لا يوجد طباعة أو إجراء هنا بعد حذف السطر الفارغ

            await asyncio.sleep(120)
            is_trade_running = False
        else:
            is_trade_running = False


async def execute_trade_immediately():
    global last_trade_loss, is_trade_running

    pair = "EURUSD-OTCq"
    direction = "call"
    duration_seconds = 60

    pair = correct_asset_name(pair)

    balance = await quotex_client.get_balance()
    amount = trade_amount
    last_trade_loss = False
    current_gale_count = 0
    current_trade_amount = trade_amount
    balance, profit, success = await execute_trade(amount, pair, direction, duration_seconds, balance, is_gale=False,
                                                   gale_used=False, total_lost=0)

    if success:
        print_success(f"Immediate trade successful! Profit: {profit}")
    else:
        print_error("Immediate trade failed or resulted in a loss.")

    await asyncio.sleep(180)
    is_trade_running = False


async def main():
    global QUOTEX_EMAIL, QUOTEX_PASSWORD, telegram_client, quotex_client, trade_amount

    display_ascii_art()

    # Get login credentials
    email, password, use_saved = await get_login_credentials()
    QUOTEX_EMAIL = email
    QUOTEX_PASSWORD = password

    # Initialize Quotex client
    quotex_client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, lang="en")

    if await connect_with_retries(quotex_client):
        account_type = await select_account(quotex_client)
        quotex_client.change_account(account_type)

        balance = await quotex_client.get_balance()
        print_header("ACCOUNT BALANCE")
        print(f"\n{PRIMARY_COLOR}{account_type} account balance: {balance}\n")

        trade_amount = await set_trade_amount(balance)
        await set_gale_limit(balance)
        await set_trading_limits()

        # امسح الشاشة بعد الإعدادات وأعد طباعة الواجهة
        clear_screen()
        display_ascii_art()

        try:
            # شغل التليجرام باستخدام التوكن مباشرة
            await telegram_client.start(bot_token=BOT_TOKEN)
            print_header("SYSTEM STATUS")
            print_success("Telegram bot started successfully!")
            await telegram_client.run_until_disconnected()
        except Exception as e:
            print_error(f"Failed to start Telegram client: {e}")
    else:
        print_error("Failed to connect to Quotex.")


if __name__ == '__main__':
    asyncio.run(main())