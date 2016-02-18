# -*- coding: utf-8 -*-

import logging
import re
import arrow

class DataTransformer(object):
    """The DataTransformer class reprsents all transformation done to build the resulting report
       split members
       fill in tags, special tags
       fill in epics
       e2e specific:
         take project from report.yml
         take epic members from linked assignments
    """

    def __init__(self, _report_config, _source_report, _split_members):
        """
        :param _report_config: report configuration(particularly the tag information
        :param _source_report: unprocessed report
        """
        self.logger = logging.getLogger("sysengreporting")

        self.report_config = _report_config
        self.source_report = _source_report
        self.dest_report = {':collected_content': {
                               ':assignments': {},
                               ':epics': {},
                               ':projects': {}
                           } }
        self.dest_report[':output_metadata'] =  {}
        self.dest_report[':output_metadata'][':gen_date'] = self.source_report[':output_metadata'][':gen_date']
        self.special_tags = _report_config[':transform'][':tags']
        self.split_members = _split_members

    def __str__(self):
        return "Report '%s' on '%s' owned by '%s'" % (self.name, self.board_lists)

    def repopulate_report(self):
        """main func that repopulates self.dest_report with the processed data"""

        self.add_list_data()
        source = self.source_report[':collected_content']

        # Order is IMPORTANT
        # 1.  Apply external info from the config to cards. f.e. Add Sprint information per :sprint_list config parameter in the configuration file.
        if ':sprint_list' in self.report_config[':transform']:
            sprints = []
            for board in self.report_config[':transform'][':sprint_list'].keys():
                # Find the Sprint card
                sprints.append(self._find_sprint_card(self.report_config[':transform'][':sprint_list'][board]))

        # 2. Per card actions. before continueing apply epics, labels, tags as they exist per individual card
        for card in source.keys():
            self.apply_actions(source[card]);
            self.apply_labels(source[card]);
            self.apply_tags(source[card]);
            self.add_for_board(source[card]);
            self._populate_children(source[card]);
            if ':sprint_list' in self.report_config[':transform']:
                self._add_sprint_data(source[card],sprints);
            #self.logger.debug('All card info: %s' % (source[card]))

        # 3. Per card actions. populate members in epics before the loop, since it'll add line items: epic_id + full_name
        self.fill_epics_info(source);

        # 4. Per member-card actions. Main cycle to split members in separate line items
        dest_assignments = self.dest_report[':collected_content'][':assignments']
        dest_epics = self.dest_report[':collected_content'][':epics']
        dest_projects = self.dest_report[':collected_content'][':projects']
        for card in source.keys():
            if source[card][':card_type'] == 'assignment':
                self._process_card(card, dest_assignments);
            elif source[card][':card_type'] == 'epic':
                self._process_card(card, dest_epics);
            elif source[card][':card_type'] == 'project':
                self._process_card(card, dest_projects);
            else:
                self.logger.error('Lost card %s' % (card))

    def _process_card(self, card, dest_section):
        source = self.source_report[':collected_content']
        if not self.split_members:
            dest_section[source[card][':id']] = source[card].copy()
            return;
        if not source[card][':members']:
            dest_section[source[card][':id']] = source[card].copy()
            dest_section[source[card][':id']][':members'] = ''
            dest_section[source[card][':id']][':user_id'] = ''
        for (user_id, owner) in source[card][':members']:
            dest_section[source[card][':id'] + owner] = source[card].copy()
            dest_section[source[card][':id'] + owner][':members'] = owner
            dest_section[source[card][':id'] + owner][':user_id'] = user_id

    def apply_tags(self, card):
        card[':tags'] = [];

        for tag_type in self.special_tags.keys():
            card[":" + tag_type] = []

        # obtain all tags
        _all_tags = re.findall('\[.*?\]',card[':name'])
        _all_tags.extend(re.findall('\[.*?\]', card[':desc']))
        #self.logger.debug('all tags: %s' % _all_tags)
        _all_tags = list(set(_all_tags)) # get rid of duplicate tags

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
        card[':status'] = 'n/a'
        for label in card[':labels']:
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
        if not ':add_for_board' in  self.report_config[':transform']:
            return;
        for project in self.report_config[':transform'][':add_for_board'].keys():
            if card[':board_id'] == self.report_config[':transform'][':add_for_board'][project][':board_id']:
                card[':project'].append(self.report_config[':transform'][':add_for_board'][project][':project'])
                return;

    def _add_sprint_data(self, card, sprints):
        """for e2e board only. Find card named 'Sprint XXX' in 'In Progress' list, then use this card's due date on all the cards in this list"""
        for sprint in sprints:
            if card[':list_id'] == sprint[':list_id']:
                card[':due_date'] = sprint[':due_date']
                card[':sprint'] = sprint[':name']

    def _find_sprint_card(self, config):
        """Locate the sprint card according to the config and return its properties"""
        source = self.source_report[':collected_content']
        sprint = {}

        for card_id in source.keys():
            if source[card_id][':list_id'] == config[':list_id'] and source[card_id][':name'][0:7] == "Sprint ":
                sprint[':name'] = source[card_id][':name'];
                sprint[':due_date'] = source[card_id][':due_date']
                sprint[':list_id'] = source[card_id][':list_id']
                #self.logger.debug('Found sprint %s' % (sprint))
                return sprint;

    def fill_epics_info(self, source):
        """specific to e2e board for now. epic members are taken from the related assignments"""
        assignments = source.copy()
        for epic_id in source.keys():
            if source[epic_id][':card_type'] != 'epic' or source[epic_id][':epic'] == []:
                continue; #not an epic
            epic_members = set([]) 
            for a_id in assignments.keys():
                #self.logger.debug('Considering epic %s assignment %s' % (source[epic_id][':epic'], assignments[a_id]))
                if assignments[a_id][':card_type'] != 'assignment' or assignments[a_id][':epic'] != source[epic_id][':epic'] : #not an assignments, or wrong epic
                    continue;
                epic_members = epic_members.union(assignments[a_id][':members'])
                source[a_id][':epic_friendly'] = source[epic_id][':name']  # add friendly epic name
                #self.logger.debug('Assignmed friendly epic name to %s' % (source[a_id]))
            source[epic_id][':members'] = list(epic_members)
            #self.logger.debug('Epic %s has members %s' % (source[epic_id][':name'], source[epic_id][':members']))

    def _populate_children(self, card):
        """populate :children for each epic and project with the array of IDs of children cards"""
        source = self.source_report[':collected_content']
        if card[':card_type'] == 'project':
           card[':children'] = []
           for a_id in source:
               if ':project' in source[a_id] and ':project' in card:
                   if source[a_id][':project'] == card[':project']:
                       card[':children'].append(a_id)

    def add_list_data(self):
        """
        Add list_name, card_type, completed fields to the card.
        put it in the correct card_type bucket.
        """

        self.source_report[':collected_content'] = {}

        tr_lists = self.source_report[':output_metadata'][':trello_sources'][':lists']
        #self.logger.debug('The lists are %s' % (tr_lists))
        for card in self.source_report[':output_metadata'][':trello_sources'][':cards']:
            #self.logger.debug('adding list data to the card %s' % (card))
            list_id = card[':list_id']
            if not list_id in tr_lists: #list is not included in the reports
                continue;
            card[':card_type'] = tr_lists[list_id][':card_type'][1:-1]
            card[':list_name'] = tr_lists[list_id][':name']
            card[':completed'] = tr_lists[list_id][':completed']
            self.source_report[':collected_content'][card[':id']] = card

    def apply_actions(self, card):
        """
        :card: card to which to apply the actions
        The actions are added to this card: latest_move, latest comment(detailed_status), completed_date
        """
        unsorted_comments = []
        for comment in self.source_report[':output_metadata'][':trello_sources'][':boards'][card[':board_id']][':actions']:
            if comment['data']['card']['id'] == card[':id'] and comment['type'] == 'commentCard':
                unsorted_comments.append((comment['data']['text'], arrow.get(comment['date']).format('YYYY-MM-DD HH:mm:ss')))
        #self.logger.debug('For card %s, the comments are %s' % (card,unsorted_comments))
        if len(unsorted_comments) > 0:
            comments = sorted(unsorted_comments, key=lambda x: x[-1], reverse=True)
            #self.logger.debug("The last comment is '{0}'".format(comments[0]))
            card[':detailed_status'] = comments[0][0]
            card[':comment_date'] = comments[0][1]


        unsorted_actions = []
        for action in self.source_report[':output_metadata'][':trello_sources'][':boards'][card[':board_id']][':actions']:
            if action['data']['card']['id'] == card[':id'] and action['type'] in ['createCard', 'updateCard', 'copyCard', 'moveCardToBoard', 'convertToCardFromCheckItem']:
                unsorted_actions.append(arrow.get(action['date']).format('YYYY-MM-DD HH:mm:ss'))
        #self.logger.debug('For card %s, the actions are %s' % (card,unsorted_actions))
        if len(unsorted_actions) > 0:
            actions = sorted(unsorted_actions, reverse=True)
            #self.logger.debug("The last action is '{0}'".format(actions[0]))
            card[':latest_move'] = actions[0]
