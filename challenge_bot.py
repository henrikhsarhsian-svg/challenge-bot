import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

participants = {}
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1001234567890"))
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id not in participants:
        participants[user_id] = {'name': user_name, 'marks': [], 'joined_date': datetime.now()}
    
    keyboard = [
        [InlineKeyboardButton("Я держусь 💪", callback_data="mark_today")],
        [InlineKeyboardButton("Мой статус", callback_data="show_status")],
        [InlineKeyboardButton("Таблица участников", callback_data="show_leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Привет, {user_name}! 🔥\n\nТы присоединился к челленджу на 21 день.\n\nНажимай 'Я держусь' каждый час, чтобы отметиться.\nВсе видят твой прогресс и будут тебя поддерживать.",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if query.data == "mark_today":
        now = datetime.now()
        current_hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        if user_id not in participants:
            participants[user_id] = {'name': user_name, 'marks': [], 'joined_date': now}
        
        last_mark = participants[user_id]['marks'][-1] if participants[user_id]['marks'] else None
        
        if last_mark and last_mark >= current_hour_start:
            await query.edit_message_text("✅ Ты уже отметился в этот час. Попробуй через час.")
        else:
            participants[user_id]['marks'].append(now)
            streak = len(participants[user_id]['marks'])
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"✅ {user_name} держится! Серия: {streak} отметок"
            )
            
            await query.edit_message_text(
                f"✅ Отмечено!\n\nСерия: {streak} отметок\nВремя: {now.strftime('%H:%M')}\n\nМолодец! 💪"
            )
    
    elif query.data == "show_status":
        if user_id not in participants:
            await query.edit_message_text("Ты ещё не присоединился. Используй /start")
            return
        
        marks = participants[user_id]['marks']
        streak = len(marks)
        joined = participants[user_id]['joined_date']
        days_in = (datetime.now() - joined).days + 1
        
        await query.edit_message_text(
            f"📊 Твой статус\n\nИмя: {user_name}\nОтметок: {streak}\nДней: {days_in}\nПоследняя: {marks[-1].strftime('%H:%M') if marks else 'Нет'}"
        )
    
    elif query.data == "show_leaderboard":
        sorted_participants = sorted(
            participants.items(),
            key=lambda x: len(x[1]['marks']),
            reverse=True
        )
        
        text = "🏆 Таблица участников\n\n"
        for idx, (uid, data) in enumerate(sorted_participants[:20], 1):
            text += f"{idx}. {data['name']} — {len(data['marks'])} отметок\n"
        
        await query.edit_message_text(text)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
