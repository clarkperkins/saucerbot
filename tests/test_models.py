# -*- coding: utf-8 -*-

import logging

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest
from lowerpines.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_get_user_no_session():
    from saucerbot.groupme.models import get_user

    fake_request = HttpRequest()
    fake_request.session = SessionStore()

    u = get_user(fake_request)

    assert u is None


@pytest.mark.django_db
def test_get_user_invalid_id():
    from saucerbot.groupme.models import SESSION_KEY, get_user

    fake_request = HttpRequest()
    fake_request.session = SessionStore()
    fake_request.session[SESSION_KEY] = 182

    u = get_user(fake_request)

    assert u is None


@pytest.mark.django_db
def test_get_user_valid():
    from saucerbot.groupme.models import SESSION_KEY, User, get_user

    user = User.objects.create(access_token="123456", user_id="123456")

    fake_request = HttpRequest()
    fake_request.session = SessionStore()
    fake_request.session[SESSION_KEY] = user.pk

    u = get_user(fake_request)

    assert u is not None
    assert u.access_token == "123456"
    assert u.user_id == "123456"

    # Make sure it looks correct
    assert u.is_active
    assert not u.is_staff
    assert not u.is_superuser
    assert not u.is_anonymous
    assert u.is_authenticated
    assert u.groups.count() == 0
    assert u.user_permissions.count() == 0


@pytest.mark.django_db
def test_new_user_valid(gmi):
    from saucerbot.groupme.models import SESSION_KEY, get_gmi, new_user

    # pre-create the user
    gmi = get_gmi("abcdef")
    user = gmi.user.get()
    user.user_id = "abcdef"
    user.save()

    fake_request = HttpRequest()
    fake_request.session = SessionStore()

    new_user(fake_request, "abcdef")

    assert SESSION_KEY in fake_request.session
    assert fake_request.session[SESSION_KEY] is not None


@pytest.mark.django_db
def test_new_user_invalid(monkeypatch):
    from saucerbot.core.models import InvalidUser
    from saucerbot.groupme.models import (
        SESSION_KEY,
        get_gmi,
        new_user,
    )

    gmi = get_gmi("abcdef")

    # Make sure the gmi raises the expected exception
    def fake_get():
        raise UnauthorizedException()

    monkeypatch.setattr(gmi.user, "get", fake_get)

    fake_request = HttpRequest()
    fake_request.session = SessionStore()

    with pytest.raises(InvalidUser):
        new_user(fake_request, "abcdef")

    assert SESSION_KEY not in fake_request.session
