# -*- coding: UTF-8 -*-
import sys
import os
import inspect
import time
import json
import tweepy
import csv

from datetime import datetime, timedelta
from pytz import timezone
from tweepy.error import TweepError
from tweepy.parsers import JSONParser


def parse_tweet_entities(entities):
    entities_dict = {
        'urls'          : [url['expanded_url'] for url in entities['urls']],
        'user_mentions' : [mention['screen_name'] for mention in entities['user_mentions']],
        'hashtags'      : [ht['text'] for ht in entities['hashtags']],
        'media'         : []
    }

    if 'media' in entities.keys():
        entities_dict['media'] = [item['media_url_https'] for item in entities['media'] if 'media' in entities.keys()]

    return entities_dict

def parse_tweet(status, replies):
    status = status._json

    reply_count = 0
    if status['id_str'] in replies:
        reply_count = replies[status['id_str']]

    parsed_status_dict = {
        'tweet': {
            'text': status['text'],
            'retweet_count': status['retweet_count'],
            'id': status['id_str'],
            'in_reply_to_user_id_str': status['in_reply_to_user_id_str'],
            'in_reply_to_screen_name': status['in_reply_to_screen_name'],
            'in_reply_to_status_id_str': status['in_reply_to_status_id_str'],
            'reply_count': reply_count,
            'created_at': status['created_at'],
            'updated_at': datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            'user_id': status['user']['id_str'],
            'likes': status['favorite_count'],
            'code': None
        },
        'user': {
            'name': status['user']['name'],
            'likes': status['user']['favourites_count'],
            'URL': status['user']['url'],
            'id': status['user']['id_str'],
            'followers_count': status['user']['followers_count'],
            'description': 'Hillary Clinton' if status['user']['screen_name'] == 'HillaryClinton' else status['user']['description'],
            'statuses_count': status['user']['statuses_count'],
            'user_name': status['user']['screen_name']
        }
    }

    return parsed_status_dict

def run_insert(filename, type):
    with open(filename, 'r') as infile:
        lines = infile.readlines()
        for line in lines:
            try:
                if(type == 'tweet'):
                    insert_tweet_data(json.loads(line))
                else:
                    insert_reply_tweet_data(json.loads(line))
            except:
                pass

    os.remove(filename)

def timeline(filename, handle, replies, api):
    status_count = 0
    with open(filename, 'a') as outfile:
        timeline = tweepy.Cursor(api.user_timeline, screen_name=handle, count=200).items()
        collecting = True

        while collecting:
            try:
                status = next(timeline)
                parsed_status = parse_tweet(status, replies)

                outfile.write(json.dumps(parsed_status).encode('utf-8'))
                outfile.write('\n')
                status_count += 1

            except TweepError as e:
                print e
                print('Received timeout. Sleeping for 15 minutes.')
                time.sleep(15 * 60)

            except StopIteration as e:
                collecting = False

    return status_count

def replies(filename, handle, api):
    reply_count = 0
    reply_counts_dict = {}
    utc = timezone('UTC')

    with open(filename, 'a') as outfile:
        search_results = tweepy.Cursor(
            api.search,
            q='to:{}'.format(handle),
            result_type='recent',
            count=100
        ).items()

        collecting = True
        while collecting:
            try:
                status = next(search_results)
                parsed_status = status._json
                reply_id = parsed_status['in_reply_to_status_id_str']
                reply_tweet = parse_tweet(status, '')

                if reply_id is not None:
                    if reply_id in reply_counts_dict:
                        reply_counts_dict[reply_id] += 1
                    else:
                        reply_counts_dict[reply_id] = 1
                    reply_count += 1
                    outfile.write(json.dumps(reply_tweet).encode('utf-8'))
                    outfile.write('\n')

            except TweepError as e:
                print('Received timeout. Sleeping for 15 minutes.',e)
                time.sleep(15 * 60)

            except StopIteration as e:
                collecting = False

    return reply_count, reply_counts_dict

def collect(auth, handle):

    api_auth = tweepy.OAuthHandler(auth['consumer_key'], auth['consumer_secret'])
    api_auth.set_access_token(auth['access_token'], auth['access_token_secret'])
    api = tweepy.API(api_auth)

    print('COLLECTING FOR: {}'.format(handle))
    print()

    if api.verify_credentials:
        print('Successfully authenticated with Twitter.')
    else:
        print('Failed to authenticate with Twitter. Please try again.')
        sys.exit(1)

    reply_counts_dict = []
    reply_count = 0

    filename = 'output/account_comment/tw_comment_{}.json'.format(handle)

    print('Collecting replies...')
    reply_count, reply_counts_dict = replies(filename, handle, api)
    print('TOTAL Replies Collected: {}'.format(reply_count))
    print('')

    #print('Now inserting replies...')
    #run_insert(filename, 'reply')
    #print('Insertion completed')
    #print('')

    filename = 'output/account_media/tw_post_{}.json'.format(handle)
    print('Collecting {}\'s timeline'.format(handle))
    status_count = timeline(filename, handle, reply_counts_dict, api)
    print('')
    print('TOTAL Tweets Collected: {}'.format(status_count))
    print('')

    #print('Now inserting...')
    #run_insert(filename, 'tweet')
    #print('Insertion completed')
    #print('')


def run_timeline(auth):

    csvfile = open("../microceleb-users.csv", "r")
    users = csv.DictReader(csvfile, delimiter=',')

    error = []
    for u in users:
        username = u['tw_name'].strip()
        collect(auth, username)

        #time.sleep(20 * 60)
