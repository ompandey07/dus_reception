# DUS Reception & Events Booking Management System

A **fully functional, dynamic booking management system** designed for DUS reception and events management. Built to manage bookings, users, and activities efficiently, with separate dashboards for admins and users.

## Developer

**Om Pandey**
GitHub: [https://github.com/ompandey07/dus_reception](https://github.com/ompandey07/dus_reception)

---

## Features

### Admin Dashboard

* View all bookings and activities
* Add, edit, or delete bookings
* Generate reports
* Manage user activities
* Full control over reception and event management

### User Dashboard

* Make new bookings
* View own booking history
* Access personal dashboard with activity overview
* Real-time booking status updates

### General

* Fully dynamic booking system
* Interactive and user-friendly interface
* Responsive design for desktop and mobile

---

## Technology Stack

* **Frontend:** HTML, Tailwind CSS, JavaScript
* **Backend:** Python, Django
* **Database:** PostgreSQL
* **Version Control:** GitHub

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/ompandey07/dus_reception.git
   cd dus_reception
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:

   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

5. **Apply migrations**

   ```bash
   python manage.py migrate
   ```

6. **Run the server**

   ```bash
   python manage.py runserver
   ```

7. **Access the app**
   Open your browser and go to [http://localhost:8000](http://localhost:8000)

---

---

## Contribution

Contributions are welcome! Feel free to fork the repository and submit a pull request.

---

## License

This project is open-source and available under the MIT License.

---

## Contact

**Developer:** Om Pandey
**GitHub:** [https://github.com/ompandey07](https://github.com/ompandey07)
