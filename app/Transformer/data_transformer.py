# -*- coding: utf-8 -*-

import logging
import re

class DataTransformer(object):
    """The DataTransformer class reprsents all transformation done to build the resulting report
       split members
       fill in tags, special tags
       fill in epics
       e2e specific:
         take project from report.yml
         take epic members from linked assignments
    """

    def __init__(self, _report_config, _source_report):
        """
        :param _report_config: report configuration(particularly the tag information
        :param _source_report: unprocessed report
        """
        self.logger = logging.getLogger("sysengreporting")

        self.report_config = _report_config
        self.source_report = _source_report
        self.dest_report = {':collected_content': {} }
        self.dest_report[':output_metadata'] = self.source_report[':output_metadata'].copy()
        self.special_tags = _report_config[':transform'][':tags']

    def __str__(self):
        return "Report '%s' on '%s' owned by '%s'" % (self.name, self.board_lists)

    def repopulate_report(self):
        """main func that repopulates self.dest_report with the processed data"""
        source = self.source_report[':collected_content']

        # before continueing apply epics labels
        for card in source.keys():
            self.apply_labels(source[card]);
            self.apply_tags(source[card]);
            self.add_for_board(source[card]);

        # populate members in epics before the loop, since it'll add line items: epic_id + full_name
        self.fill_epics_info(source);

        # Main cycle to split members in separate line items
        for card in source.keys():

            if not source[card][':members']:
                self.dest_report[':collected_content'][source[card][':id']] = source[card].copy()
                self.dest_report[':collected_content'][source[card][':id']][':members'] = ''
                self.dest_report[':collected_content'][source[card][':id']][':user_id'] = ''
            for (user_id, owner) in source[card][':members']:
                self.dest_report[':collected_content'][source[card][':id'] + owner] = source[card].copy()
                self.dest_report[':collected_content'][source[card][':id'] + owner][':members'] = owner
                self.dest_report[':collected_content'][source[card][':id'] + owner][':user_id'] = user_id

    def apply_tags(self, card):
        card[':tags'] = [];

        for tag_type in self.special_tags.keys():
            card[":" + tag_type] = []

        # obtain all tags
        _all_tags = re.findall('\[.*?\]',card[':name'])
        _all_tags.extend(re.findall('\[.*?\]', card[':desc']))
        #self.logger.debug('all tags: %s' % _all_tags)

        # filter out special tag types, see report.yml for tag types.
        for tag in _all_tags:
            for tag_type in self.special_tags.keys(): #Break from the cycle once 'special tag' match is discovered.
                cur_tag = self.special_tags[tag_type][':tag_prefix']; # tag type being currently reviewed
                if tag[1:len(cur_tag)+1] == cur_tag:
                    break
            if tag[1:len(cur_tag)+1] == cur_tag:
                    card[":" + tag_type].append(tag[len(cur_tag)+1:-1]) #Special tag gets appended to the respective list
            else:
                card[':tags'].append(tag); #Other tags go to general tags list


    def apply_labels(self, card):
        card[':epic'] = ''
        card[':status'] = 'n/a'
        for label in card[':labels']:
            if label[0:5] == 'epic-':
                card[':epic'] = label;
                continue;
            if label == 'Ok':
                card[':status'] = '3-Ok';
                continue;
            if label == 'Issues':
                card[':status'] = '2-Issues';
                continue;
            if label == 'Blocked':
                card[':status'] = '1-Blocked';
                continue;

    def add_for_board(self, card):
        """controlled by :add_for_board key in the report.yml
        will add special project for specific board"""
        if not self.report_config[':transform'][':add_for_board']:
            pass;
        for project in self.report_config[':transform'][':add_for_board'].keys():
            if card[':board_id'] == self.report_config[':transform'][':add_for_board'][project][':board_id']:
                card[':project'].append(self.report_config[':transform'][':add_for_board'][project][':project'])
                card[':team'].append(self.report_config[':transform'][':add_for_board'][project][':team'])
                return;

    def fill_epics_info(self, source):
        """specific to e2e board for now. epic members are taken from the related assignments"""
        assignments = source.copy()
        for epic_id in source.keys():
            if source[epic_id][':card_type'] != 'epic' or source[epic_id][':epic'] == '':
                continue; #not an epic
            epic_members = set([]) 
            for a_id in assignments.keys():
                self.logger.debug('Considering epic %s assignment %s' % (source[epic_id][':epic'], assignments[a_id]))
                if assignments[a_id][':card_type'] != 'assignment' or assignments[a_id][':epic'] != source[epic_id][':epic'] : #not an assignments, or wrong epic
                    continue;
                epic_members = epic_members.union(assignments[a_id][':members'])
                source[a_id][':epic_friendly'] = source[epic_id][':name']  # add friendly epic name
                self.logger.debug('Assignmed friendly epic name to %s' % (source[a_id]))
            source[epic_id][':members'] = list(epic_members)
            #self.logger.debug('Epic %s has members %s' % (source[epic_id][':name'], source[epic_id][':members']))

