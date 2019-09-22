# -*- coding: utf-8 -*-

import logging

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_login_redirect_no_session():
    from saucerbot.groupme.views import LoginRedirectView

    fake_request = HttpRequest()
    fake_request.session = SessionStore()

    v = LoginRedirectView()
    v.setup(fake_request)

    r = v.get(fake_request)

    assert r.status_code == 302
    assert r.url.startswith('https://oauth.groupme.com')


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
    assert not r.url.startswith('https://oauth.groupme.com')
    assert '/groupme/api/bots/' in r.url


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
    u.user_id = '123456'
    u.save()

    from saucerbot.groupme.views import OAuthView, SESSION_KEY

    fake_request = HttpRequest()
    fake_request.session = SessionStore()
    fake_request.GET['access_token'] = 'abcdef'

    v = OAuthView()
    v.setup(fake_request)

    r = v.get(fake_request)

    assert r.status_code == 302
    assert not r.url.startswith('https://oauth.groupme.com')
    assert '/groupme/api/bots/' in r.url

    assert SESSION_KEY in fake_request.session
