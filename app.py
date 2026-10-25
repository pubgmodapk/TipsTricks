import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Configuration & Links
TOKEN = "8306748863:AAFBJdo9BWZX_We65MJ8tR5CCvlwhRBydF0"
ADMIN_ID = 8542717243
REQUIRED_CHANNEL = "@Helpingzonetime"
PROXY_SHOP_BOT_LINK = "https://t.me/TipsTricks_Proxysaller_bot"

# Data storage variables
deposit_codes = []  
total_added_count = 0  
claimed_count = 0      
all_users = set()      
already_referred_users = set()  
user_referral_counts = {}       
user_claimable_rewards = {}     
user_last_claim_time = {}       

# Main Menu Markup Helper
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Get Free Deposit Code", callback_data="get_code")],
        [InlineKeyboardButton("👥 My Invite Link", callback_data="my_link")]
    ])

# 1. Start Command & Force Join Check
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global claimed_count
    user = update.effective_user
    user_id = user.id
    all_users.add(user_id)  

    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id and user_id not in already_referred_users:
                already_referred_users.add(user_id)  
                user_referral_counts[referrer_id] = user_referral_counts.get(referrer_id, 0) + 1
                
                if user_referral_counts[referrer_id] % 5 == 0:
                    user_claimable_rewards[referrer_id] = user_claimable_rewards.get(referrer_id, 0) + 1
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text="🎉 Congratulations! You have successfully completed 5 referrals. Go to 'My Invite Link' to claim your free deposit code!"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass

    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ['left', 'kicked']:
            raise Exception("Not joined")
    except Exception:
        keyboard = [
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ I Have Joined (Verify)", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ You must join our channel first to use this bot!",
            reply_markup=reply_markup
        )
        return

    welcome_text = f"Welcome, {user.first_name}!\nChoose an option below to get codes or invite friends."
    if user_id == ADMIN_ID:
        welcome_text += "\n\n🔑 You are the Admin! Send `/admin` to open the control panel."

    await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard())

# Admin Control Panel (/admin)
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    remaining_codes = len(deposit_codes)
    total_users_count = len(all_users)

    panel_text = (
        f"🛠 Admin Control Panel:\n\n"
        f"👥 Total Users Joined: {total_users_count}\n"
        f"📦 Total Codes Added: {total_added_count}\n"
        f"✅ Codes Claimed: {claimed_count}\n"
        f"🔹 Codes Remaining: {remaining_codes}\n\n"
        f"➕ Admin Commands:\n"
        f"• Add Codes: /addcodes CODE1, CODE2, CODE3\n"
        f"• Broadcast: /broadcast Your message here\n"
        f"• Clear Codes: /clear (Clear all remaining codes)"
    )
    await update.message.reply_text(panel_text)

# Add Codes Command
async def add_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_added_count
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    
    text = update.message.text.replace("/addcodes", "").strip()
    if not text:
        await update.message.reply_text("⚠️ Please provide codes. Example:\n/addcodes CODE1, CODE2, CODE3")
        return
    
    new_ones = [c.strip() for c in text.split(",")]
    deposit_codes.extend(new_ones)
    total_added_count += len(new_ones)
    
    await update.message.reply_text(f"✅ Successfully added {len(new_ones)} new codes. Total remaining: {len(deposit_codes)}")

# Clear Codes Command
async def clear_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    
    global deposit_codes
    deposit_codes.clear()
    await update.message.reply_text("🗑 All remaining deposit codes have been cleared successfully.")

# Broadcast Command for Admin
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    
    message_text = update.message.text.replace("/broadcast", "").strip()
    if not message_text:
        await update.message.reply_text("⚠️ Please provide a message to broadcast. Example:\n/broadcast Hello users, new codes added!")
        return

    success_count = 0
    for uid in all_users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Announcement:\n\n{message_text}")
            success_count += 1
        except Exception:
            pass
    
    await update.message.reply_text(f"✅ Broadcast sent successfully to {success_count} users.")

# Button and Action Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global claimed_count
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check_join":
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            if member.status in ['left', 'kicked']:
                await query.edit_message_text("❌ You have not joined the channel yet. Please join first.")
                return
        except Exception:
            await query.edit_message_text("❌ Verification failed. Please join the channel.")
            return

        await query.edit_message_text("Thank you! Now you can use the bot:", reply_markup=get_main_menu_keyboard())

    elif query.data == "main_menu":
        await query.edit_message_text("Main Menu:", reply_markup=get_main_menu_keyboard())

    elif query.data == "get_code":
        now = datetime.now()
        if user_id in user_last_claim_time:
            elapsed_time = now - user_last_claim_time[user_id]
            cooldown_period = timedelta(hours=48)
            
            if elapsed_time < cooldown_period:
                remaining_time = cooldown_period - elapsed_time
                hours = int(remaining_time.total_seconds() // 3600)
                minutes = int((remaining_time.total_seconds() % 3600) // 60)
                
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]])
                await query.edit_message_text(
                    f"⏳ You have already received a deposit code.\n"
                    f"Your next deposit code will be available in {hours} hours and {minutes} minutes.",
                    reply_markup=keyboard
                )
                return

        if not deposit_codes:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]])
            await query.edit_message_text("😔 Sorry, no deposit codes are available right now. Please check back later.", reply_markup=keyboard)
            return
        
        code = deposit_codes.pop(0)
        user_last_claim_time[user_id] = now  
        claimed_count += 1
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]])
        await query.edit_message_text(
            f"✅ Your deposit code is: {code}\n\n"
            f"📌 Note: This code is only valid for this proxy shop bot:\n{PROXY_SHOP_BOT_LINK}",
            reply_markup=keyboard
        )

    elif query.data == "my_link":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        refs_count = user_referral_counts.get(user_id, 0)
        remainder = refs_count % 5
        needed = 5 - remainder if remainder != 0 else 0
        claimable = user_claimable_rewards.get(user_id, 0)
        
        keyboard_buttons = []
        if claimable > 0:
            keyboard_buttons.append([InlineKeyboardButton("🎁 Claim Free Deposit Code (Reward)", callback_data="claim_ref_code")])
        keyboard_buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard_buttons)
        
        await query.edit_message_text(
            f"🔗 Your Referral Link:\n{ref_link}\n\n"
            f"👥 Total Successful Referrals: {refs_count}\n"
            f"📊 Progress to next reward: {remainder}/5 ({needed} more needed)\n"
            f"🎁 Claimable Rewards: {claimable}",
            reply_markup=reply_markup
        )

    elif query.data == "claim_ref_code":
        claimable = user_claimable_rewards.get(user_id, 0)
        if claimable <= 0:
            await query.answer("You don't have any claimable rewards right now!", show_alert=True)
            return
        
        if not deposit_codes:
            await query.answer("Sorry, no deposit codes available right now. Please check back later!", show_alert=True)
            return
        
        code = deposit_codes.pop(0)
        user_claimable_rewards[user_id] -= 1  
        claimed_count += 1
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]])
        await query.edit_message_text(
            f"✅ Here is your referral reward deposit code: {code}\n\n"
            f"📌 Note: This code is only valid for this proxy shop bot:\n{PROXY_SHOP_BOT_LINK}",
            reply_markup=keyboard
        )

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("addcodes", add_codes))
    application.add_handler(CommandHandler("clear", clear_codes))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is starting successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
