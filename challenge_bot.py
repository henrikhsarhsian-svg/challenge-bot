import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# Данные в памяти (для продакшена — переведи на БД)
participants = {}  # {user_id: {'name': str, 'marks': [timestamps]}}
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1001234567890"))  # Твой ID закрытого канала
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Токен от BotFather

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id not in participants:
        participants[user_id] = {
            'name': user_name,
            'marks': [],
            'joined_date': datetime.now()
        }
    
    keyboard = [
        [InlineKeyboardButton("Я держусь 💪", callback_data="mark_today")],
        [InlineKeyboardButton("Мой статус", callback_data="show_status")],
        [InlineKeyboardButton("Таблица участников", callback_data="show_leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Привет, {user_name}! 🔥\n\n"
        f"Ты присоединился к челленджу на 21 день.\n\n"
        f"Нажимай 'Я держусь' каждый час, чтобы отметиться.\n"
        f"Все видят твой прогресс и будут тебя поддерживать.",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка инлайн-кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if query.data == "mark_today":
        # Проверяем, не отметился ли уже в этот час
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
            
            # Отправляем уведомление в канал
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"✅ {user_name} держится! Серия: {streak} отметок",
                parse_mode=ParseMode.HTML
            )
            
            await query.edit_message_text(
                f"✅ Отмечено!\n\n"
                f"Серия: <b>{streak}</b> отметок\n"
                f"Время: {now.strftime('%H:%M')}\n\n"
                f"Молодец! Ты уже близко к следующему часу 💪",
                parse_mode=ParseMode.HTML
            )
    
    elif query.data == "show_status":
        if user_id not in participants:
            await query.edit_message_text("Ты ещё не присоединился к челленджу. Используй /start")
            return
        
        marks = participants[user_id]['marks']
        streak = len(marks)
        joined = participants[user_id]['joined_date']
        days_in = (datetime.now() - joined).days + 1
        
        await query.edit_message_text(
            f"📊 Твой статус\n\n"
            f"Имя: {user_name}\n"
            f"Отметок: <b>{streak}</b>\n"
            f"Дней в челлендже: {days_in}\n"
            f"Последняя отметка: {marks[-1].strftime('%H:%M') if marks else 'Нет отметок'}",
            parse_mode=ParseMode.HTML
        )
    
    elif query.data == "show_leaderboard":
        # Таблица участников
        sorted_participants = sorted(
            participants.items(),
            key=lambda x: len(x[1]['marks']),
            reverse=True
        )
        
        leaderboard_text = "🏆 Таблица участников\n\n"
        for idx, (uid, data) in enumerate(sorted_participants[:20], 1):
            marks = len(data['marks'])
            leaderboard_text += f"{idx}. {data['name']} — {marks} отметок\n"
        
        await query.edit_message_text(leaderboard_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats — статистика челленджа"""
    total = len(participants)
    active_today = sum(1 for p in participants.values() if p['marks'] and 
                      (datetime.now() - p['marks'][-1]).seconds < 86400)
    total_marks = sum(len(p['marks']) for p in participants.values())
    
    stats_text = (
        f"📈 Статистика челленджа\n\n"
        f"Участников: {total}\n"
        f"Активных сегодня: {active_today}\n"
        f"Всего отметок: {total_marks}"
    )
    
    await update.message.reply_text(stats_text)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reset — только для администратора"""
    # Проверяем, что это администратор (замени на свой ID)
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У тебя нет прав.")
        return
    
    if context.args and context.args[0] == "confirm":
        participants.clear()
        await update.message.reply_text("✅ Данные очищены.")
    else:
        await update.message.reply_text(
            "⚠️ Это удалит все данные челленджа.\n"
            "Введи /reset confirm чтобы подтвердить."
        )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()
