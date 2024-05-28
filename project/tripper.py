import warnings
from datetime import datetime, timedelta

from googleapiclient.discovery import Resource
from requests import PreparedRequest

from project.event_handler import CalendarEvent
from project.location import maps, tu_building_code
from project.user import User
from project.utils import get_cal_service, color_id

DAYS_AHEAD = 14
TIME_SHIFT = 0

CURRENT_USER: User | None = None


def init_tripper_calendar(service: Resource) -> tuple[dict, list[dict]]:
    """Checks if travel time calendar exists or creates it,
        returns tripper calendar and all calendars that should be checked."""
    cal_data = service.calendarList().list().execute()
    calendars = cal_data['items']
    listen_cals: list[dict] = []
    tripper_cal: dict = {}
    for calendar in calendars:
        if '[Tripper]' in calendar.get('summaryOverride', ''):
            listen_cals.append(calendar)
        elif '[Tripper]' in calendar.get('description', ''):
            listen_cals.append(calendar)
        elif '[Tripper]' in calendar.get('summary', ''):
            listen_cals.append(calendar)
        if 'Tripper Travel Time' in calendar.get('summary', ''):
            tripper_cal = calendar
    if tripper_cal == {}:
        body = {
            'summary': 'Tripper Travel Time',
            'description': """Use Tripper to never run late and start walking, so you won't get overweight.
                           \rAdd Tripper now to your Google account and receive a 20% discount!""",
            'timeZone': 'Europe/Amsterdam'
        }
        tripper_cal = service.calendars().insert(body=body).execute()
    return tripper_cal, listen_cals


def get_all_events(service: Resource, calendars: list[dict]) -> list[CalendarEvent]:
    """Returns all events in all listen calendars"""
    all_events: list[CalendarEvent] = []
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    for calendar in calendars:
        events_result = service.events().list(calendarId=calendar['id'], timeMin=now,
                                              maxResults=20, singleEvents=True,
                                              orderBy='startTime').execute()
        for event_dict in events_result['items']:
            if 'date' in event_dict['start']:
                continue
            if datetime.strptime(event_dict['start']['dateTime'],
                                 '%Y-%m-%dT%H:%M:%S%z') < datetime.now().astimezone() + timedelta(days=DAYS_AHEAD):
                event = CalendarEvent(service, calendar['id'], event_dict, True)
                all_events.append(event)
    all_events_sorted = sorted(all_events)
    return all_events_sorted


def get_previous_location(destination: CalendarEvent, home, previous: CalendarEvent = None):
    if previous is None or previous.location is None:
        start_location = home
    elif destination.start.datetime.date() != previous.end.datetime.date():
        start_location = home
    else:
        start_location = tu_building_code(previous.location)
    return start_location


def new_tripper_event(service: Resource, tripper_cal_id: str, destination_event: CalendarEvent, user: User,
                      previous_event: CalendarEvent | None = None) -> CalendarEvent | str:
    """Creates a new tripper event."""
    start_location = get_previous_location(destination_event, user.data('home').get('address'), previous_event)
    if not needs_event(destination_event):
        return "No location set (or No Room location) or event start in the past"
    destination_location = tu_building_code(destination_event.location)
    route = mode_selector(start_location, destination_location, destination_event.start.datetime, user)
    if route['duration'] < 60:
        print(f"Route very short, {route['duration']} secs")
    if route == 'Not found':
        warnings.warn(f"WARNING Route not found from '{start_location}' to '{destination_location}'")
        return f"Route not found from '{start_location}' to '{destination_location}'"
    start_time = destination_event.start.datetime - timedelta(seconds=route['duration'])
    if start_time <= previous_event.start.datetime:
        return "Trip starts before previous event start"
    dur = route['duration'] // 60
    if dur == 0:
        dur = 1
    source_url = 'https://www.google.com/maps/dir/?api=1'
    params = {'origin': start_location,
              'destination': destination_location,
              'travelmode': route['mode'],
              'dir_action': 'navigate'}
    req = PreparedRequest()
    req.prepare_url(source_url, params)
    desc = f"Tripper Travel Time, Never Too Late!\nfrom:\n{start_location}\nto:\n{destination_location}\n\nnavigation link: {req.url}"
    new_trip = (
        CalendarEvent.new(service, calendar_id=tripper_cal_id)
        .set_title(f"Tripper: {dur} mins of {route['mode']}")
        .set_start_datetime(start_time - timedelta(minutes=TIME_SHIFT))
        .set_end_datetime(destination_event.start.datetime - timedelta(minutes=TIME_SHIFT))
        .set_description(desc)
        .set_color_id(color_id(route['mode']))
        .set_next_event(destination_event.calendar_id, destination_event.event_id)
        .set_prev_event(previous_event.calendar_id, previous_event.event_id)
    )
    return new_trip.execute()


def mode_selector(origin: str, destination: str, arr_time: datetime, user: User):
    """Selects the best mode(s) of transport."""
    modes = ['walking', 'bicycling', 'driving', 'transit']
    excluded = user.data('excluded_modes')
    max_walk = user.data('max_walking_distance')
    max_bicycle = user.data('max_bicycling_distance')
    if excluded is not None:
        for mode in excluded:
            modes.remove(mode)
    routes = maps(origin, destination, modes, arrival_time=arr_time)
    calc_routes = routes
    if 'driving' in calc_routes:
        calc_routes['driving']['duration'] += 180
    if 'bicycling' in calc_routes:
        calc_routes['bicycling']['duration'] += 90
    if routes == 'Not found':
        return 'Not found'
    if max_bicycle is not None and routes.get('bicycling', None) is not None and 'bicycling' in modes:
        if routes['bicycling']['distance'] > max_bicycle:
            modes.remove('bicycling')
    if max_walk is not None and routes.get('walking', None) is not None and 'walking' in modes:
        if routes['walking']['distance'] > max_walk:
            modes.remove('walking')
    best_mode = {'duration': 999999999}
    for mode, route in calc_routes.items():
        if route['duration'] < best_mode['duration']:
            best_mode = route
            best_mode['mode'] = mode
    return best_mode


def update_tripper_event(service: Resource, tripper_event: CalendarEvent, previous_event: CalendarEvent, user: User,
                         events_dict: dict[CalendarEvent]):
    """"Returns True if a new tripper event is needed, with reason in string"""
    move_trig = False
    if tripper_event.next_event_ref.event_id not in events_dict:
        service.events().delete(calendarId=tripper_event.calendar_id, eventId=tripper_event.event_id).execute()
        del tripper_event
        return True, 'listener event not found'

    paired_event = events_dict[tripper_event.next_event_ref.event_id]
    if paired_event.start.datetime != tripper_event.end.datetime:
        duration = tripper_event.end.datetime - tripper_event.start.datetime
        tripper_event.set_start_datetime(paired_event.start.datetime - duration)
        tripper_event.set_end_datetime(paired_event.start.datetime)
        tripper_event.execute()
        move_trig = True

    # Check if route locations are still the same
    desc = tripper_event.description.split('\n')
    trip_start = desc[2]
    trip_destination = desc[4]
    if move_trig:
        previous_event = get_relative_event(service, tripper_event, -1)
    if (trip_start != get_previous_location(paired_event, user.data('home')['address'], previous_event)
            or trip_destination != tu_building_code(paired_event.location)):
        if tripper_event.start.datetime <= previous_event.start.datetime:
            return False, 'Trip starts before previous event'
        service.events().delete(calendarId=tripper_event.calendar_id, eventId=tripper_event.event_id).execute()
        del tripper_event
        return True, 'location data different'

    return False, f'no event update needed, time shifted: {move_trig}'


def update_tripper(service: Resource, tripper_cal_id: str, tripper_events: list[CalendarEvent],
                   all_events: list[CalendarEvent], user: User):
    """Checks for changes and updates all future Tripper events."""
    events_dict = {event.event_id: event for event in all_events}
    listened_ids = [event.next_event_ref.event_id for event in tripper_events]
    listened_ids.extend([event.event_id for event in tripper_events])
    tripper_all_events = tripper_events
    tripper_all_events.extend(all_events)
    tripper_all_events.sort()

    for i in range(len(tripper_all_events) - 1):
        if not tripper_all_events[i].event_id in listened_ids and needs_event(tripper_all_events[i]):
            print('New event.\n', tripper_all_events[i].title)
            print(new_tripper_event(service, tripper_cal_id, tripper_all_events[i], user, tripper_all_events[i - 1]))
        if tripper_all_events[i].calendar_id != tripper_cal_id or i == 0:
            continue
        new_event_bool, reason = update_tripper_event(service, tripper_all_events[i], tripper_all_events[i - 1], user,
                                                      events_dict)
        if reason != 'no event update needed, time shifted: False':
            print(reason, tripper_all_events[i])
        if new_event_bool:
            print(f'New event needed, {reason}')
            print(new_tripper_event(service, tripper_cal_id, tripper_all_events[i + 1], user, tripper_all_events[i - 1]))


def needs_event(event: CalendarEvent) -> bool:
    """
    Returns True if event needs a Tripper event

    Args:
        event (CalendarEvent): the event that will be tested on the need of a Tripper event

    Returns:
        bool: True if the event needs a Tripper event
    """
    if tu_building_code(event.location) is None or event.start.datetime < datetime.now().astimezone():
        return False
    return True


def get_relative_event(service: Resource, event: CalendarEvent, delta: int) -> CalendarEvent | None:
    """
    Get the event with sorted index offset delta

    Args:
        service (Resource): a Google Calendar resource
        event (CalendarEvent): a Google Calendar Event of which the relative event
        delta (int): the index offset of the requested CalendarEvent

    Returns:
        CalendarEvent | None: the requested CalendarEvent gets returned if available otherwise None
    """
    tripper_cal, listen_cals = init_tripper_calendar(service)
    all_events: list[CalendarEvent] = get_all_events(service, listen_cals)
    all_events.extend(get_all_events(service, [tripper_cal]))
    all_events.sort()
    index: int = all_events.index(event)
    try:
        relative_event: CalendarEvent = all_events[index + delta]
    except KeyError:
        return None
    return relative_event


def main(service: Resource, user: str, refresh=False):
    global CURRENT_USER
    CURRENT_USER = User(user)
    tripper_cal, listen_cals = init_tripper_calendar(service)
    all_events = get_all_events(service, listen_cals)
    tripper_events = get_all_events(service, [tripper_cal])
    if refresh:
        for event in tripper_events:
            service.events().delete(calendarId=event.calendar_id, eventId=event.event_id).execute()
        main(service, user)
        return
    update_tripper(service, tripper_cal['id'], tripper_events, all_events, CURRENT_USER)


if __name__ == '__main__':
    # service = get_cal_service()
    main(get_cal_service('42069'), '42069')
