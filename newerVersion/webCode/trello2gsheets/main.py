#!/usr/bin/env python3

from trello2gsheets.trello_collector import TrelloCollector
from trello2gsheets.data_transformer import DataTransformer
from trello2gsheets.trello_updater import TrelloUpdater
from trello2gsheets.gspreadsheet_exporter import GSpreadSheetExporter
from flask import Flask, jsonify, abort, make_response
from flask import request

import logging
import tempfile
import os
import yaml
import argparse

import httplib2
from apiclient import discovery



app = Flask(__name__)

logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=logging_format, level=logging.INFO)

logger = logging.getLogger(__name__)




tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})


@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})


@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': tasks[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    tasks.append(task)
    return jsonify({'task': task}), 201


@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': task[0]})

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    tasks.remove(task[0])
    return jsonify({'result': True})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)




#-----------------------------------------------------------------------------------------


def report(trello_secret_config, reportType):

    parser = argparse.ArgumentParser()
#    parser.add_argument('--config', help='report config', default="config/report.yml")
    parser.add_argument('--config', help='report config', default=reportType)
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

#    with open("secrets/trello_secret.yml", 'r') as stream:
#        trello_secret_config = yaml.load(stream)
#    print "!!!!!!!!!!!!!trello_secret_config from json3  %s  " %trello_secret_config

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
#    exporter = GSpreadSheetExporter(report_config, "secrets/");
#    exporter.write_spreadsheet(transformer.dest_report)
    return transformer.dest_report

def main():
    app.run(debug=True)

@app.route('/assignments', methods=['POST'])
def generate_assignments():
    logger.info("generating assignment report ")
    if not request.json or not ':consumer_key' in request.json:
        abort(400)

    reportResult = report(request.json,"config/report.yml")
    logger.debug('Report return back is %s' % (reportResult))
    return jsonify(reportResult), 201

@app.route('/issues', methods=['POST'])
def generate_issues():
    logger.info("generating issues report ")

    if not request.json or not ':consumer_key' in request.json:
        abort(400)

    reportResult = report(request.json,"config/issues.yml")
    logger.debug('Report return back is %s' % (reportResult))
    return jsonify(reportResult), 201


if __name__ == '__main__':

    main()
