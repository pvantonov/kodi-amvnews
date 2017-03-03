# coding=utf-8
"""
Routing rules.
"""
import xbmcgui
from amvnews import *
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
        },
        {
            'label': PLUGIN.get_string(10006),
            'icon': None,
            'thumbnail': None,
            'context_menu': [],
            'path': PLUGIN.url_for('create_evaluated_amv_list', page=0)
        },
        {
            'label': PLUGIN.get_string(10008),
            'icon': None,
            'thumbnail': None,
            'context_menu': [],
            'path': PLUGIN.url_for('create_favourite_amv_list', page=0)
        }
    ]
    PLUGIN.set_content('videos')
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
        items.append(_create_prev_page_item('create_featured_amv_list', page))
    for amv in get_featured_amv_list(page):
        context_menu = []
        if PLUGIN.get_setting('username') and PLUGIN.get_setting('password'):
            context_menu.extend([
                (PLUGIN.get_string(10004), 'RunPlugin(%s)' % PLUGIN.url_for('evaluate', amv_id=amv['id'])),
                (PLUGIN.get_string(10005), 'RunPlugin(%s)' % PLUGIN.url_for('add_to_favourites', amv_id=amv['id']))
            ])
        item = _create_amv_item(amv, context_menu)
        item['label'] = u'{} ({})'.format(amv['title'], amv['date'])
        items.append(item)
    items.append(_create_next_page_item('create_featured_amv_list', page))
    PLUGIN.set_content('videos')
    return PLUGIN.finish(items, update_listing=not created_from_main_listing)


@PLUGIN.route('/evaluated/<page>')
def create_evaluated_amv_list(page):
    """
    Create list of evaluated AMV for specified page.

    To avoid heavy queries featured AMV are demonstrated by small portions
    (pages). Each page is constucted independently by demand.

    :param int page: Page number.
    :return: List of evaluated AMV.
    :rtype: list[dict]
    """
    if not PLUGIN.get_setting('username') or not PLUGIN.get_setting('password'):
        xbmcgui.Dialog().notification(PLUGIN.name, PLUGIN.get_string(10007))
    else:
        page = int(page)
        created_from_main_listing = (page == 0)
        if page == 0:
            page = 1

        items = []
        if page > 1:
            items.append(_create_prev_page_item('create_evaluated_amv_list', page))
        for amv in get_evaluated_amv_list(page):
            context_menu = [
                (PLUGIN.get_string(10004), 'RunPlugin(%s)' % PLUGIN.url_for('evaluate', amv_id=amv['id'])),
                (PLUGIN.get_string(10005), 'RunPlugin(%s)' % PLUGIN.url_for('add_to_favourites', amv_id=amv['id']))
            ]
            items.append(_create_amv_item(amv, context_menu))
        items.append(_create_next_page_item('create_evaluated_amv_list', page))
        PLUGIN.set_content('videos')
        return PLUGIN.finish(items, update_listing=not created_from_main_listing)


@PLUGIN.route('/favourite/<page>')
def create_favourite_amv_list(page):
    """
    Create list of favourite AMV for specified page.

    To avoid heavy queries featured AMV are demonstrated by small portions
    (pages). Each page is constucted independently by demand.

    :param int page: Page number.
    :return: List of favourite AMV.
    :rtype: list[dict]
    """
    if not PLUGIN.get_setting('username') or not PLUGIN.get_setting('password'):
        xbmcgui.Dialog().notification(PLUGIN.name, PLUGIN.get_string(10007))
    else:
        page = int(page)
        created_from_main_listing = (page == 0)
        if page == 0:
            page = 1

        items = []
        if page > 1:
            items.append(_create_prev_page_item('create_favourite_amv_list', page))
        for amv in get_favourite_amv_list(page):
            context_menu = [
                (PLUGIN.get_string(10004), 'RunPlugin(%s)' % PLUGIN.url_for('evaluate', amv_id=amv['id'])),
                (PLUGIN.get_string(10009), 'RunPlugin(%s)' % PLUGIN.url_for('remove_from_favourites', amv_id=amv['id']))
            ]
            items.append(_create_amv_item(amv, context_menu))
        items.append(_create_next_page_item('create_favourite_amv_list', page))
        PLUGIN.set_content('videos')
        return PLUGIN.finish(items, update_listing=not created_from_main_listing)


@PLUGIN.route('/evaluate/<amv_id>')
def evaluate(amv_id):
    """
    Evaluate AMV.

    :param int amv_id: AMV identifier.
    """
    chosen_mark = xbmcgui.Dialog().select(PLUGIN.get_string(10201), map(PLUGIN.get_string, xrange(10202, 10207))) + 1
    set_amv_mark(int(amv_id), chosen_mark)


@PLUGIN.route('/favourite/add/<amv_id>')
def add_to_favourites(amv_id):
    """
    Make AMV favorite.

    :param int amv_id: AMV identifier.
    """
    add_amv_to_favourites(int(amv_id))


@PLUGIN.route('/favourite/remove/<amv_id>')
def remove_from_favourites(amv_id):
    """
    Remove AMV from favorite.

    :param int amv_id: AMV identifier.
    """
    remove_amv_from_favourites(int(amv_id))


@PLUGIN.route('/play/<amv_id>')
def play_amv(amv_id):
    """
    Play AMV.

    :param int amv_id: AMV identifier.
    """
    metadata = PLUGIN.get_storage('amv_metadata')[int(amv_id)]
    PLUGIN.set_resolved_url(metadata['path'], metadata.get('subtitles', None))


def _create_next_page_item(view_name, current_page):
    """
    Create list item to show next page of view.

    :param str view_name: Name of view.
    :param int current_page: Current page number.
    :return: List item to show next page.
    :rtype: dict
    """
    return {
        'label': PLUGIN.get_string(10003),
        'icon': None,
        'thumbnail': None,
        'context_menu': [],
        'path': PLUGIN.url_for(endpoint=view_name, page=current_page + 1)
    }


def _create_prev_page_item(view_name, current_page):
    """
    Create list item to show previous page of view.

    :param str view_name: Name of view.
    :param int current_page: Current page number.
    :return: List item to show previous page.
    :rtype: dict
    """
    return {
        'label': PLUGIN.get_string(10002),
        'icon': None,
        'thumbnail': None,
        'context_menu': [],
        'path': PLUGIN.url_for(endpoint=view_name, page=current_page - 1)
    }


def _create_amv_item(amv_info, context_menu):
    """
    Create list item for AMV.

    :param dict amv_info: AMV information.
    :param list context_menu: Context menu for item.
    :return: List item for AMV.
    :rtype: dict
    """
    return {
        'label': amv_info['title'],
        'icon': amv_info['image'],
        'thumbnail': amv_info['image'],
        'path': PLUGIN.url_for('play_amv', amv_id=amv_info['id']),
        'is_playable': True,
        'context_menu': context_menu,
        'info': {
            'count': amv_info['id'],
            'size': amv_info['size'],
            'director': amv_info['author'],
            'plot': amv_info['description'],
            'aired': amv_info['aired'],
            'dateadded': amv_info['added'],
            'votes': amv_info['votes'],
            'genre': amv_info['genre'],
            'rating': amv_info['rating'] * 2,
            'userrating': amv_info['user_rating'] * 2,
            'title': amv_info['title'],
            'duration': amv_info['duration'],
            'mediatype': 'musicvideo'
        },
        'stream_info': {
            'video': {
                'codec': amv_info['video_codec'],
                'aspect': amv_info['video_aspect'],
                'width': amv_info['video_width'],
                'height': amv_info['video_height'],
                'duration': amv_info['duration']
            },
            'audio': {
                'codec': amv_info['audio_codec']
            }
        }
    }
