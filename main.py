import tweepy
import datetime
from time import sleep
from os import environ
import psycopg2
import traceback
from fuzzywuzzy import process

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

def get_mentions(api, cur, since_id):
    print('Retrieving mentions')
    
    mentions = tweepy.Cursor(api.mentions_timeline, since_id=since_id).items()

    if len(mentions > 0):
        print(f'{len(mentions)} mentions')
        return mentions
    else:
        print('No mentions')
        return None

def learn(language, base_word, trans_word):
    if 'significa' in text:

        if '@tradubot' in text:
            text = text.replace('@tradubot','')
        if '@TraduBot' in text:
            text = text.replace('@TraduBot','')
    
        words      = text.split('significa')
        base_word  = words[0].strip()
        trans_word = words[1].strip()
        
        
        print(words[0].strip() + ' para ' + words[1].strip())
        

        cur.execute('select * from words where BASE_WORD = %s', (base_word,))
        exist = cur.fetchone()

        if exist is not None:
            tweetar(api,
                    f'A palavra {base_word} já existe no meu dicionário',
                    reply_to=tweet.id)
        
        else:
            print('inserindo na tabela...')
            cur.execute("insert into words(BASE_WORD, TRANS_WORD) values (%s, %s)",
                        (base_word, trans_word))
            tweetar(api,
                    f'Entendi! A palavra {base_word} siginifica {trans_word}!',
                    reply_to=tweet.id)

def meaning(language, word):
    if 'o que significa' in text.lower():
        base_word = text.replace('o que significa','')
        base_word = base_word.repalce('?','')
        base_word = base_word.repalce('!','')

        cur.execute('SELECT trans_word FROM words WHERE base_word = %s', base_word)

        trans_word = cur.fetchone()[0]

        tweetar(api,
                f'{base_word} significa {trans_word}',
                reply_to=tweet.id)

def translate(text, language):

    cur.execute('select BASE_WORD, TRANS_WORD from words')
    all_dict = cur.fetchall()
    
    for words in all_dict:
        if words[0] in text:
            text = text.replace(words[0], words[1])
    
    tweetar(api,
            text,
            reply_to=tweet.id)

def analysis(tweet):
    text = tweet.text.lower()

    languages = get_languages()

    # Remove no texto as linguagens que já existem
    for language in languages:
        text = text.replace(language, '')

    # Remove o @
    text = text.replace('@tradubot', '')

    print(f'Será avaliado o texto "{text}"')

    best_match = process.extractOne(text, get_texts_to_match())

    print(f'{best_match[0]} foi o melhor resultado com {best_match[1]}% de semelhança.')

    action = select_action_by_match(best_match[0])

    print(f'A ação selecionada é "{action}"')

    return action

def select_action_by_match(text):
    cur.execute(f'SELECT action FROM word_matching WHERE text = "{text}"";')
    return cur.fetchall()

def get_texts_to_match():
    cur.execute('SELECT text FROM word_matching;')
    return cur.fetchall()

def new_language(cursor, user_name, language):
    print(f'{user_name} is creating new language: {language.lower()}')

    try:
        cursor.execute(f'ALTER TABLE words ADD COLUMN {language.lower()} TEXT;')
        return True
    except:
        print('Error while creating new language')
        return False

def a(tweet):

    if tweet.in_reply_to_status_id is not None:
        pass
    
    print(f'Answering to {tweet.user.name}')

    if not tweet.user.following:
        tweet.user.follow()
    
    
             
    return new_since_id

def get_last_id(cursor):
    cursor.execute('SELECT last_id FROM last_id')
    return int(cursor.fetchone()[0])

def set_last_id(cursor, id):
    cursor.execute("UPDATE last_id SET last_id=%s WHERE id=1", [id])

def get_languages():
    
    cur.execute("""SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name   = 'words'
                    AND column_name NOT IN ('id','base_word')
                    ;""")

    return cur.fetchall()

def main():        
    api = create_api()

    tweetar(api, 'Iniciando...')

    while True:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()

        since_id = get_last_id(cur)

        print('O ID atual é: ' + str(since_id))

        last_since_id = since_id

        mentions = get_mentions(api, cur, since_id)

        if mentions is not None:
            for mention in mentions:
                last_since_id = max(mention.id, last_since_id)

                set_last_id(cur, last_since_id)

                action = analysis(mention)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print('Waiting...')
        sleep(30)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM words;")
    ret = cur.fetchall()
    for row in ret:
        print(row)
        
    conn.commit()
    cur.close()
    conn.close()
        
if __name__ == '__main__':
    main()
