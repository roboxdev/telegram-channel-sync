import os
from urllib.parse import quote_plus

import requests
import yaml

from post import Post

GITLAB_API_TOKEN = os.environ.get('GITLAB_API_TOKEN')
REPOSITORY_BASE_URL = os.environ.get('REPOSITORY_BASE_URL')
TG_POST_FILE_PATH = os.environ.get('TG_POST_FILE_PATH',
                                   'content/tgposts/{}/index.md')


class GitlabPost:
    branch: str = 'master'
    _post: Post = None
    _post_id: int = None

    @classmethod
    def from_post(cls, post: Post):
        gitlab_post = cls()
        gitlab_post._post = post
        return gitlab_post

    @classmethod
    def from_id(cls, post_id: int):
        gitlab_post = cls()
        gitlab_post._post_ = post_id
        return gitlab_post

    @property
    def post_id(self):
        return self._post_id or self.post.post_id

    @property
    def post(self):
        return self._post

    @property
    def auth_headers(self):
        return {
            'Authorization': 'Bearer {}'.format(GITLAB_API_TOKEN),
        }

    @property
    def url(self):
        filepath = TG_POST_FILE_PATH.format(self.post_id)
        url = '{}/{}'.format(REPOSITORY_BASE_URL, quote_plus(filepath))
        return url

    @property
    def front_matter(self):
        return yaml.dump({
            'post_id': self.post_id,
            'title': self.post.title,
            'date': self.post.date,
            'edit_date': self.post.edit_date,
            'link': self.post.message_link,
            'html': '',
            'media_html': self.post.media_html,
        })

    def get(self):
        response = requests.get(
            url=self.url,
            headers=self.auth_headers,
        )
        if response.status_code == requests.codes.not_found:
            pass

    def create_or_update(self, is_update=False):
        post = self.post

        action = 'Create new' if not is_update else 'Update'
        commit_message = f'{action} tgpost {self.post_id}: [{post.date}]: {post.title}'

        payload = {
            'branch': self.branch,
            'content': f'---\n{self.front_matter}\n---\n{post.html}\n',
            'commit_message': commit_message,
        }

        response = requests.request(
            method='PUT' if is_update else 'POST',
            url=self.url,
            json=payload,
            headers=self.auth_headers,
        )
        if not response.ok:
            raise ValueError(f'{self.post_id}: {response.text}')

    def delete(self):
        commit_message = f'Delete tgpost {self.post_id}'

        payload = {
            'branch': self.branch,
            'commit_message': commit_message,
        }

        response = requests.delete(
            url=self.url,
            json=payload,
            headers=self.auth_headers,
        )
        if not response.ok:
            raise ValueError(f'{self.post_id}: {response.text}')
