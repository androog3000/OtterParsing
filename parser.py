
# Install commands to check before running program
'''
pip install flask
pip install spacy
pip install pdfplumber
pip install PyMuPDF
!spacy download en_core_web_lg
#python -m spacy download en_core_web_lg
'''
import spacy
import re
from spacy import displacy
#import en_core_web_trf
import json
from skills import technical_skills
import os
import sqlite3
from flask import Flask, request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
#from resources.models
import sqlite3
import os
import pdfplumber
import fitz
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['DATABASE'] = 'database.db'

#connect to database
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def read_pdf_fitz(file_path):
  text = ""
  with fitz.open(file_path) as doc:
      for page_num in range(len(doc)):
          page = doc.load_page(page_num)
          text += page.get_text()
  return text

def getName(someName):
  # regex patter for lastname titles
  regExPattern_LastNameTitle = "([jrJRJrSrSR]{2}|\s[iI]{1,})"

  # case first/last name
  if( len(someName) == 2):
    return [someName[0], None, someName[1]]
  # case first/middle/last name
  elif( len(someName) > 2 ):
      checkForLastNameTitle = re.findall(regExPattern_LastNameTitle, someName[-1])
      # check for case of last name title
      if( len(checkForLastNameTitle) > 0 ):
        if(len(someName) == 3):
            return [someName[0], None, someName[-2:]]
        elif(len(someName) > 3):
            return [someName[0], (someName[1])[0], someName[-2:]]
      # no last name title found
      else:
        return [someName[0], (someName[1])[0], someName[2]]
  # catch all case to trigger use of model for name
  else:
    return [None, None, None]

def getNameFromModel(resume):

  # load custom name model
  nlp = spacy.load("./resources/models/info-model")
  #nlp = spacy.load("/Users/andrewgrant/Desktop/Class/Capstone/Models/Info_Model/model-best_info")
  ts = nlp(resume)
  fullName = [None, None, None]

  for ent in ts.ents:
    if ent.label_.upper() == 'FIRST_NAME':
        fullName[0] = f'{ent.text}'
    if ent.label_.upper() == 'LAST_NAME':
        fullName[2] = f'{ent.text}'
    if ent.label_.upper() == 'MIDDLE_NAME':
        fullName[1] = f'{ent.text}'[0]

  return fullName

def getAddressFromModel(resume):
  # find state
  regExPattern_State = "AL|AK|AS|AZ|AR|CA|CO|CT|DE|DC|FM|FL|GA|GU|HI|ID|IL|IN|IA|KS|KY|LA|ME|MH|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|MP|OH|OK|OR|PW|PA|PR|RI|SC|SD|TN|TX|UT|VT|VI|VA|WA|WV|WI|WY|Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New[ ]Hampshire|New[ ]Jersey|New[ ]Mexico|New[ ]York|North[ ]Carolina|North[ ]Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode[ ]Island|South[ ]Carolina|South[ ]Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West[ ]Virginia|Wisconsin|Wyoming"
  fullLocation = ["", ""]

  # load stock spacy model
  model = spacy.load('en_core_web_lg')
  ts = model(resume)

  i = 0
  for ent in ts.ents:
    if ent.label_.upper() == 'GPE':
      checkForState = re.findall(regExPattern_State, f'{ent.text}')
      if(fullLocation[1] == "" and len(checkForState) > 0 ):
          fullLocation[1] = f'{ent.text}'
          i += 1
      elif(fullLocation[0] == ""):
          fullLocation[0] = f'{ent.text}'
          i += 1
    if(i > 1 and fullLocation[0] != "" and fullLocation[1] != ""):
      break

  return fullLocation

def make_basicinfo(resume):

  # regEx Patterns for basic information extraction
  regExPattern_Name = "((?:[ \-]?[A-Z][a-z]+|[A-Z]+|[A-Z][a-z]?\.?)+)((?: ?[A-Z]\.?|[A-Z][a-z]+)*)([A-Za-z]{,3}(?:[ \-]?[A-Z]'?[A-Z]?[a-z]+\.?,?)+|[A-Z]+|[A-Z .]*)"
  regExPattern_Email = "[a-z0-9!#$%&'*+=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
  regExPattern_PhoneUSOnly = "(?:\+|\d{1,2}\s)?\(?(\d{3})\)?.?\s?(\d{3}).?\s?(\d{4})"
  regExPattern_Address = "(\d[A-Za-z0-9 \.\&]*(?:Creek|Place|Terrace|Highway|Road|St?reet?|Road|Lane|Suite|Avenue|Parkway|Court|Boulevard|Rd|Island|Drive|Pike|Floor|St|Falls|Park|Spring|Ave|Drive|Dr|\d+)[.| ])?([A-Za-z .-]+(?:[ |,]+))(AL|AK|AS|AZ|AR|CA|CO|CT|DE|DC|FM|FL|GA|GU|HI|ID|IL|IN|IA|KS|KY|LA|ME|MH|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|MP|OH|OK|OR|PW|PA|PR|RI|SC|SD|TN|TX|UT|VT|VI|VA|WA|WV|WI|WY|Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New[ ]Hampshire|New[ ]Jersey|New[ ]Mexico|New[ ]York|North[ ]Carolina|North[ ]Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode[ ]Island|South[ ]Carolina|South[ ]Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West[ ]Virginia|Wisconsin|Wyoming){1}[ ]?(\d{5}(?:-\d{4})?)?"
  regexPattern_WillingToTravel = "[W|w]illing[A-Za-z ]+[T|t]ravel"

  # initialize all basic info
  basicinfo = {
      "FirstName": "",
      "LastName": "",
      "MidInitial": "",
      "PhysicalAddress": "",
      "PhysicalAddress2": "",
      "PhysicalCountry": "",
      "PhysicalCity": "",
      "PhysicalState": "",
      "PhysicalPostalCode": "",
      "PrimaryPhone": "",
      "PrimaryEmail": "",
      "SecondaryPhone": "",
      "SecondaryEmail": "",
      "WillingToTravel": ""
      }

  ##################### name extraction ############################
  # minimum result needed is first, last name
  results_Name = re.search(regExPattern_Name, resume[:50])

  # check if match type was returned
  if(type(results_Name) == re.Match):
    # get first match and split it
    resultName = results_Name[0].split()
    fullName = getName(resultName)
    # check if name is a location
    checkName = getAddressFromModel(str(fullName))
    if(checkName[0] != "" or  checkName[-1] != ""):
      #set vars so custom model will execute
      fullName[0] = ""
      fullName[-1:] = ""
  # minimum first/last name not returned, use custom model
  if(fullName[0] == "" or fullName[-1:] == ""):
    fullName = getNameFromModel(resume)

  basicinfo["FirstName"] = fullName[0]
  basicinfo["LastName"] = fullName[2]
  basicinfo["MidInitial"] = fullName[1]

  ##################### address extraction ############################
  # minimum result needed is city, state
  results_Address = re.findall(regExPattern_Address, resume[:100])
  basicinfo["PhysicalCountry"] = "US"
  # at least two elements of the address are found
  if len(results_Address) > 0:
    basicinfo["PhysicalAddress"] = results_Address[0][0]
    basicinfo["PhysicalAddress2"] = ""
    basicinfo["PhysicalCity"] = results_Address[0][1]
    basicinfo["PhysicalState"] = results_Address[0][2]
    basicinfo["PhysicalPostalCode"] = results_Address[0][3]
  # check minimum of city/state elements found, use base spacy model
  if(basicinfo["PhysicalCity"] == "" or basicinfo["PhysicalState"] == ""):
    fullLocation = getAddressFromModel(resume)
    basicinfo["PhysicalCity"] = fullLocation[0]
    basicinfo["PhysicalState"] = fullLocation[1]

  ##################### phone number extraction ############################
  results_PhoneNumber = re.findall(regExPattern_PhoneUSOnly, resume[:1000])
  if len(results_PhoneNumber) > 1:
      basicinfo["PrimaryPhone"] = results_PhoneNumber[0]
      basicinfo["SecondaryPhone"] = results_PhoneNumber[1]
  elif len(results_PhoneNumber) == 1:
      basicinfo["PrimaryPhone"] = results_PhoneNumber[0]

  ##################### email extraction ############################
  results_Email = re.findall(regExPattern_Email, resume.lower())
  if len(results_Email) > 1:
    basicinfo["PrimaryEmail"] = results_Email[0]
    basicinfo["SecondaryEmail"] = results_Email[1]
  elif len(results_Email) == 1:
    basicinfo["PrimaryEmail"] = results_Email[0]

  ##################### will travel extraction ############################
  results_Travel = re.findall(regexPattern_WillingToTravel, resume)
  if len(results_Travel) > 0:
    basicinfo["WillingToTravel"] = True

  return basicinfo

"""# Using regex to find the header sections within the resume
## Assuming that most resumes utilize a Work Experience header coded as /nExperience/n
"""

#Regex expressions to find headers that begin each section

exp = "\n.{0,1}relevant work experience.{0,1}\n|\n.{0,1}work experience.{0,1}\n|\n.{0,1}experience.{0,1}\n|\n.{0,1}professional experience.{0,1}\n|\n.{0,1}job history.{0,1}\n|\n.{0,1}work history.{0,2}\n|\n.{0,1}professional background.{0,1}\n|\n.{0,1}employment history.{0,1}\n|\nrelated experience.{0,1}\n"

#some people have one section for "Education and Certifications", in this case we can combine it into the education section
edu = "\n.{0,2}educational background.{0,1}\n|\n.{0,1}education.{0,1}\n|\n.{0,1}school.{0,1}\n|\n.{0,1}educational qualification.{0,1}\n|\n.{0,1}education qualifications.{0,1}\n|\n.{0,1}education and credentials.{0,1}\n|\n.{0,1}education and certifications.{0,1}\n|\n.{0,1}education and certification.{0,1}\n|\n.{0,1}education & certifications.{0,1}\n|\n.{0,1}education & related experience.{0,1}\n|\n.{0,1}education history.{0,1}\n|\n.{0,1}education & training.{0,1}\n|\n.{0,1}education and training.{0,1}\n"

certs = "\n.{0,1}certifications.{0,1}\n|\n.{0,1}certificates.{0,1}\n|\n.{0,1}licenses.{0,1}\n|\n.{0,1}certificates and licenses.{0,1}\n|\n.{0,1}licenses and certificates.{0,1}\n|\n.{0,1}licenses and certifications.{0,1}\n|\n.{0,1}certifications and licenses.{0,1}\n"

skills = "\n.{0,1}tools.{0,1}\n|\n.{0,1}skills.{0,1}\n|\n.{0,1}additional skills.{0,1}\n|\n.{0,1}professional skills.{0,1}\n|\n.{0,1}relevant skills.{0,1}\n|\n.{0,1}technical skills.{0,1}\n|\n.{0,1}related skills.{0,1}\n|\n.{0,2}computer skills.{0,2}\n|\n.{0,1}skills & tools.{0,1}\n"

#Note: projects is not a section we are required to extract but it is included here so that it may be identified and removed in order to reduce false positives in other sections
projects = "\n.{0,1}projects.{0,1}\n|\n.{0,1}additional projects.{0,1}\n|\n.{0,1}academic projects.{0,1}\n|\n.{0,1}production projects.{0,1}\n|\n.{0,1}web projects.{0,1}\n|\n.{0,1}relevant projects.{0,1}\n|\n.{0,1}web development projects.{0,1}\n"

regexs = {"exp":exp, "edu":edu, "certs":certs, "skills":skills, "projects":projects}



def section_start(regex, text):
  txt = text.lower()
  x = re.search(regex, txt)
  try:
    start = x.start()
    return start
  except:
    return 0

#Function to be used both for separating sections to create training datasets
# and to analyze new resumes by separating sections so the respective models can be applied
def make_sections(text, regexs):
  txt = text.lower()
  regex_start_dict = {}
  for name, regex in regexs.items():
    #find the starting places and eventually order them
    start_regex = []
    regex_start_dict[name] = section_start(regex, txt)
  sections = {}
  sorted_tuples = sorted(regex_start_dict.items(), key=lambda x:x[1])
  for i in range(5):
    #if no exp section is detected, just use the entire resume
    if sorted_tuples[i][1] == 0 and sorted_tuples[0] == 'exp':
      sections[sorted_tuples[i][0]] = text
    #for other sections if nothing is detected, use empty string
    elif sorted_tuples[i][1] == 0:
      sections[sorted_tuples[i][0]] = ""
    else:
      #if its not the 5th and final section, the section is a slice until the next section
      if i != 4:
        sections[sorted_tuples[i][0]] = text[sorted_tuples[i][1]:sorted_tuples[i+1][1]]
      #if it is the final section, the slice is from its start until the end
      else:
        sections[sorted_tuples[i][0]] = text[sorted_tuples[i][1]:]

  #print("make sections sections:", sections)
  return sections


# Ideally work experiences are distinctly placed within the resume with each field having the exact same number of found entities
# ie for each job, there is 1 jobtitle, 1 employer, 1 startdate, 1 enddate, without any false positives or without spacy missing any fields
# This algorithm tracks the progress of spacy entities through a series of iterators and stores the fields (jobtitle, employer, startdate, enddate) in a job dictionary
# When it detects that a field iterator has exceeded the job iterator, it will increment the job iterator, append the job dictionary to the job list and reset the job dictionary
# This algorithm will still append a job if certain fields are missing, but will ignore cases where only start and end dates have been identified

def make_jobs(exp_section):
  jobtitle_it = 0
  employer_it = 0
  startdate_it = 0
  enddate_it = 0
  job_it = 0
  ent_it = 0

  jobs = []
  job_default = {"Notes": "", "Employer":"", "EmploymentStartDate":"", "EmploymentEndDate": ""}
  job = job_default.copy()

  if exp_section == "":
    jobs.append(job_default.copy())
    return jobs

  #load custom spacy model for work experience
  nlp = spacy.load("./resources/models/exp-model-best")

  #create a spacy doc from the experience section using the custom trained model
  doc = nlp(exp_section)

  #loop through spacy doc entities
  while ent_it < len(doc.ents):

    entity = doc.ents[ent_it]
    if entity.label_ == "JOBTITLE":

      #ent iterator progresses through loop of doc entities
      ent_it += 1

      #LABEL iterator keeps track of how many of each we encounter
      jobtitle_it += 1

      #signifies next job starting
      if jobtitle_it > job_it:

        #if this is the first job, increment job it and proceed
        if job_it == 0:
          job_it += 1
          job = job_default.copy()
          job["Notes"] = entity.text

        #if it's not the first job, then job is ready to be appended
        else:
          jobs.append(job)
          job_it += 1
          employer_it, startdate_it, enddate_it = job_it - 1, job_it - 1, job_it - 1
          job = job_default.copy()
          job["Notes"] = entity.text
      else:
        #if job_it == FIELD_it then we can add FIELD text to current job dict
        job["Notes"] = entity.text

    if entity.label_ == "EMPLOYER":

      #ent iterator progresses through loop of doc entities
      ent_it += 1

      #LABEL iterator keeps track of how many of each we encounter
      employer_it = employer_it + 1

      #signifies next job starting
      if employer_it > job_it:

        #if this is the first job, increment job it and proceed
        if job_it == 0:
          job_it += 1
          job = job_default.copy()
          job["Employer"] = entity.text

        #if it's not the first job, then job is ready to be appended
        else:
          jobs.append(job)
          job_it += 1
          jobtitle_it, startdate_it, enddate_it = job_it - 1, job_it - 1, job_it - 1
          job = job_default.copy()
          job["Employer"] = entity.text
      else:
        #if job_it == FIELD_it then we can add FIELD text to current job dict
        job["Employer"] = entity.text

    if entity.label_ == "STARTDATE":

      #ent iterator progresses through loop of doc entities
      ent_it += 1

      #LABEL iterator keeps track of how many of each we encounter
      startdate_it += 1

      #signifies next job starting
      if startdate_it > job_it:

        #if this is the first job, increment job it and proceed
        if job_it == 0:
          job_it += 1
          job = job_default.copy()
          job["EmploymentStartDate"] = entity.text
        else:

          #start and end dates need an extra check since I don't want to append jobs with only dates
          if job["Notes"] == "" and job["Employer"] == "":

            #if only dates have been found, clear job object and proceed
            job = job_default.copy()
            job["EmploymentStartDate"] = entity.text
            job_it += 1
            jobtitle_it, employer_it, enddate_it = job_it - 1, job_it - 1, job_it - 1

          #job is ready to be appended AND jobtitle or employer are not empty
          else:
            jobs.append(job)
            job_it += 1

            #bring everything else up to 1 less than the job it
            jobtitle_it, employer_it, enddate_it = job_it - 1, job_it - 1, job_it - 1
            job = job_default.copy()
            job["EmploymentStartDate"] = entity.text

      #if job_it == FIELD_it then we can add FIELD text to current job dict
      else:
        job["EmploymentStartDate"] = entity.text

    if entity.label_ == "ENDDATE":

      #ent iterator progresses through loop of doc entities
      ent_it += 1

      #LABEL iterator keeps track of how many of each we encounter
      enddate_it = enddate_it + 1

      #signifies next job starting
      if enddate_it > job_it:

        #if this is the first job, increment job it and proceed
        if job_it == 0:
          job_it += 1
          job = job_default.copy()
          job["EmploymentEndDate"] = entity.text
        else:

          #start and end dates need an extra check since I don't want to append jobs with only dates
          if job["Notes"] == "" and job["Employer"] == "":

            #if only dates have been found, clear job object and proceed
            job = job_default.copy()
            job["EmploymentEndDate"] = entity.text
            job_it += 1
            jobtitle_it, employer_it, startdate_it = job_it - 1, job_it - 1, job_it - 1
          #job is ready to be appended AND jobtitle or employer are not empty
          else:
            jobs.append(job)
            job_it += 1
            jobtitle_it, employer_it, startdate_it = job_it - 1, job_it - 1, job_it - 1
            job = job_default.copy()
            job["EmploymentEndDate"] = entity.text

      else:
        job["EmploymentEndDate"] = entity.text

  #at the end, append what's left in the job dict as long as it's not only dates
  if job["Notes"] != "" or job["Employer"] != "":
    jobs.append(job)
    job = job_default.copy()

  #if no entities have been found, append the empty default job dictionary
  if not jobs:
    jobs.append(job_default.copy())

  return jobs


"""#### Note:  this algorithm does not account for situations where spacy identifies multiple jobtitles per a singular experience, or creates a false positive for an extra employer. In these situations the final result will not be accurate

#### However I have trained the model in Prodigy only highlighting instances where there was exactly one of each field, so hopefully with enough annotations, the algorithm will work in a high percentage of situations

#### Another flaw would be a situation where spacy did not recognize a field in a job, but then begins the next job with that field. For example, job 1 did not have a jobtitle detected. But job 2 begins with its jobtitle, job 2's jobtitle would be grouped into job 1. A potential fix to this is TBD with another algorithm that establishes the expected order of labels within each section

#Now repeating the previous algorithm for education
"""

#required fields, INSTITUTION, DEGREE, YEAR

def make_edus(edu_section):
  inst_it = 0
  degree_it = 0
  year_it = 0

  edu_it = 0
  ent_it = 0

  edus = []
  edu_default = {"Institution": "", "Degree":"", "YearEarned":""}
  edu = edu_default.copy()

  if edu_section == "":
    edus.append(edu_default.copy())
    return edus

  #load custom model  
  nlp = spacy.load("./resources/models/edu-model")

  #make spacy doc from education section
  doc = nlp(edu_section)

  #loop through spacy doc entities
  while ent_it < len(doc.ents):
    entity = doc.ents[ent_it]
    if entity.label_ == "INSTITUTION":
      ent_it += 1
      inst_it +=1
      if inst_it > edu_it:
        if edu_it == 0:
          edu_it += 1
          edu = edu_default.copy()
          edu["Institution"] = entity.text
        else:
          edus.append(edu)
          edu_it += 1
          degree_it, year_it = edu_it - 1, edu_it - 1
          edu = edu_default.copy()
          edu["Institution"] = entity.text
      else:
        edu["Institution"] = entity.text
    if entity.label_ == "DEGREE":
      ent_it += 1
      degree_it += 1
      if degree_it > edu_it:
        if edu_it == 0:
          edu_it += 1
          edu = edu_default.copy()
          edu["Degree"] = entity.text
        else:
          edus.append(edu)
          edu_it += 1
          inst_it, year_it = edu_it - 1, edu_it - 1
          edu = edu_default.copy()
          edu["Degree"] = entity.text
      else:
        edu["Degree"] = entity.text
    if entity.label_ == "YEAR":
      ent_it += 1
      year_it += 1
      if year_it > edu_it:
        if edu_it == 0:
          edu_it += 1
          edu = edu_default.copy()
          edu["YearEarned"] = entity.text
        else:
          if edu["Degree"] == "" and edu["Institution"] == "":
            edu = edu_default.copy()
            edu["YearEarned"] = entity.text
            edu_it += 1
            degree_it, inst_it = edu_it - 1, edu_it - 1
          else:
            edus.append(edu)
            edu_it += 1
            degree_it, inst_it = edu_it - 1, edu_it - 1
            edu = edu_default.copy()
            edu["YearEarned"] = entity.text
      else:
        edu["YearEarned"] = entity.text
  if edu["Degree"] != "" or edu["Institution"] != "":
    edus.append(edu)
    edu = edu_default.copy()

  if not edus:
    edus.append(edu_default.copy())

  return edus


"""#Once more for Certifications"""
#required fields/labels, INSTITUTION, CERT, YEAR
# as they appear in final JSON: "Institution", "AcquiredDate", "Notes"

def make_certs(certs_section):
  inst_it = 0
  notes_it = 0
  year_it = 0

  cert_it = 0
  ent_it = 0

  certs = []
  cert_default = {"Institution": "", "AcquiredDate":"", "Notes":""}
  cert = cert_default.copy()

  if certs_section == "":
    certs.append(cert_default.copy())
    return certs

  #load custom model
  nlp = spacy.load("./resources/models/certs-model-best")

  #make spacy doc from certs section
  doc = nlp(certs_section)

  #loop through spacy doc entities
  while ent_it < len(doc.ents):
    entity = doc.ents[ent_it]
    if entity.label_ == "CERT_INST":
      ent_it += 1
      inst_it +=1
      if inst_it > cert_it:
        if cert_it == 0:
          cert_it += 1
          cert = cert_default.copy()
          cert["Institution"] = entity.text
        else:
          certs.append(cert)
          cert_it += 1
          notes_it, year_it = cert_it - 1, cert_it - 1
          cert = cert_default.copy()
          cert["Institution"] = entity.text
      else:
        cert["Institution"] = entity.text

    if entity.label_ == "CERT_NAME":
      ent_it += 1
      notes_it += 1
      if notes_it > cert_it:
        if cert_it == 0:
          cert_it += 1
          cert = cert_default.copy()
          cert["Notes"] = entity.text
        else:
          certs.append(cert)
          cert_it += 1
          inst_it, year_it = cert_it - 1, cert_it - 1
          cert = cert_default.copy()
          cert["Notes"] = entity.text
      else:
        cert["Notes"] = entity.text

    if entity.label_ == "CERT_DATE":
      ent_it += 1
      year_it += 1
      if year_it > cert_it:
        if cert_it == 0:
          cert_it += 1
          cert = cert_default.copy()
          cert["AcquiredDate"] = entity.text
        else:
          if cert["Notes"] == "" and cert["Institution"] == "":
            cert = cert_default.copy()
            cert["AcquiredDate"] = entity.text
            cert_it += 1
            inst_it, notes_it = cert_it - 1, cert_it - 1
          else:
            certs.append(cert)
            cert_it += 1
            inst_it, notes_it = cert_it - 1, cert_it - 1
            cert = cert_default.copy()
            cert["AcquiredDate"] = entity.text
      else:
        cert["AcquiredDate"] = entity.text
  if cert["Institution"] != "" or cert["Notes"] != "":
    certs.append(cert)
    cert = cert_default.copy()

  if not certs:
    certs.append(cert_default.copy())

  return certs


#make_skills uses a model to analyze the skills section in a resume
def make_skills(skills_section):

  nlp = spacy.load("./resources/models/skills-model-best")

  #make spacy doc from education section
  doc = nlp(skills_section)

  skills = []
  skill_default = {"SkillName":""}

  if skills_section == "":
    skills.append(skill_default)
    return skills

  for ent in doc.ents:
    skill = {"SkillName": ent.text}
    skills.append(skill)

  if not skills:
    skills.append(skill_default)

  return skills


#find_skills looks through the entire resume and checks for names in the technical_skills list
def find_skills(resume):
  words = resume.strip().split()
  skills = []
  final_skills = []
  for word in words:
    if word in technical_skills:
      skills.append(word)
  skills = list(set(skills))
  for skill in skills:
    skill_dict = {}
    skill_dict['SkillName'] = skill
    final_skills.append(skill_dict)
  return final_skills

#for eventually creating employment duration field
def convert_date(text):
  present_words = ['present', 'current', 'till date', 'now', 'currently', 'presently', 'present day']
  if text == "":
      return ""
  if text.lower() in present_words:
    return datetime.now().year
  #for instances of "2021-"
  if text[-1] == "-":
    last_two = text[-3:-1]
  else:
    last_two = text[-2:]   
    try:
      last_two_int = int(last_two)
      if last_two_int <= int(str(datetime.now().year)[-2:]):
        year = 2000 + last_two_int
      else:
        year = 1900 + last_two_int
      return year
    except Exception:
      print("EXCEPT:", text)
      return ""

#work duration will not be displayed but will just be for the job duration search modifier
def add_work_duration(resume_work_exp):
  updated_work_exp = resume_work_exp
  for job in updated_work_exp:
    if job['Notes'] == "" and job['Employer'] == "":
      job['EmploymentDuration'] = ""
      #continue
    else:
      start_date = convert_date(job['EmploymentStartDate'])
      end_date = convert_date(job['EmploymentEndDate'])
      #if start or end dates were not detected by spaCy
      if start_date == "" or end_date == "":
        duration = 1
      else:
        duration = end_date - start_date
      #minimum default duration is 1 year even if experience is less than 1 year
        if duration == 0:
          duration = 1
      job['EmploymentDuration'] = duration
  return updated_work_exp

""" Final output functions taking the results of section functions """

#Accepts a list of resumes and outputs a list of dictionaries
def combine_parsing_list(resumes):
  dict_list = []
  for resume in resumes:
    sections = make_sections(resume, regexs)
    resume_info = make_basicinfo(resume)
    work_exp = make_jobs(sections["exp"])
    work_exp_dur = add_work_duration(work_exp)
    resume_info["ResourceWorkExperience"] = work_exp_dur
    resume_info["ResourceEducation"] = make_edus(sections["edu"])
    resume_info["ResourceCredentials"] = make_certs(sections["certs"])
    #first use skills model on skills section
    skills = make_skills(sections["skills"])
    #if the skills model didn't find anything, look for skills stored in 'skills.py'
    if skills[0]['SkillName'] == "":
      skills = find_skills(resume)
    resume_info["Skills"] = skills
    sys_pro_res = {"SystemProviderResources":resume_info}
    dict_list.append(sys_pro_res)
  return dict_list

#Accepts a single resume as argument when used inside of another loop
def combine_parsing_single(resume):
  sections = make_sections(resume, regexs)
  resume_info = make_basicinfo(resume)
  work_exp = make_jobs(sections["exp"])
  work_exp_dur = add_work_duration(work_exp)
  resume_info["ResourceWorkExperience"] = work_exp_dur
  resume_info["ResourceEducation"] = make_edus(sections["edu"])
  resume_info["ResourceCredentials"] = make_certs(sections["certs"])
  resume_info["Skills"] = make_skills(resume)
  sys_pro_res = {"SystemProviderResources":resume_info}
  return sys_pro_res

