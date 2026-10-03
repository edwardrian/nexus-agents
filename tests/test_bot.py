from app.bot import handlers
from app.bot.handlers import is_allowed, split_message


def test_split_message_short():
    assert split_message("hola") == ["hola"]


def test_split_message_long():
    chunks = split_message("a" * 5000)
    assert [len(c) for c in chunks] == [4096, 904]


def test_is_allowed_without_restriction(monkeypatch):
    monkeypatch.setattr(handlers.settings, "TELEGRAM_ALLOWED_USER_IDS", "")
    assert is_allowed(123)


def test_is_allowed_with_restriction(monkeypatch):
    monkeypatch.setattr(handlers.settings, "TELEGRAM_ALLOWED_USER_IDS", "111, 222")
    assert is_allowed(111)
    assert is_allowed(222)
    assert not is_allowed(333)
