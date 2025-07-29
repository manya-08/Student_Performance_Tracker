import os
#print(os.urandom(24).hex())

from dotenv import load_dotenv

load_dotenv()  #This line loads the environment variables from .env

from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, add_student, get_all_students, get_student_by_id, add_grade, get_student_grades, get_student_by_roll_number, update_grade_record, delete_student_record, delete_grade_record
from collections import defaultdict

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_dev') # Used for flash messages

# Initialize the database when the app starts
with app.app_context():
    init_db()

@app.route('/')
def index():
    students = get_all_students()
    return render_template('index.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_new_student():
    if request.method == 'POST':
        name = request.form['name'].strip()
        roll_number = request.form['roll_number'].strip()

        if not name or not roll_number:
            flash('Name and Roll Number are required!', 'danger')
            return redirect(url_for('add_new_student'))

        # Check if roll number already exists
        if get_student_by_roll_number(roll_number):
            flash(f'Student with Roll Number "{roll_number}" already exists.', 'danger')
            return redirect(url_for('add_new_student'))

        student_id = add_student(name, roll_number)
        if student_id:
            flash(f'Student "{name}" (Roll: {roll_number}) added successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Error adding student.', 'danger')
    return render_template('add_student.html')

@app.route('/student/<int:student_id>')
def student_details(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('index'))

    grades = get_student_grades(student_id)

    # Calculate average grade
    average_grade = 0
    if grades:
        total_grades = sum(grade['score'] for grade in grades)
        average_grade = total_grades / len(grades)

    return render_template('student_details.html', student=student, grades=grades, average_grade=average_grade)

@app.route('/add_grade/<int:student_id>', methods=['POST'])
def add_new_grade(student_id):
    subject = request.form['subject'].strip()
    score = request.form['score'].strip()

    if not subject or not score:
        flash('Subject and Score are required!', 'danger')
        return redirect(url_for('student_details', student_id=student_id))

    try:
        score = int(score)
        if not (0 <= score <= 100):
            flash('Score must be between 0 and 100.', 'danger')
            return redirect(url_for('student_details', student_id=student_id))
    except ValueError:
        flash('Score must be a number.', 'danger')
        return redirect(url_for('student_details', student_id=student_id))

    # Check if a grade for this subject already exists for the student
    existing_grades = get_student_grades(student_id)
    for grade in existing_grades:
        if grade['subject'].lower() == subject.lower():
            update_grade_record(grade['id'], score)
            flash(f'Grade for "{subject}" updated to {score} for this student.', 'info')
            return redirect(url_for('student_details', student_id=student_id))

    add_grade(student_id, subject, score)
    flash(f'Grade {score} for "{subject}" added successfully!', 'success')
    return redirect(url_for('student_details', student_id=student_id))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = get_student_by_id(student_id)
    if student:
        delete_student_record(student_id)
        flash(f'Student "{student["name"]}" and all their grades deleted successfully.', 'success')
    else:
        flash('Student not found.', 'danger')
    return redirect(url_for('index'))

@app.route('/delete_grade/<int:student_id>/<int:grade_id>', methods=['POST'])
def delete_grade(student_id, grade_id):
    grade_deleted = delete_grade_record(grade_id)
    if grade_deleted:
        flash('Grade deleted successfully.', 'success')
    else:
        flash('Grade not found.', 'danger')
    return redirect(url_for('student_details', student_id=student_id))

@app.route('/subject_analytics')
def subject_analytics():
    all_students = get_all_students()
    
    # Structure for subject-wise data: {subject: [{student_name, score, roll_number}, ...]}
    subject_data = defaultdict(list)
    
    for student in all_students:
        grades = get_student_grades(student['id'])
        for grade in grades:
            subject_data[grade['subject'].title()].append({
                'student_name': student['name'],
                'roll_number': student['roll_number'],
                'score': grade['score']
            })

    subject_results = {}
    for subject, grades_list in subject_data.items():
        if not grades_list:
            continue

        # Calculate class average for the subject
        total_scores = sum(g['score'] for g in grades_list)
        class_average = total_scores / len(grades_list)

        # Find subject topper
        topper = max(grades_list, key=lambda x: x['score'])

        subject_results[subject] = {
            'class_average': class_average,
            'topper': topper
        }
    
    # Sort subjects alphabetically for consistent display
    sorted_subject_results = dict(sorted(subject_results.items()))

    return render_template('subject_topper.html', subject_results=sorted_subject_results)

if __name__ == '__main__':
    # When running locally, Flask uses a built-in server.
    # On Heroku, Gunicorn will handle this.
    app.run(debug=True) # debug=True allows automatic reloading and provides a debugger