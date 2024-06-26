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

    print(courses_info)

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    print(courses_info)
    
    role = courses_info[0].get('USER_TYPE')
    course_name = courses_info[0].get('COURSE_NAME')
    professor = courses_info[0].get('PROFESSOR')

    return render_template("course.html", ROLE=role, COURSE_ID=course_id, COURSE_NAME=course_name, PROFESSOR=professor)


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

    if role == "STUDENT":
        try:
            assignments_list = ss.get_course_assignments(email, course_id)
            return render_template("assignments.html", assignments=assignments_list, course_id=course_id)
        except Exception as e:
            flash(str(e))
            return redirect("/user/courses")
    
    else:
        try:
            assignments_list = ss.get_course_assignments_teacher(course_id)
            return render_template("assignments_teacher.html", assignments=assignments_list, course_id=course_id)
        except Exception as e:
            flash(str(e))
            return redirect("/user/courses")



@courses_routes.route("/courses/<course_id>/assignments/<assignment_id>")
@authenticated_route
@student_route()
def assignment(course_id, assignment_id):
    print(f"COURSE {course_id}: ASSIGNMENT {assignment_id}")
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')

    role = courses_info[0].get('USER_TYPE')

    if role == "STUDENT":

        email = current_user["email"]

        #TODO: CHANGE THIS ####
        email = "st4505@nyu.edu"
        #######################

        try:
            assignment_details = ss.get_assignment_scores(email, course_id, assignment_id)
            return render_template("assignment.html", assignment_details=assignment_details)

        except Exception as e:
            flash('Error, could not fetch assignment details')
            flash(str(e))
            return redirect(f'/courses/{course_id}')

    else:
        assignment_name, assignment_grades = ss.get_assignment_grades_teacher(course_id, assignment_id)
        return render_template("assignment_grades_teacher.html", assignment_grades=assignment_grades, assignment_name=assignment_name, assignment_id=assignment_id, course_id=course_id)


#TA/TEACHER ROUTES
@courses_routes.route("/courses/<course_id>/roster")
@authenticated_route
@student_route()
def courses_teacher_roster(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    roster_data = ss.get_course_roster(course_id)

    current_user = session.get('current_user')
    user_courses = current_user.get('user_courses')
    
    course_status_list = [c for c in user_courses if int(c.get('COURSE_ID')) == int(course_id)]
    course_status = course_status_list[0].get('USER_TYPE')
    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    return render_template("course_roster.html", roster_data=roster_data, course_id=course_id, personal_course_info=courses_info[0], course_status=course_status)




@courses_routes.route("/courses/<course_id>/students/<student_email>/assignments")
@authenticated_route
@ta_route()
def student_grades(course_id, student_email):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    try:
        assignments_list = ss.get_course_assignments(student_email, course_id)
    except:
        flash('Error, could not fetch student details')
        return redirect("/courses/<course_id>/roster")
    
    return render_template("student_assignments_teacher.html", assignments=assignments_list, course_id=course_id, student_email=student_email)


@courses_routes.route("/courses/<course_id>/students/<student_email>/assignments/<assignment_id>")
@authenticated_route
@ta_route()
def assignment_details(course_id, student_email, assignment_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    #try:
    assignment_details = ss.get_assignment_scores(student_email, course_id, assignment_id)

    """
    except Exception as e:
        flash('Error, could not fetch assignment details')
        flash(str(e))
        return redirect(f'/courses/{course_id}')
    """

    return render_template("assignment_teacher.html", assignment_details=assignment_details, student_email=student_email)


@courses_routes.route("/courses/<course_id>/check_ins")
@authenticated_route
@student_route()
def check_ins(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]
    #TODO: change hard coded email to "email" fetched from session
    email = "at2015@nyu.edu"
    ##################################


    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    user_role = courses_info[0].get('USER_TYPE')
    course_name = courses_info[0].get('COURSE_NAME')
    check_in_sheet_name = courses_info[0].get('CHECK_IN_SHEET_NAME')
    check_in_form_id = courses_info[0].get('CHECK_IN_FORM_ID')

    if user_role == "STUDENT":
        check_in_data, check_in_headers = ss.get_weekly_check_ins(course_id=course_id, email=email, user_role=user_role, check_in_sheet_name=check_in_sheet_name)
        return render_template("check_ins_student.html", course_id=course_id, course_name=course_name, check_in_data=check_in_data, check_in_headers=check_in_headers, check_in_form_id=check_in_form_id)
    
    else: #ta, teacher, or admin
        check_in_data, check_in_headers, week_numbers = ss.get_weekly_check_ins(course_id=course_id, email=email, user_role=user_role, check_in_sheet_name=check_in_sheet_name)
        return render_template("check_ins_teacher.html", course_id=course_id, course_name=course_name, check_in_data=check_in_data, check_in_headers=check_in_headers, week_numbers=week_numbers)
    

@courses_routes.route("/courses/<course_id>/check_ins/chart")
@authenticated_route
@ta_route()
def check_ins_chart(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]


    courses_info = [c for c in current_user.get('user_courses') if int(c['COURSE_ID']) == int(course_id)]

    if len(courses_info) == 0:
        flash(str(courses_info))
        return redirect('/user/courses')
    
    user_role = courses_info[0].get('USER_TYPE')
    course_name = courses_info[0].get('COURSE_NAME')
    check_in_sheet_name = courses_info[0].get('CHECK_IN_SHEET_NAME')
    check_in_form_id = courses_info[0].get('CHECK_IN_FORM_ID')

    formatted_data = ss.get_check_ins_chart(course_id=course_id, check_in_sheet_name=check_in_sheet_name)
    return render_template("check_ins_chart.html", course_name=course_name, formatted_data=formatted_data)