# coding=utf-8
"""
Routing rules.
"""
from amvnews import get_featured_amv_list
from constants import PLUGIN


@PLUGIN.route('/')
def create_main_listing():
    """
    Create main menu of the plugin.
    :return: List of menu entries.
    :rtype: list[dict]
    """
    items = [
        {
            'label': PLUGIN.get_string(10001),
            'icon': None,
            'thumbnail': None,
            'context_menu': [],
            'path': PLUGIN.url_for(endpoint='create_featured_amv_list', page=1)
        }
    ]
    return items


@PLUGIN.route('/featured/<page>')
def create_featured_amv_list(page):
    """
    Create list of featured AMV for specified page.

    To avoid heavy queries featured AMV are demonstrated by small portions
    (pages). Each page is constucted independently by demand.

    :param int page: Page number.
    :return: List of featured AMV.
    :rtype: list[dict]
    """
    page = int(page)
    items = []
    if page > 1:
        items.append({
            'label': PLUGIN.get_string(10002),
            'icon': None,
            'thumbnail': None,
            'context_menu': [],
            'path': PLUGIN.url_for(
                endpoint='create_featured_amv_list',
                page=page - 1
            )
        })
    for amv in get_featured_amv_list(page):
        items.extend([
            {
                'label': u'{} ({})'.format(amv['title'], amv['date']),
                'icon': amv['image'],
                'thumbnail': amv['image'],
                'context_menu': [],
                'path': amv['path'],
                'is_playable': True,
                'info': {
                    'count': amv['id'],
                    'size': amv['size'],
                    'plot': amv['description'],
                    'genre': 'Anime Music Video',
                    'raiting': amv['rating'] * 2,
                    'title': amv['title'],
                    'duration': amv['duration'],
                    'mediatype': 'musicvideo'
                }
            }
        ])
    items.extend([
        {
            'label': PLUGIN.get_string(10003),
            'icon': None,
            'thumbnail': None,
            'context_menu': [],
            'path': PLUGIN.url_for(
                endpoint='create_featured_amv_list',
                page=page + 1
            )
        }
    ])
    return items
