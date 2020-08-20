import tweepy
import datetime
from time import sleep
from os import environ
import psycopg2
import traceback
from fuzzywuzzy import fuzz



class tradubot():
    def __init__(self):
        DATABASE_URL = environ['DATABASE_URL']

        self.api = self.create_api()

        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.cur = self.conn.cursor()

        self.tweetar('Iniciando...')

    def main(self):        
        while True:

            since_id = self.get_last_id()

            print('O ID atual é: ' + str(since_id))

            last_since_id = since_id

            mentions =self.get_mentions(since_id)

            for mention in mentions:
                
                last_since_id = max(mention.id, last_since_id)

                if mention.in_reply_to_status_id is not None:
                    pass
        
                print(f'Answering to {mention.user.name}')

                if not mention.user.following:
                    mention.user.follow()

                action, text, best_match, language = self.analysis(mention)

                if action == 'create':
                    if ':' in text:
                        new_language_name = text.split(':')[-1]

                    elif ',' in text:
                        new_language_name = text.split(',')[-1]

                    else:
                        new_language_name = text.split()[-1]


                    sucess = self.new_language(mention.user.name, new_language_name)
                    
                    if sucess:
                        self.tweetar(f'O idioma {new_language_name.upper()} foi criado por {mention.user.name}')

                    else:
                        self.tweetar('Alguma coisa deu errado! Entre em contato por DM por favor.', reply_to=mention.id)
                
                elif action == 'learn':
                    sucess = self.learn(text, best_match, language)


                self.set_last_id(last_since_id) 

            self.conn.commit()
            
            print('Waiting...')
            sleep(60)

        cur.close()
        conn.close()

    def analysis(self, tweet):
        text = tweet.text.lower()

        languages = self.get_languages()

        # Remove no texto as linguagens que já existem
        for language in languages:
            print(language[0])
            if language[0] in text:
                text = text.replace(language[0], 'LANGUAGE')
                language = language[0]
                break
        
        # Remove o @
        text = text.replace('@tradubot', '')


        print(f'Será avaliado o texto "{text}"')

        best_score = 0
        best_match = ''
        
        for text_to_match in self.get_texts_to_match():
            text_to_match = text_to_match[0]

            text_splited          = text.split(' ')
            print(text_splited)
            text_to_match_splited = text_to_match.split(' ')
            print(text_to_match_splited)

            for word in text_splited:
                if word.strip() not in text_to_match_splited:
                    text_new = text.replace(word, '')
            
            score = fuzz.token_set_ratio(text_to_match, text_new)

            print(f'{score} - {text_to_match} versus {text_new}')

            if score > best_score:
                best_match = text_to_match
                best_score = score

        #best_match = process.extractOne(text, self.get_texts_to_match())

        print(f'{best_match} foi o melhor resultado com {best_score}% de semelhança.')

        action = self.select_action_by_match(best_match)[0][0]

        print(f'A ação selecionada é "{action}"')

        return action, text, best_match[0][0], language

    def create_api(self):
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

    def tweetar(self, msg, reply_to=None):
        try:
            if reply_to != None:
                self.api.update_status(status=msg,
                                       in_reply_to_status_id=reply_to,
                                       auto_populate_reply_metadata=True)
            elif reply_to == None:
                self.api.update_status(status=msg)

        except tweepy.TweepError as e:
            if e.api_code == 187:
                print('Duplicated message')
            else:
                raise error

    def get_mentions(self, since_id):
        print('Retrieving mentions')
        
        mentions = tweepy.Cursor(self.api.mentions_timeline, since_id=since_id).items()

        return mentions

    def learn(self, text, best_match, language):
        separated_text = eval(self.select_separated_text_by_match(best_match)[0][0])

        text = text.split()

        for num, part in enumerate(separated_text):
            if part == 'BASE_WORD':
                base_word = text[num + 1]
            elif part == 'TRANS_WORD':
                trans_word = text[num + 1]

        print(f'Base_word: {base_word}')
        print(f'Trans_word: {trans_word}')
        print(f'Language: {language}')
        
    def meaning(self, language, word):
        if 'o que significa' in text.lower():
            base_word = text.replace('o que significa','')
            base_word = base_word.repalce('?','')
            base_word = base_word.repalce('!','')

            cur.execute('SELECT trans_word FROM words WHERE base_word = %s', base_word)

            trans_word = cur.fetchone()[0]

            self.tweetar(api,
                    f'{base_word} significa {trans_word}',
                    reply_to=tweet.id)

    def translate(self, text, language):

        cur.execute('select BASE_WORD, TRANS_WORD from words')
        all_dict = cur.fetchall()
        
        for words in all_dict:
            if words[0] in text:
                text = text.replace(words[0], words[1])
        
        self.tweetar(api,
                text,
                reply_to=tweet.id)
    
    def select_separated_text_by_match(self, match):
        self.cur.execute(f"SELECT separated_text FROM word_matching WHERE text = '{match}';")
        return self.cur.fetchall()

    def select_action_by_match(self, text):
        self.cur.execute(f"SELECT action FROM word_matching WHERE text = '{text}';")
        return self.cur.fetchall()

    def get_texts_to_match(self):
        self.cur.execute("SELECT text FROM word_matching;")
        return self.cur.fetchall()

    def new_language(self, user_name, language):
        print(f'{user_name} is creating new language: {language.lower()}')

        try:
            self.cur.execute(f'ALTER TABLE words ADD COLUMN {language.lower()} TEXT;')
            return True
        except:
            print('Error while creating new language')
            return False

    def get_last_id(self):
        self.cur.execute("SELECT last_id FROM last_id")
        return int(self.cur.fetchone()[0])

    def set_last_id(self, id):
        self.cur.execute("UPDATE last_id SET last_id=%s WHERE id=1", [id])

    def get_languages(self):
        
        self.cur.execute("""SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                            AND table_name   = 'words'
                            AND column_name NOT IN ('id','base_word')
                            ;""")

        return self.cur.fetchall()

    
        
if __name__ == '__main__':
    bot = tradubot()
    bot.main()
