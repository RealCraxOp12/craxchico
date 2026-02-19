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

# Categories
CATEGORIES = [
    "Punching Bins",
    "Punching Methods",
    "Enroll Bins",
    "Enroll Methods",
    "Logs"
]

# In-memory storage: {user_id: {category: [entries]}}
user_data_storage = {}


def get_main_keyboard():
    """Create main menu keyboard with Add, View, and Delete buttons"""
    keyboard = [
        [
            InlineKeyboardButton("Add", callback_data="main_add"),
            InlineKeyboardButton("View", callback_data="main_view")
        ],
        [
            InlineKeyboardButton("Delete", callback_data="main_delete")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_category_keyboard(action):
    """Create category selection keyboard"""
    keyboard = []
    for category in CATEGORIES:
        callback_data = f"{action}_{category}"
        keyboard.append([InlineKeyboardButton(category, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("« Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"Hello {user.first_name}! 👋\n\n"
        "Welcome to the Category Manager Bot.\n"
        "Choose an option:",
        reply_markup=get_main_keyboard()
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "main_add":
        await query.edit_message_text(
            "Select a category to add data:",
            reply_markup=get_category_keyboard("add")
        )
    
    elif data == "main_view":
        await query.edit_message_text(
            "Select a category to view data:",
            reply_markup=get_category_keyboard("view")
        )
    
    elif data == "main_delete":
        await query.edit_message_text(
            "Select a category to delete data from:",
            reply_markup=get_category_keyboard("delete")
        )
    
    elif data == "back_to_main":
        await query.edit_message_text(
            "Choose an option:",
            reply_markup=get_main_keyboard()
        )


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
            message += f"{idx}. {entry}\n"
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
                reply_markup=get_main_keyboard()
            )
    else:
        await query.edit_message_text(
            "❌ Item not found.",
            reply_markup=get_main_keyboard()
        )


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
        await query.edit_message_text(
            "❌ No data found.",
            reply_markup=get_main_keyboard()
        )


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input from user"""
    user_id = update.effective_user.id
    text = update.message.text
    
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
        reply_markup=get_main_keyboard()
    )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Cancelled.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END


def main():
    """Start the bot"""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    TOKEN = "8449356059:AAEwGyZW6J5ODmmfj9tYg8G8tYgnk6eItRY"
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler for adding data
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_category_callback, pattern="^add_")],
        states={
            WAITING_FOR_TEXT: [
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
