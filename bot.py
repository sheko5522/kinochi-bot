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
MONGO_URL = os.environ.get('MONGODB_URL', 'mongodb+srv://odilovshaxzod19_db_user:<db_password>@cluster0.2axuavi.mongodb.net/?appName=Cluster0')

# ADMIN IDlar - FAQAT ULAR VIDEO QO'SHA OLADI
ADMIN_IDS = [123456789, 987654321]  # ⚠️ O'ZINGIZNI TELEGRAM ID INGIZNI KIRITING

# Majburiy obuna kanallari
CHANNELS = [
    {"name": "Kanal 1", "username": "DjiVr44CLI4wMmMy", "url": "https://t.me/+DjiVr44CLI4wMmMy", "type": "private"},
    {"name": "Kanal 2", "username": "igUvKXzOJ1BkODAy", "url": "https://t.me/+igUvKXzOJ1BkODAy", "type": "private"}
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

# JSON fayl
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

def is_admin(user_id):
    """Admin tekshirish"""
    return user_id in ADMIN_IDS

def add_video_to_db(file_id, caption, kod):
    try:
        kod_str = str(kod).strip()
        
        # ✅ DUBLIKAT TEKSHIRISH
        existing = get_video_from_db(kod_str)
        if existing:
            logger.warning(f"⚠️ Kod dublikat: {kod_str}")
            return False
        
        if collection is not None:
            video_data = {
                "file_id": file_id,
                "caption": caption,
                "kod": kod_str,
                "date": int(time.time())
            }
            collection.insert_one(video_data)
            logger.info(f"✅ Video MongoDB ga qo'shildi: {kod_str}")
            return True
        else:
            videos = load_videos()
            videos.append({
                "file_id": file_id,
                "caption": caption,
                "kod": kod_str,
                "date": int(time.time())
            })
            logger.info(f"✅ Video JSON ga qo'shildi: {kod_str}")
            return save_videos(videos)
    except Exception as e:
        logger.error(f"Video qo'shish xatosi: {e}")
        return False

def get_video_from_db(kod):
    try:
        kod_str = str(kod).strip()
        
        if collection is not None:
            video = collection.find_one({"kod": kod_str})
            return video
        else:
            videos = load_videos()
            for video in videos:
                if str(video.get("kod", "")).strip() == kod_str:
                    return video
            return None
    except Exception as e:
        logger.error(f"Video olish xatosi: {e}")
        return None

def get_all_videos_from_db():
    try:
        if collection is not None:
            return list(collection.find().sort("kod", 1))
        else:
            return sorted(load_videos(), key=lambda x: x.get("kod", ""))
    except Exception as e:
        logger.error(f"Videolarni olish xatosi: {e}")
        return []

def delete_video_from_db(kod):
    try:
        kod_str = str(kod).strip()
        
        if collection is not None:
            result = collection.delete_one({"kod": kod_str})
            return result.deleted_count > 0
        else:
            videos = load_videos()
            new_videos = [v for v in videos if str(v.get("kod", "")).strip() != kod_str]
            if len(new_videos) != len(videos):
                return save_videos(new_videos)
            return False
    except Exception as e:
        logger.error(f"Video o'chirish xatosi: {e}")
        return False

def get_videos_count():
    try:
        if collection is not None:
            return collection.count_documents({})
        else:
            return len(load_videos())
    except Exception as e:
        logger.error(f"Videolar soni xatosi: {e}")
        return 0

def check_user(user_id):
    """Kanal obunasini tekshirish - faqat public kanallar uchun"""
    for channel in CHANNELS:
        if channel.get("type") == "private":
            continue  # Private kanallarni tekshirib bo'lmaydi
        
        try:
            channel_username = channel.get("username", "")
            if not channel_username:
                continue
            
            status = bot.get_chat_member("@" + channel_username, user_id).status
            if status in ['left', 'kicked']:
                return False
        except Exception as e:
            logger.error(f"Kanal tekshirish xatosi: {e}")
            continue
    return True

def ask_to_subscribe(chat_id):
    markup = types.InlineKeyboardMarkup()
    
    for channel in CHANNELS:
        markup.add(types.InlineKeyboardButton(text=f"📢 {channel['name']}", url=channel['url']))
    
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription"))
    
    bot.send_message(
        chat_id, 
        "🤖 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", 
        reply_markup=markup
    )

def show_welcome_message(chat_id, name):
    welcome_text = f"""🎬 Xush kelibsiz, {name}!

📝 Kino kodini yuboring:
Misol: <code>1001</code>"""
    
    bot.send_message(chat_id, welcome_text, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    
    if check_user(user_id):
        show_welcome_message(message.chat.id, name)
    else:
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
            "❌ Hali obuna bo'lmagansiz!",
            show_alert=True
        )

@bot.message_handler(commands=['getfileid'])
def get_file_id(message):
    """ADMIN: Video file_id sini olish"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda ruxsat yo'q!")
        return
    
    if message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        bot.reply_to(message, f"🎥 Video File ID:\n`{file_id}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Videoga reply qiling!")

@bot.message_handler(commands=['addreal'])
def add_real_video(message):
    """ADMIN: Haqiqiy video qo'shish"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda ruxsat yo'q!")
        return
    
    try:
        if not message.reply_to_message or not message.reply_to_message.video:
            bot.reply_to(message, "❌ Videoga reply qiling: /addreal 1001")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Kod kiriting: /addreal 1001")
            return
        
        kod = parts[1].strip()
        
        if not kod.isdigit():
            bot.reply_to(message, "❌ Kod faqat raqamlardan iborat bo'lishi kerak!")
            return
        
        # ✅ DUBLIKAT TEKSHIRISH
        existing = get_video_from_db(kod)
        if existing:
            bot.reply_to(message, f"❌ {kod} kodli kino allaqachon mavjud!")
            return
        
        video = message.reply_to_message.video
        caption = message.reply_to_message.caption or "🎬 Kino"
        
        # ✅ FILE ID VALIDATSIYA
        if len(video.file_id) < 20:
            bot.reply_to(message, "❌ File ID noto'g'ri!")
            return
        
        success = add_video_to_db(video.file_id, f"{caption}\n🔢 Kod: {kod}", kod)
        
        if success:
            bot.reply_to(message, f"✅ Kino qo'shildi!\n📁 Kod: {kod}")
        else:
            bot.reply_to(message, "❌ Kod allaqachon mavjud yoki xatolik!")
        
    except Exception as e:
        logger.error(f"addreal xatosi: {e}")
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['listvideos'])
def list_videos(message):
    """ADMIN: Barcha videolar ro'yxati"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda ruxsat yo'q!")
        return
    
    try:
        videos = get_all_videos_from_db()
        
        if not videos:
            bot.reply_to(message, "📭 Bazada kino yo'q")
            return
        
        text = f"📋 Bazadagi kinolar ({len(videos)} ta):\n\n"
        for video in videos[:20]:  # Faqat 20 tasini ko'rsatish
            kod = video.get('kod', 'Noma\'lum')
            text += f"🔢 {kod}\n"
        
        if len(videos) > 20:
            text += f"\n... va yana {len(videos) - 20} ta kino"
        
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['deletevideo'])
def delete_video(message):
    """ADMIN: Video o'chirish"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda ruxsat yo'q!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Kod kiriting: /deletevideo 1001")
            return
        
        kod = parts[1].strip()
        success = delete_video_from_db(kod)
        
        if success:
            bot.reply_to(message, f"✅ {kod} kodli kino o'chirildi!")
        else:
            bot.reply_to(message, f"❌ {kod} kodli kino topilmadi!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['stats'])
def stats(message):
    """ADMIN: Bot statistikasi"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda ruxsat yo'q!")
        return
    
    try:
        total_videos = get_videos_count()
        db_type = "MongoDB" if collection is not None else "JSON"
        bot.reply_to(message, 
            f"📊 Statistika:\n\n"
            f"🎬 Kinolar: {total_videos}\n"
            f"🗄️ Baza: {db_type}"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Obuna tekshirish
    if not check_user(user_id):
        ask_to_subscribe(message.chat.id)
        return
    
    # Faqat raqam bo'lsa qidirish
    if message.text and message.text.strip().isdigit():
        search_code = message.text.strip()
        logger.info(f"🔍 Qidiruv: {search_code}")
        
        try:
            video = get_video_from_db(search_code)
            
            if video:
                try:
                    bot.send_video(
                        message.chat.id, 
                        video["file_id"], 
                        caption=video.get("caption", f"🎬 Kod: {search_code}")
                    )
                    logger.info(f"✅ Video yuborildi: {search_code}")
                except Exception as e:
                    logger.error(f"Video yuborish xatosi: {e}")
                    bot.reply_to(message, f"❌ Videoni yuborishda xatolik!")
            else:
                bot.reply_to(message, f"❌ {search_code} kodli kino topilmadi!")
                
        except Exception as e:
            logger.error(f"Qidiruv xatosi: {e}")
            bot.reply_to(message, f"❌ Xatolik yuz berdi!")
    else:
        bot.send_message(message.chat.id, "📝 Kino kodini yuboring (faqat raqam)")

def main():
    logger.info("🤖 Bot ishga tushdi...")
    total_videos = get_videos_count()
    db_type = "MongoDB" if collection is not None else "JSON"
    logger.info(f"📊 Kinolar: {total_videos}")
    logger.info(f"🗄️ Baza: {db_type}")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"❌ Xato: {e}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()
