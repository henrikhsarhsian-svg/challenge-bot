import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

participants = {}
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id not in participants:
        participants[user_id] = {'name': user_name, 'marks': [], 'joined_date': datetime.now()}
    
    keyboard = [[InlineKeyboardButton("Я держусь 💪", callback_data="mark_today")],
                [InlineKeyboardButton("Мой статус", callback_data="show_status")],
                [InlineKeyboardButton("Таблица участников", callback_data="show_leaderboard")]]
    
    await update.message.reply_text(f"Привет, {user_name}! 🔥\n\nТы в челлендже на 21 день.", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if query.data == "mark_today":
        if user_id not in participants:
            participants[user_id] = {'name': user_name, 'marks': [], 'joined_date': datetime.now()}
        
        now = datetime.now()
        participants[user_id]['marks'].append(now)
        streak = len(participants[user_id]['marks'])
        
        await context.bot.send_message(CHANNEL_ID, f"✅ {user_name} держится! {streak} отметок")
        await query.edit_message_text(f"✅ Отмечено! Серия: {streak}")
    
    elif query.data == "show_status":
        marks = len(participants.get(user_id, {}).get('marks', []))
        await query.edit_message_text(f"📊 Статус: {marks} отметок")
    
    elif query.data == "show_leaderboard":
        text = "🏆 Таблица\n\n"
        sorted_p = sorted(participants.items(), key=lambda x: len(x[1]['marks']), reverse=True)
        for idx, (uid, data) in enumerate(sorted_p[:10], 1):
            text += f"{idx}. {data['name']} — {len(data['marks'])}\n"
        await query.edit_message_text(text)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
