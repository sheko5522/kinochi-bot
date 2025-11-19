import os
import telebot
from telebot import types
from pymongo import MongoClient
import time
import json
import logging

# Log sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sozlamalar
TOKEN = os.environ.get('BOT_TOKEN', '8473633645:AAG5CL9e7-8XuE2oEQLNAgsLlKefPpZpWPk')
MONGO_URL = os.environ.get('MONGODB_URL', 'mongodb+srv://odilovshaxzod19_db_user:82bAh70O3wSleL53@cluster0.2axuavi.mongodb.net/?appName=Cluster0')

# Majburiy obuna kanallari
CHANNELS = [
    {"name": "Kanal 1", "url": "https://t.me/+DjiVr44CLI4wMmMy"},
    {"name": "Kanal 2", "url": "https://t.me/+igUvKXzOJ1BkODAy"},
    {"name": "Kanal 3", "url": "https://www.instagram.com/mozda_academy_"}
]

bot = telebot.TeleBot(TOKEN)

# MongoDB ulanish
try:
    client = MongoClient(
        MONGO_URL,
        tlsAllowInvalidCertificates=True,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )
    
    client.admin.command('ismaster')
    db = client["kinochi_bot"]
    collection = db["videos"]
    logger.info("✅ MongoDB ga muvaffaqiyatli ulandi")
    
except Exception as e:
    logger.error(f"❌ MongoDB ulanish xatosi: {e}")
    collection = None
    logger.info("📁 JSON fayldan foydalaniladi")

# JSON fayl bilan ishlash
JSON_FILE = "videos.json"

def load_videos():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_videos(videos):
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"JSON saqlash xatosi: {e}")
        return False

def add_video_to_db(file_id, caption, kod):
    try:
        if collection:
            video_data = {
                "file_id": file_id,
                "caption": caption,
                "kod": kod,
                "date": int(time.time())
            }
            collection.insert_one(video_data)
            return True
        else:
            videos = load_videos()
            videos.append({
                "file_id": file_id,
                "caption": caption,
                "kod": kod,
                "date": int(time.time())
            })
            return save_videos(videos)
    except Exception as e:
        logger.error(f"Video qo'shish xatosi: {e}")
        return False

def get_video_from_db(kod):
    try:
        if collection:
            return collection.find_one({"kod": kod})
        else:
            videos = load_videos()
            for video in videos:
                if str(video.get("kod")) == str(kod):
                    return video
            return None
    except Exception as e:
        logger.error(f"Video olish xatosi: {e}")
        return None

def get_all_videos_from_db():
    try:
        if collection:
            return list(collection.find().sort("kod", 1))
        else:
            return load_videos()
    except Exception as e:
        logger.error(f"Videolarni olish xatosi: {e}")
        return []

def delete_video_from_db(kod):
    try:
        if collection:
            result = collection.delete_one({"kod": kod})
            return result.deleted_count > 0
        else:
            videos = load_videos()
            new_videos = [v for v in videos if str(v.get("kod")) != str(kod)]
            if len(new_videos) != len(videos):
                return save_videos(new_videos)
            return False
    except Exception as e:
        logger.error(f"Video o'chirish xatosi: {e}")
        return False

def get_videos_count():
    try:
        if collection:
            return collection.count_documents({})
        else:
            return len(load_videos())
    except Exception as e:
        logger.error(f"Videolar soni xatosi: {e}")
        return 0

def check_user(user_id):
    for channel in CHANNELS:
        try:
            if channel["url"].startswith("https://t.me/+"):
                continue
            channel_username = channel["url"].split("/")[-1]
            status = bot.get_chat_member("@" + channel_username, user_id).status
            if status in ['left', 'kicked']:
                return False
        except Exception as e:
            logger.error(f"Kanal tekshirish xatosi: {e}")
            continue
    return True

def ask_to_subscribe(chat_id):
    markup = types.InlineKeyboardMarkup()
    
    markup.add(types.InlineKeyboardButton(text="📢 Kanal 1", url="https://t.me/+DjiVr44CLI4wMmMy"))
    markup.add(types.InlineKeyboardButton(text="🛍 Kanal 2", url="https://t.me/+igUvKXzOJ1BkODAy"))
    markup.add(types.InlineKeyboardButton(text="📷 Kanal 3", url="https://www.instagram.com/mozda_academy_"))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription"))
    
    bot.send_message(
        chat_id, 
        "🤖 Botdan to'liq foydalanish uchun quyidagi 3 ta kanalga obuna bo'ling:", 
        reply_markup=markup
    )

def show_welcome_message(chat_id, name):
    welcome_text = f"""🎬 Assalomu alaykum {name}!

Kino qidirish botiga xush kelibsiz!

📝 **Qanday ishlatish:**
Kino kodini raqam shaklida yuboring

Misol: <code>1001</code>"""
    
    bot.send_message(chat_id, welcome_text, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start(message):
    ask_to_subscribe(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_callback(call):
    user_id = call.from_user.id
    name = call.from_user.first_name
    
    if check_user(user_id):
        show_welcome_message(call.message.chat.id, name)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Hali barcha kanallarga obuna bo'lmagansiz!",
            show_alert=True
        )

# 🔽 YANGI: File ID olish uchun
@bot.message_handler(commands=['getfileid'])
def get_file_id(message):
    """Video file_id sini olish"""
    if message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        bot.reply_to(message, f"🎥 Video File ID:\n`{file_id}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Videoga reply qiling!")

@bot.message_handler(commands=['addvideo'])
def add_video(message):
    """Video qo'shish"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, 
                "❌ Video file_id va kodni kiriting:\n"
                "Misol: /addvideo BAACAgIAAxkBAAIB... 1001\n\n"
                "File ID olish uchun videoni /getfileid buyrug'i bilan oling"
            )
            return
        
        file_id = parts[1]
        kod = parts[2] if len(parts) > 2 else None
        
        if not kod or not kod.isdigit():
            bot.reply_to(message, "❌ Kod kiriting: /addvideo file_id 1001")
            return
        
        existing = get_video_from_db(kod)
        if existing:
            bot.reply_to(message, f"❌ {kod} kodli kino allaqachon mavjud!")
            return
        
        success = add_video_to_db(file_id, f"🎬 Kino\n🔢 Kod: {kod}", kod)
        
        if success:
            bot.reply_to(message, f"✅ Kino bazaga qo'shildi!\n📁 Kod: {kod}")
        else:
            bot.reply_to(message, "❌ Kino qo'shishda xatolik!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# 🔽 YANGI: Haqiqiy video qo'shish
@bot.message_handler(commands=['addreal'])
def add_real_video(message):
    """Haqiqiy video qo'shish"""
    try:
        if not message.reply_to_message or not message.reply_to_message.video:
            bot.reply_to(message, "❌ Videoga reply qiling: /addreal 1001")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Kod kiriting: /addreal 1001")
            return
        
        kod = parts[1]
        
        if not kod.isdigit():
            bot.reply_to(message, "❌ Kod faqat raqamlardan iborat bo'lishi kerak!")
            return
        
        video = message.reply_to_message.video
        caption = message.reply_to_message.caption or f"🎬 Kino\n🔢 Kod: {kod}"
        
        existing = get_video_from_db(kod)
        if existing:
            bot.reply_to(message, f"❌ {kod} kodli kino allaqachon mavjud!")
            return
        
        success = add_video_to_db(video.file_id, f"{caption}\n🔢 Kod: {kod}", kod)
        
        if success:
            bot.reply_to(message, f"✅ Haqiqiy kino qo'shildi!\n📁 Kod: {kod}")
        else:
            bot.reply_to(message, "❌ Kino qo'shishda xatolik!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['listvideos'])
def list_videos(message):
    try:
        videos = get_all_videos_from_db()
        
        if not videos:
            bot.reply_to(message, "📭 Bazada hech qanday kino yo'q")
            return
        
        text = f"📋 Bazadagi kinolar ({len(videos)} ta):\n\n"
        for video in videos:
            caption_preview = video.get('caption', 'Kino').split('\n')[0]
            text += f"🔢 Kod: {video.get('kod', 'Noma\'lum')}\n"
            text += f"   {caption_preview[:40]}...\n\n"
        
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['deletevideo'])
def delete_video(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ O'chirish uchun kod kiriting: /deletevideo 1001")
            return
        
        kod = parts[1]
        success = delete_video_from_db(kod)
        
        if success:
            bot.reply_to(message, f"✅ {kod} kodli kino o'chirildi!")
        else:
            bot.reply_to(message, f"❌ {kod} kodli kino topilmadi!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['stats'])
def stats(message):
    try:
        total_videos = get_videos_count()
        db_type = "MongoDB" if collection else "JSON fayl"
        bot.reply_to(message, f"📊 Bot statistikasi:\n\n🎬 Kinolar soni: {total_videos}\n🗄️ Ma'lumotlar bazasi: {db_type}")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    if not check_user(user_id):
        ask_to_subscribe(message.chat.id)
        return
    
    if message.text.isdigit():
        search_code = message.text
        try:
            video = get_video_from_db(search_code)
            
            if video:
                try:
                    bot.send_video(message.chat.id, video["file_id"], caption=video["caption"])
                except Exception as e:
                    bot.reply_to(message, 
                        f"❌ Videoni yuborishda xatolik!\n"
                        f"Kod: {search_code}\n"
                        f"File ID noto'g'ri yoki video o'chirilgan"
                    )
            else:
                bot.reply_to(message, f"❌ {search_code} kodli kino topilmadi!")
        except Exception as e:
            bot.reply_to(message, f"❌ Bazadan o'qish xatosi: {e}")
    else:
        help_text = """📋 **Botdan foydalanish:**

Kino kodini raqam shaklida yuboring.

Misol: <code>1001</code>"""
        bot.send_message(message.chat.id, help_text, parse_mode='HTML')

def main():
    logger.info("🤖 Bot ishga tushmoqda...")
    total_videos = get_videos_count()
    db_type = "MongoDB" if collection else "JSON fayl"
    logger.info(f"📊 Bazadagi kinolar: {total_videos} ta")
    logger.info(f"🗄️ Ma'lumotlar bazasi: {db_type}")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"❌ Bot xatosi: {e}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()
