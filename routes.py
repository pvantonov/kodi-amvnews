# coding=utf-8
"""
Routing rules.
"""
import xbmcgui
from amvnews import get_featured_amv_list, set_amv_mark, add_amv_to_favourites
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
            'path': PLUGIN.url_for('create_featured_amv_list', page=0)
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
    created_from_main_listing = (page == 0)
    if page == 0:
        page = 1

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
        context_menu = []
        if PLUGIN.get_setting('username') and PLUGIN.get_setting('password'):
            context_menu.extend([
                (PLUGIN.get_string(10004), 'RunPlugin(%s)' % PLUGIN.url_for('evaluate', amv_id=amv['id'])),
                (PLUGIN.get_string(10005), 'RunPlugin(%s)' % PLUGIN.url_for('add_to_favourites', amv_id=amv['id']))
            ])

        items.extend([
            {
                'label': u'{} ({})'.format(amv['title'], amv['date']),
                'icon': amv['image'],
                'thumbnail': amv['image'],
                'path': PLUGIN.url_for('play_amv', amv_id=amv['id']),
                'is_playable': True,
                'context_menu': context_menu,
                'info': {
                    'count': amv['id'],
                    'size': amv['size'],
                    'director': amv['author'],
                    'plot': amv['description'],
                    'aired': amv['aired'],
                    'dateadded': amv['added'],
                    'votes': amv['votes'],
                    'genre': amv['genre'],
                    'rating': amv['rating'] * 2,
                    'userrating': amv['user_rating'] * 2,
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
    PLUGIN.set_content('videos')
    return PLUGIN.finish(items, update_listing=not created_from_main_listing)


@PLUGIN.route('/evaluate/dialog/<amv_id>')
def evaluate(amv_id):
    """
    Evaluate AMV.

    :param int amv_id: AMV identifier.
    """
    chosen_mark = xbmcgui.Dialog().select(PLUGIN.get_string(10201), map(PLUGIN.get_string, xrange(10202, 10207))) + 1
    set_amv_mark(int(amv_id), chosen_mark)


@PLUGIN.route('/favorite/add/<amv_id>')
def add_to_favourites(amv_id):
    """
    Make AMV favorite.

    :param int amv_id: AMV identifier.
    """
    add_amv_to_favourites(int(amv_id))


@PLUGIN.route('/play/<amv_id>')
def play_amv(amv_id):
    """
    Play AMV.

    :param int amv_id: AMV identifier.
    """
    metadata = PLUGIN.get_storage('amv_metadata')[int(amv_id)]
    PLUGIN.set_resolved_url(metadata['path'], metadata.get('subtitles', None))
