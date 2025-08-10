import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# === Выбор качества ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь мне ссылку на YouTube видео 🎥")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    context.user_data['url'] = url

    keyboard = [
        [InlineKeyboardButton("🎵 Аудио (mp3)", callback_data="audio")],
        [InlineKeyboardButton("📹 Видео 360p", callback_data="360")],
        [InlineKeyboardButton("📹 Видео 720p", callback_data="720")],
        [InlineKeyboardButton("📹 Видео 1080p", callback_data="1080")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выбери формат:", reply_markup=reply_markup)

# === Загрузка и отправка файла ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data
    url = context.user_data.get('url')

    if not url:
        await query.edit_message_text("Сначала отправь ссылку на видео!")
        return

    await query.edit_message_text("⏳ Загружаю... Подожди.")

    ydl_opts = {}
    filename = "downloaded"

    if choice == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{filename}.mp3",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
    elif choice in ["360", "720", "1080"]:
        resolutions = {
            "360": "bestvideo[height<=360]+bestaudio/best",
            "720": "bestvideo[height<=720]+bestaudio/best",
            "1080": "bestvideo[height<=1080]+bestaudio/best"
        }
        ydl_opts = {
            'format': resolutions[choice],
            'outtmpl': f"{filename}.mp4",
            'merge_output_format': 'mp4'
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_path = f"{filename}.mp3" if choice == "audio" else f"{filename}.mp4"

        await context.bot.send_document(chat_id=query.message.chat_id, document=open(file_path, 'rb'))
        os.remove(file_path)

    except Exception as e:
        await query.edit_message_text(f"Ошибка: {e}")

# === Запуск бота ===
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    app.run_polling()
