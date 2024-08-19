from flask import Flask, request, redirect, url_for, flash, render_template, json, jsonify
from werkzeug.utils import secure_filename
from parser import *
import sqlite3
import os
import pdfplumber
from pdfminer.high_level import extract_text
import re
import json
from datetime import datetime

app = Flask(__name__,template_folder='templates')
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['DATABASE'] = 'database.db'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def convert_pdf_to_text(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

#function for cleaning text used only for testing and comparison
def clean_text(text):
    # Remove all tabs and line breaks
    cleaned_text = re.sub(r'[\t\n\r]+', ' ', text)
    # Remove extra spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    # Remove all non-alphanumeric characters except spaces
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)
    # Strip leading and trailing spaces
    cleaned_text = cleaned_text.strip()
    return cleaned_text

#this function applies to the simple one-table database design and may not be needed in final product
def find_jobs_by_jobtitle(search, records):
    search = search.lower()
    #matches contains the numbers/IDs of the resumes that contain the search key 
    matches = []
    for i in range(len(records)):
        if search in records[i][4].lower():
            matches.append(i)
    cand_jobs_matches = []

    if matches:
        for i in range(len(matches)):
            info_jobs = []
            #records[resumes_match[i]] = the entire tuple contianing id, filename, pdf_text, info, exp, ...
            #work_exp will be a list of dictionaries for each work experience
            basic_info = json.loads(records[matches[i]][3])
            work_exps = json.loads(records[matches[i]][4]) 
            jobs_match = []
            #accounting for instances where one candidate has multiple matches
            #we are trying to find just the jobs with the search 
            for j in range(len(work_exps)):
                if search in work_exps[j]['Notes'].lower():
                    jobs_match.append(work_exps[j])
            cand_info = {}
            cand_info['FirstName'] = basic_info['FirstName']
            cand_info['LastName'] = basic_info['LastName']
            info_jobs.append(cand_info)
            info_jobs.append(jobs_match)
            cand_jobs_matches.append(info_jobs)
        return cand_jobs_matches
    else:
        return ""


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clear', methods=['POST'])
def clear():
    return render_template('search.html')

@app.route('/delete', methods=['POST'])
def delete():
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM SystemProviderResources')
        cur.execute('DELETE FROM ResourceWorkExperience')
        cur.execute('DELETE FROM ResourceEducation')    
        cur.execute('DELETE FROM ResourceCredentials')  
        cur.execute('DELETE FROM Skills')        
        conn.commit()

        conn.close()
        return render_template('index.html', confirm="Database cleared!")

@app.route('/search', methods=['GET', 'POST'])
def search():
    records = []

    if request.method == 'POST':
        jobtitle = request.form['jobtitle'].lower()
        skill = request.form['skill'].lower()
        duration = request.form['duration']
        if request.form['action'] == 'clear':
            return render_template('search.html')
        conn = get_db_connection()
        cur = conn.cursor()
        #if only a jobtitle is searched
        if jobtitle != "" and skill == "":
            #with consideration for duration
            if duration != "":
                duration = int(duration)
                cur.execute('''SELECT DISTINCT r.FirstName, r.LastName, r.MidInitial, r.PhysicalAddress, r.PhysicalCity, 
                            r.PhysicalCountry, r.PhysicalState, r.PhysicalPostalCode, r.PrimaryPhone, r.PrimaryEmail, 
                            r.WillingToTravel, w.Notes, w.EmploymentStartDate, w.Employer, w.EmploymentEndDate, w.EmploymentDuration 
                            FROM SystemProviderResources r JOIN ResourceWorkExperience w on w.ResourceId = r.Id 
                            WHERE w.Notes LIKE ? AND w.EmploymentDuration >= ?''', ('%' + jobtitle + '%', duration))
                records = cur.fetchall()
            #without consideration for duration
            else:
                cur.execute('''SELECT DISTINCT r.FirstName, r.LastName, r.MidInitial, r.PhysicalAddress, r.PhysicalCity,
                                      r.PhysicalCountry, r.PhysicalState, r.PhysicalPostalCode, r.PrimaryPhone,
                                      r.PrimaryEmail, r.WillingToTravel, w.Notes, w.Employer, w.EmploymentStartDate, 
                                        w.EmploymentEndDate, w.EmploymentDuration 
                                        FROM SystemProviderResources r
                                        JOIN ResourceWorkExperience w on w.ResourceId = r.Id
                                        WHERE w.Notes LIKE ?''', ('%' + jobtitle + '%',))
                records = cur.fetchall()
        if skill != "" and jobtitle == "":
            cur.execute('''SELECT DISTINCT r.FirstName, r.LastName, r.MidInitial, r.PhysicalAddress, r.PhysicalCity, 
                            r.PhysicalCountry, r.PhysicalState, r.PhysicalPostalCode, r.PrimaryPhone, r.PrimaryEmail, 
                            r.WillingToTravel, s.SkillName 
                            FROM SystemProviderResources r JOIN Skills s on s.ResourceId = r.Id
                            WHERE s.SkillName LIKE ?''', ('%' + skill + '%',))
            records = cur.fetchall()
            
        conn.close()
        if not records:
            return render_template('search.html', message="No records found!")
        else:
            return render_template('search.html', results=records)
            
    else:
        return render_template('search.html')
        
    
@app.route('/upload-folder')
def upload_folder_form():
    return render_template('upload_folder.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        flash('No file part')
        return redirect(request.url)
    files = request.files.getlist('files[]')
    resumes = []
    bad_chars = [";", ":", "!", "|", "\t", ","]
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            #pdfminer extract_text appears to preserve the PDF file's original layout best
            file_text = extract_text(file_path)
            #file_text_2 = convert_pdf_to_text(file_path)
            #file_text_3 = read_pdf_fitz(file_path)
            #remove special characters
            for i in bad_chars:
                file_text = file_text.replace(i, " ")

            resumes.append(file_text)

    final_parsing = combine_parsing_list(resumes)

    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Insert data into tables
    for item in final_parsing:
        resource = item['SystemProviderResources']
        # Insert into SystemProviderResources
        cursor.execute('''
            INSERT INTO SystemProviderResources (
                FirstName, LastName, MidInitial, PhysicalAddress, PhysicalAddress2,
                PhysicalCountry, PhysicalCity, PhysicalState, PhysicalPostalCode,
                PrimaryPhone, PrimaryEmail, SecondaryPhone, SecondaryEmail, WillingToTravel
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            resource['FirstName'], resource['LastName'], resource.get('MidInitial'), 
            resource['PhysicalAddress'], resource['PhysicalAddress2'],
            resource['PhysicalCountry'], resource['PhysicalCity'], resource['PhysicalState'], 
            resource['PhysicalPostalCode'], 
            '-'.join(resource['PrimaryPhone']) if resource['PrimaryPhone'] else None, 
            resource['PrimaryEmail'], 
            '-'.join(resource['SecondaryPhone']) if resource['SecondaryPhone'] else None,
            resource['SecondaryEmail'], 
            resource['WillingToTravel']
        ))

        resource_id = cursor.lastrowid

        # Insert into ResourceWorkExperience
        for work in resource['ResourceWorkExperience']:
            cursor.execute('''
                INSERT INTO ResourceWorkExperience (
                    ResourceId, Notes, Employer, EmploymentStartDate, EmploymentEndDate, EmploymentDuration
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                resource_id, work['Notes'], work['Employer'], 
                work['EmploymentStartDate'], work['EmploymentEndDate'], work['EmploymentDuration']
            ))

        # Insert into ResourceEducation
        for education in resource['ResourceEducation']:
            cursor.execute('''
                INSERT INTO ResourceEducation (
                    ResourceId, Institution, Degree, YearEarned
                ) VALUES (?, ?, ?, ?)
            ''', (
                resource_id, education['Institution'], education['Degree'], education['YearEarned']
            ))

        # Insert into ResourceCredentials
        for credential in resource['ResourceCredentials']:
            cursor.execute('''
                INSERT INTO ResourceCredentials (
                    ResourceId, Institution, AcquiredDate, Notes
                ) VALUES (?, ?, ?, ?)
            ''', (
                resource_id, credential['Institution'], credential['AcquiredDate'], credential['Notes']
            ))

        # Insert into Skills
        for skill in resource['Skills']:
            cursor.execute('''
                INSERT INTO Skills (
                    ResourceId, SkillName
                ) VALUES (?, ?)
            ''', (
                resource_id, skill['SkillName']
            ))

    # Commit the transaction
    conn.commit()

    # Close the connection
    conn.close()

        #TODO: double check this next section
    if resumes:
        #flash('Files successfully uploaded and saved to the database')
        #return render_template('search.html', resumes=sections_list)
        return render_template('index.html', confirm="Resumes parsed into database!")
    else:
        print("/upload inside else:")
        return render_template('index.html', confirm="Please upload files")


@app.route('/summary', methods=['GET', 'POST'])
def results():
    conn = get_db_connection()
    cur = conn.cursor()
    summary = []
    if request.method == 'POST':
        name = request.form['name'].lower()
        name_list = name.split()
        if len(name_list) == 0:
            records = cur.execute(''' SELECT Id FROM SystemProviderResources ''').fetchall()
        elif len(name_list) == 1:
            records = cur.execute(''' SELECT Id FROM SystemProviderResources r
                              WHERE r.FirstName LIKE ? OR r.LastName LIKE ?''', ('%' + name_list[0] + '%','%' + name_list[0] + '%')).fetchall()
        else:
            records = cur.execute(''' SELECT Id FROM SystemProviderResources r
                              WHERE r.FirstName LIKE ? AND r.LastName LIKE ?''', ('%' + name_list[0] + '%','%' + name_list[1] + '%')).fetchall()
    else:
        records = cur.execute(''' SELECT Id FROM SystemProviderResources ''').fetchall()
    ids = [id[0] for id in records]
    for id in ids:
        id_sections = {}
        info = cur.execute('''
            SELECT * FROM SystemProviderResources r
            WHERE r.Id = ?''', (id,)).fetchall()
        
        jobs = cur.execute('''
            SELECT * FROM ResourceWorkExperience w
            WHERE w.ResourceId = ?''', (id,)).fetchall()
        
        edus = cur.execute('''
            SELECT * FROM ResourceEducation e
            WHERE e.ResourceId = ?''', (id,)).fetchall()
        
        certs = cur.execute('''
            SELECT * FROM ResourceCredentials c
            WHERE c.ResourceId = ?''', (id,)).fetchall()

        skills = cur.execute('''
            SELECT * FROM Skills s
            WHERE s.ResourceId = ?''', (id,)).fetchall()
        
        id_sections['id'] = id
        id_sections['info'] = info
        id_sections['jobs'] = jobs
        id_sections['edus'] = edus
        id_sections['certs'] = certs
        id_sections['skills'] = skills
        summary.append(id_sections)

    return render_template('summary.html', results=summary)
        
if __name__ == '__main__':
    app.run(debug=True)

