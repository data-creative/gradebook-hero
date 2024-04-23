
import functools
from flask import session, redirect, flash, request

STATUS_DICT = {
    "USER": 1,
    "STUDENT": 2,
    "TA": 3,
    "TEACHER": 4,
    "ADMIN": 5
}

def authenticated_route(view):
    """
    Wrap a route with this decorator to prevent unauthenticated access.

    If the user is logged in, the route will have access to the "current_user" info stored in the session.

    If user is not logged in, the route will redirect them to the login page.

    See: https://flask.palletsprojects.com/en/2.0.x/tutorial/views/#require-authentication-in-other-views
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("current_user"):
            #print("CURRENT USER:", session["current_user"])
            return view(**kwargs)
        else:
            print("UNAUTHENTICATED...")
            flash("Unauthenticated. Please login!", "warning")
            return redirect("/login")
    return wrapped_view

def student_route():
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            course_id = kwargs.get('course_id', request.view_args.get('course_id'))
            current_user = session.get("current_user")
            if not current_user:
                return redirect ("/login")
            
            user_courses = current_user.get('user_courses')

            if not user_courses:
                print("USER COURSES:")
                print(user_courses)
                print("ERROR...")
                flash("ERROR! We could not find this assignment.", "warning")
                return redirect("/user/courses")
            
            course_status_list = [c for c in user_courses if int(c.get('COURSE_ID')) == int(course_id)]
            
            if len(course_status_list) == 0:
                return redirect("/user/courses") #user not in course
            
            course_status = course_status_list[0].get('USER_TYPE')

            if STATUS_DICT.get(course_status) >= STATUS_DICT.get("STUDENT"):
                return view(**kwargs)
            else:
                print("UNAUTHENTICATED...")
                flash("Unauthenticated! You are not allowed to access this page.", "warning")
                return redirect("/user/courses")
        return wrapped_view
    return decorator

def ta_route():
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            course_id = kwargs.get('course_id', request.view_args.get('course_id'))
            current_user = session.get("current_user")
            if not current_user:
                return redirect ("/login")
            
            user_courses = current_user.get('user_courses')

            if not user_courses:
                print("USER COURSES:")
                print(user_courses)
                print("ERROR...")
                flash("ERROR! We could not find this assignment.", "warning")
                return redirect("/user/courses")
            
            course_status_list = [c for c in user_courses if int(c.get('COURSE_ID')) == int(course_id)]
            
            if len(course_status_list) == 0:
                return redirect("/user/courses") #user not in course
            
            course_status = course_status_list[0].get('USER_TYPE')

            if STATUS_DICT.get(course_status) >= STATUS_DICT.get("TA"):
                return view(**kwargs)
            else:
                print("UNAUTHENTICATED...")
                flash("Unauthenticated! You are not allowed to access this page.", "warning")
                return redirect("/user/courses")
        return wrapped_view
    return decorator

def teacher_route():
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            course_id = kwargs.get('course_id', request.view_args.get('course_id'))
            current_user = session.get("current_user")
            if not current_user:
                return redirect ("/login")
            
            user_courses = current_user.get('user_courses')

            if not user_courses:
                print("USER COURSES:")
                print(user_courses)
                print("ERROR...")
                flash("ERROR! We could not find this assignment.", "warning")
                return redirect("/user/courses")
            
            course_status_list = [c for c in user_courses if int(c.get('COURSE_ID')) == int(course_id)]
            
            if len(course_status_list) == 0:
                return redirect("/user/courses") #user not in course
            
            course_status = course_status_list[0].get('USER_TYPE')

            if STATUS_DICT.get(course_status) >= STATUS_DICT.get("TEACHER"):
                return view(**kwargs)
            else:
                print("UNAUTHENTICATED...")
                flash("Unauthenticated! You are not allowed to access this page.", "warning")
                return redirect("/user/courses")
        return wrapped_view
    return decorator
