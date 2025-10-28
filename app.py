import streamlit as st
import pandas as pd
import uuid
import json  # To store lists in the SQL database
from sqlalchemy.exc import OperationalError  # To catch DB errors
from sqlalchemy import text # Import the text function

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="WorldClass Library",
    page_icon="📚",
    layout="wide",
)

# --- CONSTANTS ---
MAX_CHECKOUT_LIMIT = 5
PLACEHOLDER_COVER_URL = "https://placehold.co/300x400/eeeeee/cccccc?text=No+Cover"

# --- DATABASE CONNECTION & INITIALIZATION ---

@st.cache_resource
def get_db_connection():
    """Returns a connection to the SQLite database."""
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
                Available INTEGER,
                Cover_URL TEXT
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
                role TEXT,  -- 'admin' or 'member'
                Member_ID TEXT, -- Can be NULL for admins.
                FOREIGN KEY (Member_ID) REFERENCES members(Member_ID)
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
            if s.execute(text("SELECT COUNT(*) FROM books")).scalar() == 0:
                s.execute(text("INSERT INTO books (ISBN, Title, Author, Genre, Total_Quantity, Available, Cover_URL) VALUES "
                          "('978-0321765723', 'The Lord of the Rings', 'J.R.R. Tolkien', 'Fantasy', 5, 5, 'https://covers.openlibrary.org/b/id/12838421-L.jpg'),"
                          "('978-0132354181', 'Clean Code', 'Robert C. Martin', 'Software', 3, 3, 'https://covers.openlibrary.org/b/id/8230017-L.jpg'),"
                          "('978-0743273565', 'The Great Gatsby', 'F. Scott Fitzgerald', 'Classic', 4, 4, 'https://covers.openlibrary.org/b/id/11181672-L.jpg');"))

            if s.execute(text("SELECT COUNT(*) FROM members")).scalar() == 0:
                member1_id = 'M-001'
                member2_id = 'M-002'
                s.execute(
                    text("INSERT INTO members (Member_ID, Name, Checked_Out_ISBNs) VALUES "
                         "(:id1, 'Alice Smith', '[]'),"
                         "(:id2, 'Bob Johnson', '[]');"),
                    params={"id1": member1_id, "id2": member2_id}
                )

                if s.execute(text("SELECT COUNT(*) FROM users")).scalar() == 0:
                    s.execute(text("INSERT INTO users (username, password, role, Member_ID) VALUES "
                              "('admin', 'admin123', 'admin', NULL),"
                              "('alice', 'pass123', 'member', :id1),"
                              "('bob', 'pass456', 'member', :id2);"),
                              params={"id1": member1_id, "id2": member2_id})
            
            s.commit()
        except OperationalError as e:
            st.error(f"Error during initialization: {e}")
            s.rollback()

# Run initialization
initialize_database()

# --- AUTHENTICATION ---

def check_login(username, password):
    """Checks if username and password are correct."""
    with conn.session as s:
        result = s.execute(
            text("SELECT role, Member_ID FROM users "
            "WHERE username = :username AND password = :password"),
            params={"username": username, "password": password}
        ).first()
        
        if result:
            role, member_id = result
            st.session_state.logged_in = True
            st.session_state.user_role = role
            st.session_state.username = username
            st.session_state.member_id = member_id
            st.rerun()
        else:
            st.error("Incorrect username or password")

def show_login_page():
    """Displays the login form."""
    st.set_page_config(page_title="Library Login")
    
    with st.container(border=True):
        st.title("📚 WorldClass Library Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submitted:
                check_login(username, password)
                
        st.info("Sample Logins:\n- Admin: `admin` / `admin123`\n- Member: `alice` / `pass123`")

# --- PAGE 1: HOME/DASHBOARD ---

def page_home():
    st.title(f"📚 Welcome, {st.session_state.username}!")
    st.markdown("Welcome to the WorldClass Library Management System.")

    st.warning("🚨 **Note:** This app uses an ephemeral SQLite database. "
               "All data will be **RESET** when the app restarts.", icon="⚠️")
    
    # Admin Dashboard
    if st.session_state.user_role == 'admin':
        st.subheader("Admin Dashboard")
        
        # Fetch metrics
        total_books_result = conn.query("SELECT SUM(Total_Quantity) FROM books", ttl=5).iloc[0, 0]
        available_books_result = conn.query("SELECT SUM(Available) FROM books", ttl=5).iloc[0, 0]
        total_members_result = conn.query("SELECT COUNT(*) FROM members", ttl=5).iloc[0, 0]
        total_titles_result = conn.query("SELECT COUNT(*) FROM books", ttl=5).iloc[0, 0]

        total_books = total_books_result if total_books_result is not None else 0
        available_books = available_books_result if available_books_result is not None else 0
        total_members = total_members_result if total_members_result is not None else 0
        total_titles = total_titles_result if total_titles_result is not None else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Book Titles", total_titles)
        col2.metric("Total Book Copies", f"{available_books} / {total_books}")
        col3.metric("Total Members", total_members)
        
        st.divider()
        st.subheader("Recent Transactions")
        transactions_df = conn.query(
            "SELECT T.Timestamp, T.Type, M.Name, B.Title FROM transactions T "
            "JOIN members M ON T.Member_ID = M.Member_ID "
            "JOIN books B ON T.ISBN = B.ISBN "
            "ORDER BY T.Timestamp DESC LIMIT 10", 
            ttl=5
        )
        st.dataframe(transactions_df, use_container_width=True)

    # Member Dashboard
    if st.session_state.user_role == 'member':
        member_id = st.session_state.member_id
        if not member_id:
            st.error("Your user account is not linked to a member profile. Please contact an admin.")
            return

        tab1, tab2 = st.tabs(["Your Checked-Out Books", "Your Transaction History"])

        with tab1:
            st.subheader("Your Checked-Out Books")
            with conn.session as s:
                json_isbns = s.execute(
                    text("SELECT Checked_Out_ISBNs FROM members WHERE Member_ID = :id"),
                    params={"id": member_id}
                ).scalar()
            isbns = json.loads(json_isbns)
            
            if not isbns:
                st.info("You have no books checked out. Visit the Book Catalog to find one!")
            else:
                placeholders = ','.join('?' for _ in isbns)
                books_df = conn.query(
                    f"SELECT Title, Author, Cover_URL FROM books WHERE ISBN IN ({placeholders})",
                    params=isbns,
                    ttl=5
                )
                
                cols = st.columns(4)
                for i, row in enumerate(books_df.itertuples()):
                    with cols[i % 4]:
                        with st.container(border=True):
                            st.image(row.Cover_URL if row.Cover_URL else PLACEHOLDER_COVER_URL, use_column_width=True)
                            st.caption(f"**{row.Title}** by {row.Author}")

        with tab2:
            st.subheader("Your Past Transactions")
            history_df = conn.query(
                "SELECT T.Timestamp, T.Type, B.Title, B.Author FROM transactions T "
                "JOIN books B ON T.ISBN = B.ISBN "
                "WHERE T.Member_ID = :id ORDER BY T.Timestamp DESC",
                params={"id": member_id},
                ttl=5
            )
            if history_df.empty:
                st.info("You have no transaction history.")
            else:
                st.dataframe(history_df, use_container_width=True)


# --- PAGE 2: BOOK CATALOG (All Users) ---

def page_book_catalog():
    st.title("📖 Book Catalog")
    st.markdown("Browse and search our entire collection.")

    books_df = conn.query("SELECT * FROM books", ttl=5)
    
    if books_df.empty:
        st.info("The library catalog is currently empty.")
        return

    # --- Search Bar ---
    search_query = st.text_input("Search by Title, Author, or Genre")
    
    if search_query:
        filtered_df = books_df[
            books_df['Title'].str.contains(search_query, case=False, na=False) |
            books_df['Author'].str.contains(search_query, case=False, na=False) |
            books_df['Genre'].str.contains(search_query, case=False, na=False)
        ]
    else:
        filtered_df = books_df

    if filtered_df.empty:
        st.warning("No books found matching your search.")
        return

    # --- Book Grid Display ---
    cols = st.columns(4)
    for i, row in enumerate(filtered_df.itertuples()):
        with cols[i % 4]:
            with st.container(border=True):
                cover_url = row.Cover_URL if row.Cover_URL else PLACEHOLDER_COVER_URL
                st.image(cover_url, use_column_width=True)
                st.subheader(row.Title)
                
                with st.expander("Details"):
                    st.markdown(f"**Author:** {row.Author}")
                    st.markdown(f"**Genre:** {row.Genre}")
                    st.markdown(f"**ISBN:** {row.ISBN}")
                    if row.Available > 0:
                        st.success(f"**Available:** {row.Available} / {row.Total_Quantity}")
                    else:
                        st.error(f"**Not Available:** {row.Available} / {row.Total_Quantity}")


# --- PAGE 3: ADMIN PANEL (Admin Only) ---

def page_admin_panel():
    st.title("🛡️ Admin Panel")
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin only.")
        return

    tab_books, tab_members, tab_users = st.tabs(["Manage Books", "Manage Members", "Manage User Accounts"])

    # --- Book Management Tab ---
    with tab_books:
        st.subheader("Manage Books")
        with st.expander("Add New Book", expanded=False):
            with st.form("add_book_form", clear_on_submit=True):
                isbn = st.text_input("ISBN (Unique Identifier)", max_chars=13)
                title = st.text_input("Title")
                author = st.text_input("Author")
                genre = st.text_input("Genre")
                quantity = st.number_input("Total Quantity", min_value=1, value=1)
                cover_url = st.text_input("Cover Image URL (Optional)")
                
                submitted = st.form_submit_button("Add Book")

                if submitted:
                    if not all([isbn, title, author, genre, quantity]):
                        st.error("Please fill in all required fields.")
                    else:
                        try:
                            with conn.session as s:
                                s.execute(
                                    text("INSERT INTO books (ISBN, Title, Author, Genre, Total_Quantity, Available, Cover_URL) "
                                    "VALUES (:isbn, :title, :author, :genre, :qty, :avail, :url)"),
                                    params={
                                        "isbn": isbn, "title": title, "author": author, 
                                        "genre": genre, "qty": quantity, "avail": quantity,
                                        "url": cover_url if cover_url else None
                                    }
                                )
                                s.commit()
                            st.success(f"Book '{title}' by {author} added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to add book. ISBN might already exist. Error: {e}")

        st.divider()
        st.subheader("Existing Books")
        books_df = conn.query("SELECT * FROM books", ttl=5)
        st.dataframe(books_df, use_container_width=True)
        
        # Edit/Delete Section
        st.subheader("Edit or Remove Book")
        if books_df.empty:
            st.info("No books to manage.")
        else:
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
                    checked_out_count = book_data['Total_Quantity'] - book_data['Available']
                    min_qty = int(checked_out_count) 
                    
                    new_total_quantity = st.number_input(
                        "Update Total Quantity", 
                        min_value=min_qty,
                        value=int(book_data['Total_Quantity'])
                    )
                    if st.button("Update Quantity"):
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
                    if st.button("Remove Book from Library", type="primary"):
                        if book_data['Available'] < book_data['Total_Quantity']:
                            st.error("Cannot remove book. Some copies are still checked out.")
                        else:
                            with conn.session as s:
                                s.execute(text("DELETE FROM transactions WHERE ISBN = :isbn"), params={"isbn": isbn_to_manage})
                                s.execute(text("DELETE FROM books WHERE ISBN = :isbn"), params={"isbn": isbn_to_manage})
                                s.commit()
                            st.success("Book removed!")
                            st.rerun()

    # --- Member Management Tab ---
    with tab_members:
        st.subheader("Manage Members")
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
        
    # --- User Account Management Tab ---
    with tab_users:
        st.subheader("Manage User Accounts")
        with st.expander("Add New User Account", expanded=False):
            with st.form("add_user_form", clear_on_submit=True):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                role = st.selectbox("Role", ["member", "admin"])
                
                member_id_to_link = None
                if role == 'member':
                    member_options_df = conn.query(
                        """
                        SELECT m.Member_ID, m.Name FROM members m
                        LEFT JOIN users u ON m.Member_ID = u.Member_ID
                        WHERE u.username IS NULL
                        ORDER BY m.Name
                        """,
                        ttl=5
                    )
                    if member_options_df.empty:
                        st.warning("No unlinked member profiles available.")
                    else:
                        member_id_to_link = st.selectbox(
                            "Link to Member Profile", 
                            options=member_options_df['Member_ID'],
                            format_func=lambda x: f"{x} - {member_options_df.set_index('Member_ID').loc[x, 'Name']}"
                        )
                
                submitted = st.form_submit_button("Create User")
                
                if submitted:
                    if not (username and password and role):
                        st.error("Please fill all fields.")
                    elif role == 'member' and not member_id_to_link:
                        st.error("Please select a member profile to link.")
                    else:
                        try:
                            with conn.session as s:
                                s.execute(
                                    text("INSERT INTO users (username, password, role, Member_ID) VALUES (:user, :pass, :role, :member_id)"),
                                    params={
                                        "user": username, "pass": password, "role": role, 
                                        "member_id": member_id_to_link
                                    }
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

# --- PAGE 4: TRANSACTIONS ---

def page_transactions():
    st.title("🔄 Book Transactions")

    books_df = conn.query("SELECT * FROM books", ttl=5)
    members_df = conn.query("SELECT * FROM members", ttl=5)

    if books_df.empty or members_df.empty:
        st.warning("Please add books and members before managing transactions.")
        return

    # Define a better formatting function for select boxes
    def format_member_name(member_id):
        return f"{member_id} - {members_df.set_index('Member_ID').loc[member_id, 'Name']}"

    if st.session_state.user_role == 'member':
        st.subheader(f"Transactions for: {st.session_state.username}")
        member_id_options = [st.session_state.member_id]
        if not st.session_state.member_id:
            st.error("Your account is not linked to a member profile. Cannot check out books.")
            return
    else:
        member_id_options = members_df['Member_ID']


    col1, col2 = st.columns(2)

    # --- Check Out Section ---
    with col1:
        st.subheader("Check Out Book")
        with st.form("checkout_form", clear_on_submit=True):
            member_id = st.selectbox(
                "Select Member", 
                options=member_id_options,
                format_func=format_member_name
            )
            
            available_books_df = books_df[books_df['Available'] > 0]
            if available_books_df.empty:
                st.info("No books are currently available to check out.")
                isbn = None
            else:
                isbn = st.selectbox(
                    "Select Book (Available)", 
                    options=available_books_df['ISBN'],
                    format_func=lambda x: f"{available_books_df.set_index('ISBN').loc[x, 'Title']} by {available_books_df.set_index('ISBN').loc[x, 'Author']}"
                )
            
            checkout_submitted = st.form_submit_button("Check Out", type="primary")

            if checkout_submitted and member_id and isbn:
                with conn.session as s:
                    json_isbns = s.execute(
                        text("SELECT Checked_Out_ISBNs FROM members WHERE Member_ID = :id"),
                        params={"id": member_id}
                    ).scalar()
                    isbns = json.loads(json_isbns)
                    
                    if isbn in isbns:
                        st.error("This member already has this book checked out.")
                    elif len(isbns) >= MAX_CHECKOUT_LIMIT:
                        st.error(f"Member has reached the checkout limit of {MAX_CHECKOUT_LIMIT} books.")
                    else:
                        isbns.append(isbn)
                        new_json_isbns = json.dumps(isbns)
                        
                        s.execute(
                            text("UPDATE members SET Checked_Out_ISBNs = :json_isbns WHERE Member_ID = :id"),
                            params={"json_isbns": new_json_isbns, "id": member_id}
                        )
                        s.execute(
                            text("UPDATE books SET Available = Available - 1 WHERE ISBN = :isbn"),
                            params={"isbn": isbn}
                        )
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
                format_func=format_member_name,
                key="return_member_select"
            )
            
            books_to_return_options = []
            if member_id_return:
                json_isbns_result = conn.query(
                    "SELECT Checked_Out_ISBNs FROM members WHERE Member_ID = :id",
                    params={"id": member_id_return},
                    ttl=5
                )
                if not json_isbns_result.empty:
                    json_isbns = json_isbns_result.iloc[0,0]
                    books_to_return_options = json.loads(json_isbns)
            
            if not books_to_return_options:
                st.info("This member has no books checked out.")
                isbn_return = None
            else:
                isbn_return = st.selectbox(
                    "Select Book to Return",
                    options=books_to_return_options,
                    format_func=lambda x: f"{books_df.set_index('ISBN').loc[x, 'Title']} by {books_df.set_index('ISBN').loc[x, 'Author']}"
                )
            
            return_submitted = st.form_submit_button("Return Book")

            if return_submitted and member_id_return and isbn_return:
                with conn.session as s:
                    json_isbns = s.execute(
                        text("SELECT Checked_Out_ISBNs FROM members WHERE Member_ID = :id"),
                        params={"id": member_id_return}
                    ).scalar()
                    
                    isbns = json.loads(json_isbns)
                    if isbn_return not in isbns:
                        st.error("Book not found in member's checked out list. Refreshing.")
                        st.rerun()
                    else:
                        isbns.remove(isbn_return)
                        new_json_isbns = json.dumps(isbns)
                        
                        s.execute(
                            text("UPDATE members SET Checked_Out_ISBNs = :json_isbns WHERE Member_ID = :id"),
                            params={"json_isbns": new_json_isbns, "id": member_id_return}
                        )
                        s.execute(
                            text("UPDATE books SET Available = Available + 1 WHERE ISBN = :isbn"),
                            params={"isbn": isbn_return}
                        )
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
    st.session_state.current_page = "🏠 Home" # Add this line

if not st.session_state.logged_in:
    show_login_page()
else:
    # --- Sidebar Navigation ---
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    st.sidebar.markdown(f"Role: **{st.session_state.user_role.capitalize()}**")
    
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    st.sidebar.divider()
    st.sidebar.header("Navigation")

    # Define pages based on role
    if st.session_state.user_role == 'admin':
        PAGES = {
            "🏠 Home": page_home,
            "📖 Book Catalog": page_book_catalog,
            "🔄 Transactions": page_transactions,
            "🛡️ Admin Panel": page_admin_panel
        }
    else:  # 'member'
        PAGES = {
            "🏠 Home": page_home,
            "📖 Book Catalog": page_book_catalog,
            "🔄 Transactions": page_transactions
        }

    # Replace radio buttons with modern buttons
    for page_name, page_fn in PAGES.items():
        # Add a subtle visual cue for the active page
        button_type = "primary" if st.session_state.current_page == page_name else "secondary"
        if st.sidebar.button(page_name, use_container_width=True, type=button_type):
            st.session_state.current_page = page_name
            st.rerun() # Rerun to reflect the page change immediately
    
    st.sidebar.divider()
    st.sidebar.info("Made with 📚 Streamlit")

    # Display the selected page
    page_function = PAGES[st.session_state.current_page]
    page_function()

