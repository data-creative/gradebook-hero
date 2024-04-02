from flask import Blueprint, render_template, flash, redirect, current_app, url_for, session, request #, jsonify

courses_routes = Blueprint("courses_routes", __name__)

from web_app.routes.wrappers import authenticated_route, student_route, teacher_route

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

    if current_user.get('user_type') == "student":
        assignments_list = ss.get_course_assignments(email, course_id)
        return render_template("assignments.html", assignments=assignments_list, course_id=course_id)
    elif current_user.get('user_type') == "teacher":
        roster_data = ss.get_course_roster(course_id)
        return render_template("course_roster.html", roster_data=roster_data)
    return render_template("assignments.html", assignments=assignments_list, course_id=course_id)


@courses_routes.route("/courses/<course_id>/assignments/<assignment_id>")
@authenticated_route
@student_route
def assignment(course_id, assignment_id):
    print(f"COURSE {course_id}: ASSIGNMENT {assignment_id}")
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]

    #TODO: CHANGE THIS ####
    email = "st4505@nyu.edu"
    #######################

    assignment_details = ss.get_assignment_scores(email, course_id, assignment_id)

    print(assignment_details)

    return render_template("assignment.html", assignment_details=assignment_details)