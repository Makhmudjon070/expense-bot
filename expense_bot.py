import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    amount INTEGER
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xarajat kiriting.\nMisol: ovqat 850"
    )

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        category, amount = update.message.text.split()
        amount = int(amount)

        cursor.execute(
            "INSERT INTO expenses (category, amount) VALUES (?, ?)",
            (category, amount)
        )
        conn.commit()

        cursor.execute("SELECT SUM(amount) FROM expenses")
        total = cursor.fetchone()[0] or 0

        await update.message.reply_text(
            f"✅ Qo'shildi\n{category}: {amount}¥\n\nJami: {total}¥"
        )

    except:
        await update.message.reply_text(
            "Misol: ovqat 850"
        )

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0] or 0

    await update.message.reply_text(
        f"📊 Jami xarajat: {total}¥"
    )

TOKEN = "8956480665:AAHi15OhnRvZ0pjy41tjJsE2yWBZMf8UDf4"

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense))


print("Bot ishga tushdi")
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense))

print("Bot ishga tushdi")
app.run_polling()
