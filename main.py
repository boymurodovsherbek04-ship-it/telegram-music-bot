import os
import asyncio
import shutil
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp

# --- SOZLAMALAR ---
TOKEN = "8248425244:AAEQI8sjsOYgGWtDxf72vfQ_tkNSTVmEMBs"   # bu yerga o'z tokeningizni qo'ying
MAX_AUDIO_SIZE_MB = 49  # Telegram fayl limitiga mos (ko'proq bo'lsa (.oga) streaming kerak)

# --- YT-DLP OPTIONS ---
YDL_OPTS_AUDIO = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    # filename template: temporary folder will be used
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}

# --- HELPERS ---
def sizeof_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024

async def fetch_audio_from_query(query: str, tempdir: str) -> Path:
    """
    yt-dlp orqali 'ytsearch:' qidiruvi bilan topib audio mp3 yuklaydi.
    Qaytaradi: Path(mp3 fayl) yoki oshirishda Exception tashlanadi.
    """
    opts = YDL_OPTS_AUDIO.copy()
    opts["outtmpl"] = os.path.join(tempdir, "%(id)s.%(ext)s")
    # use ytsearch to find first match
    search = f"ytsearch:{query}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(search, download=True)
        # info for ytsearch returns 'entries' list
        if "entries" in info and info["entries"]:
            entry = info["entries"][0]
            # prepare filename: yt-dlp postprocessor produces mp3 with id.mp3
            file_stem = entry.get("id")
            # possible ext mp3
            mp3_path = Path(tempdir) / f"{file_stem}.mp3"
            if mp3_path.exists():
                return mp3_path
            # sometimes different naming: try to search for any mp3 created
            for p in Path(tempdir).glob("*.mp3"):
                return p
    raise FileNotFoundError("Audio topilmadi yoki yuklab bo'lmadi.")

async def fetch_audio_from_url(url: str, tempdir: str) -> Path:
    opts = YDL_OPTS_AUDIO.copy()
    opts["outtmpl"] = os.path.join(tempdir, "%(id)s.%(ext)s")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # find mp3 in tempdir
        for p in Path(tempdir).glob("*.mp3"):
            return p
    raise FileNotFoundError("URL dan audio olinmadi.")

# --- HANDLERLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Salom! Musiqa botga xush kelibsiz.\n\n"
        "Foydalanish:\n"
        "- Qo'shiq nomini yoki 'artist - nom' yozing → bot topib MP3 yuboradi.\n"
        "- YouTube/Instagram havolasini yuboring → bot audio yuklab yuboradi.\n"
        "⚠️ Iltimos, faqat qonuniy materiallardan foydalaning."
    )

async def song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /song <query>
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("❗️ Iltimos: /song <qo'shiq nomi yoki havola>")
        return
    await process_request(update, query)

async def text_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # treat free text as song query
    text = update.message.text.strip()
    # ignore commands
    if text.startswith("/"):
        return
    await process_request(update, text)

async def process_request(update: Update, query_or_url: str):
    msg = await update.message.reply_text("🔎 Izlanmoqda, audio yuklanmoqda... Iltimos kuting.")
    tempdir = tempfile.mkdtemp(prefix="songdl_")
    try:
        # detect if message looks like URL
        if query_or_url.startswith("http://") or query_or_url.startswith("https://"):
            path = await fetch_audio_from_url(query_or_url, tempdir)
        else:
            path = await fetch_audio_from_query(query_or_url, tempdir)

        # check size
        size_mb = sizeof_mb(path)
        if size_mb > MAX_AUDIO_SIZE_MB:
            # agar katta bo'lsa — userga link yuboramiz yoki qisqartirish
            await msg.edit_text(f"⚠️ Audio fayli juda katta ({size_mb:.1f} MB). Men fayl linkini yuboraman.")
            # alternativa: yuborish uchun Telegram fayl hosting ishlatish yoki faylni Google Drive ga yuklash
            # lekin hozir: faylni yuborishda harakat qilamiz (Telegram qoida bilan moslashadi)
            await update.message.reply_document(document=open(path, "rb"))
        else:
            await msg.edit_text("🔊 Audio tayyor, yuborilmoqda...")
            await update.message.reply_audio(audio=open(path, "rb"))
            await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❗ Xato: {e}")
    finally:
        # tozalash
        shutil.rmtree(tempdir, ignore_errors=True)

# --- ASOSIY ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("song", song_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_search_handler))
    print("Bot ishga tushdi. /start yuboring.")
    app.run_polling()

if __name__ == "__main__":
    main()
