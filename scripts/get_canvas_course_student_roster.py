from pathlib import Path

import pandas as pd
from canvasapi import Canvas
from canvasapi.user import User as CanvasUser, User
from canvasapi.course import Course as CanvasCourse

import os
from dotenv import load_dotenv


# Load environment variables from a .env file
load_dotenv()

# Canvas API URL and Key
CANVAS_API_URL = "https://canvas.instructure.com/"
CANVAS_API_KEY = os.getenv('CANVAS_API_KEY')
CANVAS_COURSE_CODE = os.getenv('CANVAS_COURSE_CODE')
if CANVAS_API_KEY is None:
    raise ValueError("Please set the CANVAS_API_KEY environment variable.")
if CANVAS_COURSE_CODE is None:
    raise ValueError("Please set the CANVAS_COURSE_CODE environment variable.")
    
# Initialize a new Canvas object
canvas = Canvas(CANVAS_API_URL, CANVAS_API_KEY)

def get_course_by_code(course_code: str):
    user:User = canvas.get_current_user()
    courses: CanvasCourse = user.get_courses()

    for course in courses:
        if course.course_code == course_code:
            return course

    raise ValueError(f"Course with code {course_code} not found.")


def save_student_identifiers(course_code: str, output_directory: str = "."):
    global df
    course = get_course_by_code(course_code=course_code)
    users: list[CanvasUser] = list(course.get_users())
    for user in users:
        print(user)
    # save to CSV
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'name': user.name,
            'login_id': user.login_id,
            'email': user.email,
            'sis_user_id': user.sis_user_id,
        })
    df = pd.DataFrame(users)
    save_path = Path(output_directory) / f"{course_code}_student_identifiers.csv"
    df.to_csv(save_path, index=False)
    print(f"Saved {len(users)} users to {course_code}_student_identifiers.csv")


if __name__ == "__main__":

    save_student_identifiers(course_code=CANVAS_COURSE_CODE, output_directory=".")

