import json
import os.path

from project.location import location_data


def get_user(telegram_id: str) -> dict:
    """
    Returns user data from telegram_id.

    Args:
        telegram_id (str): the users telegramID or '*' for all data

    Returns:
        dict: the dict with the requested data
    """
    with open('.\\data\\users.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    if telegram_id in data:
        return data[telegram_id]
    elif telegram_id == '*':
        return data
    return {}


def check_user_file():
    """
    Check if 'users.json' exists otherwise create it.
    """
    if not os.path.exists(".\\data\\users.json"):
        data = {}
        with open(".\\data\\users.json", 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    try:
        with open(".\\data\\users.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
    except json.decoder.JSONDecodeError:
        data = {}
        with open(".\\data\\users.json", 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)


class User:
    """Contains all userdata."""

    def __init__(self, telegram_id: str):
        """
        Get the data from a user with a specified telegramId

        Args:
            telegram_id (str): the telegramId of the user of which to get the data

        Returns:
             User: A new instance of user filled with the corresponding user data
        """
        check_user_file()
        self.telegram_id = telegram_id
        self.userdata = get_user(self.telegram_id)
        self.data('telegram_id', self.telegram_id)

    def data(self, user_property: str, value=None) -> dict | str | int | None:
        if value is None:
            if user_property == '*':
                return self.userdata
            elif user_property in self.userdata:
                return self.userdata[user_property]
        else:
            if user_property == 'home':
                self.userdata['home'] = location_data(value)
                self.save_data()
            else:
                self.userdata[user_property] = value
                self.save_data()
            return self.userdata
        return None

    def __repr__(self):
        return f"User: {self.telegram_id}"

    @classmethod
    def load_users(cls):
        """Loads all users from users.json"""
        users = get_user('*')
        users_obj = []
        for user in users.keys():
            user_obj = User(user)
            users_obj.append(user_obj)
        return users_obj

    def save_data(self):
        """
        Save the (updated) userdata in this User instance to 'user.json'.

        Returns:
            None: nothing
        """
        new_data = {self.telegram_id: self.userdata}
        with open('.\\data\\users.json', "r", encoding='utf-8') as file:
            data = json.load(file)
        with open('.\\data\\users.json', "w", encoding='utf-8') as file:
            data.update(new_data)
            json.dump(data, file, indent=4)
