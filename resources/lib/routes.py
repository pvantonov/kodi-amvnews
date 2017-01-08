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
            'path': PLUGIN.url_for('create_featured_amv_list', page=1)
        }
    ]
    PLUGIN.set_content('musicvideos')
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
                'context_menu': [
                    ('Toggle watched', 'Action(ToggleWatched)')
                ],
                'path': PLUGIN.url_for('play_amv', url=amv['path']),
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
                },
                'stream_info': {
                    'video': {
                        'codec': amv['video_codec'],
                        'aspect': amv['video_aspect'],
                        'width': amv['video_width'],
                        'height': amv['video_height'],
                        'duration': amv['duration']
                    },
                    'audio': {
                        'codec': amv['audio_codec']
                    }
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
    PLUGIN.set_content('musicvideos')
    return items


@PLUGIN.route('/play/<url>')
def play_amv(url):
    """
    Play AMV.

    Though this function doesn't work nothing but returning file url to Kodi
    it is necessary for marking as wathed to work properly. Possibly Kodi bug.

    :param str url: AMV URL.
    """
    PLUGIN.set_resolved_url(url)
