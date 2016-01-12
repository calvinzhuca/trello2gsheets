# -*- coding: utf-8 -*-

import logging
import re

class DataTransformer(object):
    """The DataTransformer class reprsents all transformation done to build the resulting report
       split members
       fill in tags, special tags
       fill in epics"""

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
        self.special_tags = _report_config[':tags']

    def __str__(self):
        return "Report '%s' on '%s' owned by '%s'" % (self.name, self.board_lists)

    def repopulate_report(self):
        """main func that repopulates self.dest_report with the processed data"""
        source = self.source_report[':collected_content']
        for card in source.keys():
            self.apply_tags(source[card]);
            self.apply_labels(source[card]);

            if not source[card][':members']:
                self.dest_report[':collected_content'][source[card][':id']] = source[card].copy()
                self.dest_report[':collected_content'][source[card][':id']][':members'] = ''
            for owner in source[card][':members']:
                self.dest_report[':collected_content'][source[card][':id'] + owner] = source[card].copy()
                self.dest_report[':collected_content'][source[card][':id'] + owner][':members'] = owner


    def apply_tags(self, card):
        card[':tags'] = [];

        for tag_type in self.special_tags.keys():
            card[":" + tag_type] = []

        # obtain all tags
        _all_tags = re.findall('\[.*?\]',card[':name'])
        _all_tags.extend(re.findall('\[.*?\]', card[':desc']))
        self.logger.debug('all tags: %s' % _all_tags)

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
