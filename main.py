import tweepy
import datetime
import configparser

keys = configparser.ConfigParser()
keys.read('keys.ini')

auth = tweepy.OAuthHandler(keys.get('keys', 'API_key'),
                           keys.get('keys', 'API_key_s'))

auth.set_access_token(keys.get('keys', 'acess_tkn'),
                      keys.get('keys', 'acess_tkn_s'))

api = tweepy.API(auth)

api.update_status('Esse tweet é pythonico!')