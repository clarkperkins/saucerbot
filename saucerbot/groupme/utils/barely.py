# -*- coding: utf-8 -*-

import os
import random
import re
from pathlib import Path
from typing import Optional, Set, Union

from django.conf import settings
from lowerpines.message import ComplexMessage, RefAttach

from saucerbot.handlers import BotContext, Message

emojis = [
    "👌",  # ok sign
    "🙏",  # praying hands
    "🙌",  # field goal hands
    "🙋‍♂️",  # guy raising hand
    "🙋‍♀️",  # woman raising hand
]

quips = {
    "Barely know her": emojis,
    "{match}? I barely know her!": emojis,
    "{match}? Nice one <person>!": emojis,
    "{match}? High fives all around!!!": emojis[3:],
    "LOLOLOL {match}": emojis,
    "Props to <person>, I barely know her though": emojis,
    "heh heh heh {match}": emojis,
    "{match}?! wowwww <person>": emojis,
    "Idk, <person>, I don't know her well enough to {match}": emojis,
    "Gimme 5 <person>!": emojis[3:],
    "{match}? Brian would be proud": emojis,
    "Dang <person>, I barely know her": emojis,
    "{match}? Come on, <person> don't leave me hangin": emojis[3:],
}

PERCENT_CHANCE = int(os.environ.get("BARELY_KNOW_HER_CHANCE", 35))


def get_er_words() -> Set[str]:
    er_words_file: Path = settings.BASE_DIR / "saucerbot" / "resources" / "er_words.txt"
    with er_words_file.open("rt", encoding="utf8") as er_words:
        return set(word.strip() for word in er_words if not word.startswith("#"))


matching_words = get_er_words()


def i_barely_know_her(context: BotContext, message: Message) -> bool:
    if message.content is not None and random.choice(range(0, 100)) < PERCENT_CHANCE:
        quip = get_quip(message)
        if quip is not None:
            context.post(quip)
            return True
    return False


def get_quip(message: Message) -> Optional[Union[ComplexMessage, str]]:
    matches = []
    for word in re.split(r"[^a-zA-Z]", message.content):
        if word.strip().lower() in matching_words:
            matches.append(word.strip().lower())
    if matches:
        match = max(matches, key=str.__len__)
        quip = random.choice(list(quips.keys()))
        emoji = random.choice(quips[quip])
        split_quip = quip.format(match=match).split("<person>")
        if len(split_quip) > 1:
            user_ref = RefAttach(message.user_id, f"@{message.user_name}")
            return split_quip[0] + user_ref + split_quip[1] + " " + emoji
        else:
            return split_quip[0] + " " + emoji
    return None
