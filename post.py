import re

from telegram import Message
import requests

from lxml import etree
from lxml.html import document_fromstring, Element

MEDIA_ATTRS: list[str] = ['photo', 'video', 'media_group_id']


class Post:
    _message: Message
    _element: Element = None

    @classmethod
    def from_message(cls, message: Message):
        post = cls()
        post._message = message
        return post

    @property
    def element(self):
        if not self._element:
            response = requests.get(
                url=self.message_link,
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
            if exists := getattr(self._message, media_type):
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
        html = self._message.text_html_urled or self._message.caption_html_urled
        return f'<div class="tg_post_body">{html}</div>'

    @property
    def contains_media(self):
        return any([getattr(self._message, a) for a in MEDIA_ATTRS])

    @property
    def media_html(self):
        if not self.contains_media:
            return None
        return self.get_media_html()

    @property
    def post_id(self):
        return self._message.forward_from_message_id or self._message.message_id

    @property
    def message_link(self):
        if self.is_forward:
            return f'{self._message.forward_from_chat.link.removesuffix("/")}' \
                   f'/{self._message.forward_from_message_id}'
        return self._message.link

    @property
    def message_text_md(self):
        return self._message.text_markdown_v2 or self._message.caption_markdown_v2

    @property
    def message_text(self):
        return self._message.text or self._message.caption

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
        return (self._message.text_markdown_v2_urled
                or self._message.caption_markdown_v2_urled)

    @property
    def html(self):
        xpath = '//div[contains(@class, "js-message_text")]'
        return ''.join(self.get_html_by_xpath(xpath))

    @property
    def is_forward(self):
        return bool(self._message.forward_from_message_id)

    @property
    def date(self):
        return self._message.forward_date if self.is_forward else self._message.date

    @property
    def edit_date(self):
        return self._message.date if self.is_forward else self._message.edit_date
