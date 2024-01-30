
# adapted from:
# ... https://developers.google.com/sheets/api/guides/authorizing
# ... https://gspread.readthedocs.io/en/latest/oauth2.html
# ... https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
# ... https://github.com/s2t2/birthday-wishes-py/blob/master/app/sheets.py
# ... https://raw.githubusercontent.com/prof-rossetti/flask-sheets-template-2020/master/web_app/spreadsheet_service.py

import os
from datetime import datetime, timezone
from pprint import pprint

from dotenv import load_dotenv
import gspread
from gspread.exceptions import SpreadsheetNotFound


load_dotenv()

DEFAULT_FILEPATH = os.path.join(os.path.dirname(__file__), "..", "gradebook-hero-google-credentials.json")
GOOGLE_CREDENTIALS_FILEPATH = os.getenv("GOOGLE_CREDENTIALS_FILEPATH", default=DEFAULT_FILEPATH)

GOOGLE_SHEETS_DOCUMENT_ID = os.getenv("GOOGLE_SHEETS_DOCUMENT_ID", default="OOPS Please get the spreadsheet identifier from its URL, and set the 'GOOGLE_SHEETS_DOCUMENT_ID' environment variable accordingly...")


class SpreadsheetService:

    def __init__(self, credentials_filepath=GOOGLE_CREDENTIALS_FILEPATH, document_id=GOOGLE_SHEETS_DOCUMENT_ID):
        print("INITIALIZING NEW SPREADSHEET SERVICE...")
        self.client = gspread.service_account(filename=credentials_filepath)
        self.document_id = document_id


    @staticmethod
    def generate_timestamp():
        return datetime.now(tz=timezone.utc)

    @staticmethod
    def parse_timestamp(ts:str):
        """
            ts (str) : a timestamp string like '2023-03-08 19:59:16.471152+00:00'
        """
        date_format = "%Y-%m-%d %H:%M:%S.%f%z"
        return datetime.strptime(ts, date_format)

    @property
    def doc(self):
        """note: this will make an API call each time, to get the new data"""
        return self.client.open_by_key(self.document_id) #> <class 'gspread.models.Spreadsheet'>

    def get_sheet(self, sheet_name):
        return self.doc.worksheet(sheet_name)

    def get_records(self, sheet_name):
        """Gets all records from a sheet,
            converts datetime columns back to Python datetime objects
        """
        #print(f"GETTING RECORDS FROM SHEET: '{sheet_name}'")
        sheet = self.get_sheet(sheet_name) #> <class 'gspread.models.Worksheet'>
        records = sheet.get_all_records() #> <class 'list'>
        for record in records:
            if record.get("created_at"):
                record["created_at"] = self.parse_timestamp(record["created_at"])
        return sheet, records

    def destroy_all(self, sheet_name):
        """Removes all records from a given sheet, except the header row."""
        sheet, records = self.get_records(sheet_name)
        # start on the second row, and delete one more than the number of records,
        # ... to account for the header row
        sheet.delete_rows(start_index=2, end_index=len(records)+1)



if __name__ == "__main__":

    ss = SpreadsheetService()

    docs = ss.client.list_spreadsheet_files()
    for doc in docs:
        print(type(doc))
        pprint(doc)
