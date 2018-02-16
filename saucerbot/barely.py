import random
import os
import io
import re
from typing import Set
from saucerbot import app, APP_HOME
from lowerpines.endpoints.message import Message
from lowerpines.message import RefAttach

emojis = [
    '\U0001f44c',   # ok sign
    '\U0001f64f',   # praying hands
    '\U0001f64c',   # field goal hands
    '\U0001f64b\u200d\u2642\ufe0f',   # guy raising hand
    '\U0001f64b\u200d\u2640\ufe0f',   # woman raising hand
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
    "Idk, <person>, I barely know her": emojis,
    "Gimme 5 <person>!": emojis[3:]
}


def get_er_words() -> Set[str]:
    er_words_file = os.path.join(APP_HOME, 'saucerbot', 'resources', 'er_words.txt')
    er_words = io.open(er_words_file, 'rt')
    words = [word.strip() for word in er_words]
    er_words.close()
    return set(words)

matching_words = get_er_words()


def i_barely_know_her(message: Message):
    if message.text is not None and random.choice(range(0, 10)) <= 5:
        quip = get_quip(message)
        if quip is not None:
            app.bot.post(quip)


def get_quip(message: Message):
    matches = []
    for word in re.split(r'[^a-zA-Z]', message.text):
        if word.strip().lower() in matching_words:
            matches.append(word.strip().lower())
    if len(matches) > 0:
        match = max(matches, key=str.__len__)
        quip = random.choice(list(quips.keys()))
        emoji = random.choice(quips[quip])
        split_quip = quip.format(match=match).split('<person>')
        if len(split_quip) > 1:
            return split_quip[0] + RefAttach(message.user_id, '@{}'.format(message.name)) + split_quip[1] + ' ' + emoji
        else:
            return split_quip[0] + ' ' + emoji
    return None






