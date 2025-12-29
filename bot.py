import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from config import Config
from database import SimpleDB
from datetime import datetime

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create database
db = SimpleDB(Config.DB_FILE)

# Main menu buttons
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ad")],
        [InlineKeyboardButton("📋 Micro Tasks", callback_data="micro_tasks")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite_friends")],
        [InlineKeyboardButton("🖥️ Open Web App", web_app=WebAppInfo(url=Config.WEB_APP_URL))],
        [InlineKeyboardButton("💰 My Balance", callback_data="my_balance")],
        [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check if user came from invite link
    invite_link = context.args[0] if context.args else None
    
    # Get or create user
    user_data = db.get_user(user.id)
    
    # Reset daily stats if new day
    if user_data["daily_stats"]["last_login"]:
        last_login = datetime.fromisoformat(user_data["daily_stats"]["last_login"])
        if last_login.date() < datetime.now().date():
            db.reset_daily_stats(user.id)
    
    # Update last login
    db.update_user(user.id, {
        "daily_stats.last_login": datetime.now().isoformat(),
        "username": user.username,
        "first_name": user.first_name
    })
    
    welcome_text = f"""
🤖 Welcome to {Config.BOT_NAME}, {user.first_name}!

✨ {Config.BOT_NAME} is a smart earning system that allows you to:
• 📺 Earn by watching ads
• 📋 Collect coins by completing small tasks
• 👥 Get rewards by inviting friends
• 💰 Manage your earnings

🎯 {Config.BOT_NAME} Benefits:
✓ Fast and reliable payments
✓ Easy to use interface
✓ 24/7 support
✓ Complete security

👇 Choose an option to start:
"""
    
    # Handle referral
    if invite_link and invite_link.isdigit():
        try:
            inviter_id = int(invite_link)
            if not user_data.get("invited_by") and inviter_id != user.id:
                db.update_user(user.id, {"invited_by": inviter_id})
                
                # Add to inviter's invite list
                inviter_data = db.get_user(inviter_id)
                invites = inviter_data.get("invites", [])
                if str(user.id) not in invites:
                    invites.append(str(user.id))
                    db.update_user(inviter_id, {"invites": invites})
                
                # Reward inviter
                db.add_coins(inviter_id, Config.REWARDS["invite"], f"Invite reward from user {user.id}")
                
                # Gift to new user
                db.add_coins(user.id, 10, "Welcome gift for joining via referral")
                
                welcome_text += f"\n\n🎉 You joined via friend's invite! Received 10 coins gift!"
        except Exception as e:
            logger.error(f"Error processing invite: {e}")
    
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

# Show ads
async def show_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    
    # Check daily limit
    if user_data["daily_stats"]["ads_watched"] >= Config.LIMITS["max_ads_per_day"]:
        await query.edit_message_text(
            "⚠️ Daily Limit Reached\n\n"
            "You have reached the maximum number of ads for today.\n"
            "🕒 Please try again tomorrow.",
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )
        return
    
    # Ad content
    ad_content = f"""
📺 {Config.BOT_NAME} Ads

🎯 Special Offer for You:
Learn Python Programming - Free Course

⏱️ Duration: 30 seconds

💡 Please watch the ad completely to receive your reward.

👇 After watching completely, click the confirm button below.
"""
    
    keyboard = [
        [InlineKeyboardButton("✅ I Watched", callback_data="confirm_ad")],
        [InlineKeyboardButton("❌ Cancel", callback_data="back")]
    ]
    
    await query.edit_message_text(
        ad_content,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Confirm ad watch
async def confirm_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    
    # Check if already at limit
    if user_data["daily_stats"]["ads_watched"] >= Config.LIMITS["max_ads_per_day"]:
        await query.edit_message_text(
            "⚠️ Daily limit already reached.",
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )
        return
    
    # Add coins
    coins = db.add_coins(user_id, Config.REWARDS["ad_watch"], "Watched ad")
    
    # Update daily stats
    user_data["daily_stats"]["ads_watched"] += 1
    db.save_data()
    
    await query.edit_message_text(
        f"✅ Ad watched successfully!\n\n"
        f"🎁 {Config.REWARDS['ad_watch']} coins added to your account.\n"
        f"💰 Current balance: {coins} coins\n\n"
        f"📊 Today's stats: {user_data['daily_stats']['ads_watched']}/{Config.LIMITS['max_ads_per_day']} ads",
        reply_markup=main_menu(),
        parse_mode='Markdown'
    )

# Show micro tasks
async def show_micro_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tasks = [
        {"id": 1, "title": "Complete a survey", "reward": 5, "time": "2 minutes"},
        {"id": 2, "title": "Watch a tutorial", "reward": 8, "time": "3 minutes"},
        {"id": 3, "title": "Test a feature", "reward": 10, "time": "5 minutes"},
        {"id": 4, "title": "Rate our service", "reward": 3, "time": "1 minute"},
        {"id": 5, "title": "Share feedback", "reward": 7, "time": "2 minutes"}
    ]
    
    keyboard = []
    for task in tasks:
        keyboard.append([
            InlineKeyboardButton(
                f"📌 {task['title']} - {task['reward']} coins",
                callback_data=f"task_{task['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    
    await query.edit_message_text(
        f"📋 {Config.BOT_NAME} Micro Tasks\n\n"
        "Complete tasks and earn coins:\n"
        "Click on a task to start.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Show invite page
async def show_invite_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    
    invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
    
    text = f"""
👥 {Config.BOT_NAME} Referral System

🔗 Your personal invite link:
`{invite_link}`

🎁 Referral rewards:
• 👤 You: **{Config.REWARDS['invite']} coins** per successful invite
• 👥 Your friend: **10 coins** welcome gift

📊 Your referral stats:
• Total invites: **{len(user_data.get('invites', []))}**
• Maximum allowed: **{Config.LIMITS['max_invites']}**
• Total rewards: **{len(user_data.get('invites', [])) * Config.REWARDS['invite']} coins**

💡 How it works:
1. Share your link with friends
2. They join using your link
3. They complete their first task
4. You get {Config.REWARDS['invite']} coins!
"""
    
    keyboard = [
        [InlineKeyboardButton("🔗 Copy Link", callback_data="copy_link")],
        [InlineKeyboardButton("📤 Share Link", callback_data="share_link")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# Show balance
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    
    text = f"""
💰 Your Financial Status in {Config.BOT_NAME}

💎 Coin balance: {user_data['coins']}
🏦 Total earned: {user_data['total_earned']} coins

📊 Recent transactions:
"""
    
    # Show last 5 transactions
    transactions = user_data.get("transactions", [])[-5:]
    for t in reversed(transactions):
        date = datetime.fromisoformat(t['date']).strftime("%H:%M")
        text += f"\n• [{date}] {t['reason']}: **{t['amount']} coins**"
    
    if not transactions:
        text += "\n• No transactions yet"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# Show stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    
    stats = user_data["daily_stats"]
    
    text = f"""
📊 Your Daily Stats in {Config.BOT_NAME}

📺 Ads watched: {stats['ads_watched']}/{Config.LIMITS['max_ads_per_day']}
📋 Tasks completed: {stats['tasks_completed']}/{Config.LIMITS['max_tasks_per_day']}
👥 Successful invites: {len(user_data.get('invites', []))}

💰 Overall performance:
• Total earned: **{user_data['total_earned']} coins**
• Current balance: **{user_data['coins']} coins**
• Available for withdrawal: **{user_data['coins']} coins**

📈 Daily progress:
• Ads: {int((stats['ads_watched'] / Config.LIMITS['max_ads_per_day']) * 100)}%
• Tasks: {int((stats['tasks_completed'] / Config.LIMITS['max_tasks_per_day']) * 100)}%
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# Handle task completion
async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    
    # Check limit
    if user_data["daily_stats"]["tasks_completed"] >= Config.LIMITS["max_tasks_per_day"]:
        await query.edit_message_text(
            "⚠️ You have reached the maximum tasks allowed for today.",
            reply_markup=main_menu()
        )
        return
    
    # Task info
    task_info = {
        1: {"title": "Complete a survey", "reward": 5},
        2: {"title": "Watch a tutorial", "reward": 8},
        3: {"title": "Test a feature", "reward": 10},
        4: {"title": "Rate our service", "reward": 3},
        5: {"title": "Share feedback", "reward": 7}
    }
    
    task = task_info.get(task_id, {"title": "Task", "reward": 5})
    
    # Simulate task completion
    await query.edit_message_text(
        f"🔄 Completing task: {task['title']}\nPlease wait...",
        parse_mode='Markdown'
    )
    
    import asyncio
    await asyncio.sleep(2)  # Simulate task delay
    
    # Give reward
    coins = db.add_coins(user_id, task["reward"], f"Completed task: {task['title']}")
    
    # Update stats
    user_data["daily_stats"]["tasks_completed"] += 1
    db.save_data()
    
    await query.edit_message_text(
        f"✅ Task '{task['title']}' completed successfully!\n\n"
        f"🎁 {task['reward']} coins added to your account.\n"
        f"💰 Current balance: {coins} coins",
        reply_markup=main_menu()
    )

# Handle Web App data
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        user_id = update.effective_user.id
        
        if data.get('action') == 'get_user_data':
            user_data = db.get_user(user_id)
            response = {
                'balance': user_data['coins'],
                'stats': user_data['daily_stats'],
                'total_earned': user_data['total_earned']
            }
            await update.message.reply_text(
                f"📊 Your data:\n\n"
                f"Balance: {response['balance']} coins\n"
                f"Ads watched: {response['stats']['ads_watched']}\n"
                f"Tasks completed: {response['stats']['tasks_completed']}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")

# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "watch_ad":
        await show_ad(update, context)
    elif data == "confirm_ad":
        await confirm_ad(update, context)
    elif data == "micro_tasks":
        await show_micro_tasks(update, context)
    elif data == "invite_friends":
        await show_invite_page(update, context)
    elif data == "my_balance":
        await show_balance(update, context)
    elif data == "my_stats":
        await show_stats(update, context)
    elif data == "back":
        await query.edit_message_text(
            "Main menu:",
            reply_markup=main_menu()
        )
    elif data.startswith("task_"):
        task_id = int(data.split("_")[1])
        await handle_task(update, context, task_id)
    elif data == "copy_link":
        await query.answer("Link is displayed above. Please copy manually.", show_alert=True)
    elif data == "share_link":
        await query.answer("Share the link displayed above with your friends.", show_alert=True)

# Admin commands
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != Config.ADMIN_ID:
        await update.message.reply_text("⛔ Access denied.")
        return
    
    commands = """
👑 Admin Commands:

/addcoins [user_id] [amount] - Add coins to user
/removecoins [user_id] [amount] - Remove coins from user
/setcoins [user_id] [amount] - Set user coins
/userinfo [user_id] - Get user info
/broadcast [message] - Broadcast message to all users
/stats - Get bot statistics
"""
    
    await update.message.reply_text(commands, parse_mode='Markdown')

# Main function
def main():
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    
    # Start bot
    print(f"🤖 {Config.BOT_NAME} Bot started successfully...")
    print(f"📞 Bot username: @{application.bot.username}")
    print(f"🔄 Listening for messages...")
    print(f"📊 Database file: {Config.DB_FILE}")
    
    application.run_polling()

if __name__ == "__main__":
    main()