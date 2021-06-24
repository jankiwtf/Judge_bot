import logging
from datetime import datetime
from url_db import sql_connection


# New user
def sql_new_user(user_id):
    con = sql_connection()
    cur = con.cursor()
    now_date = datetime.now()
    data = ('None', user_id, now_date, False)
    with con:
        cur.execute("INSERT INTO users(user_name, user_id, date_registration, admin_check) VALUES(?, ?, ?, ?)", data)
    logging.info("User %s added in DB" % user_id)
    con.commit()
    con.close()


# add username
def sql_update_name(username, user_id):
    con = sql_connection()
    cur = con.cursor()
    data = (username, user_id)
    with con:
        cur.execute("UPDATE users SET user_name = ? WHERE user_id = ?", data)
    logging.info(f"User's ({user_id}) name update")
    con.commit()
    con.close()


# Check user
def sql_init_user(user_id):
    con = sql_connection()
    cur = con.cursor()
    db_user = cur.execute("SELECT user_id, admin_check FROM users").fetchall()
    con.commit()
    cur.close()
    for row in db_user:
        if row[0] == int(user_id):
            return {'verif': True, 'admin': row[1]}
    return False


# Saved users
def sql_show_users():
    con = sql_connection()
    cur = con.cursor()
    users = cur.execute("SELECT user_id, user_name FROM users").fetchall()
    con.commit()
    cur.close()
    return users


# Delete user
def sql_delete_user(user_id):
    con = sql_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM users WHERE user_id ='%s'" % int(user_id))
    logging.info("User %s deleted from DB" % user_id)
    con.commit()
    cur.close()


# Count saved users
def sql_count_users():
    con = sql_connection()
    cur = con.cursor()
    count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    con.commit()
    cur.close()
    return count


# New user's table
def sql_create_user_table():
    con = sql_connection()
    cur = con.cursor()
    with con:
        cur.execute("CREATE TABLE IF NOT EXISTS users ("
                    "user_name TEXT, "
                    "user_id INTEGER PRIMARY KEY, "
                    "date_registration DATETIME, "
                    "admin_check BOOL);")
        data = ('@janki_wtf', 199225478, None, True)
        cur.execute("INSERT INTO users(user_name, user_id, date_registration, admin_check) VALUES(?, ?, ?, ?)", data)
    con.commit()
    cur.close()
