from app.system import is_windows_admin


def test_is_windows_admin_returns_boolean():
    assert isinstance(is_windows_admin(), bool)
