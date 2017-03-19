import sys
import os
from timeline_dev import run_timeline


AUTH = {
    'consumer_key': '',
    'consumer_secret': '',
    'access_token': '
    'access_token_secret': ''
}
def init():
    # Create directories
    directory = './output/account_stat'
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory = './output/account_media'
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory = './output/account_comment'
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory = './output/account_media_around'
    if not os.path.exists(directory):
        os.makedirs(directory)


def main(method):
    methods = ['timeline', 'reply', 'init']
    method = method.strip('--')

    if method not in methods:
        print('ERROR: Invalid method. Please include a valid method.')
        sys.exit(1)
    elif method == 'init':
        init()
    elif method == 'timeline':
        run_timeline(AUTH)


if __name__ == '__main__':
    method = sys.argv[1]
    main(method)
