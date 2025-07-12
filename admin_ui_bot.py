import json
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8128063909:AAG0WFoqw9eOT3-m0TrWofAtI8LaPfCZSH4"
ADMIN_USERNAME = "@TAKIHAMATA"
CLIENTS_FILE = "clients.json"

def load_clients():
    try:
        with open(CLIENTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_clients(clients):
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, indent=4)

def is_admin(update: Update):
    return update.effective_user.username == ADMIN_USERNAME.strip("@")

# === واجهة رئيسية ===
async def show_main_menu(update_or_query, context):
    keyboard = [
        [InlineKeyboardButton("🔑 مفاتيحي", callback_data="list_keys")],
        [InlineKeyboardButton("➕ إضافة مفتاح جديد", callback_data="add_key_prompt")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_home")]  # حتى في الواجهة الأولى
    ]
    text = "📋 مرحبًا بك في لوحة التحكم"
    if hasattr(update_or_query, "message"):
        await update_or_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update_or_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    await show_main_menu(update, context)

# === زر الرجوع الديناميكي ===
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    previous = context.user_data.get("last_menu", "main")
    if previous.startswith("view_"):
        update.callback_query.data = previous
        await handle_callback(update, context)
    else:
        await show_main_menu(update.callback_query, context)

# === جميع الأزرار ===
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update): return

    data = query.data
    clients = load_clients()

    if data == "list_keys":
        if not clients:
            await query.edit_message_text("ℹ️ لا توجد مفاتيح حالياً.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back_home")]]))
            return
        buttons = [[InlineKeyboardButton(f"🔑 {k}", callback_data=f"view_{k}")] for k in clients]
        buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_home")])
        await query.edit_message_text("🔑 قائمة المفاتيح:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("view_"):
        key = data[5:]
        context.user_data["last_menu"] = "list_keys"
        if key not in clients:
            await query.edit_message_text("❌ المفتاح غير موجود.")
            return
        k = clients[key]
        text = f"""🔑 *{key}*
⏳ ينتهي: {k['expires_at']}
👥 المستخدمون: {len(k['users'])} / {k['max_users']}
{"✅ مفعّل" if k['active'] else "⛔ موقوف"}"""
        buttons = [
            [InlineKeyboardButton("⏳ تغيير المدة", callback_data=f"extend_{key}")],
            [InlineKeyboardButton("⛔ توقيف المفتاح", callback_data=f"revoke_{key}")],
            [InlineKeyboardButton("🗑 حذف المفتاح", callback_data=f"delete_{key}")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="list_keys")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("extend_"):
        key = data[7:]
        context.user_data["extend"] = key
        context.user_data["last_menu"] = f"view_{key}"
        buttons = [[InlineKeyboardButton("⬅️ رجوع", callback_data=f"view_{key}")]]
        await query.edit_message_text(f"✏️ أرسل عدد الأيام الجديدة للمفتاح `{key}`", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "add_key_prompt":
        context.user_data["add"] = True
        context.user_data["last_menu"] = "main"
        buttons = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back_home")]]
        await query.edit_message_text("✍️ أرسل المفتاح والمدة وعدد المستخدمين (مثال: VIPKEY 7 30)",
                                      reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("revoke_"):
        key = data[7:]
        if key in clients:
            clients[key]["active"] = False
            save_clients(clients)
            await query.edit_message_text(f"⛔ تم توقيف المفتاح: {key}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data=f"view_{key}")]]))

    elif data.startswith("delete_"):
        key = data[7:]
        if key in clients:
            del clients[key]
            save_clients(clients)
            await query.edit_message_text(f"🗑 تم حذف المفتاح: {key}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="list_keys")]]))

    elif data == "back_home":
        await show_main_menu(query, context)

# === استقبال الردود ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    msg = update.message.text.strip()
    clients = load_clients()

    if "extend" in context.user_data:
        key = context.user_data.pop("extend")
        context.user_data["last_menu"] = f"view_{key}"
        try:
            days = int(msg)
            if key in clients:
                old = datetime.datetime.fromisoformat(clients[key]["expires_at"])
                clients[key]["expires_at"] = (old + datetime.timedelta(days=days)).isoformat()
                save_clients(clients)
                await update.message.reply_text(f"✅ تم تمديد `{key}` لمدة {days} يومًا", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ المفتاح غير موجود.")
        except:
            await update.message.reply_text("❌ صيغة خاطئة. أرسل رقمًا صحيحًا.")
        return

    if "add" in context.user_data:
        context.user_data.pop("add")
        try:
            key, days, max_users = msg.split()
            expires = (datetime.datetime.now() + datetime.timedelta(days=int(days))).isoformat()
            clients[key] = {"active": True, "expires_at": expires, "max_users": int(max_users), "users": []}
            save_clients(clients)
            await update.message.reply_text(f"✅ تم إنشاء المفتاح `{key}` لمدة {days} يوم و {max_users} مستخدم", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ صيغة غير صحيحة. مثال:\nVIPKEY 7 30")
        return

# === تشغيل البوت ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CallbackQueryHandler(go_back, pattern="back_home"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Telegram Admin Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
