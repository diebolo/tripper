from datetime import datetime

from telegram import (CallbackQuery, Chat, InlineKeyboardMarkup, Message,
                      ReplyKeyboardMarkup, Update, User)
from telegram.ext import CallbackContext

import project.telegram_bot as tb
from project.telegram_bot import (check_fist_text, check_for_reset,
                                  clear_user_data, confirm_address,
                                  get_confirmation_keyboard,
                                  get_location_keyboard,
                                  get_preference_keyboard, handle_user_texts,
                                  tgc_change_home, tgc_change_preference,
                                  updater)


test_user_id: int = 0000
test_context: CallbackContext = CallbackContext(updater.dispatcher)
test_chat: Chat = Chat(test_user_id, "private")
test_user: User = User(test_user_id, "Biggus", True, last_name="Dickus")
test_message: Message = Message(0, datetime.now(), test_chat, from_user=test_user)
test_update: Update = Update(0, message=test_message)
test_callback_query = CallbackQuery("0", test_user, str(test_user_id))


def test_keyboard_types():
    assert isinstance(get_confirmation_keyboard(), InlineKeyboardMarkup)
    assert isinstance(get_location_keyboard(), ReplyKeyboardMarkup)
    assert isinstance(get_preference_keyboard(), ReplyKeyboardMarkup)


def test_check_first_text(mocker):
    mocker.patch("telegram.Bot.send_message")
    test_context._user_id_and_data = (test_user_id, {})
    assert hasattr(test_context, "user_data")
    assert test_context.user_data.get("conversation_status", None) is None
    check_fist_text(test_update, test_context)
    assert test_context.user_data.get("conversation_status", None) == tb.LISTENING


def test_check_for_reset():
    test_conversation_status = tb.AWAITING_ADDRESS
    test_context._user_id_and_data = (test_user_id, {"conversation_status": test_conversation_status})
    assert hasattr(test_context, "user_data")
    assert test_context.user_data.get("conversation_status", None) == test_conversation_status
    check_for_reset(str(test_user_id), test_context)
    assert test_context.user_data.get("conversation_status", None) == tb.LISTENING


def test_clear_user_data():
    test_context._user_id_and_data = (test_user_id, {"conversation_status": tb.LISTENING, "address": "Test Address 420"})
    assert hasattr(test_context, "user_data")
    assert test_context.user_data.get("conversation_status", None) == tb.LISTENING
    assert test_context.user_data.get("address", None) == "Test Address 420"
    clear_user_data(test_context, False)
    assert test_context.user_data.get("address", None) is None
    assert test_context.user_data.get("conversation_status", None) == tb.LISTENING
    clear_user_data(test_context, True)
    assert test_context.user_data.get("conversation_status", None) is None
    assert not test_context.user_data


def test_change_home(mocker):
    mocker.patch("telegram.Bot.send_message")
    test_context._user_id_and_data = (test_user_id, {"conversation_status": tb.LISTENING})
    assert hasattr(test_context, "user_data")
    assert test_context.user_data.get("conversation_status", None) == tb.LISTENING
    tgc_change_home(test_update, test_context)
    assert test_context.user_data.get("conversation_status", None) == tb.AWAITING_LOCATION


def test_change_preference(mocker):
    mocker.patch("telegram.Bot.send_message")
    test_context._user_id_and_data = (test_user_id, {"conversation_status": tb.LISTENING})
    assert hasattr(test_context, "user_data")
    assert test_context.user_data.get("conversation_status", None) == tb.LISTENING
    tgc_change_preference(test_update, test_context)
    assert test_context.user_data.get("conversation_status", None) == tb.AWAITING_PREFERENCE


def test_change_preference_with_args(mocker):
    def test_preference() -> str:
        mocker.patch("telegram.Message.reply_text")
        test_context._user_id_and_data = (test_user_id, {"conversation_status": tb.LISTENING})
        assert hasattr(test_context, "user_data")
        assert test_context.user_data.get("conversation_status", None) == tb.LISTENING
        tgc_change_preference(test_update, test_context)
        assert test_context.user_data.get("conversation_status", None) == tb.AWAITING_PREFERENCE_TIME
        return "OK"

    test_context.args = ["biking"]
    assert hasattr(test_context, "args")
    assert test_context.args[0] == "biking"
    assert test_preference() == "OK"
    test_context.args = ["walking"]
    assert test_context.args[0] == "walking"
    assert test_preference() == "OK"


def test_handle_user_texts(mocker):
    test_context._user_id_and_data = (test_user_id, {"conversation_status": tb.LISTENING})
    mocker.patch("project.telegram_response.TelegramResponse.handle_request", return_value=None)

    def test_text(expected_status: int, fake_text="") -> str:
        mocker.patch("telegram.Message.reply_text")
        mocker.patch("telegram.Bot.send_message")

        test_update.message.text = fake_text
        assert hasattr(test_update.message, "text")
        assert hasattr(test_context, "user_data")
        assert test_context.user_data.get("conversation_status", None) is not None
        handle_user_texts(test_update, test_context)
        assert test_context.user_data.get("conversation_status", None) == expected_status
        return "OK"

    test_context.user_data["conversation_status"] = tb.AWAITING_LOCATION
    assert test_text(tb.AWAITING_ADDRESS, "No, I'm not at home") == "OK"

    test_context.user_data["conversation_status"] = tb.AWAITING_ADDRESS
    assert test_text(tb.AWAITING_ADDRESS_CONFIRMATION) == "OK"

    test_context.user_data["conversation_status"] = tb.AWAITING_PREFERENCE
    assert test_text(tb.AWAITING_PREFERENCE_TIME, "Walking") == "OK"
    assert test_context.user_data.get("preference_to_change", None) == "walking"
    clear_user_data(test_context)

    test_context.user_data["conversation_status"] = tb.AWAITING_PREFERENCE
    assert test_text(tb.AWAITING_PREFERENCE_TIME, "Bicycling") == "OK"
    assert test_context.user_data.get("preference_to_change", None) == "biking"
    clear_user_data(test_context)

    test_context.user_data["conversation_status"] = tb.AWAITING_PREFERENCE_TIME
    assert test_text(tb.LISTENING, "I want to do that for 1001 meters") == "OK"
    # TODO: If there's time, figure out -> return payload of TelegramResponse using mocker, check if payload == 1001


def test_confirm_address(mocker):
    mocker.patch("telegram.Bot.send_message")
    mocker.patch("project.telegram_response.TelegramResponse.handle_request", return_value=None)
    mocker.patch("telegram.CallbackQuery.answer")
    test_context._user_id_and_data = (test_user_id, {"conversation_status": tb.AWAITING_ADDRESS_CONFIRMATION})
    assert hasattr(test_context, "user_data")
    test_context.user_data["address"] = "Test Address 420"
    assert test_context.user_data.get("address", None) == "Test Address 420"

    assert test_context.user_data.get("conversation_status", None) == tb.AWAITING_ADDRESS_CONFIRMATION
    test_update.callback_query = test_callback_query
    test_update.callback_query.data = "confirm"
    assert test_update.callback_query.data == "confirm"
    confirm_address(test_update, test_context)
    assert test_context.user_data.get("conversation_status", None) == tb.LISTENING
    assert test_context.user_data.get("address", None) is None

    test_context.user_data["conversation_status"] = tb.AWAITING_ADDRESS_CONFIRMATION
    assert test_context.user_data.get("conversation_status", None) == tb.AWAITING_ADDRESS_CONFIRMATION
    test_update.callback_query.data = "retry"
    assert test_update.callback_query.data == "retry"
    confirm_address(test_update, test_context)
    assert test_context.user_data.get("conversation_status", None) == tb.AWAITING_ADDRESS
