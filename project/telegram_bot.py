import logging

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ParseMode, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, Filters, MessageHandler, Updater)

from project.telegram_api_key import TELEGRAM_KEY
from project.telegram_response import TelegramResponse


LISTENING = 0
AWAITING_LOCATION = 1
AWAITING_ADDRESS = 2
AWAITING_ADDRESS_CONFIRMATION = 3
AWAITING_PREFERENCE = 4
AWAITING_PREFERENCE_TIME = 5

#  Setup logging for the bot
logging.basicConfig(format='%(asctime)s - %(name)s - %(message)s', level=logging.INFO)

updater = Updater(token=TELEGRAM_KEY, use_context=True)
dp = updater.dispatcher


def log_command(update: Update, context: CallbackContext) -> None:
    """
    Shortcut for logging info, because laziness.

    Args:
        update (:class:'telegram.Update'): the Update instance passed from the Handler.
        context (:class:'telegram.ext.CallbackContext'): the CallbackContext instance passed from the Handler.

    Returns:
        None
    """
    logging.info("User (%s): {%s} (args=%s)", update.message.from_user.id, update.message.text, context.args)


def clear_user_data(context: CallbackContext, include_constat=False) -> None:
    """
    Clear the user data from the context.user_data dict. To be used after the user has completed a change.

    Args:
        context (:class:'telegram.ext.CallbackContext'): the CallbackContext instance passed from the Handler
        include_constat (:obj:'bool'): whether to clear the conversation_status from user_data or not. Mainly to be used
            for debugging purposes.
    """
    keys_to_remove: list[str] = []
    for key in context.user_data.keys():
        if key == "conversation_status" and not include_constat:
            continue
        keys_to_remove.append(key)
    _ = [context.user_data.pop(key, None) for key in keys_to_remove]


def check_for_reset(user_id: str, context: CallbackContext) -> bool:
    """
    Checks if the user was busy with a command and switched to a different one before finishing

    Args:
        user_id (:obj:'str'): the telegram_id of the user. Can be retrieved using Update.Message.from_user
        context (:class:'telegram.ext.CallbackContext'): should the same CallbackContext
        as passed in the parent function.
    """
    conversation_status = context.user_data.get("conversation_status", LISTENING)

    if conversation_status != LISTENING:
        logging.warning("User (%s) reset conversation!", user_id)
        clear_user_data(context)
        conversation_status = LISTENING
        context.user_data["conversation_status"] = conversation_status
        return True
    return False


def check_fist_text(update: Update, context: CallbackContext) -> bool:
    """
    Check if the user has a 'conversation_status', meaning they've used the bot before.

    Args:
        update (:class:'telegram.Update'): should be the same Update as passed into the parent function.
        context (:class:'telegram.ext.CallbackContext'): should be the same CallbackContext
            as passed in parent function.
    """
    if "conversation_status" not in context.user_data:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Greetings, I see this is your first time!")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please use /start to start")
        context.user_data["conversation_status"] = LISTENING
        return True
    return False


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates the keyboard which requests user location or user address on reply.

    Returns:
        telegram.ReplyKeyboardMarkup: instructions on how to build the keyboard replacement with buttons.
    """
    buttons = [[KeyboardButton("Yes, I'm at home", request_location=True)], [KeyboardButton("No, I'm not at home")]]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    return keyboard


def get_preference_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a keyboard with all of the travel preferences the user can reply.

    Returns:
        telegram.ReplyKeyboardMarkup: similar instructions to get_location_keyboard() with different buttons texts.
    """
    buttons = [[KeyboardButton("Bicycling")], [KeyboardButton("Walking")]]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    return keyboard


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Creates buttons the user can use to confirm if the address is correct.

    Returns:
        telegram.InlineKeyboardMarkup: instructions on how to build the buttons under a specific text.
    """
    buttons = [
        [
            InlineKeyboardButton("Yes", callback_data="confirm"),
            InlineKeyboardButton("No", callback_data="retry"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    return keyboard


def send_message_without_context(user_id: str | int, msg: str, parse_mode=None) -> None:
    """
    This function allows a message to be sent to a user from anywhere within Tripper.
    To be used for when the authorization fails or expires to notify the user they should reauthorize.

    Args:
        user_id (:obj:'str'): the telegram_id of the user (can be retrieved using Update.Message.from_user)
        msg (:obj:'str'): the message the bot should send to the user. In case parse_mode is not None, this should be
            formatted according to the parse mode selected (either HTML or Markdown V2).
        parse_mode (:obj:'str'): the parsing for the message. Should be passed as a string of either 'HTML' or 'MD'.
    """
    parser = None
    if parse_mode == "HTML":
        parser = ParseMode.HTML
    elif parse_mode == "MD":
        parser = ParseMode.MARKDOWN_V2
    updater.bot.send_message(chat_id=str(user_id), text=str(msg), parse_mode=parser)


def tgc_help(update: Update, context: CallbackContext) -> None:
    """
    Sends a text to the user with all the available commands.

    Args:
        update (:class:'Update'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher.
        context (:class:'CallbackContext'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher. Contains the user unique user_data.
    """
    user_id = update.message.from_user.id
    print(update.message.chat_id)
    check_for_reset(str(user_id), context)
    log_command(update, context)
    update.message.reply_text("Here is a list of commands:", reply_markup=ReplyKeyboardRemove())
    reply = ""
    for command in commands:
        reply += f"/{command}\n"
    update.message.reply_text(reply)


def tgc_authorize_user(update: Update, context: CallbackContext) -> None:
    """
    Creates a TelegramResponse object associating the user's id with their token for Google.

    Args:
        update (:class:'Update'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher
        context (:class:'CallbackContext'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher. Contains the user unique user_data.
    """
    user_id = update.message.from_user.id
    check_for_reset(str(user_id), context)
    log_command(update, context)

    update.message.reply_text("An authorization windows has opened on the host machine")
    update.message.reply_text("In case the window got closed check the stdout of the program for the link")

    response = TelegramResponse(TelegramResponse.AUTHORIZE, user_id, "")
    response.handle_request()

    update.message.reply_text(f"Authenticated, your TelegramID is {user_id}. \
                                Please update your home and prefs before continuing if you haven't!")


def tgc_change_home(update: Update, context: CallbackContext) -> None:
    """
    First step of changing the home address. Prompt the user if they are at home.

    Args:
    update (:class:'Update'): passed in automatically in the telegram.ext.Handler when handler gets added
        to the dispatcher
    context (:class:'CallbackContext'): passed in automatically in the telegram.ext.Handler when handler gets added
        to the dispatcher. Contains the user unique user_data.
    """
    log_command(update, context)
    user_id = update.message.from_user.id
    check_for_reset(str(user_id), context)

    context.bot.send_message(chat_id=update.effective_chat.id, text="Are you at home?",
                             reply_markup=get_location_keyboard())
    context.user_data["conversation_status"] = AWAITING_LOCATION


def tgc_change_preference(update: Update, context: CallbackContext) -> None:
    """
    First step of changing the user's preferred method of travel.

    Args:
        update (:class:'Update'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher.
        context (:class:'CallbackContext'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher. Contains the user unique user_data.
    """
    log_command(update, context)
    user_id = update.message.from_user.id
    check_for_reset(str(user_id), context)
    args = context.args

    if args:
        if "cycling" in args[0].lower() or args[0].lower() == "biking":
            update.message.reply_text("How far would you be happy cycling for?")
            context.user_data["conversation_status"] = AWAITING_PREFERENCE_TIME
            context.user_data["preference_to_change"] = "biking"
        elif args[0].lower() == "walking":
            update.message.reply_text("How far would you be happy walking for?")
            context.user_data["conversation_status"] = AWAITING_PREFERENCE_TIME
            context.user_data["preference_to_change"] = "walking"
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Which preference would you like to change?",
                                 reply_markup=get_preference_keyboard())
        context.user_data["conversation_status"] = AWAITING_PREFERENCE


def handle_user_location(update: Update, context: CallbackContext) -> None:
    """
    Checks if the user location received is the home location and creates a response with said location.

    Args:
        update (:class:'Update'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher.
        context (:class:'CallbackContext'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher. Contains the user unique user_data.
    """
    if check_fist_text(update, context):
        return
    conversation_status = context.user_data["conversation_status"]
    logging.info("User (%s) sent location", update.message.from_user.id)
    if conversation_status != AWAITING_LOCATION:
        logging.warning("The location sent was not on request!")
        update.message.reply_text("Message out of context, see '/help' for commands",
                                  reply_markup=ReplyKeyboardRemove())
        return
    context.user_data["conversation_status"] = LISTENING
    user_id = update.message.from_user.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    payload = f"{latitude}, {longitude}"
    response = TelegramResponse(TelegramResponse.CHANGE_HOME, user_id, payload)
    response.handle_request()
    logging.info(response)
    update.message.reply_text("Home address updated successfully!", reply_markup=ReplyKeyboardRemove())


def handle_user_texts(update: Update, context: CallbackContext):
    """
    Handle any user texts according to the progression in the conversation. The progression is recorded in
    CallbackContext.user_data as 'conversation_status'.

    Args:
        update (:class:'Update'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher.
        context (:class:'CallbackContext'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher. Contains the user unique user_data.
    """
    if check_fist_text(update, context):
        return
    conversation_status = context.user_data["conversation_status"]
    log_command(update, context)
    user_id = update.message.from_user.id

    if update.message.text == "No, I'm not at home" and conversation_status == AWAITING_LOCATION:
        update.message.reply_text("Please send your address.", reply_markup=ReplyKeyboardRemove())
        context.user_data["conversation_status"] = AWAITING_ADDRESS
        return
    if conversation_status == AWAITING_ADDRESS:
        address = update.message.text
        context.user_data["address"] = address
        update.message.reply_text("Is this the correct address?", reply_markup=get_confirmation_keyboard())
        context.user_data["conversation_status"] = AWAITING_ADDRESS_CONFIRMATION
        logging.info("Awaiting confirmation...")
        return

    if conversation_status == AWAITING_PREFERENCE:
        if update.message.text == "Walking":
            update.message.reply_text("How far would you be happy walking for?", reply_markup=ReplyKeyboardRemove())
            context.user_data["conversation_status"] = AWAITING_PREFERENCE_TIME
            context.user_data["preference_to_change"] = "walking"
        elif update.message.text == "Bicycling":
            update.message.reply_text("How far would you be happy cycling for?", reply_markup=ReplyKeyboardRemove())
            context.user_data["conversation_status"] = AWAITING_PREFERENCE_TIME
            context.user_data["preference_to_change"] = "biking"
        return
    if conversation_status == AWAITING_PREFERENCE_TIME:
        max_distance = -1
        preference: str = "none"
        for word in update.message.text.split(" "):
            try:
                max_distance: int = int(word)
                if max_distance > 0:
                    break
            except ValueError:
                logging.warning("\t'%s' is not a valid number!", word)
        if max_distance < 0:
            logging.warning("The distance cannot be: %s!", max_distance)
            update.message.reply_text("The distance has to be a positive number. Please type a valid distance:")
            return
        try:
            preference = context.user_data["preference_to_change"]
        except KeyError:
            logging.error("No key referring to a preference was found in user_data: %s", context.user_data)
        logging.info("The new distance found to be: %s meters", max_distance)
        payload: dict[str] = {preference: max_distance}
        response = TelegramResponse(TelegramResponse.CHANGE_PREFERENCE, user_id, payload)
        error = response.handle_request()
        msg = f"Preference successfully updated to {max_distance} meters!"
        if error is not None:
            logging.error(error)
            msg = "Server side error"
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        logging.info("Preference updated successfully! (%s: %s)", user_id, preference)
        context.user_data["conversation_status"] = LISTENING
        clear_user_data(context)
        return

    update.message.reply_text("Message out of context, see '/help' for commands", reply_markup=ReplyKeyboardRemove())


def confirm_address(update: Update, context: CallbackContext) -> None:
    """
    Handles the query from the inline keyboard after an address has been sent by the user.

    Args:
        update (:class:'Update'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher.
        context (:class:'CallbackContext'): passed in automatically in the telegram.ext.Handler when handler gets added
            to the dispatcher. Contains the user unique user_data.
    """
    conversation_status = context.user_data["conversation_status"]
    if conversation_status != AWAITING_ADDRESS_CONFIRMATION:
        return
    query_data = update.callback_query.data
    logging.info("Query received (%s): %s", update.callback_query.from_user.id, query_data)
    update.callback_query.answer()

    if query_data == "confirm":
        user_id = update.callback_query.from_user.id
        address = context.user_data["address"]
        response = TelegramResponse(TelegramResponse.CHANGE_HOME, user_id, address)
        error = response.handle_request()
        msg = f"Home address updated to: {address}"
        if error is not None:
            logging.error(error)
            msg = "Server side error"
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        logging.info("Query handled (%s)", user_id)
        context.user_data["conversation_status"] = LISTENING
        clear_user_data(context)
        return

    if query_data == "retry":
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please resend your address.")
        logging.info("Query handled (%s)", update.callback_query.from_user.id)
        context.user_data["conversation_status"] = AWAITING_ADDRESS
        return

    logging.warning("Unknown query: %s!", query_data)


#  Create the command handler dictionary, to be used to match the user command with the respective function.
commands = {
    "help": tgc_help,
    "start": tgc_help,
    "authorize_user": tgc_authorize_user,
    "change_home": tgc_change_home,
    "change_preference": tgc_change_preference
}


def init_telegram_bot() -> Updater:
    """
    Initializes the telegram bot.

    Returns:
         Updater: the object that handles the queuing and passing of the telegram.Update to the dispatcher.
            N.B. The return value does not have to be used if this function is called in telegram_bot.py.
    """
    for command_text, command_function in commands.items():
        dp.add_handler(CommandHandler(command_text, command_function))
    dp.add_handler(MessageHandler(Filters.location, handle_user_location))
    dp.add_handler(MessageHandler(Filters.text, handle_user_texts))
    dp.add_handler(CallbackQueryHandler(confirm_address, pass_chat_data=True))
    updater.start_polling(0)
    logging.info("Bot started...")
    return updater


def main():
    init_telegram_bot()
    updater.idle()


if __name__ == "__main__":
    main()
