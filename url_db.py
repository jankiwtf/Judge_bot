import logging
import sqlite3
from sqlite3 import Error


def sql_connection():
    try:
        con = sqlite3.connect('botdatabase.db')
        return con
    except Error:
        print(Error)


# New key
def sql_new_key(party, info, new_url, user_id):
    con = sql_connection()
    cur = con.cursor()
    data = (party, info, new_url, user_id)
    with con:
        cur.execute("INSERT INTO keys_tab(key_party, key_info, key_link, user_id) VALUES(?, ?, ?, ?)", data)
    con.commit()
    con.close()


# Show keys
def sql_saved_keys():
    con = sql_connection()
    cur = con.cursor()
    show_link = cur.execute("SELECT key_party, key_info, key_link FROM keys_tab").fetchall()
    con.commit()
    return show_link


# Update info
def sql_update_info(info, link):
    con = sql_connection()
    cur = con.cursor()
    data = (info, link)
    with con:
        cur.execute("UPDATE keys_tab SET key_info = ? WHERE key_link = ?", data)
        logging.info("Update info in key")
    con.commit()
    con.close()


# Show party
def sql_show_party():
    con = sql_connection()
    cur = con.cursor()
    show_names = cur.execute("SELECT key_party, key_info FROM keys_tab").fetchall()
    con.commit()
    cur.close()
    return show_names

# Check link
def sql_check_link(link):
    con = sql_connection()
    cur = con.cursor()
    show_link = cur.execute("SELECT key_link FROM keys_tab").fetchall()
    for row in show_link:
        if row[0] == link:
            con.commit()
            cur.close()
            return True


# Delete one key
def sql_del_key(info):
    con = sql_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM keys_tab WHERE key_party ='%s'" % str(info))
    con.commit()
    cur.close()


# Delete all keys
def sql_del_all_keys():
    con = sql_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM keys_tab")
    logging.info("All keys is deleted")
    con.commit()
    cur.close()


# Count keys
def sql_count_keys():
    con = sql_connection()
    cur = con.cursor()
    with con:
        count = cur.execute("SELECT COUNT(*) FROM keys_tab").fetchone()[0]
    con.commit()
    cur.close()
    return count


# New keys table
def sql_create_keys_table():
    con = sql_connection()
    cur = con.cursor()
    with con:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS keys_tab ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "key_party TEXT, "
            "key_info TEXT, "
            "key_link TEXT, "
            "user_id INTEGER"
            ");")
    con.commit()
    cur.close()


# Update status
def sql_create_upd_stat_table():
    con = sql_connection()
    cur = con.cursor()
    with con:
        cur.execute("CREATE TABLE IF NOT EXISTS upd_stat ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "user_id INT, "
                    "chat_id INT UNIQUE, "
                    "update_status BOOL"
                    ");")
    con.commit()
    cur.close()


# On update status in group
def sql_on_status(user_id, chat_id, update_status):
    con = sql_connection()
    cur = con.cursor()
    data = (user_id, chat_id, update_status)
    with con:
        cur.execute("INSERT INTO upd_stat(user_id, chat_id, update_status) VALUES(?, ?, ?)", data)
    con.commit()
    con.close()


# Off update status in group
def sql_off_status(chat_id):
    con = sql_connection()
    cur = con.cursor()
    with con:
        cur.execute(f"DELETE FROM upd_stat WHERE chat_id={chat_id}")
    con.commit()
    cur.close()


# Check update status
def sql_check_status(chat_id):
    con = sql_connection()
    cur = con.cursor()
    with con:
        status = cur.execute(f"SELECT * FROM upd_stat WHERE chat_id={chat_id}").fetchone()
    con.commit()
    cur.close()
    if status:
        return True
    return False


# All records
def sql_all_status():
    con = sql_connection()
    cur = con.cursor()
    with con:
        count = cur.execute("SELECT COUNT(*) FROM upd_stat").fetchone()[0]
        status = cur.execute("SELECT chat_id FROM upd_stat WHERE update_status= 1").fetchall()
    con.commit()
    cur.close()
    if count != 0:
        return status
    return 0

# count = sql_all_status()
# for i in sql_all_status():
#     print(i[0])
