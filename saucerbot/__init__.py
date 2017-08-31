# -*- coding: utf-8 -*-

from saucerbot.app import SaucerFlask

app = SaucerFlask(__name__)


# So our views get loaded AFTER the app gets created
import saucerbot.commands
import saucerbot.handlers
import saucerbot.views
