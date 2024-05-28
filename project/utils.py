import json

from google.auth.exceptions import MutualTLSChannelError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from project.user import User


# If modifying these scopes, delete the tokens ub users.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_cal_service(user_data: User | str) -> Resource:
    """
    Get a Google Calendar Resource object (also known as a `service`) authenticated with the given user.

    Args:
        user_data (User): a User object

    Returns:
         Resource: an authenticated Google Calendar resource
    """
    if isinstance(user_data, str):
        user_data = User(user_data)
    creds: Credentials = get_creds(user_data)
    try:
        service = build('calendar', 'v3', credentials=creds)
    except MutualTLSChannelError as exc:
        raise ConnectionError from exc
    return service


def get_creds(user_data: User) -> Credentials:
    """
    Gets the Credentials of the User, makes a local authorization request if necessary.
    NOTE: The authorization is only on the local server machine due to complexity issues.

    Args:
        user_data (User): The user of which to get the Credentials

    Returns:
         Credentials: The Google Oauth2 Credentials of the user
    """
    creds: Credentials | None = None
    # The user's access and refresh tokens are stored with the other user data in 'users.json', and is
    # created automatically when the authorization flow completes for the first
    # time.
    if user_data.data('creds') is not None:
        creds = Credentials.from_authorized_user_info(json.loads(user_data.data('creds')), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        user_data.data('creds', creds.to_json())
    return creds


def color_id(mode: str) -> int:
    """
    Get the colorId corresponding to the travel method.
    If the travel method (mode) string is invalid the colorId 1 will be returned.

    Args:
        mode (str): the transportation mode string
    Returns:
        int: the corresponding colorId
    """
    modes = {
        'walking': 4,
        'bicycling': 2,
        'transit': 5,
        'driving': 10
    }
    if mode in modes:
        return modes[mode]
    else:
        return 1


def create_nested_dict(src_dict: dict, nested_name: str) -> dict:
    """
    Adds a nested dict to a pre-existing dict, if it doesn't exist yet.
    WARNING: It doesn't check if the pre-existing dict key is actually a dict.

    Args:
        src_dict (dict): the dict which will contain the nested dict
        nested_name (str): the key of the nested dict

    Returns:
        dict: the original dict with the nested dict added if it did not exist yet.
    """
    if nested_name not in src_dict:
        src_dict[nested_name] = {}
    return src_dict


if __name__=="__main__":
    user = User('test_user')
    print(get_creds(user))
