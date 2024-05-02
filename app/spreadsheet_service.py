
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
import pandas as pd


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

    def get_courses(self, email:str) -> list:
        self.set_active_document(GOOGLE_SHEETS_MASTER_DOCUMENT_ID)
        roster_sheet = self.get_sheet("roster")
        all_course_ids = roster_sheet.get_all_records()
        user_courses = [course_info for course_info in all_course_ids if course_info["EMAIL"] == email]
        
        courses_sheet = self.get_sheet("courses")
        all_courses = courses_sheet.get_all_records()

        for i in range(len(user_courses)):
            course = user_courses[i]
            general_course_info = [c for c in all_courses if c.get('COURSE_ID') == course.get('COURSE_ID')]
            if len(general_course_info) == 0:
                continue #in case generic info row not created
            general_course_info = general_course_info[0]

            if general_course_info.get('SHEETS_DOCUMENT_ID'):
                del general_course_info['SHEETS_DOCUMENT_ID']
            
            user_courses[i] = {**course, **general_course_info}
        
        print(user_courses)

        return user_courses


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
    
    def get_course_assignments_teacher(self, course_id:str) -> list:
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
        assignments_names_points = [{'NAME': a['NAME'], 'POINTS':a['POINTS'], 'DUE_DATE':a['DUE_DATE']} for a in assignments]

        #get student_grade
        gradebook_sheet = self.get_sheet("GRADEBOOK")
        all_grades_df = pd.DataFrame(gradebook_sheet.get_all_records()).dropna()
        
        for i in range(len(assignments_names_points)):
            name_points = assignments_names_points[i]
            assignment_name = name_points['NAME']
            average_score = round(all_grades_df[assignment_name].mean(),2)
            assignments_names_points[i]['AVERAGE_SCORE'] = average_score
            assignments_names_points[i]['AVERAGE_PCT'] = f"{(average_score/name_points['POINTS'])*100:.2f}%"
            

        print(assignments_names_points)
        return assignments_names_points
        

    def get_course_roster(self, course_id:str):
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

        gradebook_sheet = self.get_sheet("GRADEBOOK")
        all_grades = gradebook_sheet.get_all_records()
        
        return all_grades


    @staticmethod
    def excel_column_to_number(column):
        """
        HELPER METHOD FOR get_assignment_scores
        Converts an Excel column letter (e.g., 'A', 'Z', 'AA') into its corresponding
        column number (e.g., 1, 26, 27).
        """
        number = 0
        for char in column.upper():  # Ensure uppercase for consistency
            number = number * 26 + (ord(char) - ord('A') + 1)
        return number - 1

    def get_assignment_scores(self, student_email:str, course_id:str, assignment_id:str) -> dict:
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


        #fetch details about the assignment
        assignments_sheet = self.get_sheet("ASSIGNMENT_MASTER")
        assignments = assignments_sheet.get_all_records()
        assignment_details = [a for a in assignments if a.get('SHEET_NAME') == assignment_id]

        if len(assignment_details) == 0:
            raise Exception("assignment sheet with id not found!")
        assignment_details = assignment_details[0]

        header_row = assignment_details.get("HEADER_ROW")
        assignment_sheet = self.get_sheet(assignment_id)

        #get student's grades on the assignment
        assignment_records = assignment_sheet.get_all_records(head=header_row)
        student_assignment_row = [a for a in assignment_records if a.get('Email Address') == student_email]

        if len(student_assignment_row) == 0:
            raise Exception("Assignment details for student not found!")
        
        student_assignment_row = student_assignment_row[0]

        #transform the student data into friendly format
        scores_to_return = []
        if assignment_details.get('SCORE_COLUMNS') != '':
            assignment_score_cols = assignment_details.get('SCORE_COLUMNS').split(',')
            assignment_score_col_indices = [SpreadsheetService.excel_column_to_number(c) for c in assignment_score_cols]
            assignment_score_col_headers = [list(student_assignment_row.keys())[i] for i in assignment_score_col_indices]

            assignment_comment_cols = assignment_details.get('COMMENT_COLUMNS').split(',')
            assignment_comment_col_indices = [SpreadsheetService.excel_column_to_number(c) for c in assignment_comment_cols]
            assignment_comment_col_headers = [list(student_assignment_row.keys())[i] for i in assignment_comment_col_indices]

            scores_to_return = []
            for score_header, comment_header in zip(assignment_score_col_headers, assignment_comment_col_headers):
                metric = score_header
                score = student_assignment_row[score_header]
                comments = student_assignment_row[comment_header]

                scores_to_return.append({'metric': metric, 'score': score, 'comments': comments})

        #get student final score
        final_grade_col_index = assignment_details.get('FINAL_GRADE_COLUMN_INDEX') #we have this as a number in the sheet...
        final_grade_col_header = list(student_assignment_row.keys())[final_grade_col_index]

        student_final_grade = student_assignment_row.get(final_grade_col_header)


        #get average, stdev, etc from data
        all_student_scores = [r.get(final_grade_col_header) for r in assignment_records]
        all_student_scores = [s if isinstance(s, int) or isinstance(s, float) else 0 for s in all_student_scores]
        all_student_scores = np.array(all_student_scores)

        class_mean = round(all_student_scores.mean(),2)
        class_upper_quartile = np.percentile(all_student_scores, 75)
        class_lower_quartile = np.percentile(all_student_scores, 25)

        #transform all assignment data into website-readable format
        details_to_return = {
            "NAME": assignment_details.get('NAME'),
            "ASSIGNMENT_POINTS": assignment_details.get('POINTS'),
            "FINAL_SCORE": student_final_grade,
            "DUE_DATE": assignment_details.get('DUE_DATE'),
            "CLASS_MEAN": class_mean,
            "CLASS_UPPER_QUARTILE": class_upper_quartile,
            "CLASS_LOWER_QUARTILE": class_lower_quartile,
            "STUDENT_DETAILS": scores_to_return
        }

        return details_to_return
    

    ####################
    # WEEKLY CHECK INS #
    ####################
    def get_weekly_check_ins(self, course_id:str, email:str, user_role:str, check_in_sheet_name:str):
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

        check_in_sheet = self.get_sheet(check_in_sheet_name)
        check_in_records = check_in_sheet.get_all_records()
        
        if user_role == "STUDENT":
            student_check_in_records = [r for r in check_in_records if r.get('Email Address') == email]
            
            if len(student_check_in_records) > 0:
                student_records_df = pd.DataFrame(student_check_in_records)
                student_records_df.drop(['Timestamp', 'Email Address'])
                df_keys = list(student_records_df.columns.values)

                return student_records_df.to_dict(), df_keys
                
            else:
                #NO CHECK IN RECORDS FOUND
                return None
        elif user_role == "TEACHER" or user_role == "TA":
            all_records_df = pd.DataFrame(check_in_records)
            mean_values = all_records_df.select_dtypes(include=['number']).groupby(all_records_df['Week Number']).mean()
            return mean_values


            
    


    #####################
    #   AUTH FUNCTIONS  #
    #####################

    def get_user_courses(self, email:str) -> list:
        """
        this security is SO BAD and needs to be improved
        but it'll work for now...
        """
        self.set_active_document(GOOGLE_SHEETS_MASTER_DOCUMENT_ID)
        roster_sheet = self.get_sheet("roster")
        all_records = roster_sheet.get_all_records()
        courses_list = [row for row in all_records if row["EMAIL"] == email]

        courses_sheet = self.get_sheet("courses")
        courses_records = courses_sheet.get_all_records()

        for c in courses_list:
            course_info = [cr for cr in courses_records if int(cr['COURSE_ID']) == int(c['COURSE_ID'])]

            if len(course_info) == 0:
                continue

            course_info = course_info[0]

            c['DEPARTMENT'] = course_info['DEPARTMENT']
            c['NUMBER'] = course_info['NUMBER']
            c['COURSE_NAME'] = course_info['COURSE_NAME']

        return courses_list





if __name__ == "__main__":

    ss = SpreadsheetService()

    ss.get_weekly_check_ins("12345", "at2015@nyu.edu", "TA", "check-ins-aggregate")

    #ss.get_student_courses("st4505@nyu.edu")

    #ss.get_assignment_scores("st4505@nyu.edu", "12345", "onboarding")
