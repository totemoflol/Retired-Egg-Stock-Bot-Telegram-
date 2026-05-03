import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- DATABASE SETUP ---
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY,
    value INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    action TEXT,
    value INTEGER,
    time TEXT
)
""")

# Ensure stock row exists
cursor.execute("SELECT * FROM stock WHERE id=1")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO stock (id, value) VALUES (1, 0)")
    conn.commit()

# --- FUNCTIONS ---
def get_stock():
    cursor.execute("SELECT value FROM stock WHERE id=1")
    return cursor.fetchone()[0]

def update_stock(change, user):
    current = get_stock()
    new_value = current + change

    cursor.execute("UPDATE stock SET value=? WHERE id=1", (new_value,))
    cursor.execute(
        "INSERT INTO logs (user, action, value, time) VALUES (?, ?, ?, ?)",
        (user, "+" if change > 0 else "-", abs(change), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

def get_logs():
    cursor.execute("SELECT user, action, value, time FROM logs ORDER BY id DESC LIMIT 10")
    return cursor.fetchall()

# --- BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("➕", callback_data="add"),
            InlineKeyboardButton("➖", callback_data="minus"),
        ],
        [
            InlineKeyboardButton("📜 Logs", callback_data="logs")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Stock: {get_stock()}", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.username or query.from_user.first_name
    await query.answer()

    if query.data == "add":
        update_stock(1, user)
    elif query.data == "minus":
        update_stock(-1, user)
    elif query.data == "logs":
        logs = get_logs()
        text = "Last 10 logs:\n\n"
        for log in logs:
            text += f"{log[3]} | {log[0]} | {log[1]}{log[2]}\n"
        await query.edit_message_text(text)
        return

    keyboard = [
        [
            InlineKeyboardButton("➕", callback_data="add"),
            InlineKeyboardButton("➖", callback_data="minus"),
        ],
        [
            InlineKeyboardButton("📜 Logs", callback_data="logs")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"Stock: {get_stock()}", reply_markup=reply_markup)

# --- RUN BOT ---
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot running...")
    app.run_polling()
