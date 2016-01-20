# -*- coding: utf-8 -*-

from trello.card import *
from trello.exceptions import *

import logging
import re
import arrow


class CardDetails(object):
    """The CardDetails class reprsents a trello assignment card."""
    def __init__(self, _id, _trello):
        """
        :param _id: ID of the trello card representing this Project
        :param _trello: TrelloClient object
        """
        self.trello = _trello
        self._id = _id
        self.logger = logging.getLogger("sysengreporting")


    def query_trello(self):
        while True:
            try:
                self._card = self.trello.get_card(self._id)
                self._card.fetch(True); #fetch all card's properties at once
                self.logger.debug('Querying Trello for card: %s' % (self._card))
            except ResourceUnavailable as e:
                self.logger.error('Trello unavailable! %s' % (e))
                continue
            break
        while True:
            try:
                self._card.fetch_actions(action_filter='commentCard,updateCard:idList,createCard,copyCard,moveCardToBoard')
                self._actions = sorted(self._card.actions, key = lambda update: update['date'], reverse = True) ; #fetch all card's properties at once
                #self.logger.debug('Actions are %s' % (self._card.actions))
            except ResourceUnavailable as e:
                self.logger.error('Unable to fetch card actions! %s' % (e))
                continue
            break


    def __str__(self):
        return "Card (%s) '%s' owned by '%s'" % (self.content['id'], self.content['name'], self.content['team'])

    def fill_details(self):
        content = {}
        self.query_trello()
        content[':detailed_status'] = 'n/a'
        for action_comment in self._actions:
            if action_comment['type'] == 'commentCard':
                content[':detailed_status'] = action_comment['data']['text']
                break;
        
        content[':latest_move'] = ''
        for update in self._actions:
            #self.logger.debug('Evaluating action for latest move %s' % (update))
            if (update['type'] == 'createCard' or update['type'] == 'updateCard' or update['type'] == 'copyCard' or update['type'] == 'moveCardToBoard'):
                content[':latest_move'] = arrow.get(update['date']).format('YYYY-MM-DD HH:mm:ss')
                break;

        if self._card.due != '':
            content[':due_date'] = arrow.get(self._card.due).format('YYYY-MM-DD HH:mm:ss')
        else:
            content[':due_date'] = ''
        content[':last_updated'] = arrow.get(self._card.dateLastActivity).format('YYYY-MM-DD HH:mm:ss')
        return content

    def get_name(self):
        self.content['name'] = self._card.name.decode(encoding='UTF-8')

    def get_tags(self, special_tags):
        self.content['tags'] = [];

        for tag_type in special_tags.keys():
            self.content[tag_type] = []

        # obtain all tags
        _all_tags = re.findall('\[.*?\]',(str(self._card.name)))
        _all_tags.extend(re.findall('\[.*?\]', str(self._card.desc)))
        self.logger.debug('all tags: %s' % _all_tags)

        # filter out special tag types, see report.yml for tag types.
        for tag in _all_tags:
            for tag_type in special_tags.keys():
                cur_tag = special_tags[tag_type]; # tag type being currently reviewed
                if tag[1:len(cur_tag[':tag_prefix'])+1] == cur_tag[':tag_prefix']:
                    break
            if tag[1:len(cur_tag[':tag_prefix'])+1] == cur_tag[':tag_prefix']:
                    self.content[tag_type].append(tag[len(cur_tag[':tag_prefix'])+1:-1]) #Special tag gets appended to the respective list
            else:
                self.content['tags'].append(tag); #Other tags go to general tags list

    def get_status(self):
        for label in self._card.labels:
            if label.name == b'Ok':
                self.content['status'] = '3-Ok'
                self.content['label'] = 'success'
                return
            if label.name == b'Issues':
                self.content['status'] = '2-issues'
                self.content['label'] = 'warning';
                return;
            if label.name == b'Blocked':
                self.content['status'] =  '1-Blocked';
                self.content['label'] = 'danger';
                return;
            self.content['status'] = '0-n/a';
            self.content['label'] = 'default';
            return;

    def get_members(self):
        self.content['members'] = [];
        for _member_id in self._card.member_id:
            while True:
                try:
                    self.content['members'].append(self.trello.get_member(_member_id))
                except ResourceUnavailable as e:
                    self.logger.debug('Trello unavailable! %s' % (e))
                    continue
                break
            self.logger.debug('Adding members %s to the card %s' % (self.content['members'][-1].full_name, self.content['name']));

    def get_detailed_status(self):
        while True:
            try:
                self._card.fetch_actions('updateCard:idList')
            except ResourceUnavailable as e:
                self.logger.error('Trello unavailable! %s' % (e))
                continue
            break
        self.logger.debug('comments: %s' % (self._card.comments))
        if self._card.comments != []:
            self.content['detailed_status'] = self._card.comments[-1]['data']['text'];
        else:
            self.content['detailed_status'] = 'n/a'
        self.content['last_updated'] = self._card.dateLastActivity.strftime("%Y-%m-%d %H:%M");
        self.logger.debug('Detailed Status: %s' % (self.content['detailed_status']));
        self.logger.debug('Last Updated: %s' % (self.content['last_updated']));
        try:
            self.content['latest_move']=self._card.latestCardMove_date.strftime("%Y-%m-%d %H:%M");
        except IndexError:
            self.content['latest_move'] = self._card.create_date;
        self.content['due_date'] = self._card.due_date;

    def get_url(self):
        self.content['short_url'] = self._card.url

    def get_board_list(self, _board, _list):
        self.content['board_name'] = _board.decode(encoding='UTF-8')
        self.content['list_name'] = _list.decode(encoding='UTF-8')


    def fetch_all(self):
        self.get_name();
        self.get_status();
        self.get_members();
        self.get_detailed_status();
        self.get_url();
#        self.group_assignments[-1].get_board_list(tr_board.name, tr_list.name);
