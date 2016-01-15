#!/usr/bin/env python3

from TrelloCollector import trello_collector
from GSpreadSheetExporter import gspreadsheet_exporter
from Transformer import data_transformer

import logging
import tempfile
import os
import yaml
import argparse

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

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='report config', default="config/report.yml")
    parser.add_argument('action', nargs='?', help='report to produce the report, list to output boards and lists', default="report")
    args = parser.parse_args();


    if os.path.isfile(args.config):
         with open(args.config, 'r') as stream:
             report_config = yaml.load(stream)
    else:
        logger.error('Invalid configuration file!')
        return;

    with open("config/trello_secret.yml", 'r') as stream:
        trello_secret_config = yaml.load(stream)


    warehouse = trello_collector.TrelloCollector(report_config, trello_secret_config)
    logger.info('Welcome to the Warehouse!')

    if args.action == 'list':
        warehouse.list_boards();
        return
    elif args.action != 'report':
        logger.error('Unrecognized actions %s' % (args.action))
        return;

    unprocessed_report = warehouse.parse_trello();

    # Transform the Data
    transformer = data_transformer.DataTransformer(report_config, unprocessed_report)
    transformer.repopulate_report()

    #Write data to Google SpreadSheets
    exporter = gspreadsheet_exporter.GSpreadSheetExporter(report_config);
    exporter.write_spreadsheet(transformer.dest_report)
    #logger.debug('Report %s' % (transformer.dest_report))

if __name__ == '__main__':

    main()
