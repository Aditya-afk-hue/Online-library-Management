import streamlit as st
import pandas as pd
import uuid
import json  # To store lists in the SQL database
from sqlalchemy.exc import OperationalError  # To catch DB errors
from sqlalchemy import text # Import the text function

# --- DATABASE CONNECTION & INITIALIZATION ---

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def get_db_connection():
    """Returns a connection to the SQLite database."""
    # The URL points to a local file 'library.db'
    # On Streamlit Community Cloud, this file will be ephemeral.
    return st.connection("library_db", type="sql", url="sqlite:///library.db")

conn = get_db_connection()

def initialize_database():
    """Creates tables if they don't exist and adds sample data."""
    with conn.session as s:
        # Create books table
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS books (
                ISBN TEXT PRIMARY KEY,
                Title TEXT,
                Author TEXT,
                Genre TEXT,
                Total_Quantity INTEGER,
                Available INTEGER
            );
        """))
        # Create members table
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS members (
                Member_ID TEXT PRIMARY KEY,
                Name TEXT,
                Checked_Out_ISBNs TEXT  -- Storing list as JSON string
            );
        """))
        # Create users table for login
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                role TEXT  -- 'admin' or 'member'
            );
        """))
        # Create transactions table
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                Transaction_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Member_ID TEXT,
                ISBN TEXT,
                Type TEXT, -- 'checkout' or 'return'
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (Member_ID) REFERENCES members(Member_ID),
                FOREIGN KEY (ISBN) REFERENCES books(ISBN)
            );
        """))
        
        # Add sample data only if tables are new
        try:
            # Add sample books if table is empty
            if s.execute(text("SELECT COUNT(*) FROM books")).scalar() == 0:
                s.execute(text("INSERT INTO books (ISBN, Title, Author, Genre, Total_Quantity, Available) VALUES "
                          "('978-0321765723', 'The Lord of the Rings', 'J.R.R. Tolkien', 'Fantasy', 5, 5),"
                          "('978-0132354181', 'Clean Code', 'Robert C. Martin', 'Software', 3, 3),"
                          "('978-0743273565', 'The Great Gatsby', 'F. Scott Fitzgerald', 'Classic', 4, 4);"))

            # Add sample members if table is empty
            if s.execute(text("SELECT COUNT(*) FROM members")).scalar() == 0:
                s.execute(text("INSERT INTO members (Member_ID, Name, Checked_Out_ISBNs) VALUES "
                          "('M-001', 'Alice Smith', '[]'),"
                          "('M-002', 'Bob Johnson', '[]');"))
            
            # Add sample users if table is empty
            if s.execute(text("SELECT COUNT(*) FROM users")).scalar() == 0:
                s.execute(text("INSERT INTO users (username, password, role) VALUES "
                          "('admin', 'admin123', 'admin'),"
                          "('alice', 'pass123', 'member'),"
                          "('bob', 'pass456', 'member');"))
            
            s.commit()
        except OperationalError:
            # Handle potential race condition or DB lock
            s.rollback()

# Run initialization
initialize_database()

# --- AUTHENTICATION ---

def check_login(username, password):
    """Checks if username and password are correct."""
    with conn.session as s:
        result = s.execute(
            text("SELECT role, Member_ID FROM users "
            "LEFT JOIN members ON users.username = members.Name "
            "WHERE username = :username AND password = :password"),
            params={"username": username, "password": password}
        ).first()
        
        if result:
            role, member_id = result
            st.session_state.logged_in = True
            st.session_state.user_role = role
            st.session_state.username = username
            # If user is a member, link them to their member profile
            st.session_state.member_id = member_id if role == 'member' else None
            st.rerun()
        else:
            st.error("Incorrect username or password")

def show_login_page():
    """Displays the login form."""
    st.set_page_config(page_title="Library Login")
    st.title("📚 Zenith Library Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            check_login(username, password)
            
    st.info("Sample Logins:\n- Admin: `admin` / `admin123`\n- Member: `alice` / `pass123`")

# --- PAGE 1: HOME/DASHBOARD ---

def page_home():
    st.title(f"📚 Welcome, {st.session_state.username}!")
    st.markdown("Welcome to the Zenith Library Management System.")

    st.warning("🚨 **Note:** This app uses an SQLite database file. On Streamlit Community Cloud, "
               "this file is **ephemeral** and all data will be **RESET** when the app restarts.", icon="⚠️")
    
    # Admin Dashboard
    if st.session_state.user_role == 'admin':
        st.subheader("Admin Dashboard")
        
        # Fetch metrics
        total_books = conn.query("SELECT SUM(Total_Quantity) FROM books", ttl=5).iloc[0, 0]
        available_books = conn.query("SELECT SUM(Available) FROM books", ttl=5).iloc[0, 0]
        total_members = conn.query("SELECT COUNT(*) FROM members", ttl=5).iloc[0, 0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Book Titles", conn.query("SELECT COUNT(*) FROM books", ttl=5).iloc[0, 0])
        col2.metric("Total Book Copies", f"{available_books} / {total_books}")
        col3.metric("Total Members", total_members)
        
        st.divider()
        st.subheader("Recent Transactions")
        transactions_df = conn.query("SELECT * FROM transactions ORDER BY Timestamp DESC LIMIT 10", ttl=5)
        st.dataframe(transactions_df, use_container_width=True)

    # Member Dashboard
    if st.session_state.user_role == 'member':
        st.subheader("Your Checked-Out Books")
        member_id = st.session_state.member_id
        if not member_id:
            st.error("Your user account is not linked to a member profile. Please contact an admin.")
            return

        # Get list of ISBNs
        with conn.session as s:
            json_isbns = s.execute(
                text("SELECT Checked_Out_ISBNs FROM members WHERE Member_ID = :id"),
                params={"id": member_id}
            ).scalar()
            
        isbns = json.loads(json_isbns)
        
        if not isbns:
            st.info("You have no books checked out.")
        else:
            # Fetch book details for the checked-out ISBNs
            # Using a placeholder list for the SQL query
            placeholders = ','.join('?' for _ in isbns)
            books_df = conn.query(
                f"SELECT Title, Author, Genre FROM books WHERE ISBN IN ({placeholders})",
                params=isbns,
                ttl=5
            )
            st.dataframe(books_df, use_container_width=True)

# --- PAGE 2: BOOK MANAGEMENT (Admin Only) ---

def page_book_management():
    st.title("📖 Book Management")
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin only.")
        return

    with st.expander("Add New Book", expanded=False):
        with st.form("add_book_form", clear_on_submit=True):
            isbn = st.text_input("ISBN (Unique Identifier)", max_chars=13)
            title = st.text_input("Title")
            author = st.text_input("Author")
            genre = st.text_input("Genre")
            quantity = st.number_input("Total Quantity", min_value=1, value=1)
            
            submitted = st.form_submit_button("Add Book")

            if submitted:
                if not all([isbn, title, author, genre, quantity]):
                    st.error("Please fill in all fields.")
                else:
                    try:
                        with conn.session as s:
                            s.execute(
                                text("INSERT INTO books (ISBN, Title, Author, Genre, Total_Quantity, Available) "
                                "VALUES (:isbn, :title, :author, :genre, :qty, :avail)"),
                                params={
                                    "isbn": isbn, "title": title, "author": author, 
                                    "genre": genre, "qty": quantity, "avail": quantity
                                }
                            )
                            s.commit()
                        st.success(f"Book '{title}' by {author} added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add book. ISBN might already exist. Error: {e}")

    st.divider()
    st.subheader("Manage Existing Books")
    books_df = conn.query("SELECT * FROM books", ttl=5)
    st.dataframe(books_df, use_container_width=True)

    # Edit/Delete Section
    st.subheader("Edit or Remove Book")
    isbn_to_manage = st.selectbox(
        "Select Book (by ISBN) to Manage", 
        options=books_df['ISBN'],
        format_func=lambda x: f"{x} - {books_df.set_index('ISBN').loc[x, 'Title']}"
    )

    if isbn_to_manage:
        book_data = books_df.set_index('ISBN').loc[isbn_to_manage]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Title:** {book_data['Title']}")
            # Edit Quantity
            new_total_quantity = st.number_input(
                "Update Total Quantity", 
                min_value=book_data['Total_Quantity'] - book_data['Available'],
                value=book_data['Total_Quantity']
            )
            if st.button("Update Quantity"):
                checked_out_count = book_data['Total_Quantity'] - book_data['Available']
                new_available = new_total_quantity - checked_out_count
                
                with conn.session as s:
                    s.execute(
                        text("UPDATE books SET Total_Quantity = :total, Available = :avail WHERE ISBN = :isbn"),
                        params={"total": new_total_quantity, "avail": new_available, "isbn": isbn_to_manage}
                    )
                    s.commit()
                st.success("Quantity updated!")
                st.rerun()
        
        with col2:
            st.markdown(f"**Available:** {book_data['Available']} / {book_data['Total_Quantity']}")
            # Delete Book
            if st.button("Remove Book from Library", type="primary"):
                if book_data['Available'] < book_data['Total_Quantity']:
                    st.error("Cannot remove book. Some copies are still checked out.")
                else:
                    with conn.session as s:
                        # Need to delete transactions first due to foreign key constraint
                        s.execute(text("DELETE FROM transactions WHERE ISBN = :isbn"), params={"isbn": isbn_to_manage})
                        s.execute(text("DELETE FROM books WHERE ISBN = :isbn"), params={"isbn": isbn_to_manage})
                        s.commit()
                    st.success("Book removed!")
                    st.rerun()

# --- PAGE 3: MEMBER MANAGEMENT (Admin Only) ---

def page_member_management():
    st.title("🧑‍🤝‍🧑 Member Management")
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin only.")
        return

    st.info("Note: To create a *login* for a member, add a user in the 'User Accounts' page with a matching name.")

    with st.expander("Register New Member", expanded=False):
        with st.form("add_member_form", clear_on_submit=True):
            name = st.text_input("Member Name")
            submitted = st.form_submit_button("Register Member")
            if submitted and name:
                member_id = f"M-{uuid.uuid4().hex[:6].upper()}"
                try:
                    with conn.session as s:
                        s.execute(
                            text("INSERT INTO members (Member_ID, Name, Checked_Out_ISBNs) VALUES (:id, :name, '[]')"),
                            params={"id": member_id, "name": name}
                        )
                        s.commit()
                    st.success(f"Member '{name}' registered with ID: {member_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add member. Error: {e}")

    st.divider()
    st.subheader("Current Members")
    members_df = conn.query("SELECT * FROM members", ttl=5)
    st.dataframe(members_df, use_container_width=True)

# --- PAGE 4: USER ACCOUNTS (Admin Only) ---

def page_user_accounts():
    st.title("🔑 User Account Management")
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin only.")
        return

    with st.expander("Add New User Account", expanded=False):
        with st.form("add_user_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["member", "admin"])
            
            # Link to member profile if role is 'member'
            member_name_options = conn.query("SELECT Name FROM members ORDER BY Name", ttl=5)['Name']
            if role == 'member':
                name = st.selectbox("Link to Member Profile (Name)", member_name_options)
            
            submitted = st.form_submit_button("Create User")
            
            if submitted:
                if not (username and password and role):
                    st.error("Please fill all fields.")
                else:
                    if role == 'member' and not name:
                        st.error("Please select a member profile to link.")
                        return
                    try:
                        with conn.session as s:
                            # Note: In a real app, hash the password!
                            s.execute(
                                text("INSERT INTO users (username, password, role) VALUES (:user, :pass, :role)"),
                                params={"user": username, "pass": password, "role": role}
                            )
                            # Link user to member profile
                            if role == 'member':
                                s.execute(
                                    text("UPDATE users SET Member_ID = (SELECT Member_ID FROM members WHERE Name = :name) "
                                    "WHERE username = :user"),
                                    params={"name": name, "user": username}
                                )
                            s.commit()
                        st.success(f"User '{username}' created with role '{role}'.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create user. Username may already exist. Error: {e}")

    st.divider()
    st.subheader("Existing User Accounts")
    users_df = conn.query("SELECT username, role, Member_ID FROM users", ttl=5)
    st.dataframe(users_df, use_container_width=True)


# --- PAGE 5: TRANSACTIONS ---

def page_transactions():
    st.title("🔄 Book Transactions")

    books_df = conn.query("SELECT * FROM books", ttl=5)
    members_df = conn.query("SELECT * FROM members", ttl=5)

    if books_df.empty or members_df.empty:
        st.warning("Please add books and members before managing transactions.")
        return

    # For Members, auto-select their profile
    if st.session_state.user_role == 'member':
        st.subheader(f"Transactions for: {st.session_state.username}")
        member_id_options = [st.session_state.member_id]
        if not st.session_state.member_id:
            st.error("Your account is not linked to a member profile. Cannot check out books.")
            return
    else:
        # Admins can select any member
        member_id_options = members_df['Member_ID']


    col1, col2 = st.columns(2)

    # --- Check Out Section ---
    with col1:
        st.subheader("Check Out Book")
        with st.form("checkout_form", clear_on_submit=True):
            member_id = st.selectbox(
                "Select Member", 
                options=member_id_options,
                format_func=lambda x: f"{x} - {members_df.set_index('Member_ID').loc[x, 'Name']}"
            )
            
            available_books_df = books_df[books_df['Available'] > 0]
            isbn = st.selectbox(
                "Select Book (Available)", 
                options=available_books_df['ISBN'],
                format_func=lambda x: f"{x} - {available_books_df.set_index('ISBN').loc[x, 'Title']}"
            )
            
            checkout_submitted = st.form_submit_button("Check Out")

            if checkout_submitted and member_id and isbn:
                with conn.session as s:
                    # Get member's current book list
                    json_isbns = s.execute(
                        text("SELECT Checked_Out_ISBNs FROM members WHERE Member_ID = :id"),
                        params={"id": member_id}
                    ).scalar()
                    isbns = json.loads(json_isbns)
                    
                    if isbn in isbns:
                        st.error("This member already has this book checked out.")
                    else:
                        isbns.append(isbn)
                        new_json_isbns = json.dumps(isbns)
                        
                        # 1. Update member's list
                        s.execute(
                            text("UPDATE members SET Checked_Out_ISBNs = :json_isbns WHERE Member_ID = :id"),
                            params={"json_isbns": new_json_isbns, "id": member_id}
                        )
                        # 2. Decrement book availability
                        s.execute(
                            text("UPDATE books SET Available = Available - 1 WHERE ISBN = :isbn"),
                            params={"isbn": isbn}
                        )
                        # 3. Log transaction
                        s.execute(
                            text("INSERT INTO transactions (Member_ID, ISBN, Type) VALUES (:member_id, :isbn, 'checkout')"),
                            params={"member_id": member_id, "isbn": isbn}
                        )
                        s.commit()
                        st.success("Book checked out successfully!")
                        st.rerun()

    # --- Return Section ---
    with col2:
        st.subheader("Return Book")
        with st.form("return_form", clear_on_submit=True):
            member_id_return = st.selectbox(
                "Select Member Returning Book", 
                options=member_id_options,
                format_func=lambda x: f"{x} - {members_df.set_index('Member_ID').loc[x, 'Name']}",
                key="return_member_select"
            )
            
            books_to_return_options = []
            if member_id_return:
                json_isbns = conn.query(
                    "SELECT Checked_Out_ISBNs FROM members WHERE Member_ID = :id",
                    params={"id": member_id_return},
                    ttl=5
                ).iloc[0,0]
                books_to_return_options = json.loads(json_isbns)
            
            if not books_to_return_options:
                st.info("This member has no books checked out.")
                isbn_return = None
            else:
                isbn_return = st.selectbox(
                    "Select Book to Return",
                    options=books_to_return_options,
                    format_func=lambda x: f"{x} - {books_df.set_index('ISBN').loc[x, 'Title']}"
                )
            
            return_submitted = st.form_submit_button("Return Book")

            if return_submitted and member_id_return and isbn_return:
                with conn.session as s:
                    isbns = json.loads(json_isbns)
                    isbns.remove(isbn_return)
                    new_json_isbns = json.dumps(isbns)
                    
                    # 1. Update member's list
                    s.execute(
                        text("UPDATE members SET Checked_Out_ISBNs = :json_isbns WHERE Member_ID = :id"),
                        params={"json_isbns": new_json_isbns, "id": member_id_return}
                    )
                    # 2. Increment book availability
                    s.execute(
                        text("UPDATE books SET Available = Available + 1 WHERE ISBN = :isbn"),
                        params={"isbn": isbn_return}
                    )
                    # 3. Log transaction
                    s.execute(
                        text("INSERT INTO transactions (Member_ID, ISBN, Type) VALUES (:member_id, :isbn, 'return')"),
                        params={"member_id": member_id_return, "isbn": isbn_return}
                    )
                    s.commit()
                    st.success("Book returned successfully!")
                    st.rerun()

# --- MAIN APP ROUTER ---

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.session_state.member_id = None

if not st.session_state.logged_in:
    show_login_page()
else:
    # --- Sidebar Navigation ---
    st.sidebar.title("Navigation")
    st.sidebar.markdown(f"Logged in as: **{st.session_state.username}** (`{st.session_state.user_role}`)")
    
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    # Define pages based on role
    if st.session_state.user_role == 'admin':
        PAGES = {
            "🏠 Home": page_home,
            "📖 Book Management": page_book_management,
            "🧑‍🤝‍🧑 Member Management": page_member_management,
            "🔑 User Accounts": page_user_accounts,
            "🔄 Transactions": page_transactions
        }
    else:  # 'member'
        PAGES = {
            "🏠 Home": page_home,
            "🔄 Transactions": page_transactions
        }

    page_selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    
    st.sidebar.divider()
    st.sidebar.markdown("Made with [Streamlit](https.streamlit.io)")

    # Display the selected page
    page_function = PAGES[page_selection]
    page_function()


