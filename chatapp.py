# chat_app_sqlite.py - Working SQLite Version
import streamlit as st
import sqlite3
import hashlib
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Database connection
def get_db_connection():
    """Create a connection to SQLite database"""
    conn = sqlite3.connect('chat_app.db')
    conn.row_factory = sqlite3.Row
    return conn

# Database initialization
def init_db():
    """Initialize database schema"""
    conn = get_db_connection()
    
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Messages table with delivery status
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivered_at TIMESTAMP,
            read_at TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    """)
    
    # Chat rooms/conversations table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users(id),
            FOREIGN KEY (user2_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

# Password hashing
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication functions
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Register a new user"""
    conn = get_db_connection()
    try:
        password_hash = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Optional[int]:
    """Authenticate user and return user ID"""
    conn = get_db_connection()
    try:
        password_hash = hash_password(password)
        cursor = conn.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception:
        return None
    finally:
        conn.close()

def send_message(sender_id: int, receiver_id: int, content: str) -> bool:
    """Send a message to another user"""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
            (sender_id, receiver_id, content)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def mark_message_read(message_id: int):
    """Mark message as read"""
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE messages SET read_at = CURRENT_TIMESTAMP WHERE id = ?",
            (message_id,)
        )
        conn.commit()
    finally:
        conn.close()

def get_conversation(user1_id: int, user2_id: int, limit: int = 50) -> List[Dict]:
    """Get conversation between two users"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT m.id, m.sender_id, m.receiver_id, m.content, 
                   m.sent_at, m.delivered_at, m.read_at,
                   u.username as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.sent_at DESC
            LIMIT ?
            """,
            (user1_id, user2_id, user2_id, user1_id, limit)
        )
        
        messages = []
        for row in cursor:
            messages.append({
                'id': row['id'],
                'sender_id': row['sender_id'],
                'receiver_id': row['receiver_id'],
                'content': row['content'],
                'sent_at': row['sent_at'],
                'delivered_at': row['delivered_at'],
                'read_at': row['read_at'],
                'sender_name': row['sender_name']
            })
        return messages[::-1]  # Reverse to show oldest first
    finally:
        conn.close()

def get_all_users(current_user_id: int) -> List[Dict]:
    """Get all users except current user"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT id, username FROM users WHERE id != ? ORDER BY username",
            (current_user_id,)
        )
        return [{'id': row['id'], 'username': row['username']} for row in cursor]
    finally:
        conn.close()

def get_unread_messages(user_id: int) -> List[Dict]:
    """Get unread messages for a user"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT m.id, m.sender_id, m.receiver_id, m.content, 
                   m.sent_at, u.username as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.receiver_id = ? AND m.read_at IS NULL
            ORDER BY m.sent_at
            """,
            (user_id,)
        )
        
        messages = []
        for row in cursor:
            messages.append({
                'id': row['id'],
                'sender_id': row['sender_id'],
                'receiver_id': row['receiver_id'],
                'content': row['content'],
                'sent_at': row['sent_at'],
                'sender_name': row['sender_name']
            })
        return messages
    finally:
        conn.close()

def mark_all_delivered(user_id: int):
    """Mark all messages to user as delivered"""
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE messages SET delivered_at = CURRENT_TIMESTAMP WHERE receiver_id = ? AND delivered_at IS NULL",
            (user_id,)
        )
        conn.commit()
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT id, username FROM users WHERE id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            return {'id': result['id'], 'username': result['username']}
        return None
    finally:
        conn.close()

def get_unread_count(user_id: int, sender_id: int) -> int:
    """Get count of unread messages from a specific sender"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT COUNT(*) as count FROM messages 
            WHERE sender_id = ? AND receiver_id = ? AND read_at IS NULL
            """,
            (sender_id, user_id)
        )
        result = cursor.fetchone()
        return result['count'] if result else 0
    finally:
        conn.close()

# Streamlit UI
def init_session_state():
    """Initialize session state variables"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'

def login_page():
    """Login page"""
    st.title("💬 Chat App - Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username and password:
                    user_id = authenticate_user(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.page = 'chat'
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if not new_username or not new_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif len(new_username) < 3:
                    st.error("Username must be at least 3 characters")
                else:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.success(message)
                        st.info("Please login with your new account")
                    else:
                        st.error(message)

def chat_page():
    """Main chat page"""
    st.title(f"💬 Chat App - Welcome, {st.session_state.username}!")
    
    # Sidebar for user selection
    with st.sidebar:
        st.header("👥 Users")
        users = get_all_users(st.session_state.user_id)
        
        if users:
            for user in users:
                if user['id'] != st.session_state.user_id:
                    unread_count = get_unread_count(st.session_state.user_id, user['id'])
                    button_label = f"👤 {user['username']}"
                    if unread_count > 0:
                        button_label += f" 🔴({unread_count})"
                    
                    if st.button(button_label, key=f"user_{user['id']}", use_container_width=True):
                        st.session_state.selected_user = user
                        st.rerun()
        else:
            st.info("No other users registered yet")
        
        st.divider()
        
        unread_messages = get_unread_messages(st.session_state.user_id)
        if unread_messages:
            st.warning(f"📬 {len(unread_messages)} unread messages")
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state.page = 'login'
            st.rerun()
    
    # Main chat area
    if st.session_state.selected_user:
        selected_user = st.session_state.selected_user
        st.subheader(f"💬 Chat with {selected_user['username']}")
        
        mark_all_delivered(st.session_state.user_id)
        
        messages = get_conversation(st.session_state.user_id, selected_user['id'])
        
        chat_container = st.container()
        
        with chat_container:
            if messages:
                for msg in messages:
                    is_sender = msg['sender_id'] == st.session_state.user_id
                    
                    if is_sender:
                        with st.chat_message("user"):
                            st.write(msg['content'])
                            status = "✓✓ Read" if msg['read_at'] else ("✓ Delivered" if msg['delivered_at'] else "🕒 Sent")
                            st.caption(f"{msg['sent_at'][:16]} | {status}")
                    else:
                        with st.chat_message("assistant"):
                            st.write(msg['content'])
                            st.caption(f"From: {msg['sender_name']} | {msg['sent_at'][:16]}")
                            if not msg['read_at']:
                                mark_message_read(msg['id'])
            else:
                st.info("No messages yet. Say hello! 👋")
        
        st.divider()
        with st.form("message_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                message = st.text_input("", placeholder="Type your message here...", key="message_input")
            with col2:
                send_button = st.form_submit_button("Send 📤", use_container_width=True)
            
            if send_button and message:
                if send_message(st.session_state.user_id, selected_user['id'], message):
                    st.rerun()
    
    else:
        st.info("👈 Select a user from the sidebar to start chatting")
        
        unread = get_unread_messages(st.session_state.user_id)
        if unread:
            st.subheader("📬 Unread Messages")
            for msg in unread:
                with st.container():
                    st.markdown(f"**From {msg['sender_name']}:**")
                    with st.chat_message("assistant"):
                        st.write(msg['content'])
                        st.caption(msg['sent_at'][:16])
                        
                        sender = get_user_by_id(msg['sender_id'])
                        if sender:
                            if st.button(f"💬 Reply to {msg['sender_name']}", key=f"reply_{msg['id']}"):
                                st.session_state.selected_user = sender
                                st.rerun()
                    st.divider()

def main():
    """Main app"""
    st.set_page_config(
        page_title="Chat App",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    init_db()
    
    # Initialize session state
    init_session_state()
    
    # Route to appropriate page
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'chat':
        if st.session_state.user_id:
            chat_page()
        else:
            st.session_state.page = 'login'
            st.rerun()

if __name__ == "__main__":
    main()