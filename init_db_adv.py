import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute(''' DROP TABLE IF EXISTS SystemProviderResources ''')

c.execute('''
CREATE TABLE SystemProviderResources (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT,
    LastName TEXT,
    MidInitial TEXT,
    PhysicalAddress TEXT,
    PhysicalAddress2 TEXT,
    PhysicalCountry TEXT,
    PhysicalCity TEXT,
    PhysicalState TEXT,
    PhysicalPostalCode TEXT,
    PrimaryPhone TEXT,
    PrimaryEmail TEXT,
    SecondaryPhone TEXT,
    SecondaryEmail TEXT,
    WillingToTravel TEXT
)
''')
conn.commit()

c.execute(''' DROP TABLE IF EXISTS ResourceWorkExperience ''')
c.execute('''
CREATE TABLE ResourceWorkExperience (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    ResourceId INTEGER,
    Notes TEXT,
    Employer TEXT,
    EmploymentStartDate TEXT,
    EmploymentEndDate TEXT,
    EmploymentDuration INTEGER,
    FOREIGN KEY (ResourceId) REFERENCES SystemProviderResources(Id)
)''')
conn.commit()

c.execute(''' DROP TABLE IF EXISTS ResourceEducation ''')
c.execute('''
CREATE TABLE ResourceEducation (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    ResourceId INTEGER,
    Institution TEXT,
    Degree TEXT,
    YearEarned TEXT,
    FOREIGN KEY (ResourceId) REFERENCES SystemProviderResources(Id)
)''')
conn.commit()

c.execute(''' DROP TABLE IF EXISTS ResourceCredentials ''')
c.execute('''
CREATE TABLE ResourceCredentials (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    ResourceId INTEGER,
    Institution TEXT,
    AcquiredDate TEXT,
    Notes TEXT,
    FOREIGN KEY (ResourceId) REFERENCES SystemProviderResources(Id)
)''')
conn.commit()

c.execute(''' DROP TABLE IF EXISTS Skills ''')
c.execute('''
CREATE TABLE Skills (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    ResourceId INTEGER,
    SkillName TEXT,
    FOREIGN KEY (ResourceId) REFERENCES SystemProviderResources(Id)
)''')
conn.commit()
conn.close()