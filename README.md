# 📚 Online Library Management System (Flask + MySQL)

## 📄 Project Description

The **Online Library Management System** is a simple and efficient web application built using **Flask** (Python) and **MySQL** to manage book circulation in libraries. It allows administrators to:

- Add and manage student and book records
- Issue and return books
- Generate issue logs and reports (CSV format)

This project is designed as a beginner-friendly full-stack project for students learning backend development, databases, and web integration. It demonstrates core CRUD operations, relational database management, and session-based login systems.

**Tech Stack**:
- **Backend**: Python (Flask)
- **Database**: MySQL
- **Frontend**: HTML, Jinja Templates

## 🚀 Features

- Add/Delete Students and Books
- Issue and Return Books
- Auto-generated Reports (CSV)
- Admin Login System
- Clean and minimal UI (HTML/CSS)

## 🛠️ Setup Instructions

1. Clone the repo:
   ```bash
   git clone https://github.com/Aditya-afk-hue/Online-library-Management
   cd library-management-flask
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # For Windows
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Import the `LibraryDB` schema in MySQL Workbench or create tables manually.

5. Run the app:
   ```bash
   python app.py
   ```

6. Visit: http://127.0.0.1:5000

## 🧑‍💼 Admin Login

- **Username:** admin
- **Password:** admin123

*(Make sure you've inserted this manually into the `Admins` table if needed)*

---

## 📁 Project Structure

```
Online_Library_Management_System/
├── static/
├── templates/
├── app.py
├── librarydb.sql
├── logs
└── README.md
```

## 📄 License

This project is open-source and free to use for learning purposes.
