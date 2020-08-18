import tweepy
import datetime
from time import sleep
import logging
from os import environ
import psycopg2

DATABASE_URL = environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = con.cursor()

def create_api():

    API_KEY       = environ['API_KEY']
    API_SECRET    = environ['API_SECRET']
    ACCESS_KEY    = environ['ACCESS_KEY']
    ACCESS_SECRET = environ['ACCESS_SECRET']
    
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)

    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

    api = tweepy.API(auth)

    try:
        api.verify_credentials()
    except Exception as e:
        logging.error('Error creating API', exc_info=True)
        raise e
    logging.info('API created')

    return api

def tweetar(api, msg, reply_to=None):
    try:
        if reply_to != None:
            api.update_status(status=msg,
                                in_reply_to_status_id=reply_to,
                                auto_populate_reply_metadata=True)
        elif reply_to == None:
            api.update_status(status=msg)

    except tweepy.TweepError as e:
        if e.api_code == 187:
            print('Duplicated message')
        else:
            raise error

def check_mentions(api, since_id):
    logging.info('Retrieving mentions')
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None:
            continue
        
        logging.info(f'Answering to {tweet.user.name}')

        if not tweet.user.following:
            tweet.user.follow()

        #tweetar(api, 
        #        f'Olá {tweet.user.name} ainda estou em testes, não sei responder muita coisa.',
        #        reply_to=tweet.id)
        if 'significa' in tweet.text:
            words = tweet.text.split('siginifica')
            sql = 'insert into Tradutor(Base_word, Trans_word) values ({}, {})'.format(words[0], words[1])


    return new_since_id

def main():        
    api = create_api()

    tweetar(api, 'Iniciando...')

    while True:

        since_id = int(environ['SINCE_ID'])

        since_id = check_mentions(api, since_id)

        environ['SINCE_ID'] = str(since_id)

        logging.info('Waiting...')
        sleep(60)

if __name__ == '__main__':
    main()