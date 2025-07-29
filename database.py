import sqlite3

DATABASE = 'students.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows access to columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            UNIQUE(student_id, subject)
        )
    ''')
    conn.commit()
    conn.close()

def add_student(name, roll_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (name, roll_number) VALUES (?, ?)", (name, roll_number))
        conn.commit()
        return cursor.lastrowid # Return the ID of the newly added student
    except sqlite3.IntegrityError:
        # This handles the UNIQUE constraint violation for roll_number
        return None
    finally:
        conn.close()

def get_all_students():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return students

def get_student_by_id(student_id):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return student

def get_student_by_roll_number(roll_number):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,)).fetchone()
    conn.close()
    return student

def add_grade(student_id, subject, score):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO grades (student_id, subject, score) VALUES (?, ?, ?)", (student_id, subject, score))
        conn.commit()
    except sqlite3.IntegrityError:
        # This would typically happen if a UNIQUE constraint on (student_id, subject) is violated,
        # meaning a grade for this subject already exists. The app.py logic handles this by updating.
        pass
    finally:
        conn.close()

def get_student_grades(student_id):
    conn = get_db_connection()
    grades = conn.execute("SELECT * FROM grades WHERE student_id = ?", (student_id,)).fetchall()
    conn.close()
    return grades

def update_grade_record(grade_id, new_score):
    conn = get_db_connection()
    conn.execute("UPDATE grades SET score = ? WHERE id = ?", (new_score, grade_id))
    conn.commit()
    conn.close()

def delete_student_record(student_id):
    conn = get_db_connection()
    # ON DELETE CASCADE in the grades table definition handles deleting associated grades
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

def delete_grade_record(grade_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
    deleted_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_rows > 0 # Return True if a row was deleted, False otherwise