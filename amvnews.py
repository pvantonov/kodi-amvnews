# coding=utf-8
"""
Unofficial API to http://amvnews.ru.
"""
import datetime
import urllib.parse
import os
import re
import requests
from xml.etree import ElementTree as etree
from bs4 import BeautifulSoup
from constants import PLUGIN
from helpers import Singleton, Language
import xbmc
import xbmcvfs

__all__ = ['AmvNewsBrowser']


class AmvNewsBrowser(object):
    """
    Web browser to access AmvNews site.
    """

    __metaclass__ = Singleton

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

    @classmethod
    def get_amv_url(cls, amv_id):
        """
        Get URL to AMV file.

        :param int amv_id: Identifier of AMV
        :return: URL to AMV file.
        :rtype str
        """
        return cls._get_full_url({'go': 'Files', 'file': 'down', 'id': amv_id})

    @classmethod
    def get_subtitles_url(cls, subtitles_id):
        """
        Get URL to subtitles file.

        :param int subtitles_id: Identifier of subtitles
        :return: URL to subtitles file.
        :rtype str
        """
        return cls._get_full_url({'go': 'Files', 'file': 'down', 'sub': subtitles_id})

    def get_featured_amv_list(self, page):
        """
        Get information about featured AMV.

        To avoid heavy queries featured AMV are obtained by small portions (pages). Data for each page is
        obtained independently by demand.

        :param int page: Page number.
        :return: List of featured AMV metadata.
        :rtype: dict
        """
        html = self._get_html_page({'go': 'News', 'page': (page - 1) * 10, 'in': 'cat', 'id': 1})

        result = []
        for node in html.find_all('span', attrs={'class': 'newstitle'}):
            amv_link = node.find_parent('table').find_next_sibling('table').find(
                'a', attrs={'class': 'more-news-simple-a'}
            ).attrs['href']
            metadata = self.get_amv(int(REGEX_AMV_ID.match(amv_link).groupdict()['id']))
            metadata['amv'].update({'date': node.find_parent('td').find_next_sibling('td').text.strip()})
            result.append(metadata)
        return result

    def get_evaluated_amv_list(self, page):
        """
        Get information about evaluated AMV.

        To avoid heavy queries featured AMV are obtained by small portions (pages). Data for each page is obtained
        independently by demand.

        :param int page: Page number.
        :return: List of evaluated AMV metadata.
        :rtype: list[dict]
        """
        html = self._get_html_page({'go': 'Files', 'page': (page - 1) * 10, 'file': 'votes'})

        result = []
        for node in html.find_all('a', attrs={'class': 'ratestop'})[:10]:
            result.append(self.get_amv(int(REGEX_AMV_ID.match(node.attrs['href']).groupdict()['id'])))
        return result

    def get_favourite_amv_list(self, page):
        """
        Get information about favourite AMV.

        To avoid heavy queries featured AMV are obtained by small portions (pages). Data for each page is obtained
        independently by demand.

        :param int page: Page number.
        :return: List of favourite AMV metadata.
        :rtype: list[dict]
        """
        html = self._get_html_page({'go': 'Files', 'page': (page - 1) * 10, 'file': 'favor'})

        result = []
        for node in html.find_all('a', attrs={'class': 'ratestop'})[:10]:
            result.append(self.get_amv(int(REGEX_AMV_ID.match(node.attrs['href']).groupdict()['id'])))
        return result

    def get_amv(self, amv_id):
        """
        Get information about specified AMV.
        :param int amv_id: Identifier of AMV.
        :return: AMV metadata.
        :rtype: dict
        """
        format_version = 5

        storage = PLUGIN.get_storage('amv_metadata')
        if amv_id in storage and storage[amv_id].get('format', 0) == format_version:
            if (datetime.datetime.now() - storage[amv_id]['timestamp']).days < 3:
                return storage[amv_id]

        html = self._get_html_page({'go': 'Files', 'in': 'view', 'id': amv_id})

        metadata = {
            'id': amv_id,
            'timestamp': datetime.datetime.now(),
            'format': format_version,
            'amv': {
                'title': html.find('h1', itemprop='name').text.strip(),
                'description': html.find(itemprop='description').text.strip(),
                'rating': float(html.find(itemprop='ratingValue').text.strip()),
                'votes': int(html.find(itemprop='ratingCount').text.strip()),
                'author': html.find('span', itemprop='name').text.strip(),
                'genre': ', '.join(node.attrs['content'] for node in html.find_all(itemprop='genre')),
            },
        }

        aired, added = self._get_amv_date(html)
        metadata['amv']['aired'] = aired
        metadata['amv']['added'] = added

        user_rating_tag = html.find(id='vote-text')
        user_rating = user_rating_tag.text.strip() if user_rating_tag else '-'
        metadata['amv']['user_rating'] = float(0 if user_rating == '-' else user_rating)

        metadata['video'] = self._get_video_metadata(html)
        metadata['subtitles'] = self._get_subtitles_metadata(html)
        metadata['images'] = self._get_images(html)
        metadata['image'] = metadata['images'][0] if metadata['images'] else None

        storage[amv_id] = metadata
        return metadata

    def set_amv_mark(self, amv_id, mark):
        """
        Set mark for AMV.

        :param int amv_id: Identifier of AMV.
        :param int mark: Mark
        """
        self.session.get(self.homepage, params={'go': 'Files', 'in': 'ajaxreiting', 'id': amv_id, 'vote': mark})
        storage = PLUGIN.get_storage('amv_metadata')
        storage[amv_id]['user_rating'] = mark

    def add_amv_to_favourites(self, amv_id):
        """
        Make AMV favorite.

        :param int amv_id: Identifier of AMV.
        """
        self.session.get(self.homepage, params={'go': 'Files', 'in': 'addfav', 'id': amv_id})

    def remove_amv_from_favourites(self, amv_id):
        """
        Remove AMV from favourites.

        :param int amv_id: Identifier of AMV.
        """
        self.session.get(self.homepage, params={'go': 'Files', 'in': 'delfav', 'id': amv_id})

    def download(self, save_path, amv_id, subtitles_id=None):
        """
        Download AMV and save it on local path.

        :param str save_path: Local path where AMV will be saved.
        :param int amv_id: Identifier of AMV.
        :param int subtitles_id: Identifier of AMV subtitles.
        """
        sync_file = os.path.join(save_path, '%d.sync' % amv_id)
        if xbmcvfs.exists(sync_file):
            # AMV is already downloaded
            return

        amv_info = self.get_amv(amv_id)

        self._download_file(self.get_amv_url(amv_id), save_path, str(amv_id))
        self._create_nfo_file(save_path, amv_info)

        if amv_info['images']:
            self._download_file(amv_info['images'][0], save_path, '%d-poster' % amv_id)
            if len(amv_info['images']) > 1:
                self._download_file(amv_info['images'][1], save_path, '%d-fanart' % amv_id)

        if subtitles_id:
            self._download_file(self.get_subtitles_url(subtitles_id), save_path, str(amv_id))

        try:
            f = xbmcvfs.File(sync_file, 'w')
        finally:
            f.close()

    def _create_nfo_file(self, save_path, amv_info):
        """
        Create .nfo file

        :param str save_path: Local path where AMV will be saved.
        :param dict amv_info: AMV information.
        """
        music_video = etree.Element('musicvideo')
        etree.SubElement(music_video, 'title').text = amv_info['amv']['title']
        etree.SubElement(music_video, 'userrating').text = str(amv_info['amv']['user_rating'] * 2)
        etree.SubElement(music_video, 'plot').text = amv_info['amv']['description']
        etree.SubElement(music_video, 'year').text = amv_info['amv']['aired'].split('-')[0]
        etree.SubElement(music_video, 'dateadded').text = amv_info['amv']['added']
        etree.SubElement(music_video, 'director').text = amv_info['amv']['author']
        etree.SubElement(music_video, 'playcount').text = '1'
        for genre in amv_info['amv']['genre'].split(','):
            etree.SubElement(music_video, 'genre').text = genre.strip()

        tree = etree.ElementTree(music_video)

        temp_fullpath = xbmc.translatePath(os.path.join('special://temp', '%d.nfo' % amv_info['id']))
        save_fullpath = os.path.join(save_path, '%d.nfo' % amv_info['id'])
        tree.write(temp_fullpath, encoding='utf-8', xml_declaration=True)
        xbmcvfs.copy(temp_fullpath, save_fullpath)
        xbmcvfs.delete(temp_fullpath)

    @staticmethod
    def _download_file(url, path, filename):
        """
        Download file.

        :param str url: URL of the file.
        :param str path: Local path where file will be saved.
        :param str filename: Filename to be assigned to the downloaded file.
        :return: Full path to the downloaded file.
        :rtype: str
        """
        response = requests.get(url, stream=True)
        extension = response.url.rsplit('.', 1)[1]
        filename = '%s.%s' % (filename, extension)

        full_path = os.path.join(path, filename)

        try:
            f = xbmcvfs.File(os.path.join(path, filename), 'w')
            for chunk in response.iter_content(chunk_size=128):
                f.write(chunk)
        finally:
            f.close()

        return full_path

    @classmethod
    def _get_full_url(cls, url_params):
        """
        Get full URL to query http://amvnews.ru with specified URL params.

        :param dict url_params: URL params.
        :return: Full URL.
        :rtype: str
        """
        return '{}?{}'.format(cls.homepage, urllib.parse.urlencode(url_params))

    def _get_html_page(self, url_params):
        """
        Get HTML page generated by http://amvnews.ru for specified URL params.

        :param dict url_params: URL params.
        :return: Parsed HTML page.
        :rtype: BeautifulSoup
        """
        return BeautifulSoup(self.session.get(self.homepage, params=url_params).text.replace('&#...', '...'))

    @staticmethod
    def _get_amv_date(html):
        """
        Get information when AMV was aired and when AMV was added to the site.

        :param BeautifulSoup html: Parsed HTML page.
        :return: Dates when AMV was aired and when AMV was added to the site.
        :rtype: tuple(str, str)
        """
        aired = ''
        match = REGEX_AMV_AIRED.match(html.find(attrs={'id': 'author-block'}).text)
        if match:
            day = match.groupdict()['day']
            month = match.groupdict()['month']
            year = match.groupdict()['year']
            aired = '{}-{}-{}'.format(year, month, day)

        added = ''
        match = REGEX_AMV_ADDED.match(html.find(attrs={'id': 'sender-block'}).text)
        if match:
            day = match.groupdict()['day']
            month = match.groupdict()['month']
            year = match.groupdict()['year']
            hour = match.groupdict()['hour']
            minute = match.groupdict()['minute']
            added = '{}-{}-{} {}:{}:00'.format(year, month, day, hour, minute)

        return aired, added

    @staticmethod
    def _get_images(html):
        """
        Get AMV related images/screenshots.

        :param BeautifulSoup html: Parsed HTML page.
        :return: List of image's URL
        :rtype: list[str]
        """
        images = []
        main_image_tag = html.find(itemprop='image')
        main_image_alt = None
        if main_image_tag:
            images.append('http://amvnews.ru{}'.format(main_image_tag.attrs['src']))
            main_image_alt = main_image_tag.attrs['alt']

        title = html.find('h1', itemprop='name').text.strip()
        for image_tag in html.find_all('img', alt=[title, main_image_alt]):
            image_url = 'http://amvnews.ru{}'.format(image_tag.attrs['src'])
            if image_url not in images:
                images.append('http://amvnews.ru{}'.format(image_tag.attrs['src']))

        return images

    @staticmethod
    def _get_video_metadata(html):
        """
        Get information about video file.

        :param BeautifulSoup html: Parsed HTML page.
        :return: Video file metadata.
        :rtype: dict
        """
        result = {}
        file_block = html.find(id='main-link-block').find('a').attrs['onmouseover']

        duration = 0
        match = REGEX_AMV_DURATION.match(file_block)
        if match:
            minutes, seconds = match.groupdict()['min'], match.groupdict()['sec']
            if minutes:
                duration += int(minutes) * 60
            if seconds:
                duration += int(seconds)
        result['duration'] = duration

        size_in_bytes = 0
        match = REGEX_AMV_SIZE.match(file_block)
        if match:
            size = match.groupdict()['size']
            if size:
                size_in_bytes = int(float(size) * 1024 * 1024)
        result['size'] = size_in_bytes

        video_codec, audio_codec = '', ''
        match = REGEX_AMV_CODECS.match(file_block)
        if match:
            video_codec = match.groupdict()['video']
            audio_codec = match.groupdict()['audio']
        result['video_codec'] = video_codec
        result['audio_codec'] = audio_codec

        width, height, aspect = 0, 0, 0.0
        match = REGEX_AMV_RESOLUTION.match(file_block)
        if match:
            width = int(match.groupdict()['width'])
            height = int(match.groupdict()['height'])
            aspect = float(width) / float(height)
        result['width'] = width
        result['height'] = height
        result['aspect'] = aspect

        return result

    @staticmethod
    def _get_subtitles_metadata(html):
        """
        Get information about subtitles files.

        :param BeautifulSoup html: Parsed HTML page.
        :return: Subtitles files metadata.
        :rtype: list[tuple(Language, int)]
        """
        subtitles = []
        subtitles_block = html.find(attrs={'id': 'subtitles-block'})
        if subtitles_block:
            for subtitles_info in subtitles_block.find_all('a'):
                subtitles_id = int(REGEX_AMV_SUB_ID.match(subtitles_info.attrs['href']).groupdict()['id'])
                if u'английский' in subtitles_info.attrs['onmouseover']:
                    subtitles_lang = Language.English
                elif u'русский' in subtitles_info.attrs['onmouseover']:
                    subtitles_lang = Language.Russian
                else:
                    subtitles_lang = Language.Unknown
                subtitles.append((subtitles_lang, subtitles_id))
        return subtitles


REGEX_AMV_ID = re.compile(u'^.*id=(?P<id>\\d+).*$', re.S)
REGEX_AMV_SUB_ID = re.compile(u'^.*sub=(?P<id>\\d+).*$', re.S)
REGEX_AMV_SIZE = re.compile(u'^.*Размер</b>: ((?P<size>[\\d.]+) Мб)?.*$', re.S)
REGEX_AMV_CODECS = re.compile(u'^.*Кодеки</b>: (?P<video>.+?)/(?P<audio>.+?)<BR>.*$', re.S)
REGEX_AMV_RESOLUTION = re.compile(u'^.*Разрешение</b>: (?P<width>\\d+)x(?P<height>\\d+)@(?P<fps>[\\d.]+).*$', re.S)
REGEX_AMV_DURATION = re.compile(u'^.*Длительность</b>: ((?P<min>\\d+) мин )?((?P<sec>\\d+) сек)?.*$', re.S)
REGEX_AMV_AIRED = re.compile(u'^.*(?P<day>\\d{2})\\.(?P<month>\\d{2})\\.(?P<year>\\d{4}).*$', re.S)
REGEX_AMV_ADDED = re.compile(u'^.*(?P<day>\\d{2})\\.(?P<month>\\d{2})\\.(?P<year>\\d{4}).*(?P<hour>\\d{2}):(?P<minute>\\d{2}).*$', re.S)  # noqa
