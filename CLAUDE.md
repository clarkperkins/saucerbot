# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Saucerbot is a multi-platform chat bot that works with both GroupMe and Discord. It responds to messages using a handler-based architecture with regex pattern matching.

## Public Repository

This repository is public. Keep details of deployed environments out of it —
hostnames, addresses, log queries, or output copied from a running service — in
code, commit messages, PR bodies and comments alike. A version pinned in a file
is fine.

## Development Setup

### Environment Variables

Set `DJANGO_ENV` before running any commands:
- `DJANGO_ENV=local` - For local development
- `DJANGO_ENV=test` - For running tests
- `DJANGO_ENV=development` - For Django management commands (default in manage.py)

Valid environments are: `test`, `local`, `development`, `staging`, `production`, `build`

### Poetry & Python

This project uses Poetry 2.4+ (enforced by `requires-poetry`, needed for `solver.min-release-age` in `poetry.toml`) and requires Python 3.13+. An `.tool-versions` file is provided for asdf users.

Install dependencies:
```bash
poetry install
```

### Upgrading Dependencies

`poetry update` only moves within the constraints in `pyproject.toml`; anything
pinned there (django, djangorestframework, pylint) needs the constraint edited
first. For a major framework upgrade, two checks are worth the few minutes:

- **Diff a throwaway project against ours.** Run `django-admin startproject` on
  both the old and new version and diff the two generated trees whole — every
  file and the layout itself, not a fixed list, since a new version can add or
  move one. Then compare what changed against this repo. Settings that quietly
  stopped being read don't warn about anything, so this is the only reliable
  way to spot them.
- **The minimum database version takes care of itself.** CI reads Django's
  `minimum_database_version` and runs the suite from there up to
  `POSTGRES_CEILING`, so a Django upgrade that raises the floor is covered
  without touching any pin. Check the release notes for a new minimum anyway,
  since the database has to clear the new floor before the upgrade can ship —
  and if that floor is above `POSTGRES_CEILING`, the suite says so and stops
  rather than running nothing.

## Common Commands

### Running Tests

```bash
# Run tests with coverage (XML output for CI)
DJANGO_ENV=test make test

# Run tests with HTML coverage report and open it
DJANGO_ENV=test make cov

# Run specific test file or test
DJANGO_ENV=test poetry run pytest tests/test_handlers.py
DJANGO_ENV=test poetry run pytest tests/test_handlers.py::test_specific_function
```

### Code Quality

```bash
# Format code (runs isort + black)
make format

# Check code quality (runs isort, black, pylint, mypy)
make check

# Run all CI checks (format checks + tests)
DJANGO_ENV=test make ci
```

Before pushing code, always run:
```bash
DJANGO_ENV=test make ci
```

### Django Management Commands

```bash
# Run Django development server
python manage.py runserver

# Collect static files
python manage.py collectstatic

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Discord Bot

```bash
# Run the Discord bot worker
poetry run saucerbot discord run

# Sync Discord slash commands globally
poetry run saucerbot discord sync-global-commands
```

### Docker

```bash
# Build Docker image
make build

# Run with docker-compose (includes PostgreSQL)
docker-compose up
```

## Architecture

### Handler System

The handler system is the core of how the bot responds to messages. Handlers are decorated functions that register themselves with a global `HandlerRegistry` in `saucerbot/handlers/__init__.py`.

**Key concepts:**
- Handlers use the `@registry.handler()` decorator with regex patterns to match message content
- Handlers can specify which platforms they work on via the `platforms` parameter (defaults to both `discord` and `groupme`)
- Handlers receive a `BotContext` (for posting responses) and optionally a `Message` object and regex `match` object
- The registry checks function signatures and only passes parameters the handler needs
- Handlers with `on_by_default=True` are enabled automatically; others must be explicitly enabled
- Handlers with `always_run=True` will run even after another handler has already matched

**Handler decorator parameters:**
- `regex`: String or list of regex patterns to match against message content
- `name`: Handler name (defaults to function name)
- `case_sensitive`: Whether regex matching is case-sensitive (default: False)
- `platforms`: Set of platforms this handler works on (default: both "discord" and "groupme")
- `on_by_default`: Whether this handler is enabled by default (default: False)
- `always_run`: Whether to run this handler even if another has already matched (default: False)

**Handler locations:**
- `saucerbot/handlers/general.py` - General handlers that work on all platforms
- `saucerbot/handlers/saucer.py` - Saucer-specific handlers
- `saucerbot/handlers/vandy.py` - Vanderbilt-specific handlers
- `saucerbot/groupme/handlers.py` - GroupMe-specific handlers

**Example handler:**
```python
from saucerbot.handlers import BotContext, Message, registry

@registry.handler(r"hello", on_by_default=True)
def greet(context: BotContext, message: Message):
    """Responds to greetings"""
    context.post(f"Hello, {message.user_name}!")
```

### Platform Abstraction

The bot abstracts platform-specific details through these interfaces:
- `BotContext` - Abstract class with `post()` method for sending messages
- `Message` - Abstract class providing `user_id`, `user_name`, `content`, and `created_at` properties

**Platform implementations:**
- GroupMe: `GroupMeBotContext` and `GroupMeMessage` in `saucerbot/groupme/models.py`
- Discord: Implementation in `saucerbot/discord/` module

### Django Apps Structure

- **core** - Base user models and shared authentication
- **groupme** - GroupMe integration (models, views, handlers, bot management)
- **discord** - Discord integration (client, commands, views)
- **api** - Appears to be minimal/unused
- **handlers** - Cross-platform message handlers
- **utils** - Utility functions and parsers (sports schedules, web scraping utilities)

### Settings Management

Settings use `django-split-settings` to organize configuration:
- `saucerbot/settings/base.py` - Base Django settings
- `saucerbot/settings/email.py` - Email configuration
- `saucerbot/settings/logging.py` - Logging configuration
- `saucerbot/settings/environments/{ENV}.py` - Environment-specific settings

The `DJANGO_ENV` environment variable selects which environment file to load.

### GroupMe Integration

GroupMe uses the `lowerpines` library for API interaction. Key models:
- `User` - Represents a GroupMe user with access token
- Bot management happens through Django models that wrap lowerpines objects
- Message handling flows through the handler registry

### Discord Integration

Discord uses `discord.py` v2.0. Entry point is the CLI command `saucerbot discord run` which starts the Discord client defined in `saucerbot/discord/client.py`.

## Testing

Tests are in the `tests/` directory and use pytest with these plugins:
- `pytest-django` - Django integration
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking utilities
- `dpytest` - Discord.py testing utilities

Tests must have `DJANGO_ENV=test` set.

**The tests always run against PostgreSQL**, in containers `tests/conftest.py`
starts with testcontainers. There is no SQLite option: the suite only ever
talks to the engine this project actually uses, so a database-specific bug
cannot hide until CI. **A running Docker daemon is therefore required to run the tests.**

`tests/conftest.py` carries two pinned majors, with different jobs:

- **`POSTGRES_DEFAULT`** — the major this project targets, and the default for
  a test run, so a plain `make test` exercises the one that matters most.
  Deliberately **not** Renovate-managed: it is a standing choice rather than an
  available version, so a bot has nothing useful to say about it and it moves by
  hand. It is not derivable from this repo either — `Chart.yaml` pins a chart
  version, not a server version.
- **`POSTGRES_CEILING`** — the newest major the project means to support.
  Renovate keeps it current through a custom manager keyed on the `# renovate:`
  comment above it, so a new PostgreSQL major arrives as a failing test rather
  than a surprise later.

**This is the only PostgreSQL version Renovate bumps, and it does so without
asking.** Every other one is held back on purpose: compose's tag is
`enabled: false` for majors (a bump makes an existing `dbdata` volume
unreadable), the chart's `postgresql` subchart needs dependency-dashboard
approval (a major there means a data migration), and `POSTGRES_DEFAULT`
carries no `# renovate:` marker at all, so Renovate cannot see it. The ceiling
is ungated by an explicit `dependencyDashboardApproval: false` rule rather than
by default, so a later blanket "hold postgres majors" rule can't quietly
swallow the one bump that is supposed to happen on its own. It opens a PR; it
does not automerge, so a major still gets a human look even when CI is green.

`TEST_POSTGRES_MAJORS` chooses what a given run covers:

- Unset (the usual local case) — `POSTGRES_DEFAULT`, on its own. One
  container.
- `all` — every major from Django's own `minimum_database_version` up to
  `POSTGRES_CEILING`, each in its own container. This is what CI sets, so the
  whole supported range is covered on every PR. The floor comes from Django
  rather than a pin, so it follows a framework upgrade on its own.
- `15,18` — exactly those majors, for reproducing one CI leg without paying for
  the rest. An explicit list is an override and skips the checks below.

Only the tests that actually want a database are multiplied out (about half the
suite); the rest run once. Each version appears as a `[pg17]`-style test id, so
a failure says which server it was.

```bash
DJANGO_ENV=test make test                           # default only, ~11s
DJANGO_ENV=test TEST_POSTGRES_MAJORS=all make test  # what CI runs, ~55s
DJANGO_ENV=test TEST_POSTGRES_MAJORS=15 make test   # one specific major
```

Having both numbers lets the default run answer a question nothing else does:
**if `POSTGRES_DEFAULT` is below Django's minimum, the suite refuses to run and
says so.** That combination is not a test problem — it means the framework in
the lockfile cannot run against the major this project targets, which is
exactly what the Django 6.1 branch hit, found the hard way via a
`NotSupportedError` in CI. `TEST_POSTGRES_MAJORS=all` still works in that state,
so the code can be validated while the database question is settled. A default
*above* the ceiling is also an error — the ceiling is stale.

`settings/environments/test.py` deliberately configures no database at all —
`base.py` leaves `DATABASES` empty when `DATABASE_URL` is unset, and the
fixture fills it in. Anything reaching for a database outside that fixture
fails loudly rather than quietly running on a different engine than the real one.
The fixture repoints `DATABASES` unconditionally, so `DATABASE_URL` has no
effect on a test run — there is no supported way to aim the suite at a
PostgreSQL you manage yourself, only at the majors the two `TEST_POSTGRES_*`
variables select.

Repointing Django at a container mid-run takes more than rewriting
`settings.DATABASES`: the `ConnectionHandler` caches both the settings and the
built `DatabaseWrapper` (pytest-django issue #643), and the wrappers live in a
thread-critical `Local`, so the `sync_to_async` worker thread the async tests
use holds one of its own. `django_db_modify_db_settings` in `tests/conftest.py`
evicts all of that and then asserts the server it reached really is the major
the leg asked for — without that assertion the failure mode is several green
legs that all tested the same version.

## Code Standards

- **Formatting**: Black (with migrations excluded) and isort (black profile)
- **Type checking**: mypy with django-stubs and djangorestframework-stubs
- **Linting**: pylint with pylint-django plugin
- Migrations are excluded from formatting, type checking, and linting

## Git Preferences

- **No fixup commits**: Do not create separate commits to fix issues in previous commits. Instead, amend the original commit with `git commit --amend` and force push if necessary.
- Keep the git history clean and meaningful with each commit representing a complete, working change.
