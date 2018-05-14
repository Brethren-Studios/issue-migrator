#!/usr/bin/python3

"""
Copyright (c) 2018 Brethren Studios

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import hashlib
import json
import os
import requests
import sys
import time


__author__ = 'Evan Williams'
__copyright__ = "Copyright 2018, Brethren Studios"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "evanw555@gmail.com"


RATELIMIT_RESET_KEY = 'X-RateLimit-Reset'
CACHE_DIR = '.issuedata_cache'

authentication = None  # Should be a (username, password) tuple if authenticating

url_hash_cache = set()


class GitHubIssue:

    def __init__(self, data):
        self.assignee_login = data['assignee']['login'] if data['assignee'] else ''
        self.body = data.get('body', '')
        self.created_at = data['created_at']
        self.is_pr = 'pull_request' in data
        self.label_name = data['labels'][0]['name'] if data['labels'] else ''
        self.milestone_title = data['milestone']['title'] if data['milestone'] else ''
        self.number = data.get('number', 0)
        self.state = data.get('state', 'closed')
        self.title = data.get('title', 'Untitled')
        self.updated_at = data['updated_at']
        self.user_login = data['user']['login'] if data['user'] else ''

        self.comments = GitHubComment.from_url(data.get('comments_url')) if data.get('comments', 0) > 0 else []

    def __str__(self):
        return '{} #{}: {} [{}, {}, {} comment(s)]'.format('   PR' if self.is_pr else 'Issue', self.number, self.title[:20], self.label_name, self.state, len(self.comments))

    def from_url(url):
        issues = []
        while url:
            response = get_from_url(url)

            issues.extend([GitHubIssue(data=data) for data in response['body']])

            url = response['next_url']
        return issues


class GitHubComment:

    def __init__(self, data):
        self.body = data.get('body', '')
        self.created_at = data['created_at']
        self.id = data['id']
        self.updated_at = data['updated_at']
        self.user_login = data['user']['login']

    def from_url(url):
        comments = []
        while url:
            response = get_from_url(url)

            comments.extend([GitHubComment(data=data) for data in response['body']])

            url = response['next_url']
        return comments


class BitBucketIssue:
    status_map = {
        'open': 'open',
        'closed': 'resolved'
    }

    kind_map = {
        'bug': 'bug',
        'enhancement': 'enhancement',
        'feature': 'enhancement',
        'cleanup': 'enhancement',
        'question/comment': 'proposal',
        'workflow': 'enhancement',
        'graphics': 'enhancement',
        'content': 'enhancement'
    }

    def __init__(self, github_issue):
        if not isinstance(github_issue, GitHubIssue):
            raise Error('Must initialize BitBucketIssue with a GitHubIssue')

        self.assignee = github_issue.user_login if github_issue.is_pr else github_issue.assignee_login
        self.content = github_issue.body
        self.content_updated_on = github_issue.updated_at
        self.created_on = github_issue.created_at
        self.id = github_issue.number
        self.kind = self.kind_map.get(github_issue.label_name, 'enhancement')
        self.milestone = github_issue.milestone_title
        self.priority = 'minor'  # trivial, minor, major, critical, blocker
        self.reporter = github_issue.user_login
        self.status = self.status_map.get(github_issue.state, 'open')
        self.title = ('[PR] ' if github_issue.is_pr else '') + github_issue.title
        self.updated_on = github_issue.updated_at
        
        self.comments = [BitBucketComment(github_comment=comment, issue_id=github_issue.number) for comment in github_issue.comments]

    def __str__(self):
        return '#{}: {} [{}->{}, {}, {}, {}, {} comment(s)]'.format(self.id, self.title[:20], self.reporter, self.assignee, self.kind, self.status, self.milestone, len(self.comments))

    def to_datamap(self):
        return {
            'assignee': self.assignee,
            'content': self.content,
            'content_updated_on': self.content_updated_on,
            'created_on': self.created_on,
            'id': self.id,
            'kind': self.kind,
            'milestone': self.milestone,
            'priority': self.priority,
            'reporter': self.reporter,
            'status': self.status,
            'title': self.title,
            'updated_on': self.updated_on
        }


class BitBucketComment:

    def __init__(self, github_comment, issue_id):
        self.content = github_comment.body
        self.created_on = github_comment.created_at
        self.id = github_comment.id
        self.issue = issue_id
        self.updated_on = github_comment.updated_at
        self.user = github_comment.user_login

    def to_datamap(self):
        return {
            'content': self.content,
            'created_on': self.created_on,
            'id': self.id,
            'issue': self.issue,
            'updated_on': self.updated_on,
            'user': self.user
        }


def initialize_cache():
    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    for file in os.listdir(CACHE_DIR):
        if file.endswith('.json'):
            url_hash_cache.add(file[:-5])

def hash_url(url):
    h = hashlib.sha256()
    h.update(url.encode('utf-8'))
    return h.hexdigest()


def get_from_cache(url_hash):
    with open('{0}/{1}.json'.format(CACHE_DIR, url_hash), 'r') as fin:
        return json.loads(fin.read())


def write_to_cache(url_hash, data):
    with open('{0}/{1}.json'.format(CACHE_DIR, url_hash), 'w') as fout:
        fout.write(json.dumps(data))
        fout.close()
    url_hash_cache.add(url_hash)


def get_from_url(url):
    url_hash = hash_url(url)

    if url_hash in url_hash_cache:
        # print('cache {0}'.format(url))
        return get_from_cache(url_hash) 
    else:
        # print('get {0}'.format(url))
        response = requests.get(url, auth=authentication)

        if not response.ok:
            if RATELIMIT_RESET_KEY in response.headers:
                minutes_left = int((int(response.headers[RATELIMIT_RESET_KEY]) - time.time()) / 60)
                sys.stderr.write('Rate limit exceeded. You may make more requests again in {0} minutes'.format(minutes_left))
            else:
                sys.stderr.write(response.text)
            sys.exit(1)

        data = {
            'body': json.loads(response.text),
            'next_url': response.links['next']['url'] if response.links and 'next' in response.links else None
        }

        write_to_cache(url_hash, data)
        return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate GitHub issue data to import-ready BitBucket issue data.')
    parser.add_argument('-o', dest='org', required=True, help='Name of the organization that owns the GitHub repo')
    parser.add_argument('-r', dest='repo', required=True, help='Name of the GitHub repo')
    parser.add_argument('-u', dest='username', help='Username to authneticate requests')
    parser.add_argument('-p', dest='password', help='Password to authneticate requests')

    args = parser.parse_args()

    # Parse authentication information
    if bool(args.username) ^ bool(args.password):
        print('Must specify both username and password if authenticating!')
        sys.exit(1)
    elif args.username and args.password:
        authentication = (args.username, args.password)

    # Start fetching issue data
    if args.org and args.repo:

        initialize_cache()

        github_issues = GitHubIssue.from_url('https://api.github.com/repos/{0}/{1}/issues?state=all&per_page=100'.format(args.org, args.repo))
        bitbucket_issues = [BitBucketIssue(github_issue=issue) for issue in github_issues]
        bitbucket_comments = [comment for bitbucket_issue in bitbucket_issues for comment in bitbucket_issue.comments]

        bitbucket_data = {
            'issues': [issue.to_datamap() for issue in bitbucket_issues],
            'comments': [comment.to_datamap() for comment in bitbucket_comments],
            'attachments': [],
            'logs': [],
            'meta': {
                'default_kind': 'enhancement'
            },
            'components': [],
            'milestones': [
                {
                    'name': milestone
                }
                for milestone in list(set([issue.milestone for issue in bitbucket_issues if issue.milestone]))
            ],
            'versions': []
        }

        sys.stdout.write(json.dumps(bitbucket_data, indent=4, sort_keys=True))
        sys.stdout.close()
