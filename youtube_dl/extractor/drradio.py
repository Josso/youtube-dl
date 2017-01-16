# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    float_or_none,
    parse_iso8601,
    remove_start
)

class DRRadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dr\.dk/radio/(?:ondemand|serier)/(?:[^/]+/)*(?P<id>[\da-z-]+)(?:[/#?]|$)'
    _TESTS = [{
            'url': 'http://www.dr.dk/radio/ondemand/p3/monte-carlo-265',
            'md5': 'f910ae6bfbab868da350bf88f0bff75a',
            'info_dict': {
                'id': 'monte-carlo-265',
                'ext': 'mp3',
                'title': 'Monte Carlo på P3',
                'thumbnail': r're:^https?://.*$',
                'description': 'Peter Falktoft og Esben Bjerre vender ugens store og små begivenheder med et satirisk blik, kigger på ugens bedste tv og tester citater efter en særlig citatskala, som er opfundet til lejligheden.',
                'timestamp': 1369887511,
                'upload_date': '20130530',
            }
        }, {
            'url': 'http://www.dr.dk/radio/serier/filmland-2017-01-05',
            'md5': '9dac3d249126a6479a9b73a6ef8701b3',
            'info_dict': {
                'id': 'filmland-2017-01-05',
                'ext': 'flv',
                'title': 'Filmland: År 2017 er et Bornedal-år på DR P1',
                'thumbnail': r're:^https?://.*$',
                'description': 'Ovenpå tumulten omkring tv-serien er Ole Bornedal tilbage i de danske biografer - endda med hele to film. Senere på året kommer \'Så længe jeg lever\', hans film om sangeren John Mogensen, men allerede nu er der premiere på den grovkornede parforholdskomedie, \'Dræberne fra Nibe\'.\nOle Bornedal er årets første gæst i Filmland, der også går semi-amok i begejstring over to nye amerikanske film, Jim Jarmusch\' \'Paterson\' og Tom Fords \'Nocturnal Animals\'.\nTilrettelæggelse: Per Juul Carlsen.\nwww.dr.dk/film',
                'timestamp': 1483363467,
                'upload_date': '20170102',
            }
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)
        webpage = self._download_webpage(url, audio_id)

        programcard = self._download_json(
            'http://www.dr.dk/mu/programcard/expanded/%s' % audio_id,
            audio_id, 'Downloading audio JSON')
        data = programcard['Data'][0]

        title = remove_start(self._og_search_title(
            webpage, default=None), 'DR Netradio: Hør ') or data['Title']
        description = self._og_search_description(
            webpage, default=None) or data.get('Description')

        timestamp = parse_iso8601(data.get('CreatedTime'))

        duration = None
        thumbnail = "http://www.dr.dk/mu/programcard/imageuri/urn:dr:mu:programcard:%s" % audio_id

        restricted_to_denmark = False

        formats = []

        for asset in data['Assets']:
            if asset.get('Kind') == 'AudioResource':
                duration = float_or_none(asset.get('DurationInMilliseconds'), 1000)
                restricted_to_denmark = asset.get('RestrictedToDenmark')
                for link in asset.get('Links', []):
                    uri = link.get('Uri')
                    if not uri:
                        continue
                    target = link.get('Target')
                    ext = link.get('FileFormat')
                    format_id = target or ''
                    preference = None
                    if target == 'HDS':
                        preference = -2
                        hds_formats = self._extract_f4m_formats(
                            uri + '?hdcore=3.10.0&plugin=aasp-3.10.0.29.28',
                            audio_id, preference, f4m_id=format_id)
                        formats.extend(hds_formats)
                    elif target == 'HLS':
                        preference = -2
                        formats.extend(self._extract_m3u8_formats(
                            uri, audio_id, 'mp3', entry_protocol='m3u8_native',
                            preference=preference, m3u8_id=format_id))
                    else:
                        if target == 'Download':
                            format_id = '%s' % ext
                        bitrate = link.get('Bitrate')
                        if bitrate:
                            format_id += '-%s' % bitrate
                        if 'vodfiles.dr.dk' in uri:
                            preference = -3
                        formats.append({
                            'url': uri,
                            'format_id': format_id,
                            'tbr': int_or_none(bitrate),
                            'ext': ext,
                            'preference': preference,
                            'vcodec': 'none',
                        })

        if not formats and restricted_to_denmark:
            self.raise_geo_restricted(
                'Unfortunately, DR is not allowed to show this program outside Denmark.',
                expected=True)

        self._sort_formats(formats, field_preference=('preference', 'tbr', 'format_id'))

        return {
            'id': audio_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }
