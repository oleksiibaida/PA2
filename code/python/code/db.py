import sqlite3

class Datenbank():
    def __init__(self):
        print("init DB")
        self.connection = sqlite3.connect('include/users.db')
        # cursor gibt Json-Objekt zurück
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    id          LONGINT NOT NULL PRIMARY KEY,
                    username        VARCHAR (30),
                    device_id       VARCHAR (10),
                    first_name      VARCHAR (20),
                    last_name       VARCHAR (20),
                    is_bot          BOOLEAN,
                    language_code   VARCHAR (3),
                    added_at        TIMESTAMP
                )
                ''')
        self.connection.commit()

    def add_user(self, user_data, device_id):
        print('type_data', type(user_data))
        if type(user_data) is not dict: return
        #print(data)
        self.cursor.execute(f'''
            INSERT OR REPLACE INTO users (
                id, username, device_id, first_name, last_name, is_bot, language_code, added_at
            )   VALUES(
                '{user_data.get('id')}','{user_data.get('username')}','{device_id}','{user_data.get('first_name')}', 'None',
                {user_data.get('is_bot')},'{user_data.get('language_code')}', CURRENT_TIMESTAMP 
            )
        ''')
        print("User added")
        self.connection.commit()
        return self.cursor


    def get_user_data_db(self, id):
        self.cursor.execute(f'''
            SELECT *
            FROM users
            WHERE id = {id}
        ''')
        if self.cursor is not None:
            res = self.cursor.fetchone()
            return dict(res) 
            
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

    def list_all_users(self):
        query = "select * from users"
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        return [dict(row) for row in res]
    
    def user_exists(self, id: int):
        query = f"select * from users where id ={id}"
        print("QUERY", query)
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        if len(res) == 1: return 1
        return 0

    def get_users_on_device(self, device_id):
        query = f"select * from users where device_id = '{device_id}'"
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        return [dict(row) for row in res]

    def delete_table_users(self):
        self.cursor.execute("DROP TABLE users")

    def main():
        
        print("db.py")

    if __name__=="__main__":
        main()



# user_data = {
#     "id": 1, "username":  "myusname", "first_name":  "fn", "last_name" : "ln", "is_bot":  False, "language_code":  "ua"
#     }
# user_data_two = {
#     "id": 2, "username":  "2", "first_name":  "fn2", "last_name" : "ln2", "is_bot":  False, "language_code":  "ua2"
#     }

db = Datenbank()
# res = db.delete_table_users()
# res = db.list_all_users()
# for _ in res:
#     print(_)