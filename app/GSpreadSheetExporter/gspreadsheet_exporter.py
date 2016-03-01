# -*- coding: utf-8 -*-

import gspread

import logging
import os
import httplib2

import oauth2client
from apiclient import errors
from apiclient import discovery
from oauth2client import client
from oauth2client import tools

class GSpreadSheetExporter(object):
    """
    Class representing writing reporting data to google sheets via gspread.
    """

    def __init__(self, report_config, _secrets_dir):
        self.logger = logging.getLogger("sysengreporting")

        self.gSCOPES = "https://www.googleapis.com/auth/drive " + "https://spreadsheets.google.com/feeds/"
        self.gCLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'client_secret.json')
        self.gAPPLICATION_NAME = 'GSpreadSheet Trello Reporter'

        self.columns = report_config[':output_metadata'][':columns'];
        self.template_id = report_config[':output_metadata'][':template_id'];
        self.report_prefix = report_config[':output_metadata'][':report_name']

        self.secrets_dir = _secrets_dir
        self.credentials = self.g_authenticate();
        self.gc = gspread.authorize(self.credentials)

        http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v2', http=http)


    def write_spreadsheet(self, processed_report):
        report_name = self.report_prefix + processed_report[':output_metadata'][':gen_date']
        if not (self.copy_file(self.service, self.template_id, report_name)):
            self.logger.debug('Unable to copy the template %s successfully!' % (self.report))
        self.logger.debug('Copied the template %s successfully!' % (self.template_id))
        self.report = self.gc.open(report_name)
        self.wks_granular = self.report.worksheet('Trello Data')

        self.write_headers(self.wks_granular)
        self.write_batch_data(processed_report[':collected_content'], self.wks_granular)



    def write_batch_data(self, processed_report, sheet):
        """
        Iterate through all the rows/columns and write the actual data
        """
        total_rows = len(processed_report[':assignments']) + len(processed_report[':epics']) + len(processed_report[':projects'])
        range_name = 'A2:' + chr(ord('A') + len(self.columns) - 1) + str(total_rows + 1) # TODO: only 26 columns so far
        self.logger.debug('The worksheet range is %s' % (range_name));
        cell_range = sheet.range(range_name);
        # rows - number of lines to write

        #self.logger.debug('Columns from the config are: %s' % (self.columns))
        # cols - number of columns to write
        cell_index = 0;
        for workitem in processed_report.keys():
            for line in processed_report[workitem].keys():
                #self.logger.debug('Working on line %s' % (line))
                for c in range(len(self.columns)):
                    try:
                        cell_range[cell_index].value = processed_report[workitem][line][self.columns[c + 1][':key']];
                    except KeyError as err:
                        cell_range[cell_index].value = ''
                        #self.logger.error('no value for the key in %s. Error: %s' % (processed_report[line], err))
                    cell_index += 1;

        # Write to Google SpreadSheets
        try:
            sheet.update_cells(cell_range);
        except IndexError as e:
            self.logger.error('IndexError occurred. %s' % (e))
        return True

    def write_headers(self, sheet):
        """
        Write name/date of the report.. to 2nd worksheet?
        write 1st row here as well.
        """
        range_name = 'A1:' + chr(ord('A') + len(self.columns) - 1) + '1'  # TODO: only 26 columns so far
        #self.logger.debug('The header range is %s' % (range_name));
        cell_range = sheet.range(range_name);

        #self.logger.debug('Columns from the config are: %s' % (self.columns))
        for c in range(len(self.columns)):
            cell_range[c].value = self.columns[c + 1][':name'];
        try:
            sheet.update_cells(cell_range);
        except IndexError as e:
            self.logger.error('IndexError occurred. %s' % (e))
        return True;

    def csv_write(self, _dir_path):
        csv_file = open(os.path.join(_dir_path, self.gran_report.full_name + '.csv'),'w+');
        csv_writer = csv.writer(csv_file);
        csv_writer.writerow(["Owner", "Title", "Status", "Tags", "Funding Bucket", "Detailed Status", "Last Updated"]);
        for line in self.gran_report.line_items:
            csv_writer.writerow([line.member, line.name, line.status, line.tags, line.funding_buckets, line.detailed_status, line.last_updated]);
        csv_file.close();

    def g_authenticate(self):
        credential_dir = self.secrets_dir
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                   'drive-python-credentials.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.gCLIENT_SECRET_FILE, self.gSCOPES)
            flow.user_agent = self.gAPPLICATION_NAME
            flags = tools.argparser.parse_args(args=["--noauth_local_webserver"])
            credentials = tools.run_flow(flow, store, flags)
            print('Storing credentials to ' + credential_path)
        self.logger.debug("Authenticated to Google Drive!")
        return credentials

    def insert_file(self, service, title, description, mime_type, filename):
        """Insert new file.

        Args:
          service: Drive API service instance.
          title: Title of the file to insert, including the extension.
          description: Description of the file to insert.
          parent_id: Parent folder's ID.
          mime_type: MIME type of the file to insert.
          filename: Filename of the file to insert.
        Returns:
          Inserted file metadata if successful, None otherwise.
        """
        media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
        body = {
            'title': title,
            'description': description,
            'mimeType': mime_type,
    #        'parent' : '0Bz-unW9GjAeIMjJBWVR2eWFBQUk', # reports folder
            'convert': True,
        }
        self.logger.debug('Upload metadata: %s' % (body))

        try:
            file = service.files().insert(
                body=body,
                media_body=media_body).execute()

            return file
        except errors.HttpError as error:
            self.logger.error('An error occured: %s' % error)


    def list_files(self):
            http = self.credentials.authorize(httplib2.Http())
            service = discovery.build('drive', 'v2', http=http)

            results = service.files().list(maxResults=10).execute()
            items = results.get('items', [])
            if not items:
                self.logger.debug('No files found.')
            else:
                self.logger.debug('Files:')
                for item in items:
                    self.logger.debug('{0} ({1})'.format(item['title'], item['id']))


    def _create_new(self,
                            target_name=None,
                            folder=None,
                            sheet_description="new"):
        if target_name is None:
            raise KeyError("Must specify a name for the new document")

        body = {'title': target_name }
        if folder:
            body['parents'] = [{'kind' : 'drive#parentReference',
                                'id' : folder['id'],
                                'isRoot' : False }]

        drive_service = self.service

            # Create new blank spreadsheet.
        self.logger.debug("Creating blank spreadsheet.")

        body['mimeType'] = 'application/vnd.google-apps.spreadsheet'
        try:
            new_document = drive_service.files().insert(body=body).execute()
        except Exception as e:
            self.logger.exception("gdata API error. %s", e)
            raise e

        self.logger.info("Created %s spreadsheet with ID '%s'",
                sheet_description,
                new_document.get('id'))

        return new_document


    def copy_file(self, service, origin_file_id, copy_title):
        """Copy an existing file.
        Args:
          service: Drive API service instance.
          origin_file_id: ID of the origin file to copy.
          copy_title: Title of the copy.

        Returns:
          The copied file if successful, None otherwise.
        """
        copied_file = {'title': copy_title}
        try:
            return service.files().copy(
                fileId=origin_file_id, body=copied_file).execute()
        except errors.HttpError as error:
            self.logger.exception('An error occurred: %s' % (error))
        return None


