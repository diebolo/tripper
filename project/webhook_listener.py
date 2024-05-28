import requests
from flask import Flask, request
import random

from project.tripper import init_tripper_calendar
from project.tripper import main as run_tripper
from project.user import User
from project.utils import get_cal_service, get_creds

app = Flask(__name__)
# ADDRESS = None
# USER: str | None = None


def make_req_open(calendar_id: str, user_id: str, token: str, ttl: int = 1800):
    """Requests webhook channels from Google Calendar API."""
    url = f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/watch'
    session_id = random.randint(1000,9999)
    data = {
        "id": f"{user_id}+{session_id}",
        "type": "webhook",
        "address": ADDRESS,
        "params": {
            "ttl": ttl
        }
    }
    header = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    reply = requests.post(url, headers=header, json=data).json()
    if 'error' in reply:
        if reply['error'].get('message').split()[-1] == 'unique':
            return f"Channel {data['id']} already open"
    return reply


def make_req_stop(resource_id: str, user_id: str):
    """Used for manually stopping channels during development"""
    token = get_creds(User(user_id)).token
    url = 'https://www.googleapis.com/calendar/v3/channels/stop'
    data = {
        "id": user_id,
        "resourceId": resource_id
    }
    header = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    return requests.post(url, headers=header, json=data).text

@app.route('/hello')
def hello():
    return "Hello, I'm alive :)"

@app.route('/tripper', methods=['POST'])
def tripper_webhook():
    """Processes the webhook from Google Calendar"""
    calendar_id = list(request.headers.get('X-Goog-Resource-Uri').split('/'))[-2]
    channel_id: str = request.headers.get('X-Goog-Channel-Id')
    resource_id = request.headers.get('X-Goog-Resource-Id')
    if request.headers.get('X-Goog-Resource-State') == 'exists':
        print(
            f"\n== CHANGED RESOURCE ==\nResource ID: {resource_id}\nChannel ID: {channel_id}\nCalendar ID: {calendar_id}\n")
        run_tripper(get_cal_service(USER), USER)
        print('\n== UPDATED TRIPPER ==\n')
    elif request.headers.get('X-Goog-Resource-State') == 'sync':
        print(f"\n== SYNC ==\nResource ID: {resource_id}\nChannel ID: {channel_id}\nCalendar ID: {calendar_id}\n")
    else:
        print(request.headers)
    return 'success', 200


def main(user: str):
    """Opens the webhook channels and starts listening for triggers."""
    global USER
    USER = user
    local_user = User(user)
    service = get_cal_service(local_user)
    _, listen_cals = init_tripper_calendar(service)
    token = get_creds(local_user).token
    for calendar in listen_cals:
        etag = calendar['etag'].replace('"', '')
        channel = make_req_open(calendar['id'], etag, token)
        print(channel)
    run_tripper(service, user, refresh=True)
    app.run()


def start_main(user: str, address: str):
    global USER, ADDRESS
    USER = user
    ADDRESS = address
    main(USER)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser('Tripper-webhook')
    parser.add_argument('user')
    parser.add_argument('address')
    args = parser.parse_args()
    global ADDRESS, USER
    USER = args.user
    ADDRESS = args.address
    main(USER)
