import re
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict, Optional

from telegram import Message
import requests

from lxml import etree
from lxml.html import document_fromstring, Element

MEDIA_ATTRS: list[str] = ['photo', 'video', 'media_group_id']


class PostData(TypedDict):
    post_id: str
    title: str
    date: datetime
    edit_date: Optional[datetime]
    link: str
    html: str
    media_html: Optional[str]
    body: str


@dataclass
class PostParser:
    message: Message
    _element: Element = None

    @property
    def element(self):
        if not self._element:
            response = requests.get(
                url=self.message.link,
                params={'embed': 1},
            )
            self._element = document_fromstring(response.text)
        return self._element

    def get_html_by_xpath(self, xpath: str):
        return [
            etree.tostring(o).decode('utf-8') for o in self.element.xpath(xpath)
        ]

    def get_default_media(self):
        xpath = '//div[contains(@class, "js-message_text")]/preceding-sibling::div[contains(@class, "js-message")]'
        return self.get_html_by_xpath(xpath)

    def get_media_type_photo(self):
        xpath = '//div[contains(@class, "js-message_text")]/preceding-sibling::a[contains(@class, "photo")]'
        return self.get_html_by_xpath(xpath)

    def get_media(self):
        media = []
        for media_type in MEDIA_ATTRS:
            if exists := getattr(self.message, media_type):
                media_getter = getattr(
                    self,
                    f'get_media_type_{media_type}',
                    self.get_default_media,
                )
                media += media_getter()
        return media

    def get_media_html(self):
        return ''.join(self.get_media())

    def text_body(self):
        html = self.message.text_html_urled or self.message.caption_html_urled
        return f'<div class="tg_post_body">{html}</div>'

    @property
    def contains_media(self):
        return any([getattr(self.message, a) for a in MEDIA_ATTRS])

    @property
    def media_html(self):
        if not self.contains_media:
            return None
        return self.get_media_html()

    @property
    def post_id(self):
        return self.message.message_id

    @property
    def message_link(self):
        return self.message.link or ''

    @property
    def message_text_md(self):
        return self.message.text_markdown_v2 or self.message.caption_markdown_v2

    @property
    def message_text(self):
        return self.message.text or self.message.caption

    @property
    def title_match(self):
        return re.match(r'[^\n]?\*(?P<title>.+?)\*', self.message_text_md)

    @property
    def fallback_title(self):
        if not self.title_match:
            return ' '.join(self.message_text.splitlines()[0].split()[:10])

    @property
    def title(self):
        return self.fallback_title or self.title_match.groupdict()['title']

    @property
    def md(self):
        return (self.message.text_markdown_v2_urled
                or self.message.caption_markdown_v2_urled)

    @property
    def html(self):
        xpath = '//div[contains(@class, "js-message_text")]'
        return ''.join(self.get_html_by_xpath(xpath))

    @property
    def post_data(self):
        post_data: PostData = {
            'post_id': self.post_id,
            'title': self.title,
            'date': self.message.date,
            'edit_date': self.message.edit_date,
            'link': self.message_link,
            'html': '',
            'media_html': self.media_html,
            'body': self.html,
        }
        return post_data
