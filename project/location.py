import json

import googlemaps


def create_gmaps_client() -> googlemaps.Client:
    key = 'AIzaSyBcHrK9tGML3FLkjOkXl58Bakhy2H7v8yo'
    return googlemaps.Client(key=key)


GMAPS: googlemaps.Client = create_gmaps_client()
PAST_REQUESTS: dict[(str, str, str), dict[str]] = {}


def location_data(location: str) -> dict[list | str]:
    """returns locationData from Google Maps for input coordinates/address."""
    global GMAPS
    if GMAPS is None:
        GMAPS = create_gmaps_client()
    data = GMAPS.geocode(location, region="NL")
    coordinates: list[float] = [float(data[0]['geometry']['location']['lat']),
                                float(data[0]['geometry']['location']['lng'])]
    location_dict: dict[list | str] = {'coordinates': coordinates, 'address': str(data[0]['formatted_address'])}
    return location_dict


def tu_building_code(code: str) -> str | None:
    """Get address of TU buildings."""
    if code is None:
        return None
    input_list = code.lower().split('-')
    try:
        # print(__file__[:-25])
        with open(".\\data\\tu_codes.json", 'r', encoding='utf-8') as file:
            code_dictionary = json.load(file)
        address = code_dictionary[input_list[0]]
    except KeyError:
        return code
    else:
        return address


def get_parsed_direction_results(origin: str, destination: str, mode: str,
                                 departure_time=None, arrival_time=None) -> dict | str:
    global GMAPS, PAST_REQUESTS
    if PAST_REQUESTS is None:
        PAST_REQUESTS = {}
    if GMAPS is None:
        GMAPS = create_gmaps_client()
    if (origin, destination, mode) in PAST_REQUESTS:
        return PAST_REQUESTS[(origin, destination, mode)]

    directions_result = GMAPS.distance_matrix(origin, destination, mode=mode, departure_time=departure_time,
                                              arrival_time=arrival_time, region="NL")
    if directions_result['rows'][0]['elements'][0]['status'] == 'NOT_FOUND':
        return 'Not found'  # NOTE: This is probably fine

    if directions_result.get('status', 'NOT OK') != 'OK':
        raise ConnectionError("Maps API did not return OK")
    try:
        result = {
            'origin': directions_result['origin_addresses'][0],
            'destination': directions_result['destination_addresses'][0],
            'mode': mode,
            'distance': int(directions_result['rows'][0]['elements'][0]['distance']['value']),
            'duration': int(directions_result['rows'][0]['elements'][0]['duration']['value'])
        }
    except KeyError:
        print('Address is not valid or same as home address')
        result = {
            'origin': directions_result['origin_addresses'][0],
            'destination': directions_result['destination_addresses'][0],
            'mode': mode,
            'distance': 0,
            'duration': 30
        }
    PAST_REQUESTS[(result['origin'], result['destination'], result['mode'])] = result
    return result


def maps(origin: str, destination: str, mode: str | list[str], departure_time=None, arrival_time=None) -> dict | str:
    """Uses GMaps to calculate distance and time travelled from a start and finish
        distance returned in meters, duration in seconds, addresses are also returned for validation.
        Mode of transport accepts one string or a list of strings; transit, bicycling, driving, walking"""

    result = {}
    # directions_result = {}

    if isinstance(mode, str):
        result[mode] = get_parsed_direction_results(origin, destination, mode,
                                                    departure_time=departure_time,
                                                    arrival_time=arrival_time)
    else:
        for transport_mode in mode:
            result[transport_mode] = get_parsed_direction_results(origin, destination, transport_mode,
                                                                  departure_time=departure_time,
                                                                  arrival_time=arrival_time)
            # print(result[transport_mode])
    return result
