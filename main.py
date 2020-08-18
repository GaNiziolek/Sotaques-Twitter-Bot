import tweepy
import datetime
from time import sleep
from os import environ
import psycopg2
import traceback

DATABASE_URL = environ['DATABASE_URL']


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
        print('Error creating API')
        print(traceback.format_exc())
        raise e
    print('API created')

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

def check_mentions(api, cur, since_id):
    print('Retrieving mentions')
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None:
            continue
        
        print(f'Answering to {tweet.user.name}')

        if not tweet.user.following:
            tweet.user.follow()

        #tweetar(api, 
        #        f'Olá {tweet.user.name} ainda estou em testes, não sei responder muita coisa.',
        #        reply_to=tweet.id)
        
  
        text = tweet.text
        if 'significa' in text:

            if '@tradubot' in text:
                text = text.replace('@tradubot','')
            if '@TraduBot' in text:
                text = text.replace('@TraduBot','')
        
            words      = text.split('significa')
            base_word  = words[0].strip()
            trans_word = words[1].strip()
            
            
            print(words[0].strip() + ' para ' + words[1].strip())
            

            cur.execute('select * from TRADUTOR where BASE_WORD = %s', (base_word,))
            exist = cur.fetchone()

            if exist is not None:
                tweetar(api,
                        f'A palavra {base_word} já existe no meu dicionário',
                        reply_to=tweet.id)
            
            else:
                print('inserindo na tabela...')
                cur.execute("insert into TRADUTOR(BASE_WORD, TRANS_WORD) values (%s, %s)",
                            (base_word, trans_word))
                tweetar(api,
                        f'Entendi! A palavra {base_word} siginifica {trans_word}!',
                        reply_to=tweet.id)
        else:
            cur.execute('select BASE_WORD, TRANS_WORD from TRADUTOR')
            all_dict = cur.fetchall()
            
            for words in all_dict:
                if words[0] in text:
                    text = text.replace(words[0], words[1])
            
            tweetar(api,
                    text,
                    reply_to=tweet.id)
             
    return new_since_id

def main():        
    api = create_api()

    tweetar(api, 'Iniciando...')

    while True:

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()

        since_id = int(environ['SINCE_ID'])

        since_id = check_mentions(api, cur, since_id)
        
        environ['SINCE_ID'] = str(since_id)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print('Waiting...')
        sleep(60)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM TRADUTOR;")
    ret = cur.fetchall()
    for row in ret:
        print(row)
        
    conn.commit()
    cur.close()
    conn.close()
        
if __name__ == '__main__':
    main()
