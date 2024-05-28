from datetime import datetime, timedelta, timezone

import pytest

from project.event_handler import CalendarEvent, ReadOnlyError


def test_title():
    cal_event = CalendarEvent.new(None, 'primary')

    assert cal_event.title is None

    cal_event.set_title('cool title')
    assert cal_event._title == 'cool title'
    assert 'title' in cal_event.updated_fields
    assert cal_event.title == 'cool title'


def test_title_locked():
    # Setup
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event._locked = True
    cal_event._title = "original title"

    # Testing
    with pytest.raises(ReadOnlyError) as exc_info:
        cal_event.set_title("new title")
    assert str(exc_info.value) == "This instance of 'CalendarEvent' is LOCKED and" + \
           " the attribute 'title' is therefor Read-Only."
    assert exc_info.value.obj == cal_event
    assert exc_info.value.name == 'title'
    assert cal_event._title == "original title"
    assert 'title' not in cal_event.updated_fields


def test_location():
    cal_event = CalendarEvent.new(None, 'primary')

    assert cal_event.location is None

    cal_event.set_location('Van Hasseltlaan')
    assert cal_event._location == 'Van Hasseltlaan'
    assert 'location' in cal_event.updated_fields
    assert cal_event.location == 'Van Hasseltlaan'


def test_location_locked():
    # Setup
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event._locked = True
    cal_event._location = "original location"

    # Testing
    with pytest.raises(ReadOnlyError) as exc_info:
        cal_event.set_location("new location")
    assert str(exc_info.value) == "This instance of 'CalendarEvent' is LOCKED and" + \
           " the attribute 'location' is therefor Read-Only."
    assert exc_info.value.obj == cal_event
    assert exc_info.value.name == 'location'
    assert cal_event._location == "original location"
    assert 'location' not in cal_event.updated_fields


def test_color_id():
    cal_event = CalendarEvent.new(None, 'primary')

    assert cal_event.color_id is None

    cal_event.set_color_id('5')
    assert cal_event._color_id == '5'
    assert 'color_id' in cal_event.updated_fields
    assert cal_event.color_id == '5'


def test_description():
    cal_event = CalendarEvent.new(None, 'primary')

    assert cal_event.description is None

    cal_event.set_description("Ik ga een ijsje eten")
    assert cal_event._description == "Ik ga een ijsje eten"
    assert 'description' in cal_event.updated_fields
    assert cal_event.description == "Ik ga een ijsje eten"


def test_description_locked():
    # Setup
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event._locked = True
    cal_event._description = "original description"

    # Testing
    with pytest.raises(ReadOnlyError) as exc_info:
        cal_event.set_description("new description")
    assert str(exc_info.value) == "This instance of 'CalendarEvent' is LOCKED and" + \
           " the attribute 'description' is therefor Read-Only."
    assert exc_info.value.obj == cal_event
    assert exc_info.value.name == 'description'
    assert cal_event._description == "original description"
    assert 'description' not in cal_event.updated_fields


def test_start_datetime():
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event.set_start_datetime(datetime.strptime('2022-10-04T20:20:20', '%Y-%m-%dT%H:%M:%S'))
    assert cal_event.start.datetime == datetime(year=2022, month=10, day=4, hour=20, minute=20, second=20)
    assert 'start_datetime' in cal_event.updated_fields


def test_start_datetime_locked():
    # Setup
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event._locked = True
    original_datetime = datetime.now()
    cal_event.start.datetime = original_datetime

    # Testing
    with pytest.raises(ReadOnlyError) as exc_info:
        cal_event.set_start_datetime(datetime(year=2002, month=1, day=8, hour=19, minute=5, second=1))
    assert str(exc_info.value) == "This instance of 'CalendarEvent' is LOCKED and" + \
           " the attribute 'start.datetime' is therefor Read-Only."
    assert exc_info.value.obj == cal_event
    assert exc_info.value.name == 'start.datetime'
    assert cal_event.start.datetime == original_datetime
    assert 'start_datetime' not in cal_event.updated_fields


def test_start_timezone():
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event.set_start_timezone("Europe/Brussels")
    assert cal_event.start.timezone == "Europe/Brussels"
    assert 'start_timezone' in cal_event.updated_fields


def test_start_timezone_locked():
    # Setup
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event._locked = True
    cal_event.start.timezone = "Europe/Brussels"

    # Testing
    with pytest.raises(ReadOnlyError) as exc_info:
        cal_event.set_start_timezone("Europe/London")
    assert str(exc_info.value) == "This instance of 'CalendarEvent' is LOCKED and" + \
           " the attribute 'start.timezone' is therefor Read-Only."
    assert exc_info.value.obj == cal_event
    assert exc_info.value.name == 'start.timezone'
    assert cal_event.start.timezone == "Europe/Brussels"
    assert 'start_timezone' not in cal_event.updated_fields


def test_end_datetime():
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event.set_end_datetime(datetime.strptime('2022-10-04T20:20:20', '%Y-%m-%dT%H:%M:%S'))
    assert cal_event.end.datetime == datetime(year=2022, month=10, day=4, hour=20, minute=20, second=20)
    assert 'end_datetime' in cal_event.updated_fields


def test_end_datetime_locked():
    # Setup
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event._locked = True
    original_datetime = datetime.now()
    cal_event.end.datetime = original_datetime

    # Testing
    with pytest.raises(ReadOnlyError) as exc_info:
        cal_event.set_end_datetime(datetime(year=2002, month=1, day=8, hour=19, minute=5, second=1))
    assert str(exc_info.value) == "This instance of 'CalendarEvent' is LOCKED and" + \
           " the attribute 'end.datetime' is therefor Read-Only."
    assert exc_info.value.obj == cal_event
    assert exc_info.value.name == 'end.datetime'
    assert cal_event.end.datetime == original_datetime
    assert 'end_datetime' not in cal_event.updated_fields


def test_end_timezone():
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event.set_end_timezone("Europe/Brussels")
    assert cal_event.end.timezone == "Europe/Brussels"
    assert 'end_timezone' in cal_event.updated_fields


def test_end_timezone_locked():
    # Setup
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event._locked = True
    cal_event.end.timezone = "Europe/Brussels"

    # Testing
    with pytest.raises(ReadOnlyError) as exc_info:
        cal_event.set_end_timezone("Europe/London")
    assert str(exc_info.value) == "This instance of 'CalendarEvent' is LOCKED and" + \
           " the attribute 'end.timezone' is therefor Read-Only."
    assert exc_info.value.obj == cal_event
    assert exc_info.value.name == 'end.timezone'
    assert cal_event.end.timezone == "Europe/Brussels"
    assert 'end_timezone' not in cal_event.updated_fields


def test_set_next_event():
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event.set_next_event('primary', 'the id of the dentist appointment')
    assert cal_event.next_event_ref.calendar_id == 'primary'
    assert cal_event.next_event_ref.event_id == 'the id of the dentist appointment'
    assert repr(cal_event.next_event_ref) == "CalenderRef(primary/the id of the dentist appointment)"
    assert 'next_event' in cal_event.updated_fields


def test_set_prev_event():
    cal_event = CalendarEvent.new(None, 'primary')
    cal_event.set_prev_event('primary', 'the id of the lunch appointment')
    assert cal_event.prev_event_ref.calendar_id == 'primary'
    assert cal_event.prev_event_ref.event_id == 'the id of the lunch appointment'
    assert repr(cal_event.prev_event_ref) == "CalenderRef(primary/the id of the lunch appointment)"
    assert 'prev_event' in cal_event.updated_fields


def test_execute_unexpected_field_changed():
    cal_event = CalendarEvent.new(None, 'primary').set_title('t')
    cal_event.updated_fields.add('something unexpected')
    with pytest.raises(NotImplementedError) as exc_info:
        cal_event.execute()
    assert str(exc_info.value) == "The field 'something unexpected' is not implemented (yet)"


def test_calendar_event_lt():
    date1 = datetime(year=2022, month=10, day=4, hour=20, minute=20, second=20)
    date2 = datetime(year=2022, month=11, day=4, hour=20, minute=20, second=20)
    cal_event1 = CalendarEvent.new(None, 'primary').set_start_datetime(date1)
    cal_event2 = CalendarEvent.new(None, 'Family').set_start_datetime(date1)
    cal_event3 = CalendarEvent.new(None, 'Family').set_start_datetime(date2)
    assert cal_event1 < cal_event3
    assert cal_event2 < cal_event3
    assert cal_event1 >= cal_event2


def test_calendar_event_repr_empty():
    cal_event = CalendarEvent.new(None, 'primary')
    assert repr(cal_event) == "gc-Event(None, 'None') [ calendarId: 'primary']"


def test_calendar_event_repr_start_datetime():
    date = datetime(year=2022, month=10, day=4, hour=20, minute=20, second=20)
    cal_event = CalendarEvent.new(None, 'primary').set_start_datetime(date)
    assert repr(cal_event) == "gc-Event(None, 'None') [ calendarId: 'primary', start: '2022-10-04 20:20:20']"


def test_calendar_event_repr_end_datetime():
    date = datetime(year=2022, month=10, day=4, hour=20, minute=20, second=20)
    cal_event = CalendarEvent.new(None, 'primary').set_end_datetime(date)
    assert repr(cal_event) == "gc-Event(None, 'None') [ calendarId: 'primary', end: '2022-10-04 20:20:20']"


def test_calendar_event_update():
    cal_event = CalendarEvent(None, 'primary', {
        "kind": "calendar#event",
        "etag": "\"3328602811556000\"",
        "id": "02a1fdu6v4imkvhnajmoj7o70r_20270602T100000Z",
        "status": "confirmed",
        "htmlLink": "https://www.google.com/calendar/event?eid=MDJhMWZkdTZ2NGlta3ZobmFqbW9qN283MHJfMjAyNzA2MDJUMTAwMDAwWiBncm91cDIzc2VtQG0",
        "created": "2022-09-27T17:56:45.000Z",
        "updated": "2022-09-27T17:56:45.778Z",
        "summary": "SEM 23 Meeting",
        "creator": {
            "email": "group23sem@gmail.com",
            "self": True
        },
        "organizer": {
            "email": "group23sem@gmail.com",
            "self": True
        },
        "start": {
            "dateTime": "2027-06-02T12:00:00+02:00",
            "timeZone": "Europe/Brussels"
        },
        "end": {
            "dateTime": "2027-06-02T13:45:00+02:00",
            "timeZone": "Europe/Brussels"
        },
        "recurringEventId": "02a1fdu6v4imkvhnajmoj7o70r",
        "originalStartTime": {
            "dateTime": "2027-06-02T12:00:00+02:00",
            "timeZone": "Europe/Brussels"
        },
        "iCalUID": "02a1fdu6v4imkvhnajmoj7o70r@google.com",
        "sequence": 0,
        "reminders": {
            "useDefault": True
        },
        "eventType": "default"
    })
    assert cal_event.service is None
    assert cal_event.calendar_id == 'primary'
    assert cal_event.event_id == "02a1fdu6v4imkvhnajmoj7o70r_20270602T100000Z"

    assert not cal_event.pre_existing
    assert len(cal_event.updated_fields) == 0
    assert not cal_event._locked

    assert cal_event.title == "SEM 23 Meeting"
    assert cal_event.location is None
    assert cal_event.description is None
    assert cal_event.color_id is None

    assert cal_event.start.datetime == datetime(2027, 6, 2, 12, 0, tzinfo=timezone(timedelta(seconds=7200)))
    assert cal_event.start.timezone == "Europe/Brussels"

    assert not cal_event._end_time_unspecified
    assert cal_event.end.datetime == datetime(2027, 6, 2, 13, 45, tzinfo=timezone(timedelta(seconds=7200)))
    assert cal_event.end.timezone == "Europe/Brussels"

    assert cal_event.prev_event_ref.event_id is None
    assert cal_event.prev_event_ref.calendar_id is None

    assert cal_event.next_event_ref.event_id is None
    assert cal_event.next_event_ref.calendar_id is None

    assert cal_event._reminders_default
    assert cal_event._reminders == []
