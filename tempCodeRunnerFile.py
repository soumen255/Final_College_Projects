import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import csv
import os
import hashlib
import secrets

class ProfessionalCollegeGradeSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Bytebot's College Grade Management System")
        self.root.geometry("1500x900")
        self.root.state('zoomed')  # Start maximized
        
        # Security variables
        self.logged_in = False
        self.admin_username = ""
        self.login_attempts = 0
        self.max_login_attempts = 3
        self.locked_out = False
        
        # Style configuration
        self.setup_styles()
        
        # Initialize database (including security tables)
        self.init_database()
        
        # Show login screen first
        self.show_login_screen()
        
    def show_login_screen(self):
        """Display the login screen"""
        self.login_frame = ttk.Frame(self.root, padding="50")
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(self.login_frame, text="🔒 College Grade Management System", 
                               font=('Arial', 20, 'bold'), foreground='#2c3e50')
        title_label.pack(pady=20)
        
        subtitle_label = ttk.Label(self.login_frame, text="Administrator Login Required", 
                                  font=('Arial', 12), foreground='#7f8c8d')
        subtitle_label.pack(pady=5)
        
        # Login container
        login_container = ttk.LabelFrame(self.login_frame, text="Admin Authentication", padding="30")
        login_container.pack(pady=30, ipadx=20, ipady=20)
        
        # Username
        ttk.Label(login_container, text="Username:", font=('Arial', 11)).grid(row=0, column=0, sticky=tk.W, pady=10, padx=5)
        self.username_entry = ttk.Entry(login_container, width=25, font=('Arial', 11))
        self.username_entry.grid(row=0, column=1, pady=10, padx=10, sticky=(tk.W, tk.E))
        self.username_entry.focus()
        
        # Password
        ttk.Label(login_container, text="Password:", font=('Arial', 11)).grid(row=1, column=0, sticky=tk.W, pady=10, padx=5)
        self.password_entry = ttk.Entry(login_container, width=25, font=('Arial', 11), show="•")
        self.password_entry.grid(row=1, column=1, pady=10, padx=10, sticky=(tk.W, tk.E))
        
        # Bind Enter key to login
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Buttons
        button_frame = ttk.Frame(login_container)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="🔑 Login", command=self.login, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="🔄 Reset Password", command=self.show_reset_dialog).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Exit", command=self.root.quit).pack(side=tk.LEFT, padx=10)
        
        # Status label
        self.login_status_label = ttk.Label(login_container, text="", foreground="red")
        self.login_status_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Configure grid weights
        login_container.columnconfigure(1, weight=1)
        
        # Security notice
        notice_label = ttk.Label(self.login_frame, 
                                text="⚠️ Unauthorized access is prohibited. All activities are logged.",
                                font=('Arial', 9), foreground='#e74c3c')
        notice_label.pack(pady=20)
        
    def show_reset_dialog(self):
        """Show password reset dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reset Admin Password")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="🔐 Password Reset", font=('Arial', 14, 'bold')).pack(pady=20)
        
        # Security question frame
        security_frame = ttk.LabelFrame(dialog, text="Security Verification", padding="15")
        security_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(security_frame, text="Security Question:").pack(anchor=tk.W)
        security_question = ttk.Label(security_frame, text="What is the default admin password?", 
                                    font=('Arial', 9, 'italic'))
        security_question.pack(anchor=tk.W, pady=5)
        
        ttk.Label(security_frame, text="Answer:").pack(anchor=tk.W, pady=(10,0))
        security_answer = ttk.Entry(security_frame, width=30, show="•")
        security_answer.pack(fill=tk.X, pady=5)
        
        # New password frame
        new_pass_frame = ttk.LabelFrame(dialog, text="New Password", padding="15")
        new_pass_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(new_pass_frame, text="New Password:").pack(anchor=tk.W)
        new_password = ttk.Entry(new_pass_frame, width=30, show="•")
        new_password.pack(fill=tk.X, pady=5)
        
        ttk.Label(new_pass_frame, text="Confirm Password:").pack(anchor=tk.W, pady=(10,0))
        confirm_password = ttk.Entry(new_pass_frame, width=30, show="•")
        confirm_password.pack(fill=tk.X, pady=5)
        
        # Status label
        status_label = ttk.Label(dialog, text="", foreground="red")
        status_label.pack(pady=10)
        
        def reset_password():
            answer = security_answer.get().strip()
            new_pass = new_password.get().strip()
            confirm_pass = confirm_password.get().strip()
            
            if not all([answer, new_pass, confirm_pass]):
                status_label.config(text="Please fill all fields!")
                return
            
            if new_pass != confirm_pass:
                status_label.config(text="Passwords do not match!")
                return
            
            if len(new_pass) < 4:
                status_label.config(text="Password must be at least 4 characters!")
                return
            
            # Check security answer (default admin password is "admin123")
            if answer != "admin123":
                status_label.config(text="Security answer incorrect!")
                return
            
            # Reset password
            salt = secrets.token_hex(16)
            hashed_password = hashlib.sha256((new_pass + salt).encode()).hexdigest()
            
            self.cursor.execute('''
                UPDATE admin_users SET password_hash=?, salt=?, last_password_change=?
                WHERE username='admin'
            ''', (hashed_password, salt, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            self.conn.commit()
            
            # Log the password reset
            self.log_security_event("PASSWORD_RESET", f"Password reset for admin user")
            
            messagebox.showinfo("Success", "Password reset successfully!\nYou can now login with the new password.")
            dialog.destroy()
        
        ttk.Button(dialog, text="🔄 Reset Password", command=reset_password).pack(pady=10)
        ttk.Button(dialog, text="❌ Cancel", command=dialog.destroy).pack(pady=5)
        
    def login(self):
        """Handle login authentication"""
        if self.locked_out:
            self.login_status_label.config(text="Account locked. Please contact system administrator.")
            return
        
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.login_status_label.config(text="Please enter both username and password!")
            return
        
        # Get user from database
        self.cursor.execute('''
            SELECT username, password_hash, salt, is_locked 
            FROM admin_users WHERE username=?
        ''', (username,))
        
        user = self.cursor.fetchone()
        
        if not user:
            self.login_attempts += 1
            self.log_security_event("LOGIN_FAILED", f"Failed login attempt for non-existent user: {username}")
            self.login_status_label.config(text="Invalid username or password!")
            self.check_lockout()
            return
        
        db_username, db_password_hash, salt, is_locked = user
        
        if is_locked:
            self.login_status_label.config(text="Account locked. Please contact system administrator.")
            self.locked_out = True
            return
        
        # Verify password
        hashed_input = hashlib.sha256((password + salt).encode()).hexdigest()
        
        if hashed_input == db_password_hash:
            # Successful login
            self.logged_in = True
            self.admin_username = username
            self.login_attempts = 0
            
            # Update last login
            self.cursor.execute('''
                UPDATE admin_users SET last_login=?, login_attempts=0 
                WHERE username=?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
            self.conn.commit()
            
            # Log successful login
            self.log_security_event("LOGIN_SUCCESS", f"Successful login for user: {username}")
            
            # Destroy login frame and show main application
            self.login_frame.destroy()
            self.setup_main_application()
            
        else:
            # Failed login
            self.login_attempts += 1
            self.cursor.execute('''
                UPDATE admin_users SET login_attempts=login_attempts+1 
                WHERE username=?
            ''', (username,))
            self.conn.commit()
            
            self.log_security_event("LOGIN_FAILED", f"Failed login attempt for user: {username}")
            self.login_status_label.config(text=f"Invalid username or password! Attempts: {self.login_attempts}/{self.max_login_attempts}")
            self.check_lockout()
    
    def check_lockout(self):
        """Check if account should be locked due to failed attempts"""
        if self.login_attempts >= self.max_login_attempts:
            self.locked_out = True
            username = self.username_entry.get().strip()
            
            # Lock the account in database
            self.cursor.execute('''
                UPDATE admin_users SET is_locked=1, lockout_time=?
                WHERE username=?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
            self.conn.commit()
            
            self.log_security_event("ACCOUNT_LOCKED", f"Account locked due to failed login attempts: {username}")
            self.login_status_label.config(text="Account locked! Too many failed attempts.")
    
    def setup_main_application(self):
        """Setup the main application after successful login"""
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with user info and logout button
        self.create_header()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.department_tab = ttk.Frame(self.notebook)
        self.section_tab = ttk.Frame(self.notebook)
        self.subject_tab = ttk.Frame(self.notebook)
        self.student_tab = ttk.Frame(self.notebook)
        self.theory_grade_tab = ttk.Frame(self.notebook)
        self.practical_grade_tab = ttk.Frame(self.notebook)
        self.student_report_tab = ttk.Frame(self.notebook)
        self.admin_tab = ttk.Frame(self.notebook)  # New admin tab
        
        self.notebook.add(self.department_tab, text="🏛️ Department Setup")
        self.notebook.add(self.section_tab, text="📁 Section Management")
        self.notebook.add(self.subject_tab, text="📚 Subject Management")
        self.notebook.add(self.student_tab, text="👨‍🎓 Student Management")
        self.notebook.add(self.theory_grade_tab, text="📖 Theory Grade Entry")
        self.notebook.add(self.practical_grade_tab, text="🔬 Practical Grade Entry")
        self.notebook.add(self.student_report_tab, text="📊 Student Report")
        self.notebook.add(self.admin_tab, text="⚙️ Admin Settings")  # New admin tab
        
        # Setup all tabs
        self.setup_department_tab()
        self.setup_section_tab()
        self.setup_subject_tab()
        self.setup_student_tab()
        self.setup_theory_grade_tab()
        self.setup_practical_grade_tab()
        self.setup_student_report_tab()
        self.setup_admin_tab()  # Setup admin tab
        
        # Load initial data
        self.load_departments()
        self.load_sections()
        self.load_subjects()
        self.load_students()
        
    def create_header(self):
        """Create header with user info and controls"""
        header_frame = ttk.Frame(self.main_frame, relief='raised', borderwidth=1)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Welcome message
        welcome_label = ttk.Label(header_frame, text=f"👤 Welcome, {self.admin_username}", 
                                font=('Arial', 12, 'bold'))
        welcome_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Current time
        self.time_label = ttk.Label(header_frame, text="", font=('Arial', 10))
        self.time_label.pack(side=tk.LEFT, padx=10, pady=5)
        self.update_time()
        
        # Logout button
        logout_btn = ttk.Button(header_frame, text="🚪 Logout", command=self.logout)
        logout_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Security events button
        security_btn = ttk.Button(header_frame, text="📋 Security Log", command=self.show_security_log)
        security_btn.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def update_time(self):
        """Update current time in header"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def logout(self):
        """Handle user logout"""
        result = messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?")
        if result:
            # Log the logout event
            self.log_security_event("LOGOUT", f"User {self.admin_username} logged out")
            
            # Destroy main application and show login screen
            self.main_frame.destroy()
            self.logged_in = False
            self.admin_username = ""
            self.login_attempts = 0
            self.locked_out = False
            self.show_login_screen()
    
    def setup_styles(self):
        """Configure modern styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Warning.TLabel', foreground='orange')
        style.configure('Error.TLabel', foreground='red')
        
        # Configure buttons
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        style.configure('Primary.TButton', background='#0078D7', foreground='white')
        
    def init_database(self):
        """Initialize SQLite database with professional structure and security tables"""
        self.conn = sqlite3.connect('professional_college_system.db')
        self.cursor = self.conn.cursor()
        
        # Create admin users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                is_locked INTEGER DEFAULT 0,
                login_attempts INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                last_password_change TIMESTAMP,
                lockout_time TIMESTAMP,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create security logs table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                username TEXT,
                ip_address TEXT DEFAULT 'localhost',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create departments table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                dept_id TEXT PRIMARY KEY,
                dept_name TEXT NOT NULL,
                hod_name TEXT,
                established_year INTEGER,
                total_students INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sections table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sections (
                section_id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_name TEXT NOT NULL,
                department TEXT NOT NULL,
                semester INTEGER NOT NULL,
                batch INTEGER NOT NULL,
                class_teacher TEXT,
                room_number TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department) REFERENCES departments(dept_id),
                UNIQUE(section_name, department, semester, batch)
            )
        ''')
        
        # Create subjects table with enhanced fields if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_code TEXT UNIQUE NOT NULL,
                subject_name TEXT NOT NULL,
                credits INTEGER NOT NULL,
                semester INTEGER NOT NULL,
                department TEXT NOT NULL,
                subject_type TEXT NOT NULL,  -- Theory/Practical
                max_marks INTEGER DEFAULT 100,
                min_pass_marks INTEGER DEFAULT 40,
                teaching_hours INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department) REFERENCES departments(dept_id)
            )
        ''')
        
        # Create students table with section field if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                batch INTEGER NOT NULL,
                current_semester INTEGER DEFAULT 1,
                section TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                blood_group TEXT,
                admission_date DATE,
                status TEXT DEFAULT 'Active',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department) REFERENCES departments(dept_id),
                FOREIGN KEY (section) REFERENCES sections(section_name)
            )
        ''')
        
        # Create theory grades table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS theory_grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                subject_code TEXT NOT NULL,
                semester INTEGER NOT NULL,
                academic_year TEXT,
                internal1_marks REAL DEFAULT 0,    -- First Internal (20 marks)
                internal2_marks REAL DEFAULT 0,    -- Second Internal (20 marks)
                presentation_marks REAL DEFAULT 0, -- Presentation (10 marks)
                assignment1_marks REAL DEFAULT 0,  -- Assignment 1 (5 marks)
                assignment2_marks REAL DEFAULT 0,  -- Assignment 2 (5 marks)
                external_marks REAL DEFAULT 0,     -- External (60 marks)
                total_marks REAL DEFAULT 0,
                grade TEXT,
                grade_point REAL DEFAULT 0,
                result_status TEXT,
                back_paper INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (subject_code) REFERENCES subjects(subject_code),
                UNIQUE(student_id, subject_code, semester)
            )
        ''')
        
        # Create practical grades table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS practical_grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                subject_code TEXT NOT NULL,
                semester INTEGER NOT NULL,
                academic_year TEXT,
                lab_copies_marks REAL DEFAULT 0,    -- Lab Copies (20 marks)
                viva_marks REAL DEFAULT 0,          -- Viva (20 marks)
                practical_exam_marks REAL DEFAULT 0, -- Practical Exam (60 marks)
                total_marks REAL DEFAULT 0,
                grade TEXT,
                grade_point REAL DEFAULT 0,
                result_status TEXT,
                back_paper INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (subject_code) REFERENCES subjects(subject_code),
                UNIQUE(student_id, subject_code, semester)
            )
        ''')
        
        self.conn.commit()
        
        # Initialize admin user if not exists
        self.initialize_admin_user()
        
        # Check if database is empty and insert sample data only if needed
        self.insert_sample_data_if_empty()
    
    def initialize_admin_user(self):
        """Initialize default admin user if not exists"""
        self.cursor.execute("SELECT COUNT(*) FROM admin_users WHERE username='admin'")
        admin_count = self.cursor.fetchone()[0]
        
        if admin_count == 0:
            # Create default admin user with password "admin123"
            salt = secrets.token_hex(16)
            default_password = "admin123"
            hashed_password = hashlib.sha256((default_password + salt).encode()).hexdigest()
            
            self.cursor.execute('''
                INSERT INTO admin_users 
                (username, password_hash, salt, full_name, email, last_password_change)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', hashed_password, salt, 'System Administrator', 'admin@college.edu', 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            self.conn.commit()
            print("Default admin user created with password: admin123")
    
    def log_security_event(self, event_type, description):
        """Log security events to database"""
        try:
            self.cursor.execute('''
                INSERT INTO security_logs (event_type, description, username)
                VALUES (?, ?, ?)
            ''', (event_type, description, self.admin_username if hasattr(self, 'admin_username') else 'Unknown'))
            self.conn.commit()
        except Exception as e:
            print(f"Error logging security event: {e}")
    
    def setup_admin_tab(self):
        """Setup admin settings and security tab"""
        main_frame = ttk.Frame(self.admin_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for admin settings
        admin_notebook = ttk.Notebook(main_frame)
        admin_notebook.pack(fill=tk.BOTH, expand=True)
        
        # User Management Tab
        user_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(user_tab, text="👥 User Management")
        
        # Security Logs Tab
        security_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(security_tab, text="📋 Security Logs")
        
        # System Info Tab
        system_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(system_tab, text="⚙️ System Info")
        
        self.setup_user_management_tab(user_tab)
        self.setup_security_logs_tab(security_tab)
        self.setup_system_info_tab(system_tab)
    
    def setup_user_management_tab(self, parent):
        """Setup user management section"""
        # Left frame - User form
        left_frame = ttk.LabelFrame(parent, text="User Information", padding="15")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(left_frame, text="Username *:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.admin_username_entry = ttk.Entry(left_frame, width=25, font=('Arial', 10))
        self.admin_username_entry.grid(row=0, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Full Name:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.admin_fullname_entry = ttk.Entry(left_frame, width=30, font=('Arial', 10))
        self.admin_fullname_entry.grid(row=1, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Email:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.admin_email_entry = ttk.Entry(left_frame, width=30, font=('Arial', 10))
        self.admin_email_entry.grid(row=2, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="New Password:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.admin_password_entry = ttk.Entry(left_frame, width=25, font=('Arial', 10), show="•")
        self.admin_password_entry.grid(row=3, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Confirm Password:", font=('Arial', 10)).grid(row=4, column=0, sticky=tk.W, pady=8)
        self.admin_confirm_entry = ttk.Entry(left_frame, width=25, font=('Arial', 10), show="•")
        self.admin_confirm_entry.grid(row=4, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="➕ Add User", command=self.add_admin_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Update User", command=self.update_admin_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔓 Unlock User", command=self.unlock_admin_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Delete User", command=self.delete_admin_user).pack(side=tk.LEFT, padx=5)
        
        # Right frame - User list
        right_frame = ttk.LabelFrame(parent, text="Admin Users", padding="15")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for admin users
        columns = ("username", "full_name", "email", "last_login", "login_attempts", "is_locked")
        self.admin_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        
        headings = {
            "username": "Username",
            "full_name": "Full Name",
            "email": "Email",
            "last_login": "Last Login",
            "login_attempts": "Login Attempts",
            "is_locked": "Locked"
        }
        
        for col, text in headings.items():
            self.admin_tree.heading(col, text=text)
            self.admin_tree.column(col, width=100)
        
        self.admin_tree.column("username", width=120)
        self.admin_tree.column("full_name", width=150)
        self.admin_tree.column("email", width=150)
        self.admin_tree.column("last_login", width=150)
        
        self.admin_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.admin_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.admin_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.admin_tree.bind("<<TreeviewSelect>>", self.on_admin_user_select)
        
        # Load admin users
        self.load_admin_users()
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
    
    def setup_security_logs_tab(self, parent):
        """Setup security logs viewer"""
        # Filter frame
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Event Type:").pack(side=tk.LEFT, padx=5)
        self.event_type_combo = ttk.Combobox(filter_frame, width=15, 
                                           values=["All", "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT", 
                                                  "PASSWORD_RESET", "ACCOUNT_LOCKED", "USER_CREATED", 
                                                  "USER_DELETED"])
        self.event_type_combo.pack(side=tk.LEFT, padx=5)
        self.event_type_combo.set("All")
        
        ttk.Label(filter_frame, text="Date From:").pack(side=tk.LEFT, padx=5)
        self.date_from_entry = ttk.Entry(filter_frame, width=12)
        self.date_from_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.date_to_entry = ttk.Entry(filter_frame, width=12)
        self.date_to_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="🔍 Filter", command=self.load_security_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="🔄 Clear", command=self.clear_security_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="📤 Export Logs", command=self.export_security_logs).pack(side=tk.LEFT, padx=5)
        
        # Treeview for security logs
        columns = ("timestamp", "event_type", "username", "description")
        self.security_tree = ttk.Treeview(parent, columns=columns, show="headings", height=20)
        
        headings = {
            "timestamp": "Timestamp",
            "event_type": "Event Type",
            "username": "Username",
            "description": "Description"
        }
        
        for col, text in headings.items():
            self.security_tree.heading(col, text=text)
            self.security_tree.column(col, width=150)
        
        self.security_tree.column("description", width=300)
        self.security_tree.column("timestamp", width=180)
        
        self.security_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.security_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.security_tree.configure(yscrollcommand=scrollbar.set)
        
        # Load security logs
        self.load_security_logs()
    
    def setup_system_info_tab(self, parent):
        """Setup system information tab"""
        info_frame = ttk.LabelFrame(parent, text="System Information", padding="20")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Database info
        ttk.Label(info_frame, text="Database Information", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        # Get database statistics
        stats = self.get_database_stats()
        
        row = 1
        for key, value in stats.items():
            ttk.Label(info_frame, text=f"{key}:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
            ttk.Label(info_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
            row += 1
        
        # System actions
        action_frame = ttk.LabelFrame(parent, text="System Actions", padding="20")
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="🔄 Refresh Statistics", command=self.refresh_system_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="💾 Backup Database", command=self.backup_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🧹 Clear Old Logs", command=self.clear_old_logs).pack(side=tk.LEFT, padx=5)
    
    def load_admin_users(self):
        """Load admin users into treeview"""
        for item in self.admin_tree.get_children():
            self.admin_tree.delete(item)
        
        self.cursor.execute('''
      