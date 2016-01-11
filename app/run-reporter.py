#!/usr/bin/env python3

from TrelloCollector import trello_collector
from GSpreadSheetExporter import gspreadsheet_exporter
from Transformer import data_transformer

import logging
import tempfile
import os
import yaml

import httplib2
from apiclient import discovery

def main():
    logger = logging.getLogger("sysengreporting")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    _stdlog = logging.StreamHandler()
    _stdlog.setLevel(logging.DEBUG)
    _stdlog.setFormatter(formatter)

    logger.addHandler(_stdlog)


    with open("config/report.yml", 'r') as stream:
        report_config = yaml.load(stream)

    with open("config/trello_secret.yml", 'r') as stream:
        trello_secret_config = yaml.load(stream)

    warehouse = trello_collector.TrelloCollector(report_config, trello_secret_config)
    logger.info('Welcome to the Warehouse!')

    #warehouse.list_boards();
    
    exporter = gspreadsheet_exporter.GSpreadSheetExporter(report_config);
    unprocessed_report = warehouse.parse_trello();

    transformer = data_transformer.DataTransformer(report_config, unprocessed_report)

    transformer.repopulate_report()

    exporter.write_spreadsheet(transformer.dest_report)
    logger.debug('Report %s' % (transformer.dest_report))

if __name__ == '__main__':

    main()
