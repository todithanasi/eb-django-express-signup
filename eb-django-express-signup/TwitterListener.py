from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import json
import os
import sys
import boto3
from dateutil import parser

GEO_TABLE = 'twitter-geo'
AWS_REGION = 'eu-west-1'


class MyListener(StreamListener):

    def __init__(self):
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        try:
            self.table = dynamodb.Table(GEO_TABLE)
        except Exception as e:
            print('\nError connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            sys.exit(-1)

    def on_data(self, data):
        tweet = json.loads(data)
        if not tweet['coordinates']:
            sys.stdout.write('.')
            sys.stdout.flush()
            return True
        try:
            response = self.table.put_item(
                Item={
                    'id': tweet['id_str'],
                    'c0': str(tweet['coordinates']['coordinates'][0]),
                    'c1': str(tweet['coordinates']['coordinates'][1]),
                    'text': tweet['text'],
                    "created_at": str(parser.parse(tweet["created_at"]).timestamp()),
                }
            )
        except Exception as e:
            print('\nError adding item to database: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
        else:
            status = response['ResponseMetadata']['HTTPStatusCode']
            if status == 200:
                sys.stdout.write('x')
                sys.stdout.flush()

    def on_error(self, status):
        print('status:%d' % status)
        return True


consumer_key = os.environ["CONSUMER_KEY_API"]
consumer_secret = os.getenv("CONSUMER_SECRET_API")
access_token = os.getenv("ACCESS_TOKEN_API")
access_secret = os.getenv("ACCESS_SECRET_API")


auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

twitter_stream = Stream(auth, MyListener())
twitter_stream.filter(locations=[-2.5756, 39.0147, 5.5982, 43.957])