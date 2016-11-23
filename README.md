trello-reporter
===============

The app collects data from specified lists on specified Trello boards.

Report to Google Spreadsheets
-----------------------------
The report can be writtn directly to the Google Spreadsheets.
It uses pre-defined "template" spreadsheet to provide various views/pivots.

Linking card hierarchy
----------------------
The program can link hierarchy of cards: Assignment card to Epics/Projects, Epic cards to Projects.
When linked lower hierarchy card will be visible as a checklist item in higher hierarchy card.

Hierarchy of cards
------------------
There are 3 types of cards:
* Assignment
* Epic
* Project

Assignment may belong to only one Epic.
Epic must belong to only one Project.

Each Trello list must contain only one type of cards. i.e. the list cannot contain Assignment card and Epic card at the same time.

Card categorization
-------------------
Cards are categorized via "tags" and Trello labels.
Tag is a bracketed plain text. f.e. the following tag anywhere in the description or in the title of the card says that the card belongs to project XXX
> [project_XXX]

-------------------
instructions
1) Set up new repository, fork from https://github.com/t0ffel/trello2gsheets

git clone git@github.com:calvinzhuca/trello2gsheets.git


2) Setup access for Trello

In trello_secret.yml there are 4 variables. 

:consumer_key: <get_on_trello_com>
:consumer_secret: <get_on_trello_com>
:oauth_token: <generate_via_script>
:oauth_token_secret: <generate_via_script>


Get the first two (key and secret) from https://trello.com/app-key


Then get the oauth_token and oauth_token_secret from this project. 
https://github.com/sarumont/py-trello

git clone git@github.com:sarumont/py-trello.git

	Note: the key and secret here are from last step
	export TRELLO_API_KEY=xxxxxxxxxxxxxx
	export TRELLO_API_SECRET=xxxxxxxxxxxxx
	python ./trello/util.py


	Request Token:
	    - oauth_token        = xxxxxxxxxxxxxxxxxxxxx
	    - oauth_token_secret = xxxxxxxxxxxxxxxxxxxxx

	Go to the following link in your browser:
	https://trello.com/1/OAuthAuthorizeToken?oauth_token=738a0b94ba24965ab0064592ab00cb2c&scope=read,write&expiration=30days&name=py-trello
	Have you authorized me? (y/n) y
	What is the PIN? ed31d4ef086b1f40102f6d9540af244a
	Access Token:
	    - oauth_token        = xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	    - oauth_token_secret = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

3) Set up Google Drive access
follow this https://developers.google.com/drive/v3/web/quickstart/python
Using the Google Drive APIs wizard get the json file and copy to local

/usr/lib/python2.7/site-packages/config/client_secret.json

client_secret.json is used to read the template from Google Drive
Note: secrets/drive-python-credentials.json will be generated first time running the script. This secret is used to upload report. 


4) Setup the Google worksheet templates, current using these 2 templates
	Template of SysEng Issues Report 2016-10-19 17:20
	template SysEng Assignments Report 2016-11-16 20:20

Open them in Google worksheet, get the template id from URL, then update issues.yml and report.yml. 

5) Run in trello2gsheets to generate two reports
python setup.py install
trello2gsheets --config config/issues.yml

trello2gsheets --config config/report.yml
