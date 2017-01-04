# coding=utf-8
"""
Routing rules.
"""
from constants import PLUGIN


@PLUGIN.route('/')
def create_main_listing():
    items = [
        {
            'label': PLUGIN.get_string(10001),
            'icon': None,
            'thumbnail': None,
            'context_menu': [],
            'path': PLUGIN.url_for(endpoint='create_main_listing')
        }
    ]
    return items
