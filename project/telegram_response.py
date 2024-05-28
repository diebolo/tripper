from project.user import User
from project.utils import get_creds


class TelegramResponse:
    """
    This class will later communicate with the rest of Tripper to relay what the user wants to do.

    Args:
        response_id (:obj:'int'): the type of response that has been generated. Use TelegramResponse
            built-in constants for ease of use.
                0 => authorization of the Google account.
                1 => changing the address of your home.
                2 => changing the max distance you're willing to walk or cycle.
        user_id (:obj:'str'): the telegram_id of the user. Can be retrieved using Update.Message.from_user.
        payload (:obj:'dict[str]' | :obj:'str'): the data that was changed by the user.

    Attributes:
        response_id (:obj:'int'): an identifier for what data the user changed.
        user_id (:obj:'str'): the telegram_id (and JSON key) under which the data gets saved.
        payload (:obj:'dict[str]' | :obj:'str'): the data that will be saved to JSON.

    Methods:
        handle_request(): Invoke this method to save the data in the TelegramResponse object accordingly.

        Returns:
            str | None: A string containing why handling the request could not happen. Otherwise, None.
    """
    AUTHORIZE = 0
    CHANGE_HOME = 1
    CHANGE_PREFERENCE = 2

    def __init__(self, response_id: int, user_id: str, payload: str | dict[str]):
        self.response_id = response_id
        self.user_id = user_id if (isinstance(user_id, str)) else str(user_id)
        self.payload = payload  # This will contain the information the user wants to send over, such as their
                                # credentials or an address

    def __str__(self) -> str:
        return f"{self.user_id} requests '{self.response_id}' with payload:\n{self.payload}"

    def handle_request(self) -> None | str:
        """
        Handle the user data according to the response id:
           1 or 2: Save the user data using imported user.py methods
           0:      Request authorization link from Google
           To be invoked after the TelegramResponse has been created.

        Returns:
              str | None: a string containing the error of why the request could not be handled. Otherwise, None.
        """
        user = User(self.user_id)

        match self.response_id:
            case self.AUTHORIZE:
                if isinstance(self.payload, str):
                    print(self.payload)
                    # user.data("auth-token", self.payload)
                    get_creds(user)
                else:
                    return f"The payload for authentication must be a string, is: {type(self.payload)}"
                # return "Not implemented yet!"

            case self.CHANGE_HOME:
                if isinstance(self.payload, str):
                    print(self.payload)
                    user.data("home", self.payload)
                else:
                    return f"The payload for change home must be a string, is: {type(self.payload)}"

            case self.CHANGE_PREFERENCE:
                if not isinstance(self.payload, dict):
                    return f"The payload for change home must be a dict, is: {type(self.payload)}"
                if len(self.payload) != 1:
                    return f"The payload is the wrong length: {len(self.payload)}"
                if "biking" in self.payload:
                    pref = "max_bicycling_distance"
                    distance = int(self.payload["biking"])
                    user.data(pref, distance)
                elif "walking" in self.payload:
                    pref = "max_walking_distance"
                    distance = int(self.payload["walking"])
                    user.data(pref, distance)
                else:
                    return f"Unknown key in payload! ({self.payload.keys[0]})"
        return None
