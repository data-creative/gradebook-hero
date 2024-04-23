from flask import Blueprint, render_template, flash, redirect, current_app, url_for, session, request #, jsonify

courses_routes = Blueprint("courses_routes", __name__)

from web_app.routes.wrappers import authenticated_route, student_route, teacher_route, ta_route

@courses_routes.route("/courses/<course_id>")
@authenticated_route
def course(course_id):
    print(f"COURSE {course_id}")
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]
    #TODO: change hard coded email to "email" fetched from session
    email = "st4505@nyu.edu"
    ##################################
    assignments_list = []


    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    role = courses_info[0].get('USER_TYPE')

    if role == "STUDENT":
        assignments_list = ss.get_course_assignments(email, course_id)
        return render_template("assignments.html", assignments=assignments_list, course_id=course_id)
    elif role == "TEACHER" or role == "TA":
        roster_data = ss.get_course_roster(course_id)
        return render_template("course_roster.html", roster_data=roster_data, course_id=course_id)
    return render_template("assignments.html", assignments=assignments_list, course_id=course_id)


@courses_routes.route("/courses/<course_id>/assignments/<assignment_id>")
@authenticated_route
@student_route()
def assignment(course_id, assignment_id):
    print(f"COURSE {course_id}: ASSIGNMENT {assignment_id}")
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]

    #TODO: CHANGE THIS ####
    email = "st4505@nyu.edu"
    #######################

    try:
        assignment_details = ss.get_assignment_scores(email, course_id, assignment_id)

    except Exception as e:
        flash('Error, could not fetch assignment details')
        flash(str(e))
        return redirect(f'/courses/{course_id}')

    return render_template("assignment.html", assignment_details=assignment_details)

@courses_routes.route("/courses/<course_id>/students/<student_info>")
@authenticated_route
@ta_route()
def student_grades(course_id, student_info):
    student_info_list = student_info.split("__")
    last_name = student_info_list[0]
    first_name = student_info_list[1]
    student_email = student_info_list[2]
    ss = current_app.config["SPREADSHEET_SERVICE"]
    assignments_list = ss.get_course_assignments(student_email, course_id)
    return render_template("assignments_teacher.html", assignments=assignments_list, course_id=course_id, student_email=student_email, first_name=first_name, last_name=last_name)