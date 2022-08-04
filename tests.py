from unittest import TestCase
from post_parser import PostParser


class PostParserTestCase(TestCase):
    def test_title_parsing(self):
        p = PostParser(None)

        message_text = 'Lorem ipsum dolor sit amet, consectetur\n\nadipiscing elit'

        lorem = '*Lorem ipsum dolor sit amet, consectetur*\n\n*adipiscing elit*'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertFalse(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur', p.title)

        lorem = 'Lorem ipsum dolor sit *amet, consectetur*\n\nadipiscing elit'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertTrue(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur', p.title)

        lorem = 'Lorem ipsum dolor *sit amet,* consectetur\n\nadipiscing elit'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertTrue(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur', p.title)

        lorem = '*Lorem ipsum dolor sit amet,* consectetur\n\nadipiscing elit'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertFalse(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet,', p.title)

        lorem = 'Lorem ipsum [*dolor sit*](https://example.com/) amet, consectetur\n\nadipiscing elit'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertTrue(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur', p.title)

        lorem = 'Lorem *ipsum *[*dolor*](https://example.com/) [sit](https://example.com/) amet, consectetur\n\nadipiscing elit'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertTrue(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur', p.title)

        lorem = '[*Lorem ipsum dolor sit amet, consectetur\n\nadipiscing elit*](https://example.com/)'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertTrue(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur', p.title)

        lorem = 'Lorem ipsum dolor sit amet, consectetur\n\nadipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua\. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat\. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur\. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum\.'
        message_text = 'Lorem ipsum dolor sit amet, consectetur\n\nadipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertTrue(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur', p.title)

        lorem = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor\n\nincididunt ut labore et dolore magna aliqua\. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat\. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur\. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum\.'
        message_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor\n\nincididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
        setattr(PostParser, 'message_text_md', lorem)
        setattr(PostParser, 'message_text', message_text)
        self.assertTrue(p.fallback_title)
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do', p.title)
