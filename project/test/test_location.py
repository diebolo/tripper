from project.location import maps, PAST_REQUESTS


def test_maps():
    global PAST_REQUESTS
    if PAST_REQUESTS is None:
        PAST_REQUESTS = {}
    PAST_REQUESTS[('Station Delft, 2611 AC Delft, Netherlands',
                  'Oude Delft 91T, 2611 BD Delft, Netherlands', 'bicycling')] = {
        'origin': 'Station Delft, 2611 AC Delft, Netherlands',
        'destination': 'Oude Delft 91T, 2611 BD Delft, Netherlands',
        'mode': 'bicycling', 'distance': 271, 'duration': 45
    }
    PAST_REQUESTS[('Station Delft, 2611 AC Delft, Netherlands',
                  'Oude Delft 91T, 2611 BD Delft, Netherlands', 'walking')] = {
        'origin': 'Station Delft, 2611 AC Delft, Netherlands',
        'destination': 'Oude Delft 91T, 2611 BD Delft, Netherlands',
        'mode': 'walking', 'distance': 271, 'duration': 196
    }

    # PAST_REQUEST[()]
    data = maps('Station Delft', 'Oude Delft 91T', ['bicycling', 'walking'])
    assert data['bicycling']['distance'] == 271
