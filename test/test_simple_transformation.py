#!/usr/bin/env python3

from .. import data_transformer
import unittest
from nose2.tools import params


import logging
import tempfile
import os
import yaml
import json

class TransformerTest(unittest.TestCase):


    @params(("mock_configs/01_src_no_epics.yml", "mock_configs/01_res_no_epics.yml", "mock_configs/01_config_no_epics.yml"))
    def setUp(self):
        self.logger = logging.getLogger("transformer_test")
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        _stdlog = logging.StreamHandler()
        _stdlog.setLevel(logging.DEBUG)
        _stdlog.setFormatter(formatter)

        self.logger.addHandler(_stdlog)
        self.current_dir = os.path.dirname(__file__)

    def test_assignment_no_split_members(self):
        src_file = "mock_configs/01_assignments.yml"
        cfg_file = "mock_configs/01_config_no_epics.yml"
        with open(os.path.join(self.current_dir, src_file), 'r') as stream:
            source = yaml.load(stream)
        with open(os.path.join(self.current_dir, cfg_file), 'r') as stream:
            config = yaml.load(stream)
        transformer = data_transformer.DataTransformer(config, source, False)
        transformer.repopulate_report()
        self.assertEqual(transformer.dest_report[':output_metadata'][':gen_date'], "2016-03-08 17:57")
        self.assertIn(':collected_content',transformer.dest_report)
        self.assertIn(':assignments',transformer.dest_report[':collected_content'])
        self.assertIn('565f5d2b795d82c7539f9c59', transformer.dest_report[':collected_content'][':assignments'])

        assignment = transformer.dest_report[':collected_content'][':assignments']['565f5d2b795d82c7539f9c59']

        self.assertEqual(assignment[':board_id'], "565f5bb27fec4f69a51d1657")
        self.assertEqual(assignment[':board_name'], "New Assignment Structure")
        self.assertEqual(assignment[':card_type'], "assignment")
        self.assertFalse(assignment[':completed'])
        self.assertEqual(assignment[':desc'], "**Owner/Responsible**\n\n**Abstract**\nThis Reference Architecture\" [firsttag]")
        self.assertEqual(assignment[':due_date'], "2016-03-08 17:57:35")
        self.assertEqual(assignment[':epic'], [])
        self.assertNotIn(':epic_friendly',assignment)
        self.assertEqual(assignment[':funding_buckets'], [])
        self.assertEqual(assignment[':id'], "565f5d2b795d82c7539f9c59")
        self.assertEqual(assignment[':labels'], ['Ok'])
        self.assertEqual(assignment[':latest_move'], "2016-02-04 21:55:01")
        self.assertEqual(assignment[':list_id'], "565f5bc10c798300a5d4fe7e")
        self.assertEqual(assignment[':list_name'], "Not Completed")
        self.assertEqual(assignment[':members'], [('5627c365edf6b78399c9e31', 'Test User')])
        self.assertEqual(assignment[':name'], "This is a testing board")
        self.assertEqual(assignment[':project'], [])
        self.assertEqual(assignment[':short_url'], "https://trello.com/c/orLySrK1/3-this-is-a-testing-board")
        self.assertEqual(assignment[':sponsor'], [])
        self.assertEqual(assignment[':status'], "3-Ok")
        self.assertEqual(assignment[':tags'], ['[firsttag]'])
        #self.assertEqual(assignment[':user_id'], "5627c365edf6b78399c9e31")


    def test_assignment_split_members(self):
        src_file = "mock_configs/01_assignments.yml"
        cfg_file = "mock_configs/01_config_no_epics.yml"
        with open(os.path.join(self.current_dir, src_file), 'r') as stream:
            source = yaml.load(stream)
        with open(os.path.join(self.current_dir, cfg_file), 'r') as stream:
            config = yaml.load(stream)
        transformer = data_transformer.DataTransformer(config, source, True)
        transformer.repopulate_report()
        self.assertEqual(transformer.dest_report[':output_metadata'][':gen_date'], "2016-03-08 17:57")
        self.assertIn(':collected_content',transformer.dest_report)
        self.assertIn(':assignments',transformer.dest_report[':collected_content'])
        self.assertIn('565f5d2b795d82c7539f9c59Test User', transformer.dest_report[':collected_content'][':assignments'])

        assignment = transformer.dest_report[':collected_content'][':assignments']['565f5d2b795d82c7539f9c59Test User']

        self.assertEqual(assignment[':board_id'], "565f5bb27fec4f69a51d1657")
        self.assertEqual(assignment[':board_name'], "New Assignment Structure")
        self.assertEqual(assignment[':card_type'], "assignment")
        self.assertFalse(assignment[':completed'])
        self.assertEqual(assignment[':desc'], "**Owner/Responsible**\n\n**Abstract**\nThis Reference Architecture\" [firsttag]")
        self.assertEqual(assignment[':due_date'], "2016-03-08 17:57:35")
        self.assertEqual(assignment[':epic'], [])
        self.assertNotIn(':epic_friendly',assignment)
        self.assertEqual(assignment[':funding_buckets'], [])
        self.assertEqual(assignment[':id'], "565f5d2b795d82c7539f9c59")
        self.assertEqual(assignment[':labels'], ['Ok'])
        self.assertEqual(assignment[':latest_move'], "2016-02-04 21:55:01")
        self.assertEqual(assignment[':list_id'], "565f5bc10c798300a5d4fe7e")
        self.assertEqual(assignment[':list_name'], "Not Completed")
        self.assertEqual(assignment[':members'], 'Test User')
        self.assertEqual(assignment[':name'], "This is a testing board")
        self.assertEqual(assignment[':project'], [])
        self.assertEqual(assignment[':short_url'], "https://trello.com/c/orLySrK1/3-this-is-a-testing-board")
        self.assertEqual(assignment[':sponsor'], [])
        self.assertEqual(assignment[':status'], "3-Ok")
        self.assertEqual(assignment[':tags'], ['[firsttag]'])
        self.assertEqual(assignment[':user_id'], "5627c365edf6b78399c9e31")

if __name__ == '__main__':
    unittest.main()


