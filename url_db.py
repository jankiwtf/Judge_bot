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
def sql_new_key(con, party, info, new_url, user_id):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    data = (party, info, new_url, user_id)
    with con:
        cur.execute("INSERT INTO keys_tab(key_party, key_info, key_link, user_id) VALUES(?, ?, ?, ?)", data)
    con.commit()
    con.close()


# Show keys
def sql_saved_keys(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    show_link = cur.execute("SELECT key_party, key_info, key_link FROM keys_tab").fetchall()
    con.commit()
    return show_link


# Update info
def sql_update_info(con, info, link):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    data = (info, link)
    with con:
        cur.execute("UPDATE keys_tab SET key_info = ? WHERE key_link = ?", data)
        logging.info("Update info in key")
    con.commit()
    con.close()


# Show party
def sql_show_party(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    show_names = cur.execute("SELECT key_party FROM keys_tab").fetchall()
    con.commit()
    cur.close()
    return show_names


# Check link
def sql_check_link(con, link):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    show_link = cur.execute("SELECT key_link FROM keys_tab").fetchall()
    for row in show_link:
        if row[0] == link:
            con.commit()
            cur.close()
            return True


# Delete one key
def sql_del_key(con, info):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    cur.execute("DELETE FROM keys_tab WHERE key_party ='%s'" % str(info))
    con.commit()
    cur.close()


# Delete all keys
def sql_del_all_keys(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    cur.execute("DELETE FROM keys_tab")
    con.commit()
    cur.close()


# New keys table
def sql_create_keys_table(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    with con:
        cur.execute("CREATE TABLE keys_tab (key_party TEXT, key_info TEXT, key_link TEXT, user_id INT);")
    con.commit()
    cur.close()


# Count keys
def sql_count_keys(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    count = cur.execute("SELECT COUNT(*) FROM keys_tab").fetchone()[0]
    con.commit()
    cur.close()
    return count
