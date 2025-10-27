import streamlit as st
import pandas as pd
import uuid # To generate unique member IDs

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Zenith Library Management",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- HELPER FUNCTIONS ---

def initialize_data():
    """Initializes session state with sample data if it doesn't exist."""
    if 'books' not in st.session_state:
        # Sample book data
        sample_books = {
            'ISBN': ['978-0321765723', '978-0132354181', '978-0743273565', '978-1982137138'],
            'Title': ['The Lord of the Rings', 'Clean Code', 'The Great Gatsby', 'The Seven Husbands of Evelyn Hugo'],
            'Author': ['J.R.R. Tolkien', 'Robert C. Martin', 'F. Scott Fitzgerald', 'Taylor Jenkins Reid'],
            'Genre': ['Fantasy', 'Software', 'Classic', 'Fiction'],
            'Total Quantity': [5, 3, 4, 2],
            'Available': [5, 3, 4, 2] # Initially, all books are available
        }
        st.session_state.books = pd.DataFrame(sample_books)
        st.session_state.books.set_index('ISBN', inplace=True)

    if 'members' not in st.session_state:
        # Sample member data
        sample_members = {
            'Member ID': ['M-001', 'M-002'],
            'Name': ['Alice Smith', 'Bob Johnson'],
            'Checked Out ISBNs': [[], []] # List to store ISBNs of checked-out books
        }
        st.session_state.members = pd.DataFrame(sample_members)
        st.session_state.members.set_index('Member ID', inplace=True)

# --- PAGE 1: HOME/DASHBOARD ---

def page_home():
    st.title("📚 Zenith Library Dashboard")
    st.markdown("Welcome to the Zenith Library Management System. Use the sidebar to navigate.")

    total_books = st.session_state.books['Total Quantity'].sum()
    available_books = st.session_state.books['Available'].sum()
    total_members = len(st.session_state.members)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Book Titles", len(st.session_state.books))
    col2.metric("Total Book Copies", f"{available_books} / {total_books}")
    col3.metric("Total Members", total_members)

    st.divider()

    st.subheader("Available Books")
    available_df = st.session_state.books[st.session_state.books['Available'] > 0]
    st.dataframe(available_df, use_container_width=True)

# --- PAGE 2: BOOK MANAGEMENT ---

def page_book_management():
    st.title("📖 Book Management")

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
                elif isbn in st.session_state.books.index:
                    st.error(f"ISBN {isbn} already exists. Please use a unique ISBN.")
                else:
                    new_book_data = {
                        'Title': title,
                        'Author': author,
                        'Genre': genre,
                        'Total Quantity': quantity,
                        'Available': quantity
                    }
                    new_book_df = pd.DataFrame(new_book_data, index=[isbn])
                    st.session_state.books = pd.concat([st.session_state.books, new_book_df])
                    st.success(f"Book '{title}' by {author} added successfully!")
                    st.rerun()

    st.divider()
    
    st.subheader("Manage Existing Books")
    if st.session_state.books.empty:
        st.warning("No books in the library. Add some books above.")
        return

    # Search and Filter
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search_term = st.text_input("Search by Title or Author", placeholder="Search...")
    with filter_col:
        genre_filter = st.selectbox("Filter by Genre", options=["All"] + sorted(st.session_state.books['Genre'].unique()))

    # Apply filters
    filtered_books = st.session_state.books
    if search_term:
        filtered_books = filtered_books[
            filtered_books['Title'].str.contains(search_term, case=False) |
            filtered_books['Author'].str.contains(search_term, case=False)
        ]
    if genre_filter != "All":
        filtered_books = filtered_books[filtered_books['Genre'] == genre_filter]

    st.dataframe(filtered_books, use_container_width=True)

    # Edit/Delete Section
    st.subheader("Edit or Remove Book")
    isbn_to_manage = st.selectbox(
        "Select Book (by ISBN) to Manage", 
        options=st.session_state.books.index,
        format_func=lambda x: f"{x} - {st.session_state.books.loc[x, 'Title']}"
    )

    if isbn_to_manage:
        book_data = st.session_state.books.loc[isbn_to_manage]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Title:** {book_data['Title']}")
            st.markdown(f"**Author:** {book_data['Author']}")
            
            # Edit Quantity
            new_total_quantity = st.number_input(
                "Update Total Quantity", 
                min_value=book_data['Total Quantity'] - book_data['Available'], # Cannot be less than books checked out
                value=book_data['Total Quantity']
            )
            if st.button("Update Quantity"):
                # Calculate new available count
                checked_out_count = book_data['Total Quantity'] - book_data['Available']
                new_available = new_total_quantity - checked_out_count
                
                st.session_state.books.at[isbn_to_manage, 'Total Quantity'] = new_total_quantity
                st.session_state.books.at[isbn_to_manage, 'Available'] = new_available
                st.success("Quantity updated!")
                st.rerun()
        
        with col2:
            st.markdown(f"**Genre:** {book_data['Genre']}")
            st.markdown(f"**Available:** {book_data['Available']} / {book_data['Total Quantity']}")
            
            # Delete Book
            if st.button("Remove Book from Library", type="primary"):
                if book_data['Available'] < book_data['Total Quantity']:
                    st.error("Cannot remove book. Some copies are still checked out.")
                else:
                    st.session_state.books = st.session_state.books.drop(index=isbn_to_manage)
                    st.success("Book removed!")
                    st.rerun()

# --- PAGE 3: MEMBER MANAGEMENT ---

def page_member_management():
    st.title("🧑‍🤝‍🧑 Member Management")

    with st.expander("Register New Member", expanded=False):
        with st.form("add_member_form", clear_on_submit=True):
            name = st.text_input("Member Name")
            submitted = st.form_submit_button("Register Member")

            if submitted:
                if not name:
                    st.error("Please enter a name.")
                else:
                    # Generate a unique member ID
                    member_id = f"M-{uuid.uuid4().hex[:6].upper()}"
                    new_member_data = {
                        'Name': name,
                        'Checked Out ISBNs': [[]] # Initialize with an empty list
                    }
                    new_member_df = pd.DataFrame(new_member_data, index=[member_id])
                    
                    # Ensure the list is stored as an object
                    st.session_state.members = pd.concat([st.session_state.members, new_member_df])
                    st.session_state.members['Checked Out ISBNs'] = st.session_state.members['Checked Out ISBNs'].astype('object')

                    st.success(f"Member '{name}' registered with ID: {member_id}")
                    st.rerun()

    st.divider()

    st.subheader("Current Members")
    if st.session_state.members.empty:
        st.warning("No members registered.")
        return

    # Display members, formatting the list of ISBNs
    members_display = st.session_state.members.copy()
    members_display['Checked Out ISBNs'] = members_display['Checked Out ISBNs'].apply(lambda x: ", ".join(x) if x else "None")
    members_display.rename(columns={'Checked Out ISBNs': 'Books Checked Out'}, inplace=True)
    st.dataframe(members_display, use_container_width=True)

    # Remove Member Section
    st.subheader("Remove Member")
    member_to_remove = st.selectbox(
        "Select Member to Remove", 
        options=st.session_state.members.index,
        format_func=lambda x: f"{x} - {st.session_state.members.loc[x, 'Name']}"
    )

    if member_to_remove:
        member_data = st.session_state.members.loc[member_to_remove]
        
        if st.button("Remove Member", type="primary"):
            if member_data['Checked Out ISBNs']: # Check if list is not empty
                st.error("Cannot remove member. They still have books checked out.")
            else:
                st.session_state.members = st.session_state.members.drop(index=member_to_remove)
                st.success(f"Member {member_data['Name']} removed.")
                st.rerun()

# --- PAGE 4: TRANSACTIONS (CHECK OUT / RETURN) ---

def page_transactions():
    st.title("🔄 Book Transactions")

    if st.session_state.books.empty or st.session_state.members.empty:
        st.warning("Please add books and members before managing transactions.")
        return

    col1, col2 = st.columns(2)

    # --- Check Out Section ---
    with col1:
        st.subheader("Check Out Book")
        with st.form("checkout_form", clear_on_submit=True):
            member_id = st.selectbox(
                "Select Member", 
                options=st.session_state.members.index,
                format_func=lambda x: f"{x} - {st.session_state.members.loc[x, 'Name']}"
            )
            
            # Only show available books
            available_books = st.session_state.books[st.session_state.books['Available'] > 0]
            isbn = st.selectbox(
                "Select Book (Available)", 
                options=available_books.index,
                format_func=lambda x: f"{x} - {available_books.loc[x, 'Title']}"
            )
            
            checkout_submitted = st.form_submit_button("Check Out")

            if checkout_submitted:
                if not member_id or not isbn:
                    st.error("Please select a member and a book.")
                else:
                    # Check if member already has this book
                    member_books = st.session_state.members.at[member_id, 'Checked Out ISBNs']
                    if isbn in member_books:
                        st.error("This member already has this book checked out.")
                    else:
                        # 1. Decrement book availability
                        st.session_state.books.at[isbn, 'Available'] -= 1
                        
                        # 2. Add book to member's list
                        member_books.append(isbn)
                        st.session_state.members.at[member_id, 'Checked Out ISBNs'] = member_books
                        
                        st.success(f"Book '{st.session_state.books.at[isbn, 'Title']}' checked out to {st.session_state.members.at[member_id, 'Name']}.")
                        st.rerun()

    # --- Return Section ---
    with col2:
        st.subheader("Return Book")
        with st.form("return_form", clear_on_submit=True):
            # Select member first to filter books
            member_id_return = st.selectbox(
                "Select Member Returning Book", 
                options=st.session_state.members.index,
                format_func=lambda x: f"{x} - {st.session_state.members.loc[x, 'Name']}",
                key="return_member_select"
            )
            
            books_to_return = []
            if member_id_return:
                books_to_return = st.session_state.members.at[member_id_return, 'Checked Out ISBNs']
            
            if not books_to_return:
                st.info("This member has no books checked out.")
                isbn_return = None
            else:
                isbn_return = st.selectbox(
                    "Select Book to Return",
                    options=books_to_return,
                    format_func=lambda x: f"{x} - {st.session_state.books.loc[x, 'Title']}"
                )
            
            return_submitted = st.form_submit_button("Return Book")

            if return_submitted:
                if not member_id_return or not isbn_return:
                    st.error("Please select a member and a book to return.")
                else:
                    # 1. Increment book availability
                    st.session_state.books.at[isbn_return, 'Available'] += 1
                    
                    # 2. Remove book from member's list
                    member_books = st.session_state.members.at[member_id_return, 'Checked Out ISBNs']
                    member_books.remove(isbn_return)
                    st.session_state.members.at[member_id_return, 'Checked Out ISBNs'] = member_books
                    
                    st.success(f"Book '{st.session_state.books.at[isbn_return, 'Title']}' returned by {st.session_state.members.at[member_id_return, 'Name']}.")
                    st.rerun()


# --- MAIN APP LOGIC ---

# Initialize data on first run
initialize_data()

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Home", "📖 Book Management", "🧑‍🤝‍🧑 Member Management", "🔄 Transactions"]
)

st.sidebar.divider()
st.sidebar.markdown("Made with [Streamlit](https.streamlit.io)")

# Page routing
if page == "🏠 Home":
    page_home()
elif page == "📖 Book Management":
    page_book_management()
elif page == "🧑‍🤝‍🧑 Member Management":
    page_member_management()
elif page == "🔄 Transactions":
    page_transactions()
