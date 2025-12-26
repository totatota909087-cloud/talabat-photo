import subprocess
import sys
import time
import threading
import os
from flask import Flask, jsonify
import requests

# تثبيت المكتبات المطلوبة تلقائياً
def install_packages():
    required_packages = ['python-telegram-bot==20.7', 'flask==3.0.0', 'requests==2.31.0']
    for package in required_packages:
        package_name = package.split('==')[0]
        try:
            __import__(package_name.replace('-', '_'))
            print(f"✅ {package_name} مثبت بالفعل")
        except ImportError:
            print(f"📦 جاري تثبيت {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ تم تثبيت {package} بنجاح")

# تثبيت المكتبات
install_packages()

# الآن استيراد المكتبات بعد التثبيت
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import asyncio

# تمكين التسجيل للتصحيح
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تعريف مراحل المحادثة
APP_NAME, APP_PHOTO = range(2)

# معرف المطور
DEVELOPER_CHAT_ID = "7305720183"
DEVELOPER_USERNAME = "@jt_r3r"

# بيانات التواصل مع المطور
CONTACT_INFO = f"""
<b>إذا تأخر تسليم التطبيق لك</b>
<b>تواصل مع حمزه: {DEVELOPER_USERNAME}</b>
"""

# إنشاء تطبيق Flask
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    """الصفحة الرئيسية"""
    return jsonify({
        "status": "online",
        "service": "Telegram Bot",
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "message": "Bot is running on Render!",
        "developer": DEVELOPER_USERNAME,
        "version": "2.0"
    })

@flask_app.route('/health')
def health_check():
    """فحص صحة البوت"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "platform": "Render.com",
        "bot": "active"
    })

@flask_app.route('/keepalive')
def keep_alive_endpoint():
    """نقطة نهاية للحفاظ على البوت نشط"""
    return jsonify({
        "message": "Keep-alive triggered",
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "bot": "Active"
    })

def run_flask():
    """تشغيل خادم Flask"""
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# دالة بدء المحادثة
async def start(update: Update, context: CallbackContext) -> int:
    """يبدأ المحادثة ويرسل الرسالة الأولى."""
    user = update.effective_user
    
    # الرسالة الأولى المعدلة
    welcome_message = """<b>مرحبا بك 👋</b>

<b>1: إرسل الاسم التي تريد التطبيق يظهر به ✅❗</b>
<b>2: إرسل الصوره التي تريد التطبيق يظهر بها ⚡</b>

<b>وسيتم إنشاء تطبيق سحب الصور بنفس المواصفات اللي سترسلها ✅🥰</b>"""
    
    await update.message.reply_text(
        f"{welcome_message}",
        parse_mode='HTML'
    )
    
    # انتظار ثانيتين ثم إرسال الرسالة الثانية
    await asyncio.sleep(2)
    
    # الرسالة الثانية
    await update.message.reply_text(
        "<b>إرسل الآن إسم التطبيق</b>",
        parse_mode='HTML'
    )
    
    return APP_NAME

# دالة لمعرفة الـ ID
async def get_id(update: Update, context: CallbackContext):
    """يرجع الـ ID الخاص بالمستخدم."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await update.message.reply_text(
        f"<b>👤 معرفك: {user.id}</b>\n"
        f"<b>💬 معرف الدردشة: {chat_id}</b>\n\n"
        f"<b>📝 أرسل المعرف هذا إلى المطور ليرسله في المتغير DEVELOPER_CHAT_ID</b>",
        parse_mode='HTML'
    )

# دالة استقبال اسم التطبيق
async def receive_app_name(update: Update, context: CallbackContext) -> int:
    """يستقبل اسم التطبيق من المستخدم."""
    app_name = update.message.text
    context.user_data['app_name'] = app_name
    
    # حفظ اسم المستخدم ومعلوماته
    user = update.effective_user
    context.user_data['user_name'] = f"{user.first_name} {user.last_name or ''}"
    context.user_data['user_username'] = f"@{user.username}" if user.username else "لا يوجد"
    context.user_data['user_id'] = user.id
    
    await update.message.reply_text(
        "<b>إرسل الآن صورة التطبيق</b>",
        parse_mode='HTML'
    )
    
    return APP_PHOTO

# دالة استقبال صورة التطبيق
async def receive_app_photo(update: Update, context: CallbackContext) -> int:
    """يستقبل صورة التطبيق من المستخدم."""
    user = update.effective_user
    app_name = context.user_data.get('app_name', 'غير محدد')
    user_name = context.user_data.get('user_name', '')
    user_username = context.user_data.get('user_username', '')
    user_id = context.user_data.get('user_id', '')
    
    # الحصول على الصورة (آخر صورة هي الأعلى جودة)
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
    else:
        await update.message.reply_text(
            "<b>❌ لم يتم إرسال صورة. أرسل صورة من فضلك.</b>",
            parse_mode='HTML'
        )
        return APP_PHOTO
    
    # تجهيز معلومات الطلب للمطور
    request_info = f"""<b>📋 طلب تطبيق جديد</b>
<b>─────────────────────</b>
<b>👤 المستخدم:</b> <code>{user_name}</code>
<b>🆔 المعرف:</b> <code>{user_username}</code>
<b>📞 ID:</b> <code>{user_id}</code>
<b>─────────────────────</b>
<b>📱 اسم التطبيق:</b> <code>{app_name}</code>
<b>─────────────────────</b>"""
    
    try:
        # إرسال الطلب إلى المطور
        # أولاً: إرسال النص
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=request_info,
            parse_mode='HTML'
        )
        
        # ثانياً: إرسال الصورة
        await context.bot.send_photo(
            chat_id=DEVELOPER_CHAT_ID,
            photo=photo_file.file_id,
            caption=f"<b>صورة لتطبيق:</b> <code>{app_name}</code>",
            parse_mode='HTML'
        )
        
        # رسالة التأكيد للمستخدم
        confirmation_message = f"""<b>✅ تم إرسال طلبك لحمزه</b>

<b>📱 اسم التطبيق:</b> <code>{app_name}</code>

<b>🎯 سيتم إنشاء تطبيق سحب الصور بنفس المواصفات في أقرب وقت ممكن</b>

{CONTACT_INFO}"""
        
        await update.message.reply_text(
            confirmation_message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الطلب للمطور: {e}")
        await update.message.reply_text(
            "<b>❌ حدث خطأ في إرسال طلبك. يرجى المحاولة مرة أخرى لاحقاً.</b>",
            parse_mode='HTML'
        )
    
    # إنهاء المحادثة
    return ConversationHandler.END

# دالة الإلغاء
async def cancel(update: Update, context: CallbackContext) -> int:
    """يلغي المحادثة."""
    await update.message.reply_text(
        "<b>تم إلغاء الطلب. يمكنك البدء مرة أخرى باستخدام /start</b>",
        parse_mode='HTML'
    )
    return ConversationHandler.END

# دالة المساعدة
async def help_command(update: Update, context: CallbackContext):
    """يرسل رسالة المساعدة."""
    help_text = f"""<b>🤖 أوامر البوت:</b>

<b>/start</b> - بدء طلب تطبيق جديد
<b>/id</b> - معرفة رقم ID الخاص بك
<b>/help</b> - عرض هذه الرسالة
<b>/cancel</b> - إلغاء الطلب الحالي

<b>📝 طريقة الاستخدام:</b>
1. أرسل <b>/start</b>
2. أرسل اسم التطبيق
3. أرسل صورة توضيحية للتطبيق
4. سيتم إرسال طلبك للمطور

<b>👨‍💻 المطور:</b> حمزه {DEVELOPER_USERNAME}

<b>🌐 البوت مستضاف على Render.com</b>"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

# دالة للحفاظ على البوت نشط باستخدام Flask
def keep_alive_with_flask():
    """تشغيل Flask في thread منفصل"""
    try:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("✅ Flask server started")
        port = os.environ.get('PORT', 10000)
        print(f"🌐 Running on port: {port}")
        print(f"🔗 Web URL: http://0.0.0.0:{port}")
    except Exception as e:
        print(f"⚠️ خطأ في تشغيل Flask: {e}")

# دالة لطباعة رسالة التشغيل
def print_banner():
    """طباعة رسالة ترحيبية عند تشغيل البوت"""
    print("\n" + "="*60)
    print("🤖 TELEGRAM BOT - RENDER.COM DEPLOYMENT")
    print("="*60)
    print(f"⏰ Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("🚀 Deployment Platform: Render.com")
    print(f"🌐 Port: {os.environ.get('PORT', 10000)}")
    print("="*60)
    print("📦 Using python-telegram-bot v20.7")
    print("="*60 + "\n")

# دالة Self-ping للحفاظ على البوت نشط
def self_ping():
    """إرسال طلبات ذاتية للحفاظ على البوت نشط"""
    while True:
        try:
            port = os.environ.get('PORT', 10000)
            response = requests.get(f'http://0.0.0.0:{port}/keepalive', timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] 🔄 Self-ping sent, Status: {response.status_code}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Self-ping failed: {e}")
        
        # الانتظار 14 دقيقة (أقل من 15 دقيقة وقت السكون في Render)
        time.sleep(840)

# دالة الرئيسية
def main() -> None:
    """تشغيل البوت."""
    # توكن البوت
    TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
    
    # طباعة بانر التشغيل
    print_banner()
    
    # تشغيل Flask في thread منفصل
    keep_alive_with_flask()
    
    # انتظار قليل لبدء Flask
    time.sleep(3)
    
    # بدء نظام self-ping
    self_ping_thread = threading.Thread(target=self_ping, daemon=True)
    self_ping_thread.start()
    
    # إنشاء تطبيق Telegram مع الإصدار الصحيح
    application = Application.builder().token(TOKEN).build()
    
    # إعداد معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            APP_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_app_name)
            ],
            APP_PHOTO: [
                MessageHandler(filters.PHOTO, receive_app_photo)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # إضافة المعالجات
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    
    print("✅ Telegram bot started successfully!")
    print("📱 Send /start to the bot to begin")
    print("⚡ Bot is now ready to receive requests!")
    print("🔄 Self-ping enabled every 14 minutes")
    
    # تشغيل البوت
    print("🚀 Starting bot polling...")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()
