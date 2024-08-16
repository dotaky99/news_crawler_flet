import os, sqlite3    

DB_PATH = "RESULT"
DB_NAME = "news.db"
DB_FULL_PATH = os.path.join(DB_PATH, DB_NAME)

def keyword_init():
    conn = sqlite3.connect(DB_FULL_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT keyword FROM keyword")
    keywords = cursor.fetchall()

    list_keyword = [item[0] for item in keywords]

    conn.close()

    return list_keyword


def keyword_save(keyword):
    if keyword:
        conn = sqlite3.connect(DB_FULL_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM keyword WHERE keyword = ?", (keyword,))
        result = cursor.fetchone()

    if result:
        return "이미 존재하는 키워드 입니다."
        
    else:
        cursor.execute("INSERT INTO keyword (keyword) VALUES (?)", (keyword,))
        conn.commit()
        

    cursor.execute("SELECT keyword FROM keyword")
    keywords = cursor.fetchall()
    list_keyword = [item[0] for item in keywords]
    conn.close()
    return list_keyword

def keyword_delete(keyword):
    conn = sqlite3.connect(DB_FULL_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keyword WHERE keyword = ?", (keyword,))
    conn.commit()

    cursor.execute("SELECT keyword FROM keyword")
    keywords = cursor.fetchall()

    list_keyword = [item[0] for item in keywords]
    conn.close()

    return list_keyword

def db_init():
    DB_PATH = "RESULT"
    DB_NAME = "news.db"
    DB_FULL_PATH = os.path.join(DB_PATH, DB_NAME)

    if not os.path.exists(DB_PATH):
        msg = "폴더가 존재하지 않습니다. 폴더를 생성합니다."
        # main_ui.state_view.insertItem(0, msg)
        os.makedirs(DB_PATH)

        msg = f"'{DB_PATH}'를 생성하였습니다."
        # main_ui.state_view.insertItem(0, msg)

    else:
        msg = "폴더가 존재합니다."
        # main_ui.state_view.insertItem(0, msg)

    # SQLite 파일 경로
    if not os.path.exists(DB_FULL_PATH):
        msg = "DB가 존재하지 않습니다. DB를 생성합니다.."
        # main_ui.state_view.insertItem(0, msg)

        sqlite3.connect(DB_FULL_PATH)
        msg = f"'{DB_NAME}' 생성에 성공하였습니다."
        # main_ui.state_view.insertItem(0, msg)
    else:
        msg = f"'{DB_NAME}'가 이미 존재합니다."
        # main_ui.state_view.insertItem(0, msg)

    conn = sqlite3.connect(DB_FULL_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keyword (
            keyword TEXT UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            title TEXT,
            url TEXT UNIQUE,
            checked TEXT
        )
    ''')

    conn.commit()
    conn.close()