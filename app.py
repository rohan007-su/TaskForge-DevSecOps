from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "taskforge_secret"

UPLOAD_FOLDER = "static/uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# DATABASE
db = mysql.connector.connect(
    host="host.docker.internal",
    port=3307,
    user="root",
    password="TaskForge@123",
    database="taskforge"
)

cursor = db.cursor()

# HOME
@app.route('/')
def home():
    return render_template('login.html')


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        query = """
        INSERT INTO users(name,email,password,role)
        VALUES(%s,%s,%s,%s)
        """

        values = (name, email, password, "user")

        cursor.execute(query, values)
        db.commit()

        return redirect('/')

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['POST'])
def login():

    email = request.form['email']
    password = request.form['password']

    query = """
    SELECT * FROM users
    WHERE email=%s AND password=%s
    """

    cursor.execute(query, (email, password))

    user = cursor.fetchone()

    if user:

        session['user_id'] = user[0]
        session['name'] = user[1]
        session['email'] = user[2]
        session['role'] = user[4]

        if user[4] == "admin":
            return redirect('/admin-dashboard')

        return redirect('/dashboard')

    return "Invalid Login"


# USER DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/')

    query = """
    SELECT * FROM tasks
    WHERE user_id=%s
    """

    cursor.execute(query, (session['user_id'],))

    tasks = cursor.fetchall()

    return render_template(
        'dashboard.html',
        tasks=tasks
    )


# ADMIN DASHBOARD
@app.route('/admin-dashboard')
def admin_dashboard():

    if 'role' not in session:
        return redirect('/')

    if session['role'] != 'admin':
        return redirect('/')

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    query = """
    SELECT
        tasks.id,
        users.name,
        tasks.title,
        tasks.description,
        tasks.status,
        tasks.proof

    FROM tasks

    LEFT JOIN users
    ON tasks.user_id = users.id
    """

    cursor.execute(query)

    tasks = cursor.fetchall()

    return render_template(
        'admin_dashboard.html',
        users=users,
        tasks=tasks
    )


# ADD TASK
@app.route('/add-task', methods=['POST'])
def add_task():

    user_email = request.form['user_email']
    title = request.form['title']
    description = request.form['description']

    cursor.execute(
        "SELECT id FROM users WHERE email=%s",
        (user_email,)
    )

    user = cursor.fetchone()

    user_id = user[0]

    query = """
    INSERT INTO tasks(
        user_email,
        title,
        description,
        status,
        user_id
    )

    VALUES(%s,%s,%s,%s,%s)
    """

    values = (
        user_email,
        title,
        description,
        "Pending",
        user_id
    )

    cursor.execute(query, values)

    db.commit()

    return redirect('/admin-dashboard')


# SUBMIT TASK
@app.route('/submit-task/<int:id>', methods=['POST'])
def submit_task(id):

    proof = request.files['proof']

    filename = secure_filename(proof.filename)

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    proof.save(filepath)

    query = """
    UPDATE tasks
    SET status=%s, proof=%s
    WHERE id=%s
    """

    values = (
        "Submitted",
        filename,
        id
    )

    cursor.execute(query, values)

    db.commit()

    return redirect('/dashboard')


# APPROVE
@app.route('/approve-task/<int:id>')
def approve_task(id):

    query = """
    UPDATE tasks
    SET status='Completed'
    WHERE id=%s
    """

    cursor.execute(query, (id,))
    db.commit()

    return redirect('/admin-dashboard')


# REJECT
@app.route('/reject-task/<int:id>')
def reject_task(id):

    query = """
    UPDATE tasks
    SET status='Rejected'
    WHERE id=%s
    """

    cursor.execute(query, (id,))
    db.commit()

    return redirect('/admin-dashboard')


# DELETE TASK
@app.route('/delete-task/<int:id>')
def delete_task(id):

    query = """
    DELETE FROM tasks
    WHERE id=%s
    """

    cursor.execute(query, (id,))
    db.commit()

    return redirect('/admin-dashboard')


# FORGOT PASSWORD
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form['email']
        new_password = request.form['new_password']

        query = """
        UPDATE users
        SET password=%s
        WHERE email=%s
        """

        values = (
            new_password,
            email
        )

        cursor.execute(query, values)
        db.commit()

        return redirect('/')

    return render_template('forgot_password.html')


# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# RUN
if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
