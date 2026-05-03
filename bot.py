import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DATA_FILE = "inventory.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"inventory": 0, "pending": 0, "completed": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

async def restock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        data = load_data()
        data["inventory"] += amount
        save_data(data)
        await update.message.reply_text(f"✅ Restocked {amount}. Inventory is now {data['inventory']}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /restock <amount>")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        data = load_data()
        if amount > data["inventory"]:
            await update.message.reply_text(f"❌ Not enough inventory. Current stock: {data['inventory']}.")
            return
        data["inventory"] -= amount
        data["pending"] += amount
        save_data(data)
        await update.message.reply_text(f"🛒 Sold {amount}. Inventory: {data['inventory']} | Pending: {data['pending']}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /sell <amount>")

async def sold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        data = load_data()
        if amount > data["pending"]:
            await update.message.reply_text(f"❌ Not enough in pending. Pending: {data['pending']}.")
            return
        data["pending"] -= amount
        data["completed"] += amount
        save_data(data)
        await update.message.reply_text(f"✔️ Marked {amount} as sold. Pending: {data['pending']} | Completed: {data['completed']}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /sold <amount>")

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = (
        f"📦 *Stock Report*\n"
        f"Inventory: {data['inventory']}\n"
        f"Pending:   {data['pending']}\n"
        f"Completed: {data['completed']}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

def main():
    TOKEN = "YOUR_BOT_TOKEN_HERE"  # <- paste your token here
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("restock", restock))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("sold", sold))
    app.add_handler(CommandHandler("stock", stock))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
