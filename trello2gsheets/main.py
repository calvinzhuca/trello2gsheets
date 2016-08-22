#!/usr/bin/env python3

from trello2gsheets.trello_collector import TrelloCollector
from trello2gsheets.gspreadsheet_exporter import GSpreadSheetExporter
from trello2gsheets.data_transformer import DataTransformer
from trello2gsheets.trello_updater import TrelloUpdater

import logging
import tempfile
import os
import yaml
import argparse

import httplib2
from apiclient import discovery

def main():
    logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=logging_format,
                        level=logging.INFO)

    logger = logging.getLogger(__name__)


    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='report config', default="config/report.yml")
    parser.add_argument('--deep-scan', help='query each individual card', dest='deep_scan', action='store_true')
    parser.add_argument('--no-deep-scan', help='query each individual card', dest='deep_scan', action='store_false')
    parser.set_defaults(deep_scan=True);
    parser.add_argument('action', nargs='?', help='report to produce the report, list to output boards and lists', default="report")
    args = parser.parse_args();


    if os.path.isfile(args.config):
         with open(args.config, 'r') as stream:
             report_config = yaml.load(stream)
    else:
        logger.error('Invalid configuration file!')
        return;

    with open("secrets/trello_secret.yml", 'r') as stream:
        trello_secret_config = yaml.load(stream)

    warehouse = TrelloCollector(report_config, trello_secret_config)
    logger.info('Started querying of Trello {}'.format(warehouse))
    print('in init')

    if args.action == 'list':
        warehouse.list_boards(); #output list of Trello boards and lists 
        return
    elif args.action == 'update_projects':
        unprocessed_report = warehouse.parse_trello(False);

        # Transform the Data
        transformer = DataTransformer(report_config, unprocessed_report, False)
        transformer.repopulate_report()
        updater = trello_updater.TrelloUpdater(transformer.dest_report, trello_secret_config)
        updater.update_projects()
        #warehouse.update_epics();
        return;
    elif args.action != 'report':
        logger.error('Unrecognized actions %s' % (args.action))
        return;


    unprocessed_report = warehouse.parse_trello(args.deep_scan);
    #with open('unprocessed_report.yml', 'w') as stream:
    #    stream.write( yaml.dump(unprocessed_report, default_flow_style=False) )

    # Transform the Data
    transformer = DataTransformer(report_config, unprocessed_report, True)

    transformer.repopulate_report()

    #Write data to Google SpreadSheets
    exporter = GSpreadSheetExporter(report_config, "secrets/");
    exporter.write_spreadsheet(transformer.dest_report)
    #logger.debug('Report %s' % (transformer.dest_report))

if __name__ == '__main__':

    main()
