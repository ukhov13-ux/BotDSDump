import csv
import io
from telegram import Update
from telegram.ext import ContextTypes
from config import TELEGRAM_CHAT_ID
from db import get_db_pool

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        await update.message.reply_text("Нет доступа")
        return
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.id, c.exchange, c.symbol, s.entry_time, s.direction, s.entry_price, s.status, s.change_pct
            FROM signals s JOIN coins c ON c.id = s.coin_id
            ORDER BY s.entry_time DESC LIMIT 100
        """)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Биржа','Тикер','Время','Направление','Цена входа','Результат','Изменение %'])
    for r in rows:
        writer.writerow([r['id'], r['exchange'], r['symbol'], r['entry_time'],
                         r['direction'], r['entry_price'], r['status'], r['change_pct']])
    output.seek(0)
    await update.message.reply_document(document=output, filename='signals.csv')

async def growth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        await update.message.reply_text("Нет доступа")
        return
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.exchange, c.symbol, h.growth_pct, h.growth_start, h.detected_at, h.priority
            FROM high_growth_coins h
            JOIN coins c ON c.id = h.coin_id
            WHERE h.is_active = true
            ORDER BY h.priority DESC, h.detected_at DESC
        """)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Биржа','Тикер','Рост %','Начало роста','Обнаружено','Приоритет'])
    for r in rows:
        writer.writerow([r['exchange'], r['symbol'], f"{r['growth_pct']:.2f}%",
                         r['growth_start'], r['detected_at'], r['priority']])
    output.seek(0)
    await update.message.reply_document(document=output, filename='high_growth.csv')
