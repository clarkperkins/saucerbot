# -*- coding: utf-8 -*-
import asyncio
import os
import uuid
from collections import defaultdict

import discord.ext.test as dpytest
import pytest
import pytest_asyncio

# The PostgreSQL major this project targets, and what the tests run against by
# default. Deliberately not Renovate-managed: it is a standing choice rather
# than an available version, so a bot has nothing useful to say about it and it
# moves by hand.
POSTGRES_DEFAULT = 18

# The newest PostgreSQL this project means to support. Renovate keeps it
# current through the custom manager keyed on the comment below, so a new major
# turns up as a failing test rather than a surprise later.
# renovate: datasource=docker depName=postgres
POSTGRES_CEILING = 18


def _postgres_majors() -> list[int]:
    """
    The PostgreSQL majors to run the database tests against.

    There is no SQLite option. The suite only ever talks to the engine this
    project actually uses, so the only question is which majors.

    TEST_POSTGRES_MAJORS unset  POSTGRES_DEFAULT on its own -- one container,
                                running the targeted major.
    TEST_POSTGRES_MAJORS=all    every major from Django's own
                                minimum_database_version up to
                                POSTGRES_CEILING. CI sets this, to cover the
                                whole supported range; the floor comes from
                                Django so it follows a framework upgrade with
                                no pin to maintain.
    TEST_POSTGRES_MAJORS=15,18  exactly those, for reproducing one CI leg.
                                An explicit list bypasses the checks below --
                                it is an override, so it is taken at its word.
    """
    from django.db.backends.postgresql.features import DatabaseFeatures

    floor = DatabaseFeatures.minimum_database_version[0]

    if floor > POSTGRES_CEILING:
        raise ValueError(
            f"Django's minimum PostgreSQL is {floor}, above POSTGRES_CEILING "
            f"({POSTGRES_CEILING}) in tests/conftest.py. Raise the ceiling."
        )

    requested = os.environ.get("TEST_POSTGRES_MAJORS", "").strip()

    if requested == "all":
        return list(range(floor, POSTGRES_CEILING + 1))

    if requested:
        return [int(major) for major in requested.replace(",", " ").split()]

    # Django refuses to connect below its own minimum, so this combination is
    # not a test problem to work around: the framework in the lockfile cannot
    # run against the major this project targets. Worth saying out loud,
    # because the alternative is finding out from a NotSupportedError in CI --
    # which is exactly how the Django 6.1 upgrade went.
    if POSTGRES_DEFAULT < floor:
        raise ValueError(
            f"Django needs PostgreSQL {floor} or newer, but POSTGRES_DEFAULT "
            f"is {POSTGRES_DEFAULT}: this Django version cannot run against "
            "the targeted major. Raise POSTGRES_DEFAULT once that is possible, "
            f"or use TEST_POSTGRES_MAJORS=all to test against "
            f"{floor}-{POSTGRES_CEILING} meanwhile."
        )

    if POSTGRES_DEFAULT > POSTGRES_CEILING:
        raise ValueError(
            f"POSTGRES_DEFAULT ({POSTGRES_DEFAULT}) is newer than "
            f"POSTGRES_CEILING ({POSTGRES_CEILING}) in tests/conftest.py. "
            "Raise the ceiling to match."
        )

    return [POSTGRES_DEFAULT]


# Resolved once at collection so it can parametrise the fixtures below.
_POSTGRES_MAJORS: list[int] = _postgres_majors()


# Everything pytest-django offers for asking for a database. A test either
# names one of these fixtures or carries the django_db marker; the marker is
# not visible in metafunc.fixturenames because pytest-django pulls the helper
# in dynamically, so both have to be checked.
_DB_FIXTURES = frozenset(
    {
        "db",
        "transactional_db",
        "django_db_setup",
        "django_db_reset_sequences",
        "django_db_serialized_rollback",
    }
)


def pytest_generate_tests(metafunc):
    """
    Parametrise the database tests over the requested PostgreSQL majors.

    This has to go through pytest_generate_tests rather than params= on the
    fixture itself. pytest-django pulls its database fixtures in dynamically
    with getfixturevalue, and a param cannot be supplied retroactively to a
    dynamic request -- parametrising the fixture directly fails every database
    test with "the requested fixture has no parameter defined for test".
    Declaring the parametrisation on the test fixes that, and only doing it for
    the tests that want a database keeps the half of the suite that never
    touches one from running once per version.
    """
    wants_db = bool(_DB_FIXTURES.intersection(metafunc.fixturenames)) or any(
        metafunc.definition.iter_markers("django_db")
    )

    if wants_db:
        metafunc.parametrize(
            "postgres_major",
            _POSTGRES_MAJORS,
            indirect=True,
            scope="session",
            ids=[f"pg{major}" for major in _POSTGRES_MAJORS],
        )


@pytest.fixture(scope="session")
def postgres_major(request) -> int:
    # Only the database tests are parametrised, so the rest see the first
    # major rather than a param. They never reach a database either way.
    return getattr(request, "param", _POSTGRES_MAJORS[0])


@pytest.fixture(scope="session", autouse=True)
def _postgres_leg(postgres_major) -> int:
    """
    Put postgres_major in every test's fixture closure.

    indirect=True refuses to parametrise a fixture the test does not already
    request, and the database tests reach theirs through pytest-django's
    dynamic lookups rather than by naming them. Autouse is the supported way
    to get it into the closure; it is session scoped and returns immediately.
    """
    return postgres_major


@pytest.fixture(scope="session")
def postgres_container(postgres_major):
    from testcontainers.community.postgres import PostgresContainer

    # driver=None gives a bare postgresql:// URL. The default would hand back
    # postgresql+psycopg2://, which dj_database_url does not want and which
    # names the wrong driver -- this project is on psycopg 3.
    with PostgresContainer(f"postgres:{postgres_major}", driver=None) as container:
        yield container


@pytest.fixture(scope="session")
def django_db_modify_db_settings(
    postgres_major, postgres_container, django_db_blocker
) -> None:
    """
    Repoint Django at this leg's container before the test database is built.

    This overrides pytest-django's fixture of the same name, which django_db_setup
    depends on, so pytest-django still owns creating and tearing down the test
    database and --reuse-db/--no-migrations keep working.

    Rewriting settings.DATABASES is not enough on its own: Django's
    ConnectionHandler caches the configuration and the built DatabaseWrapper,
    so the suite carries on using whatever it resolved first. That is
    pytest-django issue #643, and it fails silently -- the tests pass against
    the wrong database. Hence the eviction below, and the assertion that the
    server really is the major this leg asked for, so a future Django release
    breaking the eviction is a loud failure rather than several green legs that
    all tested the same version.
    """
    import dj_database_url
    from asgiref.local import Local
    from django.conf import settings
    from django.db import connection, connections

    connections.close_all()

    # Swapping the whole Local out rather than deleting each alias: the
    # wrappers live in a Local(thread_critical=True), so a del here would only
    # reach the main thread's. The async tests reach the ORM through
    # sync_to_async, whose worker thread keeps a wrapper of its own, and on the
    # next leg that one still points at the container that just stopped.
    connections._connections = Local(  # pylint: disable=protected-access
        connections.thread_critical
    )

    # settings is a cached_property over _settings, so both have to go for the
    # handler to re-read DATABASES.
    connections.__dict__.pop("settings", None)
    connections._settings = None  # pylint: disable=protected-access

    settings.DATABASES["default"] = dj_database_url.parse(
        postgres_container.get_connection_url(),
        conn_max_age=600,
        conn_health_checks=True,
    )

    with django_db_blocker.unblock():
        served = connection.cursor().connection.info.server_version // 10000
        connection.close()

    assert served == postgres_major, (
        f"asked for PostgreSQL {postgres_major} but connected to {served}; "
        "the connection-cache eviction above is no longer working"
    )


@pytest.fixture(name="gmi")
def gmi(monkeypatch):
    from lowerpines.endpoints.bot import Bot
    from lowerpines.endpoints.group import Group, GroupMessagesManager
    from lowerpines.endpoints.message import Message
    from lowerpines.endpoints.user import User

    global_users = {}
    global_bots = {}
    global_groups = {}
    global_messages = defaultdict(list)

    class TestUser(User):
        def save(self):
            global_users[self.gmi.access_token] = self

        def refresh(self):
            if self.gmi.access_token in global_users:
                self._refresh_from_other(global_users[self.gmi.access_token])

    class TestGroup(Group):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.messages = TestGroupMessageManager(self)

        def save(self):
            if not self.group_id:
                self.group_id = str(uuid.uuid4()).replace("-", "")
            global_groups[self.group_id] = self

        def delete(self):
            if self.group_id in global_groups:
                del global_groups[self.group_id]

        def refresh(self):
            pass

        def add_member(self, member):
            self.members.append(member)

        @staticmethod
        def get_all(gmi):
            return global_groups.values()

        @staticmethod
        def get(gmi, group_id):
            return global_groups.get(group_id)

    class TestGroupMessageManager(GroupMessagesManager):
        @property
        def count(self):
            return len(global_messages[self.group.group_id])

        def all(self):
            return global_messages[self.group.group_id]

        def recent(self, count=100):
            return global_messages[self.group.group_id][-count:]

        def before(self, message, count=100):
            group_messages = global_messages[self.group.group_id]
            idx = group_messages.index(message)
            return group_messages[max(idx - count, 0) : idx]

        def since(self, message, count=100):
            group_messages = global_messages[self.group.group_id]
            idx = group_messages.index(message)
            return group_messages[idx : min(idx + count, len(group_messages))]

    class TestMessage(Message):
        def save(self):
            if self.message_id:
                from lowerpines.exceptions import InvalidOperationException

                raise InvalidOperationException(
                    "You cannot change a message that has already been sent"
                )
            else:
                self.message_id = str(uuid.uuid4()).replace("-", "")
                global_messages[self.group_id].append(self)

        def refresh(self):
            pass

        def like(self):
            if self.favorited_by is None:
                self.favorited_by = []
            self.favorited_by.append(self.gmi.user.get().user_id)

        def like_as(self, user_id):
            if self.favorited_by is None:
                self.favorited_by = []
            self.favorited_by.append(user_id)

        @classmethod
        def from_json(cls, gmi, json_dict, *args):
            return Message.from_json(gmi, json_dict, *args)

    class TestBot(Bot):
        def save(self):
            if self.bot_id is None:
                self.bot_id = str(uuid.uuid4()).replace("-", "")

            global_bots[self.bot_id] = self

        def delete(self):
            if self.bot_id in global_bots:
                del global_bots[self.bot_id]

        def post(self, text):
            from lowerpines.message import smart_split_complex_message

            text, attachments = smart_split_complex_message(text)
            message = TestMessage(
                self.gmi, group_id=self.group_id, text=text, attachments=attachments
            )
            message.favorited_by = []
            message.name = self.name
            message.save()

        @staticmethod
        def get_all(gmi):
            return global_bots.values()

    monkeypatch.setattr("lowerpines.endpoints.user.User", TestUser)
    monkeypatch.setattr("lowerpines.endpoints.group.Group", TestGroup)
    monkeypatch.setattr("lowerpines.endpoints.message.Message", TestMessage)
    monkeypatch.setattr("lowerpines.endpoints.bot.Bot", TestBot)
    monkeypatch.setattr("lowerpines.user.User", TestUser)
    monkeypatch.setattr("lowerpines.group.Group", TestGroup)
    monkeypatch.setattr("lowerpines.bot.Bot", TestBot)

    from lowerpines.gmi import GMI

    return GMI("faketoken")


@pytest.fixture(name="bot")
def setup_bot(db, gmi, monkeypatch):
    """
    Create a bot for saucerbot tests
    """
    monkeypatch.setattr("saucerbot.groupme.models.get_gmi", lambda a: gmi)

    from lowerpines.group import Group

    from saucerbot.groupme.models import Bot, User

    user = User.objects.create(access_token="123456", user_id="123456")

    group = Group(user.gmi, name="test group")
    group.save()

    bot = Bot.objects.create(
        owner=user, group=group, name="saucerbot", slug="saucerbot"
    )

    return bot


@pytest_asyncio.fixture(name="discord_client")
async def setup_discord_client():
    """
    dpytest needs to be configured from inside the loop the test runs on, so
    this has to be an async fixture.
    """
    from saucerbot.discord.client import SaucerbotClient

    client = SaucerbotClient()
    client.loop = asyncio.get_running_loop()

    dpytest.configure(client)

    yield client

    await dpytest.empty_queue()
