import utils
import os
import mysql.connector

MY_USER_ID = os.getenv('ME_SPOTIFY_ID')
mysqlpwd = os.getenv('MYSQL_PWD')


sp = utils.spotipySetup()

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password=mysqlpwd,
    database='spotify_toolkit'
)

mycursor = mydb.cursor()

print(utils.getRecentTracks(1, 1, sp))