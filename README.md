# AuraWear - Premium Fashion Rental Platform

AuraWear is a web-based luxury rental application designed to bridge the gap between high-end fashion and accessibility. It allows users to browse and rent premium dresses, suits, and accessories for special occasions, while offering administrators a streamlined interface to manage inventory.

## 🎯 Project Goal
The main goal of AuraWear is to provide a seamless, aesthetically pleasing platform where:
- **Customers** can easily discover and rent luxury fashion items without the commitment of purchasing.
- **Business Owners (Admins)** can efficiently manage their rental catalogue, updating stock and categories in real-time.

## ✨ Key Features

### 👤 User Portal (Customer)
- **Authentication**: Secure Login and Registration system.
- **Browse Collection**: View a curated list of items including Dresses, Jewelry, Men's Wear, and Kids' clothing.
- **Search**: Real-time search functionality to filter items by name.
- **Rental Interface**: Detailed item cards showing price per day and pickup availability.

### 🛡️ Admin Portal
- **Dashboard**: A dedicated control panel for inventory management.
- **Add Inventory**: Simple form to add new items with valid categories, prices, dates, and image URLs.
- **Manage Stock**: View full inventory list and delete outdated items.
- **Category Management**: Organized selection for Men, Women, and Kids.

## 🛠️ Technology Stack
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System).
- **Backend**: Python (Flask Framework).
- **Database**: MongoDB (Atlas) for storing Users and Items.
- **Styling**: Responsive Glassmorphism design with `Outfit` and `Playfair Display` typography.

## 🚀 Getting Started

### Prerequisites
- Python 3.x installed.
- Internet connection (for MongoDB Atlas access).

### Installation
1.  **Clone the repository** (or navigate to the folder).
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You may need to create a `requirements.txt` with `flask`, `pymongo`, `dnspython` first if not present).*
    
3.  **Run the Application**:
    ```bash
    python app.py
    ```

4.  **Access the App**:
    Open your browser and navigate to: `http://127.0.0.1:5000`

## 🔐 Credentials

### Admin Access
To access the Admin Console, use the following default credentials:
- **Username**: `admin@aurawear.com`
- **Password**: `admin123`

### User Access
- You can register a new account on the home page with any email/password.

---
*Designed & Developed for AuraWear.*
