import os
import telebot
from telebot import types
from pymongo import MongoClient
import time

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
    client = MongoClient(MONGO_URL)
    db = client["kinochi_bot"]
    collection = db["videos"]
    print("✅ MongoDB ga ulandi")
except Exception as e:
    print(f"❌ MongoDB ulanish xatosi: {e}")
    exit(1)

def check_user(user_id):
    """Foydalanuvchi barcha kanallarga obuna bo'lganligini tekshiradi"""
    for channel in CHANNELS:
        try:
            channel_username = channel["url"].split("/")[-1]
            if channel_username.startswith("+"):
                continue
            status = bot.get_chat_member("@" + channel_username, user_id).status
            if status in ['left', 'kicked']:
                return False
        except Exception as e:
            print(f"Kanal tekshirish xatosi: {e}")
            continue
    return True

def ask_to_subscribe(chat_id):
    """Obuna bo'lish so'rovini yuboradi"""
    markup = types.InlineKeyboardMarkup()
    
    markup.add(types.InlineKeyboardButton(text="📢 Kanal 1", url="https://t.me/+DjiVr44CLI4wMmMy"))
    markup.add(types.InlineKeyboardButton(text="🛍 Kanal 2", url="https://t.me/+igUvKXzOJ1BkODAy"))
    markup.add(types.InlineKeyboardButton(text="📷 Kanal 3", url="https://www.instagram.com/mozda_academy_"))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription"))
    
    bot.send_message(chat_id, "🤖 Botdan to'liq foydalanish uchun quyidagi 3 ta kanalga obuna bo'ling:", reply_markup=markup)

def show_welcome_message(chat_id, name):
    """Obuna bo'lgandan keyin ko'rsatiladigan xabar"""
    welcome_text = f"""🎬 Assalomu alaykum {name}!

Kino qidirish botiga xush kelibsiz!

📝 **Qanday ishlatish:**
Kino kodini raqam shaklida yuboring

Misol: <code>1001</code>"""
    
    bot.send_message(chat_id, welcome_text, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start(message):
    """Start komandasi"""
    ask_to_subscribe(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_callback(call):
    """Obunani tekshirish"""
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

@bot.message_handler(commands=['addvideo'])
def add_video(message):
    """Video qo'shish"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, 
                "❌ Video file_id va kodni kiriting:\n"
                "Misol: /addvideo BAACAgIAAxkBAAIB... 1001\n\n"
                "File ID olish uchun videoni @RawDataBot ga yuboring"
            )
            return
        
        file_id = parts[1]
        kod = parts[2] if len(parts) > 2 else None
        
        if not kod or not kod.isdigit():
            bot.reply_to(message, "❌ Kod kiriting: /addvideo file_id 1001")
            return
        
        # Kod takrorlanmasligini tekshiramiz
        existing = collection.find_one({"kod": kod})
        if existing:
            bot.reply_to(message, f"❌ {kod} kodli kino allaqachon mavjud!")
            return
        
        video_data = {
            "file_id": file_id,
            "caption": f"🎬 Kino\n🔢 Kod: {kod}",
            "kod": kod,
            "date": int(time.time())
        }
        
        collection.insert_one(video_data)
        bot.reply_to(message, f"✅ Kino bazaga qo'shildi!\n📁 Kod: {kod}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['quickadd'])
def quick_add(message):
    """Tez video qo'shish"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Kod kiriting: /quickadd 1001")
            return
        
        kod = parts[1]
        
        if not kod.isdigit():
            bot.reply_to(message, "❌ Kod faqat raqamlardan iborat bo'lishi kerak!")
            return
        
        # Test video file_id
        test_file_id = "BAACAgIAAxkBAAIBC2ZzAa012s9uOZqGoqHj7wABXr-5TAACbC0AAkWxyUvZcSVAAbRjAAE0BA"
        
        existing = collection.find_one({"kod": kod})
        if existing:
            bot.reply_to(message, f"❌ {kod} kodli kino allaqachon mavjud!")
            return
        
        video_data = {
            "file_id": test_file_id,
            "caption": f"🎬 Test Kino\n🔢 Kod: {kod}\n📝 Bu test kinosi",
            "kod": kod,
            "date": int(time.time())
        }
        
        collection.insert_one(video_data)
        bot.reply_to(message, f"✅ Test kino qo'shildi!\n📁 Kod: {kod}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['listvideos'])
def list_videos(message):
    """Bazadagi barcha kinolarni ko'rsatish"""
    try:
        videos = list(collection.find().sort("kod", 1))
        
        if not videos:
            bot.reply_to(message, "📭 Bazada hech qanday kino yo'q")
            return
        
        text = f"📋 Bazadagi kinolar ({len(videos)} ta):\n\n"
        for video in videos:
            caption_preview = video['caption'].split('\n')[0] if video['caption'] else "Kino"
            text += f"🔢 Kod: {video['kod']}\n"
            text += f"   {caption_preview[:40]}...\n\n"
        
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['deletevideo'])
def delete_video(message):
    """Kinoni o'chirish"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ O'chirish uchun kod kiriting: /deletevideo 1001")
            return
        
        kod = parts[1]
        result = collection.delete_one({"kod": kod})
        
        if result.deleted_count > 0:
            bot.reply_to(message, f"✅ {kod} kodli kino o'chirildi!")
        else:
            bot.reply_to(message, f"❌ {kod} kodli kino topilmadi!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(commands=['stats'])
def stats(message):
    """Bot statistikasi"""
    try:
        total_videos = collection.count_documents({})
        bot.reply_to(message, f"📊 Bot statistikasi:\n\n🎬 Kinolar soni: {total_videos}")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Barcha xabarlarni qayta ishlash"""
    user_id = message.from_user.id
    
    # Obunani tekshirish
    if not check_user(user_id):
        ask_to_subscribe(message.chat.id)
        return
    
    # Raqamli kod qidirish
    if message.text.isdigit():
        search_code = message.text
        try:
            video = collection.find_one({"kod": search_code})
            
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
    """Asosiy funksiya"""
    print("🤖 Bot ishga tushmoqda...")
    print(f"📊 Bazadagi kinolar: {collection.count_documents({})} ta")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Bot xatosi: {e}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()