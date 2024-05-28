from dataclasses import dataclass
from datetime import datetime

from googleapiclient.discovery import Resource

from project.utils import create_nested_dict


# NOTE: Probably more trouble than what it's worth
class ReadOnlyError(AttributeError):
    """Raised when an attempt to change a read-only attribute was made"""


@dataclass
class DateTimeZone:
    """
    A class to hold datetime objects with a textual timezone

    Attributes:
        datetime (datetime | None): the datetime object
        timezone (str | None): the textual timezone
    """
    datetime: datetime | None
    timezone: str | None


@dataclass
class CalenderRef:
    """
    A class that holds the information to reference another Google Calendar Event

    Attributes:
        calendar_id (str | None): the ID of the calendar which contains the referenced Google Calendar Event
        event_id (str | None): the id of the Google Calendar Event which is being referenced.
    """
    calendar_id: str | None
    event_id: str | None

    def __repr__(self) -> str:
        """Represent the CalenderRef Object"""
        return f"CalenderRef({self.calendar_id}/{self.event_id})"


class CalendarEvent:
    # pylint: enable=too-many-instance-attributes
    # Setters make it one attribute since the error is on the amount of attributes
    #   It also enables the getting of the values in a nicer way, but it does disallow for chaining behavior
    """CalendarEvent is used to retrieve and updates events

        NOTE: Starting to doubt if this is the best way.
        It's, look at custom event properties? Extended Properties for storing metadata of the traveltime
         -> Source
    """

    def __init__(self, service: Resource | None, calendar_id: str,
                 raw_data: dict, pre_existing: bool = False):
        """
        The constructor for a CalendarEvent

        IMPORTANT: WHEN REQUESTING A LIST OF EVENTS FROM THE CALENDAR USE 'singleEvents=True'
        IN ORDER TO NOT HAVE TO DEAL WITH RECURRING EVENTS IN A SPECIAL WAY

        Args:
            service (Resource | None): The Google Calendar Event Resource from the Google Calendar API
                                        This should only be None for Tests
            calendar_id (str): The CalenderID of the Calendar which contains the event
            raw_data (dict): The Event Data which is pulled from the Google Calendar API
            pre_existing (bool): If the Corresponding Google Calendar Event already exists (Default = False)

        Returns:
            CalendarEvent: A CalendarEvent Object
        """
        self.raw_data = {}  # Contains the raw data, which is returned by the Google Calendar API
        self.updated_fields: set[str] = set()  # In order to keep track of which fields are updated
        self.pre_existing: bool = pre_existing  # If the corresponding Google Calendar Event already exists

        self.service = service
        self.calendar_id = calendar_id
        self.event_id = None  # Optional, Writable
        # self._ical_uid = None  # Read-Only, Purpose: the ICAL identifier of the event, It's the same on rec events

        self._title = None  # Optional, Writable
        # self._etag = None  # Read-Only, Purpose: Changes when data is changed
        self.start = DateTimeZone(None, None)  # Writable
        self.end = DateTimeZone(None, None)  # Writable
        self._end_time_unspecified = False  # Read-Only

        self._locked = False  # Read-Only, Purpose: Indicates if certain fields can be changed
        self._location = None  # Optional, Writable
        self._description = None  # Optional, Writable
        self._color_id = None  # Optional, Writable
        # self._created_by_self = False  # Optional, Read-Only

        self._reminders_default = False  # Writable
        self._reminders = []  # Max 5 writable

        self.next_event_ref = CalenderRef(None, None)
        self.prev_event_ref = CalenderRef(None, None)

        # In order to fill the fields with the raw_data, self.__update is called.
        self.__update(raw_data)

    def __repr__(self) -> str:
        """
        An implementation for ``repr``-function for the CalendarEvent class

        Returns:
            str: a string representation of the CalendarEvent object
        """
        # Creation of the repr message Header
        repr_msg = f"gc-Event({self._title}, '{self.event_id}') [ "

        if self.calendar_id is not None:
            repr_msg += f"calendarId: '{self.calendar_id}',"
        if self.start.datetime is not None:
            repr_msg += f" start: '{self.start.datetime}',"
        if self.end.datetime is not None:
            repr_msg += f" end: '{self.end.datetime}',"
        # Take the build string, except the trailing comma and close the last bracket.
        return repr_msg[:-1] + "]"

    def __lt__(self, other: 'CalendarEvent') -> bool:
        return self.start.datetime < other.start.datetime

    def __ge__(self, other: 'CalendarEvent') -> bool:
        return not self < other

    def __eq__(self, other: 'CalendarEvent') -> bool:
        return self.event_id == other.event_id and self.calendar_id == other.calendar_id

    @classmethod
    def new(cls, service: Resource | None, calendar_id: str) -> 'CalendarEvent':
        """Make a new Event object"""
        return cls(service=service, calendar_id=calendar_id, raw_data={}, pre_existing=False)

    @classmethod
    def get_event(cls, service: Resource | None, calendar_id: str, event_id: str) -> 'CalendarEvent':
        """Get a pre-existing event from Google Calendar and create a corresponding object"""
        raw_data = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return cls(service=service, calendar_id=calendar_id, raw_data=raw_data, pre_existing=True)

    def __locked_check(self, name) -> None:
        if self._locked:
            raise ReadOnlyError(f"This instance of '{self.__class__.__name__}' is LOCKED and the attribute '{name}'" +
                                " is therefor Read-Only.", obj=self, name=name)

    @property
    def title(self) -> str | None:
        return self._title

    def set_title(self, new_title: str) -> 'CalendarEvent':
        """Set the title of the CalendarEvent object"""
        self.__locked_check('title')
        self.updated_fields.add('title')
        self._title = new_title
        return self

    def set_start_datetime(self, new_start_datetime: datetime) -> 'CalendarEvent':
        """Set the start time of the CalenderEvent object"""
        self.__locked_check('start.datetime')
        self.updated_fields.add('start_datetime')
        self.start.datetime = new_start_datetime
        return self

    def set_start_timezone(self, new_start_timezone: str) -> 'CalendarEvent':
        """Set the start timezone of the CalenderEvent object"""
        self.__locked_check('start.timezone')
        self.updated_fields.add('start_timezone')
        self.start.timezone = new_start_timezone
        return self

    def set_end_datetime(self, new_end_datetime: datetime) -> 'CalendarEvent':
        """Set the end time of the CalenderEvent object"""
        self.__locked_check('end.datetime')
        self.updated_fields.add('end_datetime')
        self.end.datetime = new_end_datetime
        return self

    def set_end_timezone(self, new_end_timezone: str) -> 'CalendarEvent':
        """Set the end timezone of the CalenderEvent object"""
        self.__locked_check('end.timezone')
        self.updated_fields.add('end_timezone')
        self.end.timezone = new_end_timezone
        return self

    @property
    def location(self) -> str | None:
        return self._location

    def set_location(self, new_location: str) -> 'CalendarEvent':
        """Set location of the CalenderEvent object"""
        self.__locked_check('location')
        self.updated_fields.add('location')
        self._location = new_location
        return self

    @property
    def color_id(self) -> str | None:
        return self._color_id

    def set_color_id(self, new_color_id: str) -> 'CalendarEvent':
        """Set location of the CalenderEvent object"""
        self.updated_fields.add('color_id')
        self._color_id = new_color_id
        return self

    @property
    def description(self) -> str | None:
        return self._description

    def set_description(self, new_description: str) -> 'CalendarEvent':
        """Set a description of the CalenderEvent object"""
        self.__locked_check('description')
        self.updated_fields.add('description')
        self._description = new_description
        return self

    def set_next_event(self, next_event_calendar_id: str, next_event_event_id: str) -> 'CalendarEvent':
        """Set the next event of the CalendarEvent object"""
        self.updated_fields.add('next_event')
        self.next_event_ref.calendar_id = next_event_calendar_id
        self.next_event_ref.event_id = next_event_event_id
        return self

    def set_prev_event(self, prev_event_calendar_id: str, prev_event_event_id: str) -> 'CalendarEvent':
        """Set the previous event of the CalendarEvent object"""
        self.updated_fields.add('prev_event')
        self.prev_event_ref.calendar_id = prev_event_calendar_id
        self.prev_event_ref.event_id = prev_event_event_id
        return self

    def _gen_patch_message(self) -> dict[str, str | dict]:
        """Generate a Patch dict"""
        patch_message = {}
        for change in self.updated_fields:
            match change:
                case 'title':
                    patch_message['summary'] = self._title
                case 'start_datetime':
                    # NOTE: Maybe do a calculation first
                    # ? Check if timezone is provided otherwise fix
                    patch_message = create_nested_dict(patch_message, 'start')
                    patch_message['start']['dateTime'] = self.start.datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
                case 'start_timezone':
                    # ? Check if timezone is provided otherwise fix
                    patch_message = create_nested_dict(patch_message, 'start')
                    patch_message['start']['timeZone'] = self.start.timezone
                case 'end_datetime':
                    # NOTE: Maybe do a calculation first
                    # ? Check if timezone is provided otherwise fix
                    patch_message = create_nested_dict(patch_message, 'end')
                    patch_message['end']['dateTime'] = self.end.datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
                case 'end_timezone':
                    # ? Check if timezone is provided otherwise fix
                    patch_message = create_nested_dict(patch_message, 'end')
                    patch_message['end']['timeZone'] = self.end.timezone
                case 'location':
                    patch_message['location'] = self._location
                case 'color_id':
                    patch_message['colorId'] = self._color_id
                case 'description':
                    patch_message['description'] = self._description
                case 'next_event':
                    patch_message = create_nested_dict(patch_message, 'extendedProperties')
                    patch_message['extendedProperties'] = create_nested_dict(
                        patch_message['extendedProperties'],
                        'private'
                    )
                    patch_message['extendedProperties']['private']['tripperNextEvent_CalendarID'] = \
                        self.next_event_ref.calendar_id
                    patch_message['extendedProperties']['private']['tripperNextEvent_EventID'] = \
                        self.next_event_ref.event_id
                case 'prev_event':
                    patch_message = create_nested_dict(patch_message, 'extendedProperties')
                    patch_message['extendedProperties'] = create_nested_dict(
                        patch_message['extendedProperties'],
                        'private'
                    )
                    patch_message['extendedProperties']['private']['tripperPrevEvent_CalendarID'] = \
                        self.prev_event_ref.calendar_id
                    patch_message['extendedProperties']['private']['tripperPrevEvent_EventID'] = \
                        self.prev_event_ref.event_id
                case other:
                    raise NotImplementedError(f"The field '{other}' is not implemented (yet)")
        return patch_message

    def execute(self):
        """Update or Create Event in Google Calendar"""
        patch_message = self._gen_patch_message()

        if self.pre_existing:
            # Patch the pre-existing event with the new data
            # Using patch is a little waste full compared to update, but it is easier to implement
            new_data_raw = self.service.events().patch(calendarId=self.calendar_id, eventId=self.event_id,
                                                       body=patch_message).execute()
        else:
            # Create the new Event with the Google Calendar API
            # Checking if begin and end time are set when creating
            if not (not ('start' not in patch_message or 'dateTime' not in patch_message['start']) or not (
                    'end' not in patch_message or 'dateTime' not in patch_message['end'])):
                raise LookupError('start and/or end datetime not supplied')
            new_data_raw = self.service.events().insert(calendarId=self.calendar_id, body=patch_message).execute()
            self.pre_existing = True
            # Require Begin and end datetime (With timezone information)
        # catch response and update object
        self.__update(new_data_raw)
        return self

    def __update(self, raw_data: dict) -> None:
        self.raw_data.update(raw_data)
        self.updated_fields.clear()  # Inorder to clear the updated field flags.

        self.event_id = raw_data.get('id', self.event_id)
        self._title = raw_data.get('summary', self._title)
        # self._etag = raw_data.get('etag', self._etag)
        # self._ical_uid = raw_data.get('iCalUID', self._ical_uid)

        if 'created' in raw_data.keys():  # The last part '.xxxZ' is for milliseconds
            self._created = datetime.strptime(raw_data['created'][:-5], '%Y-%m-%dT%H:%M:%S')
        if 'updated' in raw_data.keys():
            self._update = datetime.strptime(raw_data['updated'][:-5], '%Y-%m-%dT%H:%M:%S')

        if 'start' in raw_data.keys():
            if 'dateTime' in raw_data['start'].keys():
                self.start.datetime = datetime.strptime(raw_data['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
            self.start.timezone = raw_data['start'].get('timeZone', self.start.timezone)

        if 'end' in raw_data.keys():
            if 'dateTime' in raw_data['end'].keys():
                self.end.datetime = datetime.strptime(raw_data['end']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
            self.end.timezone = raw_data['end'].get('timeZone', self.end.timezone)
        self._end_time_unspecified = raw_data.get('endTimeUnspecified', self._end_time_unspecified)

        self._location = raw_data.get('location', self._location)
        self._description = raw_data.get('description', self._description)
        self._color_id = raw_data.get('colorId', self._color_id)

        # if 'creator' in raw_data.keys():
        #     self._created_by_self = raw_data['creator'].get('self', self._created_by_self)
        self._locked = raw_data.get('locked', self._locked)

        if 'reminders' in raw_data.keys():
            self._reminders_default = raw_data['reminders'].get('useDefault', self._reminders_default)
            self._reminders = raw_data['reminders'].get('overrides', self._reminders)

        # Custom properties
        if 'extendedProperties' in raw_data.keys():
            if 'private' in raw_data['extendedProperties']:
                self.next_event_ref.calendar_id = raw_data['extendedProperties']['private'] \
                    .get('tripperNextEvent_CalendarID', self.next_event_ref.calendar_id)
                self.next_event_ref.event_id = raw_data['extendedProperties']['private'] \
                    .get('tripperNextEvent_EventID', self.next_event_ref.event_id)

                self.prev_event_ref.calendar_id = raw_data['extendedProperties']['private'] \
                    .get('tripperPrevEvent_CalendarID', self.prev_event_ref.calendar_id)
                self.prev_event_ref.event_id = raw_data['extendedProperties']['private'] \
                    .get('tripperPrevEvent_EventID', self.prev_event_ref.event_id)
