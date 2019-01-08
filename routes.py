# coding=utf-8
"""
Routing rules.
"""
import xbmc
import xbmcgui
from amvnews import AmvNewsBrowser
from constants import PLUGIN
from helpers import Language


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
    for amv in AmvNewsBrowser().get_featured_amv_list(page):
        context_menu = []
        if PLUGIN.get_setting('username') and PLUGIN.get_setting('password'):
            context_menu.extend([
                (PLUGIN.get_string(10004), 'RunPlugin(%s)' % PLUGIN.url_for('evaluate', amv_id=amv['id'])),
                (PLUGIN.get_string(10005), 'RunPlugin(%s)' % PLUGIN.url_for('add_to_favourites', amv_id=amv['id'])),
                (PLUGIN.get_string(10010), 'RunPlugin(%s)' % PLUGIN.url_for('download', amv_id=amv['id'])),
            ])
        item = _create_amv_item(amv, context_menu)
        item['label'] = u'{} ({})'.format(amv['amv']['title'], amv['amv']['date'])
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
        xbmcgui.Dialog().ok(PLUGIN.name, PLUGIN.get_string(10007))
    else:
        page = int(page)
        created_from_main_listing = (page == 0)
        if page == 0:
            page = 1

        items = []
        if page > 1:
            items.append(_create_prev_page_item('create_evaluated_amv_list', page))
        for amv in AmvNewsBrowser().get_evaluated_amv_list(page):
            context_menu = [
                (PLUGIN.get_string(10004), 'RunPlugin(%s)' % PLUGIN.url_for('evaluate', amv_id=amv['id'])),
                (PLUGIN.get_string(10005), 'RunPlugin(%s)' % PLUGIN.url_for('add_to_favourites', amv_id=amv['id'])),
                (PLUGIN.get_string(10010), 'RunPlugin(%s)' % PLUGIN.url_for('download', amv_id=amv['id'])),
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
        xbmcgui.Dialog().ok(PLUGIN.name, PLUGIN.get_string(10007))
    else:
        page = int(page)
        created_from_main_listing = (page == 0)
        if page == 0:
            page = 1

        items = []
        if page > 1:
            items.append(_create_prev_page_item('create_favourite_amv_list', page))
        for amv in AmvNewsBrowser().get_favourite_amv_list(page):
            context_menu = [
                (PLUGIN.get_string(10004), 'RunPlugin(%s)' % PLUGIN.url_for('evaluate', amv_id=amv['id'])),
                (PLUGIN.get_string(10009), 'RunPlugin(%s)' % PLUGIN.url_for('remove_from_favourites', amv_id=amv['id'])),
                (PLUGIN.get_string(10010), 'RunPlugin(%s)' % PLUGIN.url_for('download', amv_id=amv['id'])),
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
    AmvNewsBrowser().set_amv_mark(int(amv_id), chosen_mark)
    if PLUGIN.get_setting('download_evaluated', bool) and (PLUGIN.get_setting('download_treshold', int) + 1) <= chosen_mark:
        xbmc.executebuiltin('RunPlugin(%s)' % PLUGIN.url_for('download', amv_id=amv_id))


@PLUGIN.route('/favourite/add/<amv_id>')
def add_to_favourites(amv_id):
    """
    Make AMV favorite.

    :param int amv_id: AMV identifier.
    """
    AmvNewsBrowser().add_amv_to_favourites(int(amv_id))
    if PLUGIN.get_setting('download_favorits', bool):
        xbmc.executebuiltin('RunPlugin(%s)' % PLUGIN.url_for('download', amv_id=amv_id))


@PLUGIN.route('/favourite/remove/<amv_id>')
def remove_from_favourites(amv_id):
    """
    Remove AMV from favorite.

    :param int amv_id: AMV identifier.
    """
    AmvNewsBrowser().remove_amv_from_favourites(int(amv_id))


@PLUGIN.route('/play/<amv_id>/<subtitles_id>', name='play_with_subtitles')
@PLUGIN.route('/play/<amv_id>')
def play(amv_id, subtitles_id=None):
    """
    Play AMV.

    :param int amv_id: AMV identifier.
    :param int|None subtitles_id: Subtitles identifier.
    """
    video_path = AmvNewsBrowser.get_amv_url(amv_id)
    subtitles_path = AmvNewsBrowser.get_subtitles_url(subtitles_id) if subtitles_id else None
    PLUGIN.set_resolved_url(video_path, subtitles_path)


@PLUGIN.route('/download/<amv_id>')
def download(amv_id):
    """
    Download AMV.
    :param int amv_id: AMV identifier.
    """
    if not PLUGIN.get_setting('download_path'):
        xbmcgui.Dialog().ok(PLUGIN.name, PLUGIN.get_string(10011))
    else:
        browser = AmvNewsBrowser()
        amv_info = browser.get_amv(int(amv_id))

        pDialog = xbmcgui.DialogProgressBG()
        pDialog.create(PLUGIN.name, PLUGIN.get_string(10012) % amv_info['amv']['title'])
        browser.download(PLUGIN.get_setting('download_path'), amv_info['id'], _choose_subtitles(amv_info))
        pDialog.close()
        xbmc.executebuiltin('XBMC.UpdateLibrary(video)')
        xbmcgui.Dialog().notification(PLUGIN.name, PLUGIN.get_string(10013) % amv_info['amv']['title'])

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
    amv_id = amv_info['id']
    if amv_info['subtitles']:
        path = PLUGIN.url_for('play_with_subtitles', amv_id=amv_id, subtitles_id=_choose_subtitles(amv_info))
    else:
        path = PLUGIN.url_for('play', amv_id=amv_id)

    return {
        'label': amv_info['amv']['title'],
        'icon': amv_info['image'],
        'thumbnail': amv_info['image'],
        'path': path,
        'is_playable': True,
        'context_menu': context_menu,
        'info': {
            'count': amv_id,
            'size': amv_info['video']['size'],
            'director': amv_info['amv']['author'],
            'plot': amv_info['amv']['description'],
            'aired': amv_info['amv']['aired'],
            'dateadded': amv_info['amv']['added'],
            'votes': amv_info['amv']['votes'],
            'genre': amv_info['amv']['genre'],
            'rating': amv_info['amv']['rating'] * 2,
            'userrating': amv_info['amv']['user_rating'] * 2,
            'title': amv_info['amv']['title'],
            'duration': amv_info['video']['duration'],
            'mediatype': 'musicvideo'
        },
        'stream_info': {
            'video': {
                'codec': amv_info['video']['video_codec'],
                'aspect': amv_info['video']['aspect'],
                'width': amv_info['video']['width'],
                'height': amv_info['video']['height'],
                'duration': amv_info['video']['duration']
            },
            'audio': {
                'codec': amv_info['video']['audio_codec']
            }
        }
    }


def _choose_subtitles(amv_info):
    """
    Choose best subtitles for AMV.

    :param dict amv_info: AMV information
    :return: Subtitles identifier.
    :rtype: int
    """
    if not amv_info['subtitles']:
        return None

    if PLUGIN.get_setting('subtitles_lang') == '0':
        subtitles_lang = Language.Russian
    elif PLUGIN.get_setting('subtitles_lang') == '1':
        subtitles_lang = Language.English

    preferable_subtitles = filter(lambda x: x[0] == subtitles_lang, amv_info['subtitles'])
    if preferable_subtitles:
        subtitles_id = preferable_subtitles[0][1]
    else:
        subtitles_id = amv_info['subtitles'][0][1]

    return subtitles_id
