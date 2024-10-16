import sqlite3

class Datenbank():
    def __init__(self):
        self.connection = sqlite3.connect('include/users.db')
        # cursor gibt Json-Objekt zurück
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    id          LONGINT NOT NULL PRIMARY KEY,
                    username        VARCHAR (30),
                    first_name      VARCHAR (20),
                    last_name       VARCHAR (20),
                    is_bot          BOOLEAN,
                    language_code   VARCHAR (3)
                )
                ''')

    def add_user(self, data):
        print('type_data', type(data))
        print(data)
        self.cursor.execute(f'''
            INSERT OR REPLACE INTO users (
                id, username, first_name, last_name, is_bot, language_code
            )   VALUES(
                '{data.get('id')}','{data.get('username')}','{data.get('first_name')}', 'None',
                {data.get('is_bot')},'{data.get('language_code')}'
            )
        ''')
        return self.cursor


    def get_user_data_db(self, id):
        self.cursor.execute(f'''
            SELECT *
            FROM users
            WHERE id = {id}
        ''')
        if self.cursor is not None:
            return self.cursor.fetchone()
            
        return None
            


    def get_user_data_json(self, chatId=0):
        if type(chatId) != int:
            print("chatID muss Integer sein")
            #TODO LOGGING
            return {}
        if chatId != 0:
            db = self.get_db_json()
            print("get_user_data ", db)
            print("chatid ", chatId)
            for ud in db.items():
                print(ud)
            user_data = db[f'{chatId}']
            if user_data is not None: return user_data
            else: return None
        return{}

    def main():
        print("db.py")

    if __name__=="__main__":
        main()