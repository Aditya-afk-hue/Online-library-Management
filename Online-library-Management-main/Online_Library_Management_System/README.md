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

## 👨‍🎓 Preloaded Data

The following student and book data has already been inserted into the database:

### Students (IDs 1–10):

| ID | Name              | Email                         |
|----|-------------------|-------------------------------|
| 1  | Aditya Samal      | aditya.samal@example.com      |
| 2  | Riya Das          | riya.das@example.com          |
| 3  | Amit Ranjan       | amit.ranjan@example.com       |
| 4  | Sneha Mohapatra   | sneha.mohapatra@example.com   |
| 5  | Rahul Sahu        | rahul.sahu@example.com        |
| 6  | Priya Nanda       | priya.nanda@example.com       |
| 7  | Sourav Behera     | sourav.behera@example.com     |
| 8  | Anjali Sethi      | anjali.sethi@example.com      |
| 9  | Manas Nayak       | manas.nayak@example.com       |
| 10 | Meera Jena        | meera.jena@example.com        |

### Books (IDs 1–10):

| ID | Title                         | Author                  |
|----|-------------------------------|-------------------------|
| 1  | Python Programming Basics     | John Zelle              |
| 2  | Let Us C                      | Yashavant Kanetkar      |
| 3  | Introduction to Algorithms    | Thomas H. Cormen        |
| 4  | Digital Logic Design          | M. Morris Mano          |
| 5  | Database Management Systems   | Raghu Ramakrishnan      |
| 6  | Artificial Intelligence       | Stuart Russell          |
| 7  | Java: The Complete Reference  | Herbert Schildt         |
| 8  | Signals and Systems           | Alan V. Oppenheim       |
| 9  | Operating Systems Concepts    | Silberschatz & Galvin   |
| 10 | Data Structures in C          | Reema Thareja           |

---

## 🛠️ Setup Instructions

1. Clone the repo:
   ```bash
   git clone https://github.com/Aditya-afk-hue/Online-library-Management
   cd Online-library-Management/Online_Library_Management_System
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

4. Import the `LibraryDB` schema in MySQL Workbench or use the included SQL insert script to load sample data.

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
├── README.md
└── requirements.txt
```

## 📄 License

This project is open-source and free to use for learning purposes.