import logging
import sqlite3
from sqlite3 import Error
import utils


def sql_connection():
    try:
        con = sqlite3.connect('botdatabase.db')
        return con
    except Error:
        print(Error)


# Add new link in table
def sql_insert(con, new_url, user_id):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    data = ('None', 'None', new_url, user_id)
    with con:
        cur.execute("INSERT INTO url_info(players, last_info, link, user_id) VALUES(?, ?, ?, ?)", data)
    con.commit()
    con.close()


# Show all links from DB
def show_all_link(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    show_link = cur.execute("SELECT link FROM url_info").fetchall()
    con.commit()
    return show_link


# Show all names from DB
def show_all_names(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    show_names = cur.execute("SELECT players FROM url_info").fetchall()
    con.commit()
    cur.close()
    return show_names


# проверка ссылки на наличие ее в базе
def check_in_base(con, link):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    show_link = cur.execute("SELECT link FROM url_info").fetchall()
    for row in show_link:
        if row[0] == link:
            con.commit()
            cur.close()
            return True


# Update information in DB
def update_info_in_base(con, link, info):
    try:
        con = sqlite3.connect('botdatabase.db')
        cur = con.cursor()
        find_link = cur.execute("SELECT * FROM url_info where link ='%s'" % str(link)).fetchall()
        bio = str()
        info_row = str()
        if utils.where_url_save(link) == 'blue_site':
            bio = info[0][2][45:]
            info_row = info[1][-2] + '\n' + info[1][-1]
        elif utils.where_url_save(link) == 'brown_site':
            bio = ', '.join(map(str, info[0][2:]))
            info_row = info[1][-2] + '\n' + info[1][-1]

        if find_link[0][0] == 'None':
            with con:
                cur.execute("UPDATE url_info SET players = ? WHERE link = ?", (bio, link))
                logging.info("Names added in DB")
        if find_link[0][1] == 'None':
            with con:
                cur.execute("UPDATE url_info SET last_info = ? WHERE link = ?", (info_row, link))
                logging.info("The last information added in DB")
        con.commit()
        cur.close()

    except sqlite3.Error as error:
        logging.info("Error while working with SQLite", error)


# Delete selected link from DB
def delete_link(con, info):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    cur.execute("DELETE FROM url_info WHERE players ='%s'" % str(info))
    con.commit()
    cur.close()


# Delete all links from DB
def delete_all_link(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    cur.execute("DELETE FROM url_info")
    con.commit()
    cur.close()


# Create the table
def sql_table(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    with con:
        # Вар.1: создание таблицы без уникальности
        cur.execute("CREATE TABLE url_info (players TEXT, last_info TEXT, link TEXT, user_id INT);")
    # Вар.2: создание таблицы с графой уникальнось - "Уникальный user_id"
    # cursorObj.execute("CREATE TABLE log(created_at TEXT, first_name TEXT, message TEXT, second_name TEXT, "
    #                   "user_id INTEGER PRIMARY KEY)")
    con.commit()
    cur.close()


# Count saved links in DB
def count_rows_sql(con):
    con = sqlite3.connect('botdatabase.db')
    cur = con.cursor()
    count = cur.execute("SELECT COUNT(*) FROM url_info").fetchone()[0]
    con.commit()
    cur.close()
    return count
