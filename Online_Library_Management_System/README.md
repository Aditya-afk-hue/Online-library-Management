# 📚 Online Library Management System (Flask + MySQL)

A simple web-based Library Management System built using Python (Flask) and MySQL. It supports basic functionalities like adding books and students, issuing/returning books, and exporting issue logs.

## 🚀 Features

- Add/Delete Students and Books
- Issue and Return Books
- Auto-generated Reports (CSV)
- Admin Login System
- Clean and minimal UI (HTML/CSS)

## 🛠️ Tech Stack

- Backend: Python, Flask
- Database: MySQL
- Frontend: HTML, CSS (Jinja Templates)

## ⚙️ Setup Instructions

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/library-management-flask.git
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

6. Visit: `http://127.0.0.1:5000`

## 🧑‍💼 Admin Login

- **Username:** admin
- **Password:** admin123

*(Make sure you've inserted this manually into the `Admins` table if needed)*

---

## 📦 Project Structure

```
Online_Library_Management_System/
├── app.py
├── templates/
├── static/
├── requirements.txt
├── .gitignore
└── README.md
```

## 📄 License

This project is open-source and free to use for learning purposes.