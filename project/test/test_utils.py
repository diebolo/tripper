from project.utils import color_id, create_nested_dict

# tests maps api, cal api, changeHome, getUser


def test_create_nested_dict_new():
    mydict = {
        'key1': 'value1',
        'key2': 'value'
    }
    mydict = create_nested_dict(mydict, 'nested_dict')
    assert mydict == {
        'key1': 'value1',
        'key2': 'value',
        'nested_dict': {}
    }


def test_create_nested_dict_preex():
    mydict = {
        'key1': 'value1',
        'key2': 'value',
        'nested_dict': {'some_value': 1}
    }
    mydict = create_nested_dict(mydict, 'nested_dict')
    assert mydict == {
        'key1': 'value1',
        'key2': 'value',
        'nested_dict': {'some_value': 1}
    }


def test_color_id():
    # Testing valid travel methods
    assert color_id('walking') == 4
    assert color_id('bicycling') == 2
    assert color_id('transit') == 5
    assert color_id('driving') == 10
    # An invalid travel method
    assert color_id('aeroplane') == 1
