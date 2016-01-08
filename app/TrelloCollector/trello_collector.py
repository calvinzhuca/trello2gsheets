# -*- coding: utf-8 -*-

import os
import csv

from trello import TrelloClient
import logging

import httplib2
import datetime


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
            #report_src[board_t][':board_name'] = 
            for list_t in trello_sources[board_t][':lists'].keys():
                self.logger.debug("Adding board %s, list %s to the report" % (trello_sources[board_t][':board_id'], trello_sources[board_t][':lists'][list_t]))
                report_src[board_t][':lists'][list_t] = {};
                report_src[board_t][':lists'][list_t][':list_id'] = trello_sources[board_t][':lists'][list_t]

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
        collected_content = self.content[':collected_content'];
        trello_sources = self.content[':output_metadata'][':trello_sources'];
        self.logger.debug('The sources are %s' % (trello_sources))
        for board_t in trello_sources.keys():
            tr_board = self.client.get_board(trello_sources[board_t][':board_id']);
            self.logger.debug('considering board %s' % (board_t))
            for list_t in trello_sources[board_t][':lists'].keys():
                tr_list = tr_board.get_list(trello_sources[board_t][':lists'][list_t][':list_id'])
                cards = tr_list.list_cards()
                self.logger.debug('got cards %s' % (cards))
                json_obj = self.client.fetch_json('/lists/' + trello_sources[board_t][':lists'][list_t][':list_id'] + '/cards/')
                self.logger.debug('list json is %s' % (json_obj))
                for card in cards:
                    collected_content[card.id] = {}
                    collected_content[card.id][':name'] = card.name.decode("utf-8")
                    collected_content[card.id][':id'] = card.id
                    collected_content[card.id][':members'] = card.member_ids
                    collected_content[card.id][':desc'] = card.desc
                    try:
                        collected_content[card.id][':last_updated'] = card.dateLastActivity
                    except AttributeError as e:
                        self.logger.debug('attribute error: %s' % (e))
                        collected_content[card.id][':last_updated'] = ""
                    collected_content[card.id][':short_url'] = card.url
                    collected_content[card.id][':labels'] = [label.name.decode("utf-8") for label in card.labels]
#                    collected_content[card.id][':due_date'] = card.due
                    self.logger.debug('processed card %s' % (collected_content[card.id]))
#                    collected_content[card.id][':board_name']
        return self.content