from telegram import Bot
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import requests
import time
import base58

TELEGRAM_BOT_TOKEN = "7905471312:AAHjxF0ano4xCLGoBT_3GgyoAvAD-H-Tweg"
RPC_URL = "https://api.mainnet-beta.solana.com"
user_wallets = {}

bot = Bot(TELEGRAM_BOT_TOKEN)

ADDING_WALLET, REMOVING_WALLET = range(2)

def get_wallet_transactions(wallet_address):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getConfirmedSignaturesForAddress2",
        "params": [wallet_address, {"limit": 10}]
    }
    try:
        response = requests.post(RPC_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("result", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transactions for {wallet_address}: {e}")
    return []

def is_valid_solana_address(address):
    try:
        decoded = base58.b58decode(address)
        return len(decoded) == 32
    except Exception:
        return False

def track_wallets():
    while True:
        for user_id, wallets in user_wallets.items():
            for wallet in wallets:
                transactions = get_wallet_transactions(wallet)
                if transactions:
                    message = f"Wallet {wallet} has new transactions:\n"
                    for tx in transactions[:3]:
                        message += f"➡️ Tx: {tx['signature']}\n"
                    try:
                        bot.send_message(chat_id=user_id, text=message)
                    except Exception as e:
                        print(f"Error sending message for wallet {wallet}: {e}")
        time.sleep(60)

def start(update, context):
    update.message.reply_text(
        """
        Welcome to the Solana Wallet Tracker Bot!
        I can help you track transactions on your favorite meme coin wallets on the Solana blockchain and notify you of new transactions directly on Telegram.

        Available Commands:
        1. /start - Welcome message
        2. /show - View currently tracked wallets
        3. /add_wallet - Add a new wallet to track
        4. /remove_wallet - Remove a wallet from tracking
        5. /help - Learn about all available commands
        """
    )

def show(update, context):
    user_id = update.message.chat_id
    wallets = user_wallets.get(user_id, [])
    if wallets:
        update.message.reply_text("\n".join(wallets))
    else:
        update.message.reply_text("There are no wallets being tracked currently.")

def add_wallet(update, context):
    update.message.reply_text("Enter wallet address you want to add:")
    return ADDING_WALLET

def handle_add_wallet(update, context):
    user_id = update.message.chat_id
    wallet_address = update.message.text
    if update.message.text.startswith('/'):
        add_wallet(update, context)
        return ConversationHandler.END
    else:
        if is_valid_solana_address(wallet_address):
            if user_id not in user_wallets:
                user_wallets[user_id] = []
            user_wallets[user_id].append(wallet_address)
            update.message.reply_text(f"Wallet {wallet_address} has been added to your tracking list.")
        else:
            update.message.reply_text(f"Invalid Solana wallet address: {wallet_address}")
        return ConversationHandler.END

def remove_wallet(update, context):
    user_id = update.message.chat_id
    if user_id in user_wallets and user_wallets[user_id]:
        update.message.reply_text("Enter wallet address you want to remove:")
        return REMOVING_WALLET
    else:
        update.message.reply_text("There are no wallets being tracked currently.")
        return ConversationHandler.END

def handle_remove_wallet(update, context):
    user_id = update.message.chat_id
    wallet_address = update.message.text
    if user_id in user_wallets and wallet_address in user_wallets[user_id]:
        user_wallets[user_id].remove(wallet_address)
        update.message.reply_text(f"Wallet {wallet_address} has been removed from your tracking list.")
    else:
        update.message.reply_text(f"Wallet {wallet_address} is not in your tracking list.")
    return ConversationHandler.END

def help_command(update, context):
    update.message.reply_text("""
    Available Commands:
    1. /start - Welcome message
    2. /show - View currently tracked wallets
    3. /add_wallet - Add a new wallet to track
    4. /remove_wallet - Remove a wallet from tracking
    5. /help - Learn about all available commands
    """)

updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)

show_handler = CommandHandler("show", show)
dispatcher.add_handler(show_handler)

help_handler = CommandHandler("help", help_command)
dispatcher.add_handler(help_handler)

add_wallet_handler = ConversationHandler(
    entry_points=[CommandHandler('add_wallet', add_wallet)],
    states={
        ADDING_WALLET: [MessageHandler(Filters.text | Filters.command, handle_add_wallet)]
    },
    fallbacks=[],
)
dispatcher.add_handler(add_wallet_handler)

remove_wallet_handler = ConversationHandler(
    entry_points=[CommandHandler('remove_wallet', remove_wallet)],
    states={
        REMOVING_WALLET: [MessageHandler(Filters.text & ~Filters.command, handle_remove_wallet)]
    },
    fallbacks=[],
)
dispatcher.add_handler(remove_wallet_handler)

updater.start_polling()

track_wallets()
