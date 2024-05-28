from project.user import User


def test_user():
    user = User("42069")
    user.data('home', '51.999083, 4.373599')
    assert user.data('*')['home']['address'] == 'Mekelweg 4, 2628 CD Delft, Netherlands'
