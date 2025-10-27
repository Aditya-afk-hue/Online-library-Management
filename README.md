Streamlit Library Management System

This is a simple, end-to-end Library Management System built entirely in Python using the Streamlit framework.

Features

Dashboard: View key metrics like total books, available books, and total members.

Book Management: Add, search, filter, update quantity, and remove books from the library.

Member Management: Register new members and remove existing ones.

Transactions: A full checkout and return system that automatically updates book availability and member checkout lists.

Session-Based Persistence: Uses st.session_state to store data, making the app fully functional for a single user session.

How to Run Locally

Clone this repository:

git clone <your-repo-url>
cd <your-repo-name>

Create a virtual environment (recommended):

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

Install the requirements:

pip install -r requirements.txt

Run the app:

streamlit run library_app.py

How to Deploy on Streamlit Community Cloud (Free)

Create a GitHub Repository:

Create a new public repository on GitHub.

Add the 3 files (library_app.py, requirements.txt, README.md) to this repository.

git add .

git commit -m "Initial commit"

git push -u origin main

Sign up for Streamlit Community Cloud:

Go to share.streamlit.io and sign up (you can use your GitHub account).

Deploy the App:

Click the "New app" button.

Select "From existing repo".

Repository: Choose the GitHub repository you just created.

Branch: main (or your default branch).

Main file path: library_app.py

Click "Deploy!"

Your application will be live in a few minutes!

⚠️ Important Note on Data Persistence

This application uses st.session_state to store all library data. This means the data is ephemeral:

The data will persist as long as a single user has the app open in their browser tab.

The data will be completely reset if the app restarts, which happens when you deploy, push new code, or if the app is inactive for a period.

For a true, permanent database, you would need to replace the st.session_state logic with a connection to an external database like Supabase, Airtable, Firebase, or Google Sheets. Streamlit's new st.connection feature makes this much easier.
