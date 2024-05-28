from datetime import datetime

from project.location import PAST_REQUESTS
from project.tripper import mode_selector
from project.test.maps_mocker import get_maps_response
from project.user import User


def test_mode_selector():
    # 1. Mock the requests by filling the cache with known values
    global PAST_REQUESTS
    # Need to verify that PAST_REQUEST is actually a dict or at least not None
    if PAST_REQUESTS is None:
        PAST_REQUESTS = {}
    routes: dict = get_maps_response()
    for mode, route in routes.items():
        PAST_REQUESTS[(route['origin'], route['destination'], mode)] = {
            'origin': route['origin'],
            'destination': route['destination'],
            'mode': mode,
            'distance': route['distance'],
            'duration': route['duration']
        }

    # 2. Stating the expected result
    expected = {'origin': 'Station Delft, 2611 AC Delft, Netherlands',
                'destination': 'Stieltjesweg 682, 2628 CK Delft, Netherlands',
                'distance': 2121,
                'duration': 418 + 90,  # Added the duration increase for getting to your bike
                'mode': 'bicycling'}

    # 3. Testing
    actual = mode_selector(routes['bicycling']['origin'], routes['bicycling']['destination'], datetime.now(),
                           User("test_user"))
    assert expected == actual
