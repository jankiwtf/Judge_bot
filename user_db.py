import logging
import sqlite3
from sqlite3 import Error
from datetime import datetime


def sql_connection():
    try:
        con = sqlite3.connect('botdatabase.db')
        return con
    except Error:
        logging.error(Error)


# New user
def sql_new_user(con, user_id):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    now_date = datetime.now()
    data = ('None', user_id, now_date, False)
    with con:
        cur.execute("INSERT INTO users(user_name, user_id, date_registration, admin_check) VALUES(?, ?, ?, ?)", data)
    logging.info("User %s added in DB" % user_id)
    con.commit()
    con.close()


# Check user
def sql_init_user(con, user_id):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    db_user = cur.execute("SELECT user_id, admin_check FROM users").fetchall()
    con.commit()
    cur.close()
    for row in db_user:
        if row[0] == int(user_id):
            return {'verif': True, 'admin': row[1]}
    return False


# Saved users
def sql_show_users(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    users = cur.execute("SELECT user_id, user_name FROM users").fetchall()
    con.commit()
    cur.close()
    return users


# Delete user
def sql_delete_user(con, user_id):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    cur.execute("DELETE FROM users WHERE user_id ='%s'" % int(user_id))
    logging.info("User %s deleted from DB" % user_id)
    con.commit()
    cur.close()


# Count saved users
def sql_count_users(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    con.commit()
    cur.close()
    return count


# New user's table
def sql_create_user_table(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    with con:
        cur.execute("CREATE TABLE users ("
                    "user_name TEXT, "
                    "user_id INT PRIMARY KEY, "
                    "date_registration DATETIME, "
                    "admin_check BOOL);")
        data = ('@janki_wtf', 199225478, None, True)
        cur.execute("INSERT INTO users(user_name, user_id, date_registration, admin_check) VALUES(?, ?, ?, ?)", data)
    con.commit()
    cur.close()
