import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

BOT_TOKEN = "8183843583:AAGFFgPYqt70-2XrHtFlFU61usTYlDjz4E4"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salam! YouTube linkini göndər, format seç və yüklə!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("📌 Zəhmət olmasa düzgün YouTube linki göndərin.")
        return

    await update.message.reply_text("🔎 Formatlar yoxlanılır...")

    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'cookiefile': 'cookies.txt'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            added_itags = set()
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    itag = f.get('format_id')
                    if itag not in added_itags:
                        added_itags.add(itag)
                        size = f.get('filesize') or 0
                        size_mb = round(size / (1024 * 1024), 1) if size else '?'
                        text = f"{f.get('format_note', '')} - {f.get('ext')} - {f.get('height', '')}p ({size_mb} MB)"
                        buttons.append([InlineKeyboardButton(text, callback_data=f"{itag}|{url}")])
            buttons.append([InlineKeyboardButton("🎵 Yalnız MP3", callback_data=f"mp3|{url}")])
            reply_markup = InlineKeyboardMarkup(buttons)
            await update.message.reply_text("🎬 Format seç:", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"❌ Xəta: {str(e)}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    itag_or_mp3, url = data.split('|')
    await query.edit_message_text("⏬ Yüklənir... Zəhmət olmasa gözləyin.")
    try:
        if itag_or_mp3 == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'yt_audio.%(ext)s',
                'quiet': True,
                'cookiefile': 'cookies.txt',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            }
        else:
            ydl_opts = {
                'format': f"{itag_or_mp3}",
                'outtmpl': 'yt_video.%(ext)s',
                'quiet': True,
                'cookiefile': 'cookies.txt',
            }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if itag_or_mp3 == "mp3":
                filename = filename.rsplit('.', 1)[0] + '.mp3'
        await context.bot.send_document(chat_id=query.message.chat.id, document=open(filename, 'rb'))
        os.remove(filename)
    except Exception as e:
        await query.edit_message_text(f"❌ Yükləmə Xətası: {str(e)}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button))
app.run_polling()
