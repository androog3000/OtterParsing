#this was a prototype database design with a single table

import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute(''' DROP TABLE IF EXISTS resumes ''')

c.execute('''
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    pdf_text TEXT,
    basic_info JSON,
    exp JSON,
    edu JSON,
    certs JSON,
    skills JSON,
    exp_id INTEGER
)
''')

conn.commit()
conn.close()

