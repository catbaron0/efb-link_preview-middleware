# coding: utf-8
import io
import os
import re
import logging
from typing import IO, Any, Dict, Optional, List, Tuple
from tempfile import NamedTemporaryFile

from ehforwarderbot import EFBMiddleware, EFBMsg, MsgType
from . import __version__ as version
from webpreview import web_preview

class LinkPreview(EFBMiddleware):
    """
    EFB Middleware - MessageBlockerMiddleware
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

        re_url = r'.*(https?:\/\/[\w\.\/]+)\s?.*'
        msg_text = message.text
        url = re.search(re_url, msg_text)
        if not url:
            return message
        
        url = url.group(1)
        try:
            title, description, _ = web_preview(url)
        except:
            self.logger.info("Failed to get link preview.")
            return message

        text = '\n'.join([
            msg_text,
            'preview'.center(23, '='),
            title.center(23),
            '-'*27,
            description
            ])
        
        message.text = text
        return message