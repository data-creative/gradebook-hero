from flask import Blueprint, render_template, flash, redirect, current_app, url_for, session, request #, jsonify

courses_routes = Blueprint("courses_routes", __name__)

from web_app.routes.wrappers import student_authenticated_route

@courses_routes.route("/courses/<course_id>")
@student_authenticated_route
def course(course_id):
    ss = current_app.config["SPREADSHEET_SERVICE"]
    current_user = session.get("current_user")
    email = current_user["email"]
    #TODO: change hard coded email to "email" fetched from session
    assignments_list = ss.get_course_assignments("st4505@nyu.edu", course_id)
    return render_template("assignments.html", assignments=assignments_list)
