# coding: utf-8
import io
import os
import re
import logging
import string
from urllib.parse import quote
import urllib.request
from bs4 import BeautifulSoup

from ehforwarderbot import EFBMiddleware, EFBMsg, MsgType
from typing import Optional
from . import __version__ as version
# from link_preview import link_preview

class LinkPreview:
    def __init__(self, url):
        if any(ord(c) > 127 for c in url):
            url = quote(url, safe = string.printable)
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'}
        req = urllib.request.Request(url=url, headers=headers)
        self._html = urllib.request.urlopen(req).read().decode('utf-8')
        self._soup = BeautifulSoup(self._html, 'html.parser')
        self.title = self._get_title()
        self.desc = self._get_description()
        self.image = self._get_image()

    def _get_title(self):
        """
        Extract title from the given web page.
        """
        soup = self._soup
        # if title tag is present and has text in it, return it as the title
        if (soup.title and soup.title.text != ""):
            return soup.title.text
        # else if h1 tag is present and has text in it, return it as the title
        if (soup.h1 and soup.h1.text != ""):
            return soup.h1.text
        # if no title, h1 return None
        return None

    def _get_description(self):
        """
        Extract description from the given web page.
        """
        soup = self._soup
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
        return None

    def _get_image(self):
        """
        Extract preview image from the given web page.
        """
        soup = self._soup
        # extract the first image which is sibling to the first h1
        first_h1 = soup.find('h1')
        if first_h1:
            first_image = first_h1.find_next_sibling('img')
            if first_image and first_image['src'] != "":
                return first_image['src']
        return None

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

        # re_url = r'http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        re_url = r'https?:\/\/\S+'
        msg_text = message.text
        url = re.search(re_url, msg_text)
        if not url:
            return message
        url = url.group(0)
        
        try:
            # dict_elem = link_preview.generate_dict(url)
            # title = dict_elem['title']
            # description = dict_elem['description']
            lp = LinkPreview(url)
            # title, description, _ = web_preview(url)
            title = lp.title
            desc = lp.desc
        except Exception as e:
            self.logger.error("Failed to get link preview: {}".format(e))
            return message

        text = '\n'.join([
            msg_text,
            'preview'.center(23, '='),
            title.center(23),
            '-'*27,
            str(desc)
            ])
        
        message.text = text
        return message