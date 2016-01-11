# -*- coding: utf-8 -*-

import os
import csv

from trello import TrelloClient
import logging

import httplib2
import datetime

from . import card_details

class TrelloCollector(object):
    """
    Class representing all Trello information required to do the SysDesEng reporting.
    """

    def __init__(self, report_config, trello_secret):
        self.logger = logging.getLogger("sysengreporting")
        self.client = TrelloClient(api_key = trello_secret[':consumer_key'],
                                   api_secret = trello_secret[':consumer_secret'],
                                   token = trello_secret[':oauth_token'],
                                   token_secret = trello_secret[':oauth_token_secret'])

        #Extract report configuration parameters
        trello_sources = report_config[':trello_sources'];
        self.special_tags = report_config[':tags'];
        self.report_parameters = report_config[':output_metadata'];
        gen_date = datetime.datetime.now().strftime("%Y-%m-%d.%H:%M")

        self.content = { ':output_metadata' : {
                              ':report_name': "Assignments Report" + gen_date,
                              ':trello_sources': {}}, 
                         ':collected_content': {}}

        report_src = self.content[':output_metadata'][':trello_sources']
        for board_t in trello_sources.keys():
            report_src[board_t] = {};
            report_src[board_t][':board_id'] = trello_sources[board_t][':board_id']
            report_src[board_t][':lists'] = {}
            report_src[board_t][':epics'] = {}
            #report_src[board_t][':board_name'] = 
            for list_t in trello_sources[board_t][':lists'].keys():
                self.logger.debug("Adding board %s, list %s to the report" % (trello_sources[board_t][':board_id'], trello_sources[board_t][':lists'][list_t]))
                report_src[board_t][':lists'][list_t] = {};
                report_src[board_t][':lists'][list_t][':list_id'] = trello_sources[board_t][':lists'][list_t]
            for epics_t in trello_sources[board_t][':epics'].keys():
                self.logger.debug("Adding board %s, epic list %s to the report" % (trello_sources[board_t][':board_id'], trello_sources[board_t][':epics'][epics_t]))
                report_src[board_t][':epics'][epics_t] = {};
                report_src[board_t][':epics'][epics_t][':list_id'] = trello_sources[board_t][':epics'][epics_t]

    def list_boards(self):
        syseng_boards = self.client.list_boards()
        for board in syseng_boards:
            for tlist in board.all_lists():
                self.logger.debug('board name: %s is here, board ID is: %s; list %s is here, list ID is: %s' % (board.name, board.id, tlist.name, tlist.id)) 

    def get_assignment_details(self, assignment_id):
        gassign = group_assignment.GroupAssignment(assignment_id, self.client)
        gassign.get_name()
        gassign.get_members()
        gassign.get_tags();
        gassign.get_status();
        gassign.get_detailed_status();
        logger.debug('latest move is: %s' % self.gassign.content['latest_move'])
        logger.debug('Card content: %s' % self.gassign.content)


    def parse_trello(self):
        trello_sources = self.content[':output_metadata'][':trello_sources'];
        self.logger.debug('The sources are %s' % (trello_sources))
        for board_t in trello_sources.keys():
            tr_board = self.client.get_board(trello_sources[board_t][':board_id']);
            tr_board.fetch();
            members = [ (m.id, m.full_name.decode('utf-8')) for m in tr_board.get_members()];
            self.logger.debug('considering board %s, and members %s' % (board_t, members))
            for list_t in trello_sources[board_t][':lists'].keys():
                self.parse_list(trello_sources[board_t][':lists'][list_t][':list_id'], tr_board, "assignment", members)
            for list_t in trello_sources[board_t][':epics'].keys():
                self.parse_list(trello_sources[board_t][':epics'][list_t][':list_id'], tr_board, "epic", members)
            return self.content

    def parse_list(self, list_id, tr_board, list_type, members):
        collected_content = self.content[':collected_content'];
        tr_list = tr_board.get_list(list_id)
        tr_list.fetch();
        cards = tr_list.list_cards()
        self.logger.debug('got cards %s' % (cards))
        for card in cards:
            collected_content[card.id] = {}
            collected_content[card.id][':name'] = card.name.decode("utf-8")
            collected_content[card.id][':id'] = card.id
            collected_content[card.id][':members'] = []
            for member_id in card.member_ids:
                for (m_id, m_full_name) in members:
                    if member_id == m_id :
                       collected_content[card.id][':members'].append(m_full_name)
            collected_content[card.id][':desc'] = card.desc
            try:
                collected_content[card.id][':last_updated'] = card.dateLastActivity
            except AttributeError as e:
                self.logger.debug('attribute error: %s' % (e))
                collected_content[card.id][':last_updated'] = ""
            collected_content[card.id][':short_url'] = card.url
            collected_content[card.id][':labels'] = [label.name.decode("utf-8") for label in card.labels]
            collected_content[card.id][':board_name'] = tr_board.name
            collected_content[card.id][':list_name'] = tr_list.name
            collected_content[card.id][':card_type'] = list_type
            details = self.parse_card_details(card.id)
            collected_content[card.id][':latest_move'] = details[':latest_move']
            collected_content[card.id][':detailed_status'] = details[':detailed_status']
            collected_content[card.id][':due_date'] = details[':due_date']
            self.logger.debug('processed card %s' % (collected_content[card.id]))
        return self.content

    def parse_card_details(self, card_id):
        card = card_details.CardDetails(card_id, self.client)
        details = card.fill_details();
        self.logger.debug('Card\'s details are: %s' % (details))
        return details
