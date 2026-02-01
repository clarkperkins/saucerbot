# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Saucerbot is a multi-platform chat bot that works with both GroupMe and Discord. It responds to messages using a handler-based architecture with regex pattern matching.

## Development Setup

### Environment Variables

Set `DJANGO_ENV` before running any commands:
- `DJANGO_ENV=local` - For local development
- `DJANGO_ENV=test` - For running tests
- `DJANGO_ENV=development` - For Django management commands (default in manage.py)

Valid environments are: `test`, `local`, `development`, `staging`, `production`, `build`

### Poetry & Python

This project uses Poetry 2.0.x and requires Python 3.11+. An `.tool-versions` file is provided for asdf users.

Install dependencies:
```bash
poetry install
```

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

# Run all CI checks (format checks + tests + sonar)
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

Test database is SQLite (`test.db`). Tests must have `DJANGO_ENV=test` set.

## Code Standards

- **Formatting**: Black (with migrations excluded) and isort (black profile)
- **Type checking**: mypy with django-stubs and djangorestframework-stubs
- **Linting**: pylint with pylint-django plugin
- Migrations are excluded from formatting, type checking, and linting

## Git Preferences

- **No fixup commits**: Do not create separate commits to fix issues in previous commits. Instead, amend the original commit with `git commit --amend` and force push if necessary.
- Keep the git history clean and meaningful with each commit representing a complete, working change.
