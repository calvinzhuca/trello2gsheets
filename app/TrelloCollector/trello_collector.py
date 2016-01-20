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
        self.report_parameters = report_config[':output_metadata'];
        gen_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        self.content = { ':output_metadata' : {
                              ':report_name': gen_date, #Report name is built as :report_name + gen_date (where :report_name is taken from the config)
                              ':trello_sources': {
                                ':epics': {},
                                ':assignments': {}}}, 
                         ':collected_content': {}}

        report_src = self.content[':output_metadata'][':trello_sources'][':assignments']
        self.parse_config_boards(trello_sources[':assignments'], self.content[':output_metadata'][':trello_sources'][':assignments'])
        if ':epics' in trello_sources:
            self.parse_config_boards(trello_sources[':epics'], self.content[':output_metadata'][':trello_sources'][':epics'])
        self.logger.debug("Report output metadata: %s" % (self.content[':output_metadata']))

    def parse_config_boards(self, config_src, report_metadata):
        """parse config_src dict to add all boards/lists for processing in the report to report_metadata"""
        for board_t in config_src.keys():
            report_metadata[board_t] = {};
            report_metadata[board_t][':board_id'] = config_src[board_t][':board_id'] #copy board id

            #iterate through all the lists and populate them
            report_metadata[board_t][':lists'] = {}
            for list_t in config_src[board_t][':lists'].keys():
                self.logger.debug("Adding board %s, list %s to the report" % (config_src[board_t][':board_id'], config_src[board_t][':lists'][list_t]))
                report_metadata[board_t][':lists'][list_t] = {};
                report_metadata[board_t][':lists'][list_t][':list_id'] = config_src[board_t][':lists'][list_t]

    def list_boards(self):
        syseng_boards = self.client.list_boards()
        for board in syseng_boards:
            for tlist in board.all_lists():
                self.logger.debug('board name: %s is here, board ID is: %s; list %s is here, list ID is: %s' % (board.name, board.id, tlist.name, tlist.id)) 

    def parse_trello(self):
        trello_sources = self.content[':output_metadata'][':trello_sources'];
        self.logger.debug('The sources are %s' % (trello_sources))

        self._parse_sources(self.content[':output_metadata'][':trello_sources'][':assignments'], "assignment")
        self._parse_sources(self.content[':output_metadata'][':trello_sources'][':epics'], "epic")
        return self.content

    def _parse_sources(self, trello_sources, card_type):
        for board_t in trello_sources.keys():
            tr_board = self.client.get_board(trello_sources[board_t][':board_id']);
            tr_board.fetch();
            members = [ (m.id, m.full_name.decode('utf-8')) for m in tr_board.get_members()];
            self.logger.debug('considering board %s, and members %s' % (board_t, members))
            for list_t in trello_sources[board_t][':lists'].keys():
                self.parse_list(trello_sources[board_t][':lists'][list_t][':list_id'], tr_board, card_type, members)
        return self.content

    def parse_list(self, list_id, tr_board, list_type, members):
        collected_content = self.content[':collected_content'];
        tr_list = tr_board.get_list(list_id)
        tr_list.fetch();
        cards = tr_list.list_cards()
        self.logger.debug('In list %s got cards %s' % (tr_list.name, cards))
        for card in cards:
            collected_content[card.id] = {}
            collected_content[card.id][':name'] = card.name.decode("utf-8")
            collected_content[card.id][':id'] = card.id
            collected_content[card.id][':members'] = []
            collected_content[card.id][':board_id'] = tr_board.id
            for member_id in card.member_ids:
                for (m_id, m_full_name) in members:
                    if member_id == m_id :
                       collected_content[card.id][':members'].append((m_id,m_full_name))
            collected_content[card.id][':desc'] = card.desc
            collected_content[card.id][':short_url'] = card.url
            collected_content[card.id][':labels'] = [label.name.decode("utf-8") for label in card.labels]
            collected_content[card.id][':board_name'] = tr_board.name
            collected_content[card.id][':list_name'] = tr_list.name
            collected_content[card.id][':card_type'] = list_type
            details = self.parse_card_details(card.id)
            collected_content[card.id][':latest_move'] = details[':latest_move']
            collected_content[card.id][':detailed_status'] = details[':detailed_status']
            collected_content[card.id][':due_date'] = details[':due_date']
            try:
                collected_content[card.id][':last_updated'] = details[':last_updated']
            except AttributeError as e:
                self.logger.debug('attribute error: %s' % (e))
                collected_content[card.id][':last_updated'] = ""
            #self.logger.debug('processed card %s' % (collected_content[card.id]))
        return self.content

    def parse_card_details(self, card_id):
        card = card_details.CardDetails(card_id, self.client)
        details = card.fill_details();
        #self.logger.debug('Card\'s details are: %s' % (details))
        return details
