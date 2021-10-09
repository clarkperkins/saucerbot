# -*- coding: utf-8 -*-

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest


@pytest.mark.django_db
def test_login_redirect_no_session():
    from saucerbot.groupme.views import LoginRedirectView

    fake_request = HttpRequest()
    fake_request.session = SessionStore()

    v = LoginRedirectView()
    v.setup(fake_request)

    r = v.get(fake_request)

    assert r.status_code == 302
    assert r.url.startswith("https://oauth.groupme.com")


@pytest.mark.django_db
def test_login_redirect_with_session():
    from saucerbot.groupme.views import LoginRedirectView, SESSION_KEY

    fake_request = HttpRequest()
    fake_request.session = SessionStore()
    fake_request.session[SESSION_KEY] = 123

    v = LoginRedirectView()
    v.setup(fake_request)

    r = v.get(fake_request)

    assert r.status_code == 302
    assert not r.url.startswith("https://oauth.groupme.com")
    assert "/api/groupme/" in r.url


@pytest.mark.django_db
def test_oauth_missing_token():
    from saucerbot.groupme.views import OAuthView, InvalidGroupMeUser

    fake_request = HttpRequest()
    fake_request.session = SessionStore()

    v = OAuthView()
    v.setup(fake_request)

    with pytest.raises(InvalidGroupMeUser):
        v.get(fake_request)


@pytest.mark.django_db
def test_oauth_with_token(gmi):
    u = gmi.user.get()
    u.user_id = "123456"
    u.save()

    from saucerbot.groupme.views import OAuthView, SESSION_KEY

    fake_request = HttpRequest()
    fake_request.session = SessionStore()
    fake_request.GET["access_token"] = "abcdef"

    v = OAuthView()
    v.setup(fake_request)

    r = v.get(fake_request)

    assert r.status_code == 302
    assert not r.url.startswith("https://oauth.groupme.com")
    assert "/api/groupme/" in r.url

    assert SESSION_KEY in fake_request.session


@pytest.mark.django_db
def test_bot_view_create(monkeypatch, gmi, client):
    monkeypatch.setattr("saucerbot.groupme.models.get_gmi", lambda a: gmi)

    u = gmi.user.get()
    u.user_id = "abcdef"
    u.save()

    # login first
    client.get("/groupme/oauth/?access_token=faketoken")

    from lowerpines.endpoints.group import Group

    group = Group(gmi, name="view test group")
    group.save()

    data = {
        "name": "test",
        "slug": "floop",
        "group": group.group_id,
        "handlers": ["system_messages"],
    }

    resp = client.post("/api/groupme/bots/", content_type="application/json", data=data)

    assert resp.status_code == 201

    from saucerbot.groupme.models import Bot

    new_bot = Bot.objects.get(slug="floop")
    gmi_bot = gmi.bots.get(name="test")

    assert new_bot.name == "test"
    assert new_bot.slug == "floop"
    assert new_bot.bot_id == gmi_bot.bot_id
    assert new_bot.group_id == group.group_id
    assert new_bot.handlers.count() == 1
    assert gmi_bot.callback_url == "https://localhost/api/groupme/bots/floop/callback/"
    assert gmi_bot.name == "test"


@pytest.mark.django_db
def test_bot_view_update(monkeypatch, gmi, client):
    monkeypatch.setattr("saucerbot.groupme.models.get_gmi", lambda a: gmi)

    u = gmi.user.get()
    u.user_id = "abcdef"
    u.save()

    # login first
    client.get("/groupme/oauth/?access_token=faketoken")

    from lowerpines.endpoints.group import Group
    from lowerpines.exceptions import NoneFoundException
    from saucerbot.groupme.models import Bot

    group = Group(gmi, name="view test group")
    group.save()

    data = {
        "name": "test",
        "slug": "floop",
        "group": group.group_id,
        "handlers": ["system_messages"],
    }

    resp = client.post("/api/groupme/bots/", content_type="application/json", data=data)

    assert resp.status_code == 201

    new_bot = Bot.objects.get(slug="floop")
    gmi_bot = gmi.bots.get(name="test")

    assert new_bot.name == "test"
    assert new_bot.slug == "floop"
    assert new_bot.bot_id == gmi_bot.bot_id
    assert new_bot.group_id == group.group_id
    assert new_bot.handlers.count() == 1
    assert gmi_bot.callback_url == "https://localhost/api/groupme/bots/floop/callback/"
    assert gmi_bot.name == "test"

    update_data = {"name": "new test", "slug": "floop2", "handlers": ["whoami"]}

    resp = client.patch(
        "/api/groupme/bots/floop/", content_type="application/json", data=update_data
    )

    assert resp.status_code == 200

    updated_bot = Bot.objects.get(slug="floop2")

    assert updated_bot.name == "new test"
    assert updated_bot.slug == "floop2"
    assert updated_bot.bot_id == gmi_bot.bot_id
    assert updated_bot.group_id == group.group_id
    assert updated_bot.handlers.count() == 1

    # The gmi bot got fixed too
    gmi_bot = gmi.bots.get(name="new test")
    assert gmi_bot.callback_url == "https://localhost/api/groupme/bots/floop2/callback/"
    assert gmi_bot.name == "new test"

    # The old bot is gone
    with pytest.raises(NoneFoundException):
        gmi.bots.get(name="test")


@pytest.mark.django_db
def test_bot_view_delete(monkeypatch, gmi, client):
    monkeypatch.setattr("saucerbot.groupme.models.get_gmi", lambda a: gmi)

    u = gmi.user.get()
    u.user_id = "abcdef"
    u.save()

    # login first
    client.get("/groupme/oauth/?access_token=faketoken")

    from lowerpines.endpoints.group import Group
    from lowerpines.exceptions import NoneFoundException
    from saucerbot.groupme.models import Bot

    group = Group(gmi, name="view test group")
    group.save()

    data = {
        "name": "test",
        "slug": "floop",
        "group": group.group_id,
        "handlers": ["system_messages"],
    }

    resp = client.post("/api/groupme/bots/", content_type="application/json", data=data)

    assert resp.status_code == 201

    new_bot = Bot.objects.get(slug="floop")
    gmi_bot = gmi.bots.get(name="test")

    assert new_bot.name == "test"
    assert new_bot.slug == "floop"
    assert new_bot.bot_id == gmi_bot.bot_id
    assert new_bot.group_id == group.group_id
    assert new_bot.handlers.count() == 1
    assert gmi_bot.callback_url == "https://localhost/api/groupme/bots/floop/callback/"
    assert gmi_bot.name == "test"

    resp = client.delete("/api/groupme/bots/floop/")

    assert resp.status_code == 204

    # The db bot is gone
    with pytest.raises(Bot.DoesNotExist):
        Bot.objects.get(slug="floop")

    # The groupme bot is gone too
    with pytest.raises(NoneFoundException):
        gmi.bots.get(name="test")
