import os
import sqlite3
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token endi kodda emas, environment variable orqali olinadi
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! Railway/Render/Heroku panelida "
        "Environment Variables bo'limiga BOT_TOKEN qo'shing."
    )

conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    amount INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER,
    note TEXT
)
""")
conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xarajat kiriting.\nMisol: ovqat 850\n\n"
        "Oylik/daromad qo'shish: /oylik 500000\n"
        "Balansni ko'rish: /balans\n"
        "Jami xarajat: /report\n"
        "Xarajatlarni tozalash: /reset\n"
        "Daromadlarni tozalash: /resetoylik"
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
            f"✅ Qo'shildi\n{category}: {amount}\n\nJami: {total}"
        )
    except (ValueError, AttributeError):
        await update.message.reply_text(
            "Misol: ovqat 850"
        )
    except Exception:
        logger.exception("Kutilmagan xato add_expense ichida")
        await update.message.reply_text(
            "Xatolik yuz berdi, qaytadan urinib ko'ring."
        )


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0] or 0
    await update.message.reply_text(
        f"📊 Jami xarajat: {total}"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("DELETE FROM expenses")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='expenses'")
    conn.commit()
    await update.message.reply_text(
        "🗑️ Barcha xarajatlar o'chirildi. Bazani 0 dan boshladik."
    )


async def reset_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("DELETE FROM income")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='income'")
    conn.commit()
    await update.message.reply_text(
        "🗑️ Barcha daromad/oylik yozuvlari o'chirildi. Daromad 0 dan boshlandi."
    )


async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split(maxsplit=1)
        # parts[0] = "/oylik", parts[1] = "500000" yoki "500000 maosh"
        rest = parts[1].split(maxsplit=1)
        amount = int(rest[0])
        note = rest[1] if len(rest) > 1 else ""
        cursor.execute(
            "INSERT INTO income (amount, note) VALUES (?, ?)",
            (amount, note)
        )
        conn.commit()

        cursor.execute("SELECT SUM(amount) FROM income")
        total_income = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM expenses")
        total_expense = cursor.fetchone()[0] or 0
        balance = total_income - total_expense

        await update.message.reply_text(
            f"💰 Qo'shildi: {amount}\n\n"
            f"Jami daromad: {total_income}\n"
            f"Joriy balans: {balance}"
        )
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Misol: /oylik 500000\nyoki: /oylik 500000 maosh"
        )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT SUM(amount) FROM income")
    total_income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expense = cursor.fetchone()[0] or 0
    balance_amount = total_income - total_expense

    await update.message.reply_text(
        f"💼 Balans hisobi\n\n"
        f"Jami daromad: {total_income}\n"
        f"Jami xarajat: {total_expense}\n"
        f"Qolgan balans: {balance_amount}"
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("resetoylik", reset_income))
    app.add_handler(CommandHandler("oylik", add_income))
    app.add_handler(CommandHandler("balans", balance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense))
    logger.info("Bot ishga tushdi")
    app.run_polling()


if __name__ == "__main__":
    main()
