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


