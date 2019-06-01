# coding: utf-8
import io
import os
import re
import logging
import string
from urllib.parse import quote
import urllib.request
from tempfile import NamedTemporaryFile
from typing import Optional

from ehforwarderbot import EFBMiddleware, EFBMsg, MsgType
from bs4 import BeautifulSoup

from . import __version__ as version
# from link_preview import link_preview

class LinkPreview:
    def __init__(self, url):
        self.type = ''
        self.desc = ''
        self.title = ''
        self.image_url = ''
        self.image = None
        if any(ord(c) > 127 for c in url):
            url = quote(url, safe = string.printable)

        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'}
        try:
            req = urllib.request.Request(url=url, headers=headers)
        except: # if no schema add http as default
            url = "http://" + url
            req = urllib.request.Request(url=url, headers=headers)

        self._res = urllib.request.urlopen(req)
        self.type = self._res.info().get_content_type()
        if self.type.startswith('image'):
            self.image_url = url
        else:
            html = urllib.request.urlopen(req).read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            self.title = self._get_title(soup)
            self.desc = self._get_description(soup)
            self.image_url = self._get_image(soup)
        
        if self.image_url:
            self.image = self._read_url(self.image_url, headers)

    def _read_url(self, url, headers):
        req = urllib.request.Request(url=url, headers=headers)
        return urllib.request.urlopen(req).read()

    # _get_*() functions refer to https://github.com/ludbek/webpreview
    def _get_title(self, soup):
        """
        Extract title from the given web page.
        """
        # Extract title following OG
        try:
            og_site_name = soup.find('meta', attrs={'property': 'og:site_name'})['content']
        except:
            og_site_name = ''
        try:
            og_title = soup.find('meta', attrs={'property': 'og:title'})['content']
        except:
            og_title = ''
        if og_site_name and og_title:
            title = ' - '.join([og_site_name, og_title ])
        else:
            title = og_site_name + og_title
        if title:
            return title

        # if title tag is present and has text in it, return it as the title
        if (soup.title and soup.title.text != ""):
            return soup.title.text
        # else if h1 tag is present and has text in it, return it as the title
        if (soup.h1 and soup.h1.text != ""):
            return soup.h1.text
        # if no title, h1 return None
        return ""

    def _get_description(self, soup):
        """
        Extract description from the given web page.
        """
        # Extract title following OG
        try:
            og_description = soup.find('meta', attrs={'property': 'og:description'})['content']
        except:
            og_description = ''
        if og_description:
            return og_description

        # extract content preview from meta[name='description']
        meta_description = soup.find('meta',attrs = {"name" : "description"})
        if(meta_description and meta_description['content'] !=""):
            return meta_description['content']
        # else extract preview from the first <p> sibling to the first <h1>
        first_h1 = soup.find('h1')
        if first_h1:
            first_p = first_h1.find_next('p')
            if (first_p and first_p.string != ''):
                return first_p.text
        # else extract preview from the first <p>
        first_p = soup.find('p')
        if (first_p and first_p.string != ""):
            return first_p.string
        # else
        return ""

    def _get_image(self, soup):
        """
        Extract preview image from the given web page.
        """
        # Extract title following OG
        try:
            og_image = soup.find('meta', attrs={'property': 'og:image'})['content']
        except:
            og_image = ''
        if og_image:
            return og_image

        # extract the first image which is sibling to the first h1
        first_h1 = soup.find('h1')
        if first_h1:
            first_image = first_h1.find_next_sibling('img')
            if first_image and first_image['src'] != "":
                return first_image['src']
        return ""

class LinkPreviewMiddleware(EFBMiddleware):
    """
    EFB Middleware - LinkPreviewMiddleware
    An extension for link preview.
    Author: Catbaron <https://github.com/catbaron>
    """

    middleware_id = "catbaron.link_preview"
    middleware_name = "Link Preview Middleware"
    __version__ = version.__version__
    logger: logging.Logger = logging.getLogger("plugins.%s.MessageLinkPreviewMiddleware" % middleware_id)


    def __init__(self, instance_id=None):
        super().__init__()

    def sent_by_master(self, message: EFBMsg) -> bool:
        author = message.author
        if author and author.module_id and author.module_id == 'blueset.telegram':
            return True
        else:
            return False

    def process_message(self, message: EFBMsg) -> Optional[EFBMsg]:
        """
        Process a message with middleware

        Args:
            message (:obj:`.EFBMsg`): Message object to process

        Returns:
            Optional[:obj:`.EFBMsg`]: Processed message or None if discarded.
        """
        if not self.sent_by_master(message):
            return message

        msg_text = message.text
        if msg_text.startswith('\\np '):
            message.text = msg_text[3:]
            return message

        # re_url = r'https?:\/\/\S+'
        # taken from django https://github.com/django/django/blob/master/django/core/validators.py#L68
        valid_url = re.compile(
            r'(https?://)?'  # scheme is validated separately
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}(?<!-)\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:[/?]\S+|[/?])?', re.IGNORECASE)
        url = valid_url.search(msg_text)
        if not url:
            return message

        url = url.group(0)
        try:
            lp = LinkPreview(url)
            title = lp.title
            desc = lp.desc
        except Exception as e:
            self.logger.error("Failed to get link preview: {}".format(e))
            return message

        text = msg_text
        if title or desc:
            text = '\n'.join([msg_text, 'preview'.center(23, '='), title.center(23), '-'*27, str(desc), ])

        if lp.type.startswith('image') and lp.image:
            suffix = os.path.splitext(lp.image_url)[1]
            message.file = NamedTemporaryFile(suffix=suffix)
            message.filename = os.path.basename(message.file.name)
            message.file.write(lp.image)
            message.file.file.seek(0)
            message.type = MsgType.Image
            message.mime = lp.type
            message.path = message.file.name

        message.text = text
        return message
