# -*- coding: utf-8 -*-

import os
import csv

from trello import TrelloClient
from trello.card import *
from trello.exceptions import *
from trello.checklist import *

import logging
import httplib2
import datetime


class TrelloUpdater(object):
    """
    Class for writing to Trello.
    """

    def __init__(self, processed_report, trello_secret):
        self.logger = logging.getLogger("sysengreporting")
        self.client = TrelloClient(api_key = trello_secret[':consumer_key'],
                                   api_secret = trello_secret[':consumer_secret'],
                                   token = trello_secret[':oauth_token'],
                                   token_secret = trello_secret[':oauth_token_secret'])

        #Extract report configuration parameters
        self.projects = processed_report[':collected_content'][':projects'];
        self.epics = processed_report[':collected_content'][':epics'];
        self.assignments = processed_report[':collected_content'][':assignments'];


    def update_projects(self):
        """Main function to update all project cards from config."""
        self.logger.info('---Started writing to Trello---')
        for project in self.projects:
            #find special card for no projects
            if self.projects[project][':name'] == 'No Project':
                no_project = project

            child_cards = [] #tuples of (name of chklist item, state of chklist item)
            #form lists of items for checklists
            for card in list(self.assignments):
                if self.assignments[card][':project'] == self.projects[project][':project'] and self.projects[project][':project'] != []:
                    chk_item_name = self.assignments[card][':short_url'] +" (" + self.assignments[card][':list_name'] + ") (" + self.assignments[card][':board_name'] + ")"
                    child_cards.append((chk_item_name, self.assignments[card][':completed']))
                    #self.logger.debug('Appending assignment %s to the project %s' % (self.assignments[card], self.projects[project][':name']))
                    self.assignments.pop(card,None)
            self.logger.debug("Project %s has assignments : %s" % (self.projects[project][':name'], child_cards))
            child_cards.sort(key = lambda x: x[1]) # Sort, so that unresolved cards are on top
            self.update_card(project, [ i[0] for i in child_cards] ,  [ i[1] for i in child_cards]);

        #assign items with no project to a special project card
        child_cards = []
        for card in self.assignments:
            chk_item_name = self.assignments[card][':short_url'] +" (" + self.assignments[card][':list_name'] + ") (" + self.assignments[card][':board_name'] + ")"
            child_cards.append((chk_item_name, self.assignments[card][':completed']))
            #self.logger.debug('Appending assignment %s to the No Project' % (self.assignments[card]))
        child_cards.sort(key = lambda x: x[1])
        self.logger.debug("Project %s has assignments : %s" % (self.projects[project][':name'], child_cards))
        self.update_card(no_project, [ i[0] for i in child_cards] ,  [ i[1] for i in child_cards]);

    def update_card(self, card_id, checklist_names, checklist_states):
        """
        Clean checklists from the card,
        Write new checklists to the card based on the report
        checklist_data: [("ID", "short_url", "list_name", "board_name", completed),...]
        """
        while True:
            try:
                tr_card = self.client.get_card(card_id)
                tr_card.fetch(eager=True)

                #self.logger.debug('Fetching checklists < %s > for Trello for card: %s' % (tr_card.checklists,self.projects[card_id][':name']))
            except ResourceUnavailable as e:
                self.logger.error('Trello unavailable! %s' % (e))
                continue
            break

        # Remove all existing checklists
        for old_chklist in tr_card.checklists:
            old_chklist.delete()

        assign_chk = tr_card.add_checklist("Assignments", checklist_names, checklist_states)

