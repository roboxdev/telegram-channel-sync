import os
from dataclasses import dataclass
from urllib.parse import quote_plus

import requests
import yaml

from post_parser import PostData

GITLAB_API_TOKEN = os.environ.get('GITLAB_API_TOKEN')
REPOSITORY_BASE_URL = os.environ.get('REPOSITORY_BASE_URL')
TG_POST_FILE_PATH = os.environ.get('TG_POST_FILE_PATH',
                                   'content/tgposts/{}/index.md')


@dataclass
class GitlabPost:
    post_id: int
    branch: str = 'master'

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

    def create_or_update(self, post_data: PostData, is_update=False):
        to_dump = post_data.copy()

        title = post_data.get('title')
        date = post_data.get('date')
        body = to_dump.pop('body')

        isodate = date.isoformat()
        front_matter_yaml = yaml.dump(to_dump)

        md_file_template = f'---\n{front_matter_yaml}\n---\n{body}\n'

        action = 'Create new' if not is_update else 'Update'
        commit_message = f'{action} tgpost {self.post_id}: [{isodate}]: {title}'

        payload = {
            'branch': self.branch,
            'content': md_file_template.format(
                date=isodate,
                title=title,
            ),
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

        # return
        response = requests.delete(
            url=self.url,
            json=payload,
            headers=self.auth_headers,
        )
        if not response.ok:
            raise ValueError(f'{self.post_id}: {response.text}')
