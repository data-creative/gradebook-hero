
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
import numpy as np


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

    @staticmethod
    def to_pct(frac):
        return f'{float(frac)*100:.2f}%'

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
        assignment_sheet = self.get_sheet("ASSIGNMENT_MASTER")
        assignments = assignment_sheet.get_all_records()


        #get student_grade
        gradebook_sheet = self.get_sheet("GRADEBOOK")
        all_grades = gradebook_sheet.get_all_records()
        student_grades = [g for g in all_grades if g.get("Email") == student_email]

        if len(student_grades) == 0:
            raise Exception("Student Grades not found in gradebook!")
        
        student_grades = student_grades[0]

        #merge student grades in with 
        for a in assignments:
            assignment_name = a.get("NAME")
            try:
                a['GRADE'] = self.to_pct(student_grades.get(assignment_name)/a.get("POINTS"))
            except TypeError as e:
                a['GRADE'] = '0.00%'

        return assignments

    def get_assignment_details(self, student_email:str, course_id:str, assignment_id:str) -> dict:
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

        assignments_sheet = self.get_sheet("ASSIGNMENT_MASTER")
        assignments = assignments_sheet.get_all_records()
        assignment_details = [a for a in assignments if a.get('SHEET_NAME') == assignment_id]

        if len(assignment_details) == 0:
            raise Exception("assignment sheet with id not found!")
        
        assignment_details = assignment_details[0]


        assignment_sheet = self.get_sheet(assignment_id)
        assignment_values = assignment_sheet.get_all_values()

        #fetch the student data
        row = 0
        header_row = []
        student_row = []
        for r in assignment_values:
            if "Email Address" in r:
                header_row = r
            elif student_email in r:
                student_row = r
            row += 1

            if header_row != [] and student_row != []:
                break

        
        if header_row == [] or student_row == []:
            raise Exception("Error! Header row or student row not found.")

        on_time_index = -1
        raw_score_index = -1
        for i in range(len(header_row)):
            if header_row[i] == "ON TIME":
                on_time_index = i
            elif header_row[i] == "RAW SCORE":
                raw_score_index = i

            if on_time_index > 0 and raw_score_index > 0:
                break

        assignments_list = []
        i = on_time_index
        while i <= raw_score_index:
            if i == raw_score_index:
                assignment_details['RAW_SCORE'] = self.to_pct(float(student_row[i]))
                break
            assignments_list.append({
                    "metric": header_row[i],
                    "score": student_row[i],
                    "comments": student_row[i+1],
            })
            i += 2

        assignment_details["DETAILS"] = assignments_list

        #now get the avg and stdev
        all_scores = []
        raw_score_found = False
        for row in assignment_values:
            raw_score = row[raw_score_index]

            if raw_score == "RAW SCORE":
                raw_score_found = True
            elif raw_score_found and (isinstance(raw_score, float) or isinstance(raw_score, int)):
                all_scores.append(float(raw_score))
            elif raw_score_found and raw_score == "":
                break

        
        all_scores = np.array(all_scores)
        scores_mean = all_scores.mean()
        scores_25percentile = np.percentile(all_scores, 25)
        scores_75percentile = np.percentile(all_scores, 75)



        return assignment_details, scores_mean, scores_25percentile, scores_75percentile
        


if __name__ == "__main__":

    ss = SpreadsheetService()

    ss.get_assignment_details("st4505@nyu.edu", "12345", "stocks-mjr")
