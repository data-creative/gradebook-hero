
from flask import Blueprint, render_template, flash, redirect, current_app, url_for, session, request #, jsonify

from web_app.routes.wrappers import student_authenticated_route

user_routes = Blueprint("user_routes", __name__)

#
# USER ROUTES
#

@user_routes.route("/user/courses")
@student_authenticated_route
def courses():
    print("USER COURSES...")
    current_user = session.get("current_user")
    ss = current_app.config["SPREADSHEET_SERVICE"]
    
    courses = ss.get_student_courses(current_user["email"])

    return render_template("courses.html", courses=courses)

#
# USER PROFILE
#

@user_routes.route("/user/profile")
@student_authenticated_route
def profile():
    print("USER PROFILE...")
    current_user = session.get("current_user")
    #user = fetch_user(email=current_user["email"])
    return render_template("user_profile.html", user=current_user) # user=user
