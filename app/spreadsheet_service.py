
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

import time


load_dotenv()

DEFAULT_FILEPATH = os.path.join(os.path.dirname(__file__), "..", "gradebook-hero-google-credentials.json")
GOOGLE_CREDENTIALS_FILEPATH = os.getenv("GOOGLE_CREDENTIALS_FILEPATH", default=DEFAULT_FILEPATH)

GOOGLE_SHEETS_MASTER_DOCUMENT_ID = os.getenv("GOOGLE_SHEETS_MASTER_DOCUMENT_ID", default="OOPS Please get the spreadsheet identifier from its URL, and set the 'GOOGLE_SHEETS_DOCUMENT_ID' environment variable accordingly...")


class SpreadsheetService:

    def __init__(self, credentials_filepath=GOOGLE_CREDENTIALS_FILEPATH, document_id=GOOGLE_SHEETS_MASTER_DOCUMENT_ID):
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

    def set_active_document(self, document_id):
        self.document_id = document_id

    def get_sheet(self, sheet_name):
        return self.doc.worksheet(sheet_name)
    
    #####################
    # COURSES FUNCTIONS #
    #####################

    def get_student_courses(self, email:str) -> list:
        self.set_active_document(GOOGLE_SHEETS_MASTER_DOCUMENT_ID)
        students_sheet = self.get_sheet("students_roster")
        all_student_course_ids = students_sheet.get_all_records()
        student_course_ids = [course["COURSE_ID"] for course in all_student_course_ids if course["STUDENT_EMAIL"] == email]
        
        courses_sheet = self.get_sheet("courses")
        all_courses = courses_sheet.get_all_records()

        student_courses_info = [course_info for course_info in all_courses if course_info["COURSE_ID"] in student_course_ids]

        return student_courses_info


    def get_course_assignments(self, student_email:str, course_id:str) -> list:
        #if coming from "courses" page, the active document will be "MASTER"
        #we want to change that to the document ID of the specific course
        start_time = time.time()
        if self.doc.id == GOOGLE_SHEETS_MASTER_DOCUMENT_ID:
            courses_sheet = self.get_sheet("courses")
            courses_records = courses_sheet.get_all_records()
        
            course_document_id_list = [c["SHEETS_DOCUMENT_ID"] for c in courses_records if c["COURSE_ID"] == int(course_id)]

            if len(course_document_id_list) == 0:
                raise Exception("course not found...")
                #TODO: handle within the route
            if len(course_document_id_list) > 1:
                raise Exception("course duplicate found...error")
                #TODO: handle within the route
            
            self.set_active_document(course_document_id_list[0])

        # now, get the assignments from the sheet
        assignments_sheet = self.get_sheet("ASSIGNMENT_MASTER")
        assignments_records = assignments_sheet.get_all_records()

        
        #now, iterate through each assignment sheet, find the grade corresponding with the email/netID
        # ?? will this reach the sheets rate limit? especially for multiple assignments...
        assignment_index = 0
        for assignment in assignments_records:
            sheet = self.get_sheet(assignment["SHEET_NAME"])
            header_row_index = -1
            
            first_column_values = sheet.col_values(1)
            for idx, value in enumerate(first_column_values, start=1):
                if value == "Timestamp":
                    header_row_index = idx
                    break
            
            emails_column_index = -1
            final_grade_column_index = -1

            header_row_values = sheet.row_values(header_row_index)

            for idx, value in enumerate(header_row_values, start=1):
                if "email" in value.lower():
                    emails_column_index = idx
                elif "raw" in value.lower() and "score" in value.lower():
                    final_grade_column_index = idx
                
                if emails_column_index > 0 and final_grade_column_index > 0:
                    break

            #now find the assignment grade
            student_row_index = -1
            for idx, email in enumerate(sheet.col_values(emails_column_index), start=1):
                if email == student_email:
                    student_row_index = idx
                    break
            try:
                student_grade = sheet.cell(student_row_index, final_grade_column_index).value
                assignments_records[assignment_index]["GRADE"] = student_grade
            except Exception as e:
                assignments_records[assignment_index]["GRADE"] = None

            assignment_index += 1



        print(assignments_records)
        print(time.time() - start_time)



if __name__ == "__main__":

    ss = SpreadsheetService()

    ss.get_course_assignments("st4505@nyu.edu", "12345")
