# coding=utf-8
"""
Unofficial API to http://amvnews.ru.
"""
import datetime
import urllib
import re
import requests
from bs4 import BeautifulSoup
from constants import PLUGIN


__all__ = ['get_featured_amv_list', 'get_amv', 'set_amv_mark', 'add_amv_to_favourites']


class AmvNewsBrowser(object):
    """
    Web browser to access AmvNews site.
    """

    # AmvNews homepage
    homepage = 'http://amvnews.ru/index.php'

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AppleWebKit/537.36 (KHTML, like Gecko)'})
        self.session.post(self.homepage, params={'go': 'Members'}, data={
            'user_name': PLUGIN.get_setting('username'),
            'user_password': PLUGIN.get_setting('password'),
            'login': '%C2%EE%E9%F2%E8...'
        })

    def get_amv_url(self, amv_id):
        """
        Get URL to AMV file.

        :param int amv_id: Identifier of AMV
        :return: URL to AMV file.
        :rtype str
        """
        return self._get_full_url({'go': 'Files', 'file': 'down', 'id': amv_id})

    def get_subtitles_url(self, subtitles_id):
        """
        Get URL to subtitles file.

        :param int subtitles_id: Identifier of subtitles
        :return: URL to subtitles file.
        :rtype str
        """
        return self._get_full_url({'go': 'Files', 'file': 'down', 'sub': subtitles_id})

    def get_featured_amv_list_html(self, page):
        """
        Get HTML page with list of featured AMV.

        :param int page: Page number.
        :return: Parsed HTML page with list of featured AMV.
        :rtype: BeautifulSoup
        """
        return self._get_html_page({'go': 'News', 'page': (page - 1) * 10, 'in': 'cat', 'id': 1})

    def get_amv_html(self, amv_id):
        """
        Get HTML page with AMV info.

        :param int amv_id: Identifier of AMV.
        :return: Parsed HTML page with AMV info.
        :rtype: BeautifulSoup
        """
        return self._get_html_page({'go': 'Files', 'in': 'view', 'id': amv_id})

    def post_amv_mark(self, amv_id, mark):
        """
        Set mark for AMV.

        :param int amv_id: Identifier of AMV.
        :param int mark: Mark
        """
        self.session.get(self.homepage, params={'go': 'Files', 'in': 'ajaxreiting', 'id': amv_id, 'vote': mark})

    def add_amv_to_favourites(self, amv_id):
        """
        Make AMV favorite.

        :param int amv_id: Identifier of AMV.
        """
        self.session.get(self.homepage, params={'go': 'Files', 'in': 'addfav', 'id': amv_id})

    def _get_full_url(self, url_params):
        """
        Get full URL to query http://amvnews.ru with specified URL params.

        :param dict url_params: URL params.
        :return: Full URL.
        :rtype: str
        """
        return '{}?{}'.format(self.homepage, urllib.urlencode(url_params))

    def _get_html_page(self, url_params):
        """
        Get HTML page generated by http://amvnews.ru for specified URL params.

        :param dict url_params: URL params.
        :return: Parsed HTML page.
        :rtype: BeautifulSoup
        """
        return BeautifulSoup(self.session.get(self.homepage, params=url_params).text)


browser = AmvNewsBrowser()


def get_featured_amv_list(page):
    """
    Get information about featured AMV.

    To avoid heavy queries featured AMV are obtained by small portions
    (pages). Data for each page is obtained independently by demand.

    :param int page: Page number.
    :return: List of featured AMV metadata.
    :rtype: dict
    """
    html = browser.get_featured_amv_list_html(page)

    result = []
    for node in html.find_all('span', attrs={'class': 'newstitle'}):
        amv_link = node.find_parent('table').find_next_sibling('table').find(
            'a', attrs={'class': 'more-news-simple-a'}
        ).attrs['href']
        metadata = get_amv(int(REGEX_AMV_ID.match(amv_link).groupdict()['id']))
        metadata.update({'date': node.find_parent('td').find_next_sibling('td').text.strip()})
        result.append(metadata)
    return result


def get_amv(amv_id):
    """
    Get information about specified AMV.
    :param int amv_id: Identifier of AMV.
    :return: AMV metadata.
    :rtype: dict
    """
    storage = PLUGIN.get_storage('amv_metadata')
    if amv_id in storage and storage[amv_id].get('format', 0) == 2:
        if (datetime.datetime.now() - storage[amv_id]['timestamp']).days < 3:
            return storage[amv_id]

    html = browser.get_amv_html(amv_id)

    metadata = {
        'id': amv_id,
        'title': html.find('h1', itemprop='name').text.strip(),
        'description': html.find(itemprop='description').text.strip(),
        'rating': float(html.find(itemprop='ratingValue').text.strip()),
        'path': browser.get_amv_url(amv_id),
        'votes': int(html.find(itemprop='ratingCount').text.strip()),
        'author': html.find('span', itemprop='name').text.strip(),
        'genre': ', '.join(node.attrs['content'] for node in html.find_all(itemprop='genre')),
        'image': 'http://amvnews.ru{}'.format(html.find(itemprop='image').attrs['src']),
        'timestamp': datetime.datetime.now(),
        'format': 2,
    }

    user_rating_tag = html.find(id='vote-text')
    user_rating = user_rating_tag.text.strip() if user_rating_tag else '-'
    metadata['user_rating'] = float(0 if user_rating == '-' else user_rating)

    file_info = html.find(id='main-link-block').find('a').attrs['onmouseover']

    duration = 0
    match = REGEX_AMV_DURATION.match(file_info)
    if match:
        minutes, seconds = match.groupdict()['min'], match.groupdict()['sec']
        if minutes:
            duration += int(minutes) * 60
        if seconds:
            duration += int(seconds)
    metadata['duration'] = duration

    size_in_bytes = 0
    match = REGEX_AMV_SIZE.match(file_info)
    if match:
        size = match.groupdict()['size']
        if size:
            size_in_bytes = int(float(size) * 1024 * 1024)
    metadata['size'] = size_in_bytes

    video_codec, audio_codec = '', ''
    match = REGEX_AMV_CODECS.match(file_info)
    if match:
        video_codec = match.groupdict()['video']
        audio_codec = match.groupdict()['audio']
    metadata['video_codec'] = video_codec
    metadata['audio_codec'] = audio_codec

    width, height, aspect = 0, 0, 0.0
    match = REGEX_AMV_RESOLUTION.match(file_info)
    if match:
        width = int(match.groupdict()['width'])
        height = int(match.groupdict()['height'])
        aspect = float(width) / float(height)
    metadata['video_width'] = width
    metadata['video_height'] = height
    metadata['video_aspect'] = aspect

    aired = ''
    match = REGEX_AMV_AIRED.match(html.find(attrs={'id': 'author-block'}).text)
    if match:
        day = match.groupdict()['day']
        month = match.groupdict()['month']
        year = match.groupdict()['year']
        aired = '{}-{}-{}'.format(year, month, day)
    metadata['aired'] = aired

    added = ''
    match = REGEX_AMV_ADDED.match(html.find(attrs={'id': 'sender-block'}).text)
    if match:
        day = match.groupdict()['day']
        month = match.groupdict()['month']
        year = match.groupdict()['year']
        hour = match.groupdict()['hour']
        minute = match.groupdict()['minute']
        added = '{}-{}-{} {}:{}:00'.format(year, month, day, hour, minute)
    metadata['added'] = added

    subtitles_info = html.find(attrs={'id': 'subtitles-block'})
    if subtitles_info:
        subtitles_id = int(REGEX_AMV_SUB_ID.match(subtitles_info.find('a').attrs['href']).groupdict()['id'])
        metadata['subtitles'] = browser.get_subtitles_url(subtitles_id)

    storage[amv_id] = metadata
    return metadata


def set_amv_mark(amv_id, mark):
    """
    Set mark for AMV.

    :param int amv_id: Identifier of AMV.
    :param int mark: Mark
    """
    browser.post_amv_mark(amv_id, mark)
    storage = PLUGIN.get_storage('amv_metadata')
    storage[amv_id]['user_rating'] = mark


def add_amv_to_favourites(amv_id):
    """
    Make AMV favorite.

    :param int amv_id: Identifier of AMV.
    """
    browser.add_amv_to_favourites(amv_id)


REGEX_AMV_ID = re.compile(u'^.*id=(?P<id>\d+).*$', re.S)  # noqa
REGEX_AMV_SUB_ID = re.compile(u'^.*sub=(?P<id>\d+).*$', re.S)  # noqa
REGEX_AMV_SIZE = re.compile(u'^.*Размер</b>: ((?P<size>[\d\.]+) Мб)?.*$', re.S)  # noqa
REGEX_AMV_CODECS = re.compile(u'^.*Кодеки</b>: (?P<video>.+?)/(?P<audio>.+?)<BR>.*$', re.S)  # noqa
REGEX_AMV_RESOLUTION = re.compile(u'^.*Разрешение</b>: (?P<width>\d+)x(?P<height>\d+)@(?P<fps>[\d\.]+).*$', re.S)  # noqa
REGEX_AMV_DURATION = re.compile(u'^.*Длительность</b>: ((?P<min>\d+) мин )?((?P<sec>\d+) сек)?.*$', re.S)  # noqa
REGEX_AMV_AIRED = re.compile(u'^.*(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4}).*$', re.S)  # noqa
REGEX_AMV_ADDED = re.compile(u'^.*(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4}).*(?P<hour>\d{2}):(?P<minute>\d{2}).*$', re.S)  # noqa
