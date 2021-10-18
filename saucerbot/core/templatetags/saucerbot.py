# -*- coding: utf-8 -*-

from typing import Optional

from django import template
from django.http import HttpRequest
from django.urls import NoReverseMatch, reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()


def _get_namespace(request: HttpRequest) -> Optional[str]:
    if request.path.startswith("/api/discord"):
        return "discord"
    elif request.path.startswith("/api/groupme"):
        return "groupme"
    else:
        return None


@register.simple_tag
def optional_login(request: HttpRequest) -> str:
    """
    Include a login snippet if REST framework's login view is in the URL conf.
    """
    namespace = _get_namespace(request)

    if namespace is None:
        return ""

    try:
        login_url = reverse(f"{namespace}:login")
    except NoReverseMatch:
        return ""

    snippet = "<li><a href='{href}?next={next}'>Log in</a></li>"
    snippet = format_html(snippet, href=login_url, next=escape(request.path))

    return mark_safe(snippet)


@register.simple_tag
def optional_logout(request: HttpRequest, user) -> str:
    """
    Include a logout snippet if REST framework's logout view is in the URL conf.
    """
    namespace = _get_namespace(request)

    if namespace is None:
        return ""

    snippet: str

    try:
        logout_url = reverse(f"{namespace}:logout")
    except NoReverseMatch:
        snippet = format_html('<li class="navbar-text">{user}</li>', user=escape(user))
        return mark_safe(snippet)

    snippet = """<li class="dropdown">
        <a href="#" class="dropdown-toggle" data-toggle="dropdown">
            {user}
            <b class="caret"></b>
        </a>
        <ul class="dropdown-menu">
            <li><a href='{href}?next={next}'>Log out</a></li>
        </ul>
    </li>"""
    snippet = format_html(
        snippet, user=escape(user), href=logout_url, next=escape(request.path)
    )

    return mark_safe(snippet)
