# -*- coding: utf-8 -*-

import json
import logging
import random
import uuid
from datetime import datetime

from locust import HttpLocust, TaskSet, task

logger = logging.getLogger(__name__)

SENTENCES = [
    ("puppy", "car", "rabbit", "girl", "monkey"),
    ("runs", "hits", "jumps", "drives", "barfs"),
    ("adorable", "clueless", "dirty", "odd", "stupid"),
    ("crazily.", "dutifully.", "foolishly.", "merrily.", "occasionally."),
]


def get_sample_message():
    created_at = int(datetime.now().timestamp())

    return {
        'attachments': [],
        'avatar_url': "https://example.com/avatar.jpeg",
        'created_at': created_at,
        'group_id': '123456',
        'id': "1234567890",
        'name': "Foo Bar",
        'sender_id': "abcdef",
        'sender_type': "user",
        'source_guid': str(uuid.uuid4()),
        'system': False,
        'text': ' '.join([random.choice(i) for i in SENTENCES]),
        'user_id': "abcdef"
    }


class SaucerbotTaskSet(TaskSet):
    @task(1)
    def groume_message(self):
        self.client.post('/groupme/callbacks/saucerbot/', json.dumps(get_sample_message()))


class SaucerbotLocust(HttpLocust):
    task_set = SaucerbotTaskSet
    min_wait = 5000
    max_wait = 9000
