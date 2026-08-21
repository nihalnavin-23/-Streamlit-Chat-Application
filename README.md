# 💬 Streamlit Chat Application

A real-time chat application built with Python, Streamlit, and SQLite. Features user authentication, one-on-one messaging, message delivery status tracking, and unread message notifications.

## ✨ Features

- **User Authentication**: Secure registration and login system with password hashing (SHA-256)
- **Real-time Messaging**: Send and receive messages instantly
- **Message Status Tracking**: 
  - 🕒 Sent (message sent but not yet delivered)
  - ✓ Delivered (message delivered to recipient)
  - ✓✓ Read (recipient has read the message)
- **Unread Message Indicators**: Red dot notification with count for unread messages
- **User List**: See all registered users in the sidebar
- **Chat History**: View complete conversation history
- **Responsive UI**: Clean, modern interface built with Streamlit

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/streamlit-chat-app.git
cd streamlit-chat-app
