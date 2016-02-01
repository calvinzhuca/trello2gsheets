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
        self.parse_config_boards(trello_sources[':assignments'], self.content[':output_metadata'][':trello_sources'][':assignments'], "assignment")
        if ':epics' in trello_sources:
            self.parse_config_boards(trello_sources[':epics'], self.content[':output_metadata'][':trello_sources'][':epics'], "epic")
        self.logger.debug("Report output metadata: %s" % (self.content[':output_metadata']))

    def parse_config_boards(self, config_src, report_metadata, card_type):
        """parse config_src dict to add all boards/lists for processing in the report to report_metadata"""
        for board_t in config_src.keys():
            board_id = config_src[board_t][':board_id']
            report_metadata[board_id] = {};
            report_metadata[board_id][':board_id'] = config_src[board_t][':board_id'] #copy board id
            report_metadata[board_id][':board_name'] = board_t

            #iterate through all the lists and populate them
            report_metadata[board_id][':lists'] = {}
            for list_t in config_src[board_t][':lists'].keys():
                self.logger.debug("Adding board %s, list %s to the report" % (config_src[board_t][':board_id'], config_src[board_t][':lists'][list_t]))
                list_id = config_src[board_t][':lists'][list_t]
                report_metadata[board_id][':lists'][list_id] = {};
                report_metadata[board_id][':lists'][list_id][':list_id'] = list_id
                report_metadata[board_id][':lists'][list_id][':completed'] = False;
                report_metadata[board_id][':lists'][list_id][':card_type'] = card_type;
            if ':done_lists' in config_src[board_t]:
                for list_t in config_src[board_t][':done_lists'].keys():
                    self.logger.debug("Adding board %s, list %s to the report" % (config_src[board_t][':board_id'], config_src[board_t][':done_lists'][list_t]))
                    list_id = config_src[board_t][':done_lists'][list_t]
                    report_metadata[board_id][':lists'][list_id] = {};
                    report_metadata[board_id][':lists'][list_id][':list_id'] = list_id
                    report_metadata[board_id][':lists'][list_id][':completed'] = True;
                    report_metadata[board_id][':lists'][list_id][':card_type'] = card_type;

    def list_boards(self):
        syseng_boards = self.client.list_boards()
        for board in syseng_boards:
            for tlist in board.all_lists():
                self.logger.debug('board name: %s is here, board ID is: %s; list %s is here, list ID is: %s' % (board.name, board.id, tlist.name, tlist.id)) 

    def parse_trello(self, deep_scan):
        """Main function to parse all Trello boards and lists.
        If deep_scan is True the scan will traverse each card, otherwise just a light scan(much faster)"""
        trello_sources = self.content[':output_metadata'][':trello_sources'];
        self.logger.debug('The sources are %s' % (trello_sources))

        self._parse_sources(self.content[':output_metadata'][':trello_sources'][':assignments'], "assignment", deep_scan)
        self._parse_sources(self.content[':output_metadata'][':trello_sources'][':epics'], "epic", deep_scan)
        return self.content

    def _parse_sources(self, trello_sources, card_type, deep_scan):
        """Helper function to scan either assignments or epics defined in the config
        If deep_scan is True the scan will traverse each card, otherwise just a light scan(much faster).
        trello_sources: dict that contains configuration and output structure
        card_type: whether we'll be parsing epics or assignments"""
        for board_t in trello_sources.keys():
            tr_board = self.client.get_board(board_t);
            tr_board.fetch();
            members = [ (m.id, m.full_name.decode('utf-8')) for m in tr_board.get_members()];
            self.logger.debug('considering board %s, and members %s' % (trello_sources[board_t][':board_name'], members))

            #parse all the regular lists from :lists section of config
            for list_t in trello_sources[board_t][':lists'].keys():
                self._parse_list(trello_sources[board_t][':lists'][list_t], tr_board, members, deep_scan)

        return self.content

    def _parse_list(self, list_config, tr_board, members, deep_scan):
        """Parse individual lists.
        list_id: Trello list ID to be parsed
        tr_board: py-trello board object, fully fetched
        list_type: whether this is a list of epics or a list of assignments
        members: list of tuples (member_id, member_full_name) of all members of the board
        deep_scan: whether we need to traverse each card"""
        collected_content = self.content[':collected_content'];
        #self.logger.debug('list_config is %s' % (list_config))
        tr_list = tr_board.get_list(list_config[':list_id'])
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
            collected_content[card.id][':card_type'] = list_config[':card_type']
            collected_content[card.id][':list_id'] = list_config[':list_id']
            collected_content[card.id][':completed'] = list_config[':completed']

            if deep_scan:
                details = self.parse_card_details(card.id)
                collected_content[card.id][':latest_move'] = details[':latest_move']
                collected_content[card.id][':detailed_status'] = details[':detailed_status']
                collected_content[card.id][':due_date'] = details[':due_date']
                collected_content[card.id][':completed_date'] = details[':completed_date']
                try:
                    collected_content[card.id][':last_updated'] = details[':last_updated']
                except AttributeError as e:
                    self.logger.debug('attribute error: %s' % (e))
                    collected_content[card.id][':last_updated'] = ""
                #self.logger.debug('processed card %s' % (collected_content[card.id]))
            else:
                collected_content[card.id][':latest_move'] = "not collected"
                collected_content[card.id][':detailed_status'] = "not collected"
                collected_content[card.id][':due_date'] = "not collected"
                collected_content[card.id][':last_updated'] = "not collected"
                collected_content[card.id][':completed_date'] = "not collected"
        return self.content

    def parse_card_details(self, card_id):
        card = card_details.CardDetails(card_id, self.client, self.content[':output_metadata'])
        details = card.fill_details();
        #self.logger.debug('Card\'s details are: %s' % (details))
        return details
