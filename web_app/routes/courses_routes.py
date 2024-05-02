from flask import Blueprint, render_template, flash, redirect, current_app, url_for, session, request #, jsonify

courses_routes = Blueprint("courses_routes", __name__)

from web_app.routes.wrappers import authenticated_route, student_route, teacher_route, ta_route

@courses_routes.route("/courses/<course_id>")
@student_route()
def course(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]
    #TODO: change hard coded email to "email" fetched from session
    email = "st4505@nyu.edu"
    ##################################


    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    print(courses_info)
    
    role = courses_info[0].get('USER_TYPE')
    course_name = courses_info[0].get('COURSE_NAME')

    return render_template("course.html", ROLE=role, COURSE_ID=course_id, COURSE_NAME = course_name)


@courses_routes.route("/courses/<course_id>/assignments")
@student_route()
def course_assignments(course_id):
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
    assignments_list = ss.get_course_assignments(email, course_id)
    return render_template("assignments.html", assignments=assignments_list, course_id=course_id)

@courses_routes.route("/courses/<course_id>/students")
@ta_route()
def course_students(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    roster_data = ss.get_course_roster(course_id)
    return render_template("course_students.html", roster_data=roster_data, course_id=course_id)



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


#TA/TEACHER ROUTES
@courses_routes.route("/courses/<course_id>/students")
@authenticated_route
@ta_route()
def courses_teacher_roster(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    roster_data = ss.get_course_roster(course_id)

    current_user = session.get('current_user')
    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    return render_template("course_roster.html", roster_data=roster_data, course_id=course_id, personal_course_info=courses_info[0])


@courses_routes.route("/courses/<course_id>/assignments")
@authenticated_route
@ta_route()
def course_assignments(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    all_assignment_data = ss.get_course_assignments_teacher(course_id)

    current_user = session.get('current_user')
    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]
    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    return render_template("assignments_teacher.html", assignments=all_assignment_data, personal_course_info=courses_info[0])


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


@courses_routes.route("/courses/<course_id>/check_ins")
@authenticated_route
@ta_route()
def student_grades(course_id, student_info):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]
    #TODO: change hard coded email to "email" fetched from session
    email = "st4505@nyu.edu"
    ##################################


    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    user_role = courses_info[0].get('USER_TYPE')
    course_name = courses_info[0].get('COURSE_NAME')
    check_in_sheet_name = courses_info[0].get('CHECK_IN_SHEET_NAME')

    if user_role == "STUDENT":
        check_in_data = ss.get_weekly_check_ins(course_id=course_id, email=email, user_role=user_role, check_in_sheet_name=check_in_sheet_name)