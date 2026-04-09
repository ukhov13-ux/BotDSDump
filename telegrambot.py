from telegram.ext import ApplicationBuilder, CommandHandler
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from handlers import stats_command, growth_command

async def run_telegram_bot(message_queue):
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("growth", growth_command))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        msg = await message_queue.get()
        text = format_message(msg)
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)

def format_message(msg):
    if msg.get('type') == 'signal':
        return (f"🔔 Сигнал №{msg['id']}\n"
                f"{msg['exchange']}: {msg['symbol']}\n"
                f"Цена: {msg['price']:.4f}\n"
                f"Направление: {msg['direction']}\n"
                f"Рост/Падение: {msg['change']*100:.2f}%")
    elif msg.get('type') == 'reversal':
        return (f"🔄 Разворот после {msg['orig_direction']}\n"
                f"{msg['exchange']}: {msg['symbol']}\n"
                f"Цена: {msg['price']:.4f}\n"
                f"Изменение: {msg['change']*100:.2f}%")
    return str(msg)
