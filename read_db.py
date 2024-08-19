#Used for displaying records from db or for general testing with print statements

from parser import *
from app import *
import sqlite3
import json

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute('''
select * from SystemProviderResources;
            ''')
records = cur.fetchall()
for row in records:
    for i in range(len(row)):
        print(row[i])
conn.close()