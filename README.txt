Project - "OtterParsing"

Description
OtterParsing is an app designed to parse resumes and extract the essential information. It is meant to be a tool for recruiters or 
hiring managers who may have to sift through hundreds or even thousands of applicants depending on the position.
While there are free tools available for this purpose, they may not be reliable. LLMs like ChatGPT may be able to handle tasks like this
but eventually the amount of data and processing required may not be available in a free tier, and could prove costly over time.

OtterParsing utilizes trained models that look for the key elements in resumes and stores them in a built in SQLite database.
For our models we used spaCy, a free and open-source library for Natural Language Processing (NLP) in Python. spaCy is created by
a company called Explosion, and they offer another paid program called Prodigy which greatly speeds up the process of training custom
spaCy models. Fortunately Explosion offers temporary free academic licenses to use Prodigy which our group was able to obtain for the
duration of this project. While our free use of Prodigy will expire, the custom models we trained will remain and could continue to be
of use in the future.

Our process has been to split up resumes by section, such as Work Experience and Education, and create training sets from these 
isolated sections. From there the training sets were imported into Prodigy where we determine a set of labels for certain entities
found within the text. For example in Work Experience we looked for all instances of job titles, employers, and start and end dates
for each individual work experience. After manually annotating 300-400 resumes per section, the models will begin to demonstrate
the ability to reliably recognize these entities within the text. The models are then exported from Prodigy and can easily be imported
into a project where we just need a bit of code to translate the found entities back into standard Python variables. 

Initially our goal was to extract all the essential resume information and export it as JSON as that would comply with our project
manager's company's API. However due to time contraints given the nature of a short-term class project we did not end up integrating
our results with the API. The app still organizes the data into Python lists of dictionaries where we then simply store the individual
fields into tables within a relational database. From there the app provides a simple visual interface including a summary page that
displays all the extracted information for each uploaded resume as well as a search page allowing the user to filter through the results.

Installation
Depending on your system, there may be certain packages or libraries that need to be installed in order to run OtterParsing as a
web application that runs in your localhost. We used the Flask framework since it is lightweight and allowed us to keep everything in Python.
Typically Flask also behaves best inside of a virtual environment. Since we have trained spaCy models, naturally the spaCy library will need to
be installed. While on most occasions we trained the spaCy models beginning with their blank template, for a candidate's basic information
we utilized spaCy's en_core_web_lg model as backup in case the basic information was not detected using regex patterns, so this model
will need to be installed as well.

pip install flask
pip install spacy
!spacy download en_core_web_lg

Project Status
There are several ways in which this project could be improved. First of all we took a somewhat non-traditional approach to NLP projects
by not entirely cleaning the text we are working with. We made a choice to isolate sections of the resume by looking for the headers that
define each section such as 'Work Experience' or 'Education' and we assumed that these headers would be wrapped in new-line characters.
So to this extent we did not remove new-line characters from the training set or from new resumes we accept for parsing in the app. 
The main issue with this approach is that we are at the mercy of how the resumes are converted from their original PDF format to single 
Python strings. If a resume uses an unusual template or otherwise presents information in a multi-column format, our results are very unlikely 
to be accurate because the conversion to a string will likely not maintain the relative order of content as intended in the resume. So an alternate
approach would be to clean the text completely and simply look to identify relavent entities such as job title or employer wherever they
occur without the need to first identify section headers. The approach still could be taken to use multiple models to identify relavent 
entities, however the training sets would simply be the entire resume as opposed to isolated sections.
Another approach would be to use one model with many labels for every relevant entity from elements of basic personal information,
to work experiences, education and so forth. This would also simplify the process of collecting the extracted information, or analyzing
the found entities. However, it is common for spaCy models to identify false positives without sufficient training. So for example,
if a model trained to identify elements of work experience is given the entire resume to look at, we believe it would require many 
additional annotations in order to ensure that the model will not detect things like universities, certificate issuing institutions or
groups related to project work as something directly tied to work experience. 
Regardless of the approach, this practice of training models naturally yields higher accuracy with more training.
As a team we did close to 2000 annotations in Prodigy, and given our design choice of including new-line characters, we found that when
resumes were in fact laid out in a traditional template with a single-column format, our results were suprisingly accurate. If another
design choice were used, like cleaning the data completely and using a single model with many labels, many features of this project
could still be utilized like our functions 'make_jobs', 'make_edus' and 'make_certs' which utilize a similar algorithm that attempts
to group entities into single experiences since it is important to not just identify employers and job titles, but actually group them correctly.


Authors and acknowledgment
One more acknowledgment for the team at Explosion for providing the temporary free academic licenses to Prodigy. We certainly could
not have done this project without them. In addition it was great to learn about spaCy, a fun to use library with excellent documentation.

We would also like to thank our project advisor George Sarkis over at OtterSoft for creating a useful and relevant project for us
and providing guidance throughout the process.

OtterParsing was a collaborative school project between students at California State University Monterey Bay - 2024
Students: Andrew Grant, Christopher Varela, David Kim, Jerry Do, Matthew Chan