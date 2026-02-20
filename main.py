"""
Telegram Bot with Category Management
Allows users to add and view data in different categories
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_TEXT = 1
WAITING_FOR_CATEGORY_NAME = 2

# Categories - now dynamic, can be modified by users
CATEGORIES = [
    "Punching Bins",
    "Punching Methods",
    "Enroll Bins",
    "Enroll Methods",
    "Logs"
]

# Store custom categories per user: {user_id: [custom_categories]}
user_custom_categories = {}

# Admin configuration - Replace with your Telegram user ID
ADMIN_USER_ID = 8167085780  # Replace with your actual Telegram user ID

# To find your user ID:
# 1. Send a message to your bot
# 2. Check the logs - your user ID will be shown
# 3. Or use @userinfobot on Telegram to get your ID

# Store user info for admin panel: {user_id: {'first_name': str, 'username': str}}
user_info = {}

# In-memory storage: {user_id: {category: [entries]}}
user_data_storage = {}


def get_main_keyboard(user_id=None):
    """Create main menu keyboard with Add, View, Delete, Add Category, and Admin buttons"""
    keyboard = [
        [
            InlineKeyboardButton("Add", callback_data="main_add"),
            InlineKeyboardButton("View", callback_data="main_view")
        ],
        [
            InlineKeyboardButton("Delete", callback_data="main_delete"),
            InlineKeyboardButton("Add Category", callback_data="main_add_category")
        ]
    ]
    
    # Add admin button only for admin user
    if user_id == ADMIN_USER_ID:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)


def get_category_keyboard(action, user_id=None):
    """Create category selection keyboard with default + custom categories"""
    keyboard = []
    
    # Add default categories
    for category in CATEGORIES:
        callback_data = f"{action}_{category}"
        keyboard.append([InlineKeyboardButton(category, callback_data=callback_data)])
    
    # Add user's custom categories if any
    if user_id and user_id in user_custom_categories:
        for category in user_custom_categories[user_id]:
            callback_data = f"{action}_{category}"
            keyboard.append([InlineKeyboardButton(f"📁 {category}", callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("« Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    # Store user info for admin panel
    user_info[user_id] = {
        'first_name': user.first_name or 'Unknown',
        'username': user.username or 'No username'
    }
    
    await update.message.reply_text(
        f"Hello {user.first_name}! 👋\n\n"
        "Welcome to the Category Manager Bot.\n"
        "Choose an option:",
        reply_markup=get_main_keyboard(user_id)
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "main_add":
        await query.edit_message_text(
            "Select a category to add data:",
            reply_markup=get_category_keyboard("add", user_id)
        )
    
    elif data == "main_view":
        await query.edit_message_text(
            "Select a category to view data:",
            reply_markup=get_category_keyboard("view", user_id)
        )
    
    elif data == "main_delete":
        await query.edit_message_text(
            "Select a category to delete data from:",
            reply_markup=get_category_keyboard("delete", user_id)
        )
    
    elif data == "main_add_category":
        context.user_data['action'] = 'add_category'
        await query.edit_message_text(
            "📁 *Add New Category*\n\n"
            "Send me the name for your new category.\n\n"
            "Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_CATEGORY_NAME
    
    elif data == "back_to_main":
        await query.edit_message_text(
            "Choose an option:",
            reply_markup=get_main_keyboard(user_id)
        )
    
    elif data == "admin_panel":
        if user_id != ADMIN_USER_ID:
            await query.answer("❌ Access denied!", show_alert=True)
            return
        
        await show_admin_panel(query)


async def add_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add category selection"""
    query = update.callback_query
    await query.answer()
    
    category = query.data[4:]  # Remove "add_" prefix
    context.user_data['action'] = 'add'
    context.user_data['category'] = category
    
    await query.edit_message_text(
        f"📝 Send me the text you want to save in:\n*{category}*\n\n"
        "Type /cancel to cancel.",
        parse_mode='Markdown'
    )
    return WAITING_FOR_TEXT


async def view_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle view category selection"""
    query = update.callback_query
    await query.answer()
    
    category = query.data[5:]  # Remove "view_" prefix
    user_id = query.from_user.id
    
    # Get user's data for this category
    entries = user_data_storage.get(user_id, {}).get(category, [])
    
    if entries:
        message = f"📋 *{category}*\n\n"
        for idx, entry in enumerate(entries, 1):
            message += f"{idx}. {entry}\n\n"  # Added extra newline for better spacing
    else:
        message = "No data found."
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Back", callback_data="main_view")
        ]])
    )


async def delete_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete category selection"""
    query = update.callback_query
    await query.answer()
    
    category = query.data[7:]  # Remove "delete_" prefix
    user_id = query.from_user.id
    
    # Get user's data for this category
    entries = user_data_storage.get(user_id, {}).get(category, [])
    
    if not entries:
        await query.edit_message_text(
            "No data found to delete.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="main_delete")
            ]])
        )
        return
    
    # Create buttons for each entry
    keyboard = []
    for idx, entry in enumerate(entries):
        # Truncate long entries for button display
        display_text = entry[:40] + "..." if len(entry) > 40 else entry
        callback_data = f"delitem_{category}_{idx}"
        keyboard.append([InlineKeyboardButton(f"{idx + 1}. {display_text}", callback_data=callback_data)])
    
    # Add "Delete All" and "Back" buttons
    keyboard.append([InlineKeyboardButton("🗑️ Delete All", callback_data=f"delall_{category}")])
    keyboard.append([InlineKeyboardButton("« Back", callback_data="main_delete")])
    
    await query.edit_message_text(
        f"🗑️ *Delete from {category}*\n\nSelect an item to delete:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle individual item deletion"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: delitem_Category_index
    parts = query.data.split("_", 2)
    category = parts[1]
    item_index = int(parts[2])
    user_id = query.from_user.id
    
    # Delete the item
    if user_id in user_data_storage and category in user_data_storage[user_id]:
        if 0 <= item_index < len(user_data_storage[user_id][category]):
            deleted_item = user_data_storage[user_id][category].pop(item_index)
            
            await query.edit_message_text(
                f"✅ Deleted successfully from *{category}*:\n\n{deleted_item}",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Back to Delete", callback_data="main_delete"),
                    InlineKeyboardButton("« Main Menu", callback_data="back_to_main")
                ]])
            )
        else:
            await query.edit_message_text(
                "❌ Item not found.",
                reply_markup=get_main_keyboard(user_id)
            )
    else:
        await query.edit_message_text(
            "❌ Item not found.",
            reply_markup=get_main_keyboard(user_id)
        )


async def show_admin_panel(query):
    """Show admin panel with list of users"""
    if not user_data_storage and not user_info:
        await query.edit_message_text(
            "👑 *Admin Panel*\n\nNo users found.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="back_to_main")
            ]])
        )
        return
    
    # Get all users who have interacted with the bot
    all_users = set(user_info.keys()) | set(user_data_storage.keys())
    
    keyboard = []
    for user_id in all_users:
        user_name = user_info.get(user_id, {}).get('first_name', f'User {user_id}')
        username = user_info.get(user_id, {}).get('username', 'No username')
        
        # Count total items for this user
        total_items = 0
        if user_id in user_data_storage:
            for category_items in user_data_storage[user_id].values():
                total_items += len(category_items)
        
        button_text = f"{user_name} (@{username}) - {total_items} items"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_user_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("« Back", callback_data="back_to_main")])
    
    await query.edit_message_text(
        "👑 *Admin Panel*\n\nSelect a user to view their data:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_user_data(query, target_user_id):
    """Show specific user's data"""
    target_user_id = int(target_user_id)
    user_name = user_info.get(target_user_id, {}).get('first_name', f'User {target_user_id}')
    username = user_info.get(target_user_id, {}).get('username', 'No username')
    
    if target_user_id not in user_data_storage or not user_data_storage[target_user_id]:
        await query.edit_message_text(
            f"👤 *{user_name}* (@{username})\n\nNo data found for this user.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to Users", callback_data="admin_panel")
            ]])
        )
        return
    
    # Create buttons for each category this user has data in
    keyboard = []
    for category, items in user_data_storage[target_user_id].items():
        if items:  # Only show categories with data
            button_text = f"{category} ({len(items)} items)"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_view_{target_user_id}_{category}")])
    
    # Add custom categories if any
    if target_user_id in user_custom_categories:
        custom_cats = user_custom_categories[target_user_id]
        if custom_cats:
            keyboard.append([InlineKeyboardButton("📁 Custom Categories", callback_data=f"admin_custom_{target_user_id}")])
    
    keyboard.append([InlineKeyboardButton("« Back to Users", callback_data="admin_panel")])
    
    await query.edit_message_text(
        f"👤 *{user_name}* (@{username})\n\nSelect a category to view:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_user_category_data(query, target_user_id, category):
    """Show specific user's data in a specific category"""
    target_user_id = int(target_user_id)
    user_name = user_info.get(target_user_id, {}).get('first_name', f'User {target_user_id}')
    
    entries = user_data_storage.get(target_user_id, {}).get(category, [])
    
    if entries:
        message = f"👤 *{user_name}*\n📋 *{category}*\n\n"
        for idx, entry in enumerate(entries, 1):
            message += f"{idx}. {entry}\n\n"
    else:
        message = f"👤 *{user_name}*\n📋 *{category}*\n\nNo data found."
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Back to User", callback_data=f"admin_user_{target_user_id}")
        ]])
    )


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin-specific callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # Check admin access
    if user_id != ADMIN_USER_ID:
        await query.answer("❌ Access denied!", show_alert=True)
        return
    
    if data == "admin_panel":
        await show_admin_panel(query)
    
    elif data.startswith("admin_user_"):
        target_user_id = data[11:]  # Remove "admin_user_" prefix
        await show_user_data(query, target_user_id)
    
    elif data.startswith("admin_view_"):
        # Parse: admin_view_userid_category
        parts = data[11:].split("_", 1)  # Remove "admin_view_" and split once
        target_user_id = parts[0]
        category = parts[1]
        await show_user_category_data(query, target_user_id, category)
    
    elif data.startswith("admin_custom_"):
        target_user_id = int(data[13:])  # Remove "admin_custom_" prefix
        user_name = user_info.get(target_user_id, {}).get('first_name', f'User {target_user_id}')
        custom_cats = user_custom_categories.get(target_user_id, [])
        
        if custom_cats:
            message = f"👤 *{user_name}*\n📁 *Custom Categories:*\n\n"
            for idx, cat in enumerate(custom_cats, 1):
                message += f"{idx}. {cat}\n"
        else:
            message = f"👤 *{user_name}*\n\nNo custom categories."
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to User", callback_data=f"admin_user_{target_user_id}")
            ]])
        )
    """Handle delete all items in a category"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: delall_Category
    category = query.data[7:]  # Remove "delall_" prefix
    user_id = query.from_user.id
    
    # Delete all items in the category
    if user_id in user_data_storage and category in user_data_storage[user_id]:
        count = len(user_data_storage[user_id][category])
        user_data_storage[user_id][category] = []
        
        await query.edit_message_text(
            f"✅ Deleted all {count} item(s) from *{category}*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to Delete", callback_data="main_delete"),
                InlineKeyboardButton("« Main Menu", callback_data="back_to_main")
            ]])
        )
    else:
        await query.edit_message_text(
            "❌ No data found.",
            reply_markup=get_main_keyboard(user_id)
        )


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input from user"""
    user_id = update.effective_user.id
    text = update.message.text
    
    action = context.user_data.get('action')
    
    if action == 'add_category':
        # Adding a new category
        if user_id not in user_custom_categories:
            user_custom_categories[user_id] = []
        
        # Check if category already exists
        all_categories = CATEGORIES + user_custom_categories[user_id]
        if text in all_categories:
            await update.message.reply_text(
                f"❌ Category '{text}' already exists!",
                reply_markup=get_main_keyboard(user_id)
            )
        else:
            user_custom_categories[user_id].append(text)
            await update.message.reply_text(
                f"✅ New category '*{text}*' added successfully!",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard(user_id)
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    elif action == 'add':
        # Adding data to a category
        category = context.user_data.get('category')
        
        # Initialize user storage if not exists
        if user_id not in user_data_storage:
            user_data_storage[user_id] = {}
        
        # Initialize category list if not exists
        if category not in user_data_storage[user_id]:
            user_data_storage[user_id][category] = []
        
        # Save the text
        user_data_storage[user_id][category].append(text)
        
        await update.message.reply_text(
            f"✅ Saved successfully in *{category}*",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(user_id)
        )
        
        context.user_data.clear()
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    user_id = update.effective_user.id
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Cancelled.",
        reply_markup=get_main_keyboard(user_id)
    )
    return ConversationHandler.END


async def delete_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete all items in a category"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: delall_Category
    category = query.data[7:]  # Remove "delall_" prefix
    user_id = query.from_user.id
    
    # Delete all items in the category
    if user_id in user_data_storage and category in user_data_storage[user_id]:
        count = len(user_data_storage[user_id][category])
        user_data_storage[user_id][category] = []
        
        await query.edit_message_text(
            f"✅ Deleted all {count} item(s) from *{category}*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to Delete", callback_data="main_delete"),
                InlineKeyboardButton("« Main Menu", callback_data="back_to_main")
            ]])
        )
    else:
        user_id = query.from_user.id
        await query.edit_message_text(
            "❌ No data found.",
            reply_markup=get_main_keyboard(user_id)
        )


def main():
    """Start the bot"""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    TOKEN = "8449356059:AAEwGyZW6J5ODmmfj9tYg8G8tYgnk6eItRY"
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler for adding data and categories
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_category_callback, pattern="^add_"),
            CallbackQueryHandler(main_menu_callback, pattern="^main_add_category$")
        ],
        states={
            WAITING_FOR_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)
            ],
            WAITING_FOR_CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
        per_message=False,
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(delete_item_callback, pattern="^delitem_"))
    application.add_handler(CallbackQueryHandler(delete_all_callback, pattern="^delall_"))
    application.add_handler(CallbackQueryHandler(delete_category_callback, pattern="^delete_"))
    application.add_handler(CallbackQueryHandler(view_category_callback, pattern="^view_"))
    application.add_handler(CallbackQueryHandler(main_menu_callback))
    
    # Start the bot
    logger.info("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
