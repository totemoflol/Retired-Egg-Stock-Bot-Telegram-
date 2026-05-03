import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# --- DATABASE ---
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

cursor.execute("SELECT * FROM stock WHERE id=1")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO stock (id, value) VALUES (1, 0)")
    conn.commit()

# --- FUNCTIONS ---
def get_stock():
    cursor.execute("SELECT value FROM stock WHERE id=1")
    return cursor.fetchone()[0]

def update_stock(change, user):
    new_value = get_stock() + change

    cursor.execute("UPDATE stock SET value=? WHERE id=1", (new_value,))
    cursor.execute(
        "INSERT INTO logs (user, action, value, time) VALUES (?, ?, ?, ?)",
        (user, "+" if change > 0 else "-", abs(change),
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

def get_logs():
    cursor.execute("SELECT user, action, value, time FROM logs ORDER BY id DESC LIMIT 10")
    return cursor.fetchall()

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("➕ Add", callback_data="add"),
            InlineKeyboardButton("➖ Remove", callback_data="minus"),
        ],
        [
            InlineKeyboardButton("📜 Logs", callback_data="logs")
        ]
    ]
    await update.message.reply_text(
        f"Stock: {get_stock()}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- BUTTON HANDLER ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.username or query.from_user.first_name
    await query.answer()

    if query.data in ["add", "minus"]:
        context.user_data["action"] = query.data
        await query.message.reply_text("Enter amount:")
        return

    elif query.data == "logs":
        logs = get_logs()
        text = "Last 10 logs:\n\n"
        for log in logs:
            text += f"{log[3]} | {log[0]} | {log[1]}{log[2]}\n"
        await query.message.reply_text(text)
        return

# --- HANDLE NUMBER INPUT ---
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "action" not in context.user_data:
        return

    user = update.message.from_user.username or update.message.from_user.first_name

    try:
        amount = int(update.message.text)
    except:
        await update.message.reply_text("Please enter a valid number.")
        return

    if context.user_data["action"] == "add":
        update_stock(amount, user)
    else:
        update_stock(-amount, user)

    context.user_data.pop("action")

    await update.message.reply_text(f"Updated stock: {get_stock()}")

# --- RUN ---
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))

    print("Bot running...")
    app.run_polling()
