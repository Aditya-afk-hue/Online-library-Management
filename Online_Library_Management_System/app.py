from flask import Flask, request, redirect, session, render_template, send_file
import mysql.connector
from datetime import date
import csv

app = Flask(__name__)
app.secret_key = 'your-secret-key'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Aditya@2005",  # Change if needed
    database="LibraryDB"
)
cursor = db.cursor()

@app.before_request
def restrict():
    if request.endpoint in ['add_student', 'add_book', 'issue_book', 'return_book'] and 'admin' not in session:
        return redirect('/login')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        cursor.execute("SELECT * FROM Admins WHERE username=%s AND password=%s", (uname, pwd))
        admin = cursor.fetchone()
        if admin:
            session['admin'] = uname
            return redirect('/')
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        cursor.execute("INSERT INTO Students (name, email) VALUES (%s, %s)", (request.form['name'], request.form['email']))
        db.commit()
        return redirect('/')
    return render_template('add_student.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        cursor.execute("INSERT INTO Books (title, author) VALUES (%s, %s)", (request.form['title'], request.form['author']))
        db.commit()
        return redirect('/')
    return render_template('add_book.html')

@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        student_id = request.form['student_id']
        book_id = request.form['book_id']
        cursor.execute("UPDATE Books SET available=FALSE WHERE book_id=%s", (book_id,))
        cursor.execute("INSERT INTO IssueLogs (student_id, book_id, issue_date) VALUES (%s, %s, %s)", (student_id, book_id, date.today()))
        db.commit()
        return redirect('/')
    return render_template('issue_book.html')

@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        cursor.execute("UPDATE Books SET available=TRUE WHERE book_id=%s", (book_id,))
        cursor.execute("UPDATE IssueLogs SET return_date=%s WHERE book_id=%s AND return_date IS NULL", (date.today(), book_id))
        db.commit()
        return redirect('/')
    return render_template('return_book.html')

@app.route('/export_logs')
def export_logs():
    cursor.execute("""
        SELECT 
            il.log_id,
            s.name AS student_name,
            b.title AS book_title,
            il.issue_date,
            il.return_date
        FROM IssueLogs il
        JOIN Students s ON il.student_id = s.student_id
        JOIN Books b ON il.book_id = b.book_id
    """)
    logs = cursor.fetchall()

    with open('logs.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Log ID', 'Student Name', 'Book Title', 'Issue Date', 'Return Date'])
        writer.writerows(logs)

    return send_file('logs.csv', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)