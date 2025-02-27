#########
saucerbot
#########

bot for the saucer groupme


******************
A Tour of the Code
******************

Handlers
========

Handlers are the main hook to making the bot do something. When a message comes in, its text is checked against the
various regexes defined by the handlers, and if they match, they fire.

Handlers are implemented as decorated functions. You can check out their implementation in the ``handlers/__init__.py``
file. Decorated functions define a regex in the decorator to match against message content, and the implementing
function takes optional arguments to assist with taking action. The BotContext provides a means to post a message back
to the source chat app, and the Message object provides a way to interact with the message that triggered the handler.
By convention all handlers are defined in that handlers directory, and meatier logic is implemented in the utils
directory.

The Rest
========

Clark can worry about the rest of the stuff that makes the app work.

************
Contributing
************

We run poetry here. You'll need Python 3.11.x or newer and Poetry 2.0.x or newer. Clark also wrote an ``asdf``
``.tool-versions`` file if you're so inclined to use it.

If you're running tests or code, there's some env vars you'll want to set. For local dev, I'd recommend the following::

  export DJANGO_ENV=local  # (or test)

There's a Makefile that will help you run the CI checks and code standard stuff. Some useful commands:

  - ``make format``: runs black and isort on the code
  - ``make test``: runs the tests. Probably have to set DJANGO_ENV. Recommend ``DJANGO_ENV=test make test``
  - ``make ci``: runs all the MR checks. Probably have to set the DJANGO_ENV env var


When you're submitting MRs or merging MRs, Clark kinda has to be involved cause he's the only one who can deploy.
