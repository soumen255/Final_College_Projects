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
        self.root.title("Professional College Grade Management System")
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
            SELECT username, full_name, email, last_login, login_attempts, is_locked
            FROM admin_users
            ORDER BY username
        ''')
        
        users = self.cursor.fetchall()
        for user in users:
            # Convert locked status to text
            user_list = list(user)
            user_list[5] = "Yes" if user[5] else "No"
            self.admin_tree.insert("", tk.END, values=user_list)
    
    def load_security_logs(self, event_type="All", date_from=None, date_to=None):
        """Load security logs with filtering"""
        for item in self.security_tree.get_children():
            self.security_tree.delete(item)
        
        query = '''
            SELECT timestamp, event_type, username, description
            FROM security_logs
            WHERE 1=1
        '''
        params = []
        
        event_type_filter = self.event_type_combo.get()
        if event_type_filter != "All":
            query += " AND event_type = ?"
            params.append(event_type_filter)
        
        date_from = self.date_from_entry.get().strip()
        date_to = self.date_to_entry.get().strip()
        
        if date_from:
            query += " AND DATE(timestamp) >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(timestamp) <= ?"
            params.append(date_to)
        
        query += " ORDER BY timestamp DESC LIMIT 1000"
        
        self.cursor.execute(query, params)
        logs = self.cursor.fetchall()
        
        for log in logs:
            self.security_tree.insert("", tk.END, values=log)
    
    def get_database_stats(self):
        """Get database statistics"""
        stats = {}
        
        # Table counts
        tables = ['departments', 'sections', 'subjects', 'students', 'theory_grades', 'practical_grades', 'admin_users', 'security_logs']
        
        for table in tables:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                stats[f"{table.capitalize()}"] = count
            except:
                stats[f"{table.capitalize()}"] = "N/A"
        
        # Database size
        try:
            self.cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            db_size = self.cursor.fetchone()[0]
            stats["Database Size"] = f"{db_size / (1024*1024):.2f} MB"
        except:
            stats["Database Size"] = "Unknown"
        
        # Last backup (placeholder)
        stats["Last Backup"] = "Never"
        
        return stats
    
    def add_admin_user(self):
        """Add new admin user"""
        username = self.admin_username_entry.get().strip()
        full_name = self.admin_fullname_entry.get().strip()
        email = self.admin_email_entry.get().strip()
        password = self.admin_password_entry.get().strip()
        confirm_password = self.admin_confirm_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required!")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return
        
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters!")
            return
        
        # Hash password
        salt = secrets.token_hex(16)
        hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
        
        try:
            self.cursor.execute('''
                INSERT INTO admin_users (username, password_hash, salt, full_name, email, last_password_change)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, salt, full_name, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            self.conn.commit()
            
            # Log the user creation
            self.log_security_event("USER_CREATED", f"New admin user created: {username}")
            
            messagebox.showinfo("Success", "Admin user added successfully!")
            self.load_admin_users()
            self.clear_admin_form()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")
    
    def update_admin_user(self):
        """Update admin user information"""
        username = self.admin_username_entry.get().strip()
        full_name = self.admin_fullname_entry.get().strip()
        email = self.admin_email_entry.get().strip()
        password = self.admin_password_entry.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please select a user to update!")
            return
        
        update_fields = []
        params = []
        
        if full_name:
            update_fields.append("full_name = ?")
            params.append(full_name)
        
        if email:
            update_fields.append("email = ?")
            params.append(email)
        
        if password:
            if len(password) < 4:
                messagebox.showerror("Error", "Password must be at least 4 characters!")
                return
            
            salt = secrets.token_hex(16)
            hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
            
            update_fields.append("password_hash = ?")
            update_fields.append("salt = ?")
            update_fields.append("last_password_change = ?")
            params.extend([hashed_password, salt, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        
        if not update_fields:
            messagebox.showinfo("Info", "No changes to update!")
            return
        
        update_query = f"UPDATE admin_users SET {', '.join(update_fields)} WHERE username = ?"
        params.append(username)
        
        self.cursor.execute(update_query, params)
        self.conn.commit()
        
        messagebox.showinfo("Success", "User updated successfully!")
        self.load_admin_users()
        self.clear_admin_form()
    
    def unlock_admin_user(self):
        """Unlock admin user account"""
        username = self.admin_username_entry.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please select a user to unlock!")
            return
        
        self.cursor.execute('''
            UPDATE admin_users SET is_locked = 0, login_attempts = 0, lockout_time = NULL
            WHERE username = ?
        ''', (username,))
        
        self.conn.commit()
        
        # Log the unlock event
        self.log_security_event("ACCOUNT_UNLOCKED", f"Admin user unlocked: {username}")
        
        messagebox.showinfo("Success", "User account unlocked successfully!")
        self.load_admin_users()
    
    def delete_admin_user(self):
        """Delete admin user"""
        username = self.admin_username_entry.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please select a user to delete!")
            return
        
        if username == "admin":
            messagebox.showerror("Error", "Cannot delete the default admin user!")
            return
        
        if username == self.admin_username:
            messagebox.showerror("Error", "Cannot delete your own account while logged in!")
            return
        
        result = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?")
        if result:
            self.cursor.execute("DELETE FROM admin_users WHERE username = ?", (username,))
            self.conn.commit()
            
            # Log the user deletion
            self.log_security_event("USER_DELETED", f"Admin user deleted: {username}")
            
            messagebox.showinfo("Success", "User deleted successfully!")
            self.load_admin_users()
            self.clear_admin_form()
    
    def on_admin_user_select(self, event):
        """Handle admin user selection"""
        selected = self.admin_tree.selection()
        if selected:
            item = selected[0]
            values = self.admin_tree.item(item, 'values')
            
            self.clear_admin_form()
            
            self.admin_username_entry.insert(0, values[0])
            self.admin_fullname_entry.insert(0, values[1])
            self.admin_email_entry.insert(0, values[2])
    
    def clear_admin_form(self):
        """Clear admin user form"""
        self.admin_username_entry.delete(0, tk.END)
        self.admin_fullname_entry.delete(0, tk.END)
        self.admin_email_entry.delete(0, tk.END)
        self.admin_password_entry.delete(0, tk.END)
        self.admin_confirm_entry.delete(0, tk.END)
    
    def clear_security_filters(self):
        """Clear security log filters"""
        self.event_type_combo.set("All")
        self.date_from_entry.delete(0, tk.END)
        self.date_to_entry.delete(0, tk.END)
        self.load_security_logs()
    
    def export_security_logs(self):
        """Export security logs to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Security Logs"
            )
            
            if filename:
                self.cursor.execute('''
                    SELECT timestamp, event_type, username, description
                    FROM security_logs
                    ORDER BY timestamp DESC
                ''')
                
                logs = self.cursor.fetchall()
                
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Timestamp', 'Event Type', 'Username', 'Description'])
                    
                    for log in logs:
                        writer.writerow(log)
                
                messagebox.showinfo("Success", f"Security logs exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")
    
    def refresh_system_info(self):
        """Refresh system information"""
        # This would refresh the system info tab
        messagebox.showinfo("Info", "System information refreshed!")
    
    def backup_database(self):
        """Create database backup"""
        try:
            backup_dir = filedialog.askdirectory(title="Select Backup Directory")
            if backup_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(backup_dir, f"college_system_backup_{timestamp}.db")
                
                # Create backup
                backup_conn = sqlite3.connect(backup_file)
                self.conn.backup(backup_conn)
                backup_conn.close()
                
                # Log the backup event
                self.log_security_event("DATABASE_BACKUP", f"Database backed up to: {backup_file}")
                
                messagebox.showinfo("Success", f"Database backed up successfully to:\n{backup_file}")
                
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {str(e)}")
    
    def clear_old_logs(self):
        """Clear security logs older than 90 days"""
        result = messagebox.askyesno("Confirm", "Delete security logs older than 90 days?")
        if result:
            self.cursor.execute('''
                DELETE FROM security_logs 
                WHERE timestamp < datetime('now', '-90 days')
            ''')
            
            deleted_count = self.cursor.rowcount
            self.conn.commit()
            
            # Log the cleanup
            self.log_security_event("LOGS_CLEANED", f"Cleared {deleted_count} old security logs")
            
            messagebox.showinfo("Success", f"Cleared {deleted_count} old security logs!")
            self.load_security_logs()
    
    def show_security_log(self):
        """Show security log dialog"""
        self.notebook.select(self.admin_tab)
        admin_notebook = self.admin_tab.winfo_children()[0]
        admin_notebook.select(1)  # Select security logs tab
    
    # [ALL THE ORIGINAL METHODS FROM YOUR CODE REMAIN EXACTLY THE SAME]
    # Only the security-related methods and admin tab methods have been added above
    
    def insert_sample_data_if_empty(self):
        """Insert professional sample data only if database is empty"""
        # Check if departments table is empty
        self.cursor.execute("SELECT COUNT(*) FROM departments")
        dept_count = self.cursor.fetchone()[0]
        
        if dept_count == 0:
            # Insert departments
            departments = [
                ('CSE', 'Computer Science & Engineering', 'Dr. Rajesh Sharma', 2005),
                ('ECE', 'Electronics & Communication Engineering', 'Dr. Priya Gupta', 2008),
                ('ME', 'Mechanical Engineering', 'Dr. Sanjay Reddy', 2000),
                ('CE', 'Civil Engineering', 'Dr. Anjali Kumar', 1998),
                ('EE', 'Electrical Engineering', 'Dr. Vikram Singh', 2002)
            ]
            
            for dept in departments:
                try:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO departments (dept_id, dept_name, hod_name, established_year) VALUES (?, ?, ?, ?)",
                        dept
                    )
                except sqlite3.IntegrityError:
                    pass
            
            # Insert sample sections for each department
            sections_data = [
                # CSE Sections
                ('CSE-A', 'CSE', 1, 2024, 'Dr. Sharma', 'Room 101'),
                ('CSE-B', 'CSE', 1, 2024, 'Dr. Verma', 'Room 102'),
                ('CSE-A', 'CSE', 2, 2023, 'Dr. Kumar', 'Room 201'),
                ('CSE-B', 'CSE', 2, 2023, 'Dr. Singh', 'Room 202'),
                
                # ECE Sections
                ('ECE-A', 'ECE', 1, 2024, 'Dr. Gupta', 'Room 301'),
                ('ECE-B', 'ECE', 1, 2024, 'Dr. Patel', 'Room 302'),
                
                # ME Sections
                ('ME-A', 'ME', 1, 2024, 'Dr. Reddy', 'Room 401'),
            ]
            
            for section in sections_data:
                try:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO sections (section_name, department, semester, batch, class_teacher, room_number) VALUES (?, ?, ?, ?, ?, ?)",
                        section
                    )
                except sqlite3.IntegrityError:
                    pass
            
            # Insert sample subjects for each department
            subjects_data = [
                # CSE Theory Subjects
                ('CSE101T', 'Programming Fundamentals', 4, 1, 'CSE', 'Theory', 100, 40, 60),
                ('CSE102T', 'Data Structures', 4, 2, 'CSE', 'Theory', 100, 40, 60),
                ('CSE103T', 'Algorithms', 4, 3, 'CSE', 'Theory', 100, 40, 60),
                ('CSE104T', 'Database Systems', 4, 4, 'CSE', 'Theory', 100, 40, 60),
                ('CSE105T', 'Computer Networks', 4, 5, 'CSE', 'Theory', 100, 40, 60),
                
                # CSE Practical Subjects
                ('CSE101P', 'Programming Lab', 2, 1, 'CSE', 'Practical', 100, 40, 30),
                ('CSE102P', 'Data Structures Lab', 2, 2, 'CSE', 'Practical', 100, 40, 30),
                ('CSE103P', 'Database Lab', 2, 4, 'CSE', 'Practical', 100, 40, 30),
                
                # ECE Subjects
                ('ECE101T', 'Circuit Theory', 4, 1, 'ECE', 'Theory', 100, 40, 60),
                ('ECE102T', 'Digital Electronics', 4, 2, 'ECE', 'Theory', 100, 40, 60),
                ('ECE101P', 'Electronics Lab', 2, 1, 'ECE', 'Practical', 100, 40, 30),
                
                # ME Subjects
                ('ME101T', 'Engineering Mechanics', 4, 1, 'ME', 'Theory', 100, 40, 60),
                ('ME102T', 'Thermodynamics', 4, 2, 'ME', 'Theory', 100, 40, 60),
                ('ME101P', 'Mechanics Lab', 2, 1, 'ME', 'Practical', 100, 40, 30),
            ]
            
            for subject in subjects_data:
                try:
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO subjects 
                        (subject_code, subject_name, credits, semester, department, subject_type, max_marks, min_pass_marks, teaching_hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', subject)
                except sqlite3.IntegrityError:
                    pass
            
            # Insert sample students with sections
            students = [
                ('CSE/2024/001', 'Aarav Sharma', 'CSE', 2024, 1, 'CSE-A', 'aarav.sharma@college.edu', '9876543210', 'Delhi', 'B+'),
                ('CSE/2024/002', 'Priya Patel', 'CSE', 2024, 1, 'CSE-A', 'priya.patel@college.edu', '9876543211', 'Mumbai', 'A+'),
                ('CSE/2024/003', 'Rohan Kumar', 'CSE', 2024, 1, 'CSE-B', 'rohan.kumar@college.edu', '9876543212', 'Bangalore', 'O+'),
                ('ECE/2024/001', 'Rahul Kumar', 'ECE', 2024, 1, 'ECE-A', 'rahul.kumar@college.edu', '9876543213', 'Bangalore', 'O+'),
                ('ME/2024/001', 'Sneha Gupta', 'ME', 2024, 1, 'ME-A', 'sneha.gupta@college.edu', '9876543214', 'Chennai', 'AB+'),
                ('CSE/2023/001', 'Ankit Singh', 'CSE', 2023, 3, 'CSE-A', 'ankit.singh@college.edu', '9876543215', 'Kolkata', 'B-'),
            ]
            
            for student in students:
                try:
                    admission_date = datetime.now().strftime("%Y-%m-%d")
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO students 
                        (student_id, name, department, batch, current_semester, section, email, phone, address, blood_group, admission_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (*student, admission_date))
                except sqlite3.IntegrityError:
                    pass
            
            self.conn.commit()
            print("Sample data inserted successfully!")

    def setup_department_tab(self):
        """Setup department management tab"""
        # Main container
        main_frame = ttk.Frame(self.department_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame - Department form
        left_frame = ttk.LabelFrame(main_frame, text="🎯 Department Information", padding="15")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        fields = [
            ("Department ID *:", "dept_id_entry", 20),
            ("Department Name *:", "dept_name_entry", 30),
            ("HOD Name:", "hod_entry", 30),
            ("Established Year:", "est_year_entry", 20)
        ]
        
        for i, (label, attr, width) in enumerate(fields):
            ttk.Label(left_frame, text=label, font=('Arial', 10)).grid(row=i, column=0, sticky=tk.W, pady=8)
            entry = ttk.Entry(left_frame, width=width, font=('Arial', 10))
            setattr(self, attr, entry)
            entry.grid(row=i, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="➕ Add Department", command=self.add_department, 
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Update", command=self.update_department).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Delete", command=self.delete_department).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Clear Form", command=self.clear_department_form).pack(side=tk.LEFT, padx=5)
        
        # Right frame - Department list
        right_frame = ttk.LabelFrame(main_frame, text="📋 Department List", padding="15")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for departments
        columns = ("dept_id", "dept_name", "hod_name", "est_year", "total_students")
        self.dept_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        headings = {
            "dept_id": "Dept ID",
            "dept_name": "Department Name",
            "hod_name": "HOD Name",
            "est_year": "Est. Year",
            "total_students": "Total Students"
        }
        
        for col, text in headings.items():
            self.dept_tree.heading(col, text=text)
            self.dept_tree.column(col, width=120)
        
        self.dept_tree.column("dept_name", width=200)
        self.dept_tree.column("hod_name", width=150)
        
        self.dept_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.dept_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.dept_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.dept_tree.bind("<<TreeviewSelect>>", self.on_department_select)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

    def setup_section_tab(self):
        """Setup section management tab"""
        main_frame = ttk.Frame(self.section_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame - Section form
        left_frame = ttk.LabelFrame(main_frame, text="📁 Section Information", padding="15")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Department selection
        ttk.Label(left_frame, text="Department *:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.sec_dept_combo = ttk.Combobox(left_frame, width=25, state="readonly", font=('Arial', 10))
        self.sec_dept_combo.grid(row=0, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Section details
        ttk.Label(left_frame, text="Section Name *:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.sec_name_entry = ttk.Entry(left_frame, width=25, font=('Arial', 10))
        self.sec_name_entry.grid(row=1, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Semester *:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.sec_semester_combo = ttk.Combobox(left_frame, width=25, values=[str(i) for i in range(1, 9)], state="readonly")
        self.sec_semester_combo.grid(row=2, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Batch *:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.sec_batch_combo = ttk.Combobox(left_frame, width=25, values=[str(i) for i in range(2020, 2030)], state="readonly")
        self.sec_batch_combo.grid(row=3, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Class Teacher:", font=('Arial', 10)).grid(row=4, column=0, sticky=tk.W, pady=8)
        self.sec_teacher_entry = ttk.Entry(left_frame, width=30, font=('Arial', 10))
        self.sec_teacher_entry.grid(row=4, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Room Number:", font=('Arial', 10)).grid(row=5, column=0, sticky=tk.W, pady=8)
        self.sec_room_entry = ttk.Entry(left_frame, width=20, font=('Arial', 10))
        self.sec_room_entry.grid(row=5, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="➕ Add Section", command=self.add_section,
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Update", command=self.update_section).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Delete", command=self.delete_section).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Clear Form", command=self.clear_section_form).pack(side=tk.LEFT, padx=5)
        
        # Right frame - Section list
        right_frame = ttk.LabelFrame(main_frame, text="📋 Section List", padding="15")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Filter frame
        filter_frame = ttk.Frame(right_frame)
        filter_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(filter_frame, text="Filter by Department:").pack(side=tk.LEFT, padx=5)
        self.filter_sec_dept_combo = ttk.Combobox(filter_frame, width=20, state="readonly")
        self.filter_sec_dept_combo.pack(side=tk.LEFT, padx=5)
        self.filter_sec_dept_combo.bind('<<ComboboxSelected>>', self.filter_sections)
        
        ttk.Button(filter_frame, text="🔄 Show All", command=self.load_sections).pack(side=tk.LEFT, padx=5)
        
        # Treeview for sections
        columns = ("section_name", "department", "semester", "batch", "class_teacher", "room_number")
        self.section_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        headings = {
            "section_name": "Section Name",
            "department": "Department",
            "semester": "Semester",
            "batch": "Batch",
            "class_teacher": "Class Teacher",
            "room_number": "Room Number"
        }
        
        for col, text in headings.items():
            self.section_tree.heading(col, text=text)
            self.section_tree.column(col, width=100)
        
        self.section_tree.column("section_name", width=120)
        self.section_tree.column("class_teacher", width=150)
        
        self.section_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.section_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.section_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.section_tree.bind("<<TreeviewSelect>>", self.on_section_select)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

    def setup_subject_tab(self):
        """Setup subject management tab"""
        main_frame = ttk.Frame(self.subject_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame - Subject form
        left_frame = ttk.LabelFrame(main_frame, text="📖 Subject Information", padding="15")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Department selection
        ttk.Label(left_frame, text="Department *:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.sub_dept_combo = ttk.Combobox(left_frame, width=25, state="readonly", font=('Arial', 10))
        self.sub_dept_combo.grid(row=0, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        fields = [
            ("Subject Code *:", "sub_code_entry", 20),
            ("Subject Name *:", "sub_name_entry", 30),
            ("Credits *:", "sub_credits_combo", 15),
            ("Semester *:", "sub_semester_combo", 15),
            ("Subject Type *:", "sub_type_combo", 15),
            ("Max Marks:", "sub_max_marks_entry", 15),
            ("Min Pass Marks:", "sub_min_marks_entry", 15),
            ("Teaching Hours:", "sub_hours_entry", 15)
        ]
        
        for i, (label, attr, width) in enumerate(fields):
            ttk.Label(left_frame, text=label, font=('Arial', 10)).grid(row=i+1, column=0, sticky=tk.W, pady=8)
            if "combo" in attr:
                if "credits" in attr:
                    combo = ttk.Combobox(left_frame, width=width, values=['1', '2', '3', '4', '5'], state="readonly")
                elif "semester" in attr:
                    combo = ttk.Combobox(left_frame, width=width, values=[str(i) for i in range(1, 9)], state="readonly")
                elif "type" in attr:
                    combo = ttk.Combobox(left_frame, width=width, values=['Theory', 'Practical'], state="readonly")
                setattr(self, attr, combo)
                combo.grid(row=i+1, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
            else:
                entry = ttk.Entry(left_frame, width=width, font=('Arial', 10))
                setattr(self, attr, entry)
                entry.grid(row=i+1, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Set default values
        self.sub_max_marks_entry.insert(0, "100")
        self.sub_min_marks_entry.insert(0, "40")
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="➕ Add Subject", command=self.add_subject,
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Update", command=self.update_subject).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Delete", command=self.delete_subject).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Clear Form", command=self.clear_subject_form).pack(side=tk.LEFT, padx=5)
        
        # Right frame - Subject list with filter
        right_frame = ttk.LabelFrame(main_frame, text="📚 Subject List", padding="15")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Filter frame
        filter_frame = ttk.Frame(right_frame)
        filter_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(filter_frame, text="Filter by Department:").pack(side=tk.LEFT, padx=5)
        self.filter_sub_dept_combo = ttk.Combobox(filter_frame, width=20, state="readonly")
        self.filter_sub_dept_combo.pack(side=tk.LEFT, padx=5)
        self.filter_sub_dept_combo.bind('<<ComboboxSelected>>', self.filter_subjects)
        
        ttk.Label(filter_frame, text="Semester:").pack(side=tk.LEFT, padx=5)
        self.filter_sub_semester_combo = ttk.Combobox(filter_frame, width=10, values=['All'] + [str(i) for i in range(1, 9)], state="readonly")
        self.filter_sub_semester_combo.pack(side=tk.LEFT, padx=5)
        self.filter_sub_semester_combo.bind('<<ComboboxSelected>>', self.filter_subjects)
        
        ttk.Button(filter_frame, text="🔄 Show All", command=self.load_subjects).pack(side=tk.LEFT, padx=5)
        
        # Treeview for subjects
        columns = ("code", "name", "dept", "semester", "credits", "type", "max_marks")
        self.subject_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        headings = {
            "code": "Subject Code",
            "name": "Subject Name",
            "dept": "Department",
            "semester": "Semester",
            "credits": "Credits",
            "type": "Type",
            "max_marks": "Max Marks"
        }
        
        for col, text in headings.items():
            self.subject_tree.heading(col, text=text)
            self.subject_tree.column(col, width=100)
        
        self.subject_tree.column("name", width=200)
        self.subject_tree.column("code", width=120)
        
        self.subject_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.subject_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.subject_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.subject_tree.bind("<<TreeviewSelect>>", self.on_subject_select)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

    def setup_student_tab(self):
        """Setup student management tab with section field"""
        main_frame = ttk.Frame(self.student_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame - Student form
        left_frame = ttk.LabelFrame(main_frame, text="👨‍🎓 Student Information", padding="15")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Student ID and Name
        ttk.Label(left_frame, text="Student ID *:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.stu_id_entry = ttk.Entry(left_frame, width=25, font=('Arial', 10))
        self.stu_id_entry.grid(row=0, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Full Name *:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.stu_name_entry = ttk.Entry(left_frame, width=30, font=('Arial', 10))
        self.stu_name_entry.grid(row=1, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Department and Batch
        ttk.Label(left_frame, text="Department *:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.stu_dept_combo = ttk.Combobox(left_frame, width=25, state="readonly", font=('Arial', 10))
        self.stu_dept_combo.grid(row=2, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.stu_dept_combo.bind('<<ComboboxSelected>>', self.on_student_dept_select)
        
        ttk.Label(left_frame, text="Batch *:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.stu_batch_combo = ttk.Combobox(left_frame, width=25, values=[str(i) for i in range(2020, 2030)], state="readonly")
        self.stu_batch_combo.grid(row=3, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.stu_batch_combo.bind('<<ComboboxSelected>>', self.on_student_batch_select)
        
        # Semester and Section
        ttk.Label(left_frame, text="Semester *:", font=('Arial', 10)).grid(row=4, column=0, sticky=tk.W, pady=8)
        self.stu_semester_combo = ttk.Combobox(left_frame, width=25, values=[str(i) for i in range(1, 9)], state="readonly")
        self.stu_semester_combo.grid(row=4, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.stu_semester_combo.bind('<<ComboboxSelected>>', self.on_student_semester_select)
        
        ttk.Label(left_frame, text="Section:", font=('Arial', 10)).grid(row=5, column=0, sticky=tk.W, pady=8)
        self.stu_section_combo = ttk.Combobox(left_frame, width=25, state="readonly")
        self.stu_section_combo.grid(row=5, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Contact Information
        ttk.Label(left_frame, text="Email:", font=('Arial', 10)).grid(row=6, column=0, sticky=tk.W, pady=8)
        self.stu_email_entry = ttk.Entry(left_frame, width=30, font=('Arial', 10))
        self.stu_email_entry.grid(row=6, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Phone:", font=('Arial', 10)).grid(row=7, column=0, sticky=tk.W, pady=8)
        self.stu_phone_entry = ttk.Entry(left_frame, width=20, font=('Arial', 10))
        self.stu_phone_entry.grid(row=7, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Address and Blood Group
        ttk.Label(left_frame, text="Address:", font=('Arial', 10)).grid(row=8, column=0, sticky=tk.W, pady=8)
        self.stu_address_entry = ttk.Entry(left_frame, width=30, font=('Arial', 10))
        self.stu_address_entry.grid(row=8, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        ttk.Label(left_frame, text="Blood Group:", font=('Arial', 10)).grid(row=9, column=0, sticky=tk.W, pady=8)
        self.stu_blood_combo = ttk.Combobox(left_frame, width=15, 
                                          values=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        self.stu_blood_combo.grid(row=9, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Status
        ttk.Label(left_frame, text="Status:", font=('Arial', 10)).grid(row=10, column=0, sticky=tk.W, pady=8)
        self.stu_status_combo = ttk.Combobox(left_frame, width=15, 
                                           values=["Active", "Inactive", "Completed", "Dropped"])
        self.stu_status_combo.grid(row=10, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.stu_status_combo.set("Active")
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="➕ Add Student", command=self.add_student,
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Update", command=self.update_student).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Delete", command=self.delete_student).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Clear Form", command=self.clear_student_form).pack(side=tk.LEFT, padx=5)
        
        # Right frame - Student list with filter
        right_frame = ttk.LabelFrame(main_frame, text="📋 Student List", padding="15")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Filter frame
        filter_frame = ttk.Frame(right_frame)
        filter_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(filter_frame, text="Filter by Department:").pack(side=tk.LEFT, padx=5)
        self.filter_stu_dept_combo = ttk.Combobox(filter_frame, width=20, state="readonly")
        self.filter_stu_dept_combo.pack(side=tk.LEFT, padx=5)
        self.filter_stu_dept_combo.bind('<<ComboboxSelected>>', self.filter_students)
        
        ttk.Button(filter_frame, text="📤 Export All", command=self.export_all_students).pack(side=tk.RIGHT, padx=5)
        ttk.Button(filter_frame, text="🔄 Show All", command=self.load_students).pack(side=tk.LEFT, padx=5)
        
        # Treeview for students
        columns = ("student_id", "name", "department", "batch", "semester", "section", "email", "phone", "status")
        self.student_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        headings = {
            "student_id": "Student ID",
            "name": "Name",
            "department": "Department",
            "batch": "Batch",
            "semester": "Semester",
            "section": "Section",
            "email": "Email",
            "phone": "Phone",
            "status": "Status"
        }
        
        for col, text in headings.items():
            self.student_tree.heading(col, text=text)
            self.student_tree.column(col, width=100)
        
        self.student_tree.column("name", width=150)
        self.student_tree.column("email", width=150)
        self.student_tree.column("student_id", width=120)
        
        self.student_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.student_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.student_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_select)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

    def setup_theory_grade_tab(self):
        """Setup theory grade entry tab with scrollable left panel"""
        main_frame = ttk.Frame(self.theory_grade_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights for main frame
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Create a frame for the left side that will contain the scrollable content
        left_container = ttk.Frame(main_frame)
        left_container.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create a canvas and scrollbar for the left container
        canvas = tk.Canvas(left_container)
        scrollbar = ttk.Scrollbar(left_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Left frame - Grade entry form (now inside scrollable frame)
        left_frame = ttk.LabelFrame(scrollable_frame, text="📖 Theory Grade Entry", padding="15")
        left_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure grid weights for left frame
        left_frame.columnconfigure(1, weight=1)
        
        # Student selection
        ttk.Label(left_frame, text="Select Student *:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.theory_student_combo = ttk.Combobox(left_frame, width=30, state="readonly", font=('Arial', 10))
        self.theory_student_combo.grid(row=0, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.theory_student_combo.bind('<<ComboboxSelected>>', self.on_theory_student_select)
        
        # Student info display
        info_frame = ttk.LabelFrame(left_frame, text="Student Information", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.theory_student_info = ttk.Label(info_frame, text="Select a student to view details", 
                                           font=('Arial', 9))
        self.theory_student_info.pack(pady=5)
        
        # Semester and subject selection
        ttk.Label(left_frame, text="Semester *:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.theory_semester_combo = ttk.Combobox(left_frame, width=30, values=[str(i) for i in range(1, 9)], state="readonly")
        self.theory_semester_combo.grid(row=2, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.theory_semester_combo.bind('<<ComboboxSelected>>', self.on_theory_semester_select)
        
        ttk.Label(left_frame, text="Select Subject *:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.theory_subject_combo = ttk.Combobox(left_frame, width=30, state="readonly")
        self.theory_subject_combo.grid(row=3, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Theory marks entry frame
        marks_frame = ttk.LabelFrame(left_frame, text="Theory Marks Distribution", padding="10")
        marks_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        theory_fields = [
            ("Internal Exam 1 (20):", "theory_internal1_entry"),
            ("Internal Exam 2 (20):", "theory_internal2_entry"),
            ("Presentation (10):", "theory_presentation_entry"),
            ("Assignment 1 (5):", "theory_assignment1_entry"),
            ("Assignment 2 (5):", "theory_assignment2_entry"),
            ("External Exam (60):", "theory_external_entry")
        ]
        
        for i, (label, attr) in enumerate(theory_fields):
            ttk.Label(marks_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=5)
            entry = ttk.Entry(marks_frame, width=15)
            setattr(self, attr, entry)
            entry.grid(row=i, column=1, pady=5, padx=5)
        
        # Results display
        result_frame = ttk.LabelFrame(left_frame, text="Results", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        result_fields = [
            ("Internal Total (40):", "theory_internal_total_label"),
            ("Total Marks (100):", "theory_total_marks_label"),
            ("Grade:", "theory_grade_label"),
            ("Grade Point:", "theory_grade_point_label"),
            ("Status:", "theory_status_label")
        ]
        
        for i, (label, attr) in enumerate(result_fields):
            ttk.Label(result_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            label_widget = ttk.Label(result_frame, text="-", font=('Arial', 9))
            setattr(self, attr, label_widget)
            label_widget.grid(row=i, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Buttons - Now clearly visible at the bottom
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="🧮 Calculate", command=self.calculate_theory_grade).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save Grade", command=self.save_theory_grade, 
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Clear", command=self.clear_theory_form).pack(side=tk.LEFT, padx=5)
        
        # Pack the canvas and scrollbar in the left container
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure the left container to expand
        left_container.columnconfigure(0, weight=1)
        left_container.rowconfigure(0, weight=1)
        
        # Right frame - Current grades and statistics
        right_frame = ttk.LabelFrame(main_frame, text="Current Semester Theory Grades", padding="15")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for right frame
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=3)  # Treeview gets more space
        right_frame.rowconfigure(1, weight=1)  # Performance frame
        
        # Treeview for current theory grades
        columns = ("subject", "internal1", "internal2", "presentation", "assign1", "assign2", "external", "total", "grade", "status")
        self.theory_grades_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        
        headings = {
            "subject": "Subject",
            "internal1": "Int1",
            "internal2": "Int2",
            "presentation": "Pres",
            "assign1": "Asg1",
            "assign2": "Asg2",
            "external": "External",
            "total": "Total",
            "grade": "Grade",
            "status": "Status"
        }
        
        for col, text in headings.items():
            self.theory_grades_tree.heading(col, text=text)
            self.theory_grades_tree.column(col, width=60)
        
        self.theory_grades_tree.column("subject", width=150)
        self.theory_grades_tree.column("total", width=70)
        self.theory_grades_tree.column("grade", width=60)
        self.theory_grades_tree.column("status", width=80)
        
        self.theory_grades_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.theory_grades_tree.yview)
        tree_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.theory_grades_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Semester performance
        performance_frame = ttk.LabelFrame(right_frame, text="Semester Performance", padding="10")
        performance_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(performance_frame, text="Total Credits:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.theory_credits_label = ttk.Label(performance_frame, text="0", font=('Arial', 10, 'bold'))
        self.theory_credits_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(performance_frame, text="SGPA:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.theory_sgpa_label = ttk.Label(performance_frame, text="0.00", font=('Arial', 12, 'bold'), foreground="blue")
        self.theory_sgpa_label.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)

    def setup_practical_grade_tab(self):
        """Setup practical grade entry tab"""
        main_frame = ttk.Frame(self.practical_grade_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights for main frame
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left frame - Grade entry form
        left_frame = ttk.LabelFrame(main_frame, text="🔬 Practical Grade Entry", padding="15")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for left frame
        left_frame.columnconfigure(1, weight=1)
        for i in range(7):  # 7 rows
            left_frame.rowconfigure(i, weight=0)
        left_frame.rowconfigure(6, weight=1)  # Button row gets extra space
        
        # Student selection
        ttk.Label(left_frame, text="Select Student *:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.practical_student_combo = ttk.Combobox(left_frame, width=30, state="readonly", font=('Arial', 10))
        self.practical_student_combo.grid(row=0, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.practical_student_combo.bind('<<ComboboxSelected>>', self.on_practical_student_select)
        
        # Student info display
        info_frame = ttk.LabelFrame(left_frame, text="Student Information", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.practical_student_info = ttk.Label(info_frame, text="Select a student to view details", 
                                              font=('Arial', 9))
        self.practical_student_info.pack(pady=5)
        
        # Semester and subject selection
        ttk.Label(left_frame, text="Semester *:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.practical_semester_combo = ttk.Combobox(left_frame, width=30, values=[str(i) for i in range(1, 9)], state="readonly")
        self.practical_semester_combo.grid(row=2, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        self.practical_semester_combo.bind('<<ComboboxSelected>>', self.on_practical_semester_select)
        
        ttk.Label(left_frame, text="Select Subject *:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.practical_subject_combo = ttk.Combobox(left_frame, width=30, state="readonly")
        self.practical_subject_combo.grid(row=3, column=1, pady=8, padx=10, sticky=(tk.W, tk.E))
        
        # Practical marks entry frame
        marks_frame = ttk.LabelFrame(left_frame, text="Practical Marks Distribution", padding="10")
        marks_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        practical_fields = [
            ("Lab Copies (20):", "practical_lab_copies_entry"),
            ("Viva (20):", "practical_viva_entry"),
            ("Practical Exam (60):", "practical_exam_entry")
        ]
        
        for i, (label, attr) in enumerate(practical_fields):
            ttk.Label(marks_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=5)
            entry = ttk.Entry(marks_frame, width=15)
            setattr(self, attr, entry)
            entry.grid(row=i, column=1, pady=5, padx=5)
        
        # Results display
        result_frame = ttk.LabelFrame(left_frame, text="Results", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        result_fields = [
            ("Total Marks (100):", "practical_total_marks_label"),
            ("Grade:", "practical_grade_label"),
            ("Grade Point:", "practical_grade_point_label"),
            ("Status:", "practical_status_label")
        ]
        
        for i, (label, attr) in enumerate(result_fields):
            ttk.Label(result_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            label_widget = ttk.Label(result_frame, text="-", font=('Arial', 9))
            setattr(self, attr, label_widget)
            label_widget.grid(row=i, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Buttons - FIXED: Made sure buttons are visible
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15, sticky=(tk.S, tk.W, tk.E))
        
        ttk.Button(button_frame, text="🧮 Calculate", command=self.calculate_practical_grade).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save Grade", command=self.save_practical_grade,
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Clear", command=self.clear_practical_form).pack(side=tk.LEFT, padx=5)
        
        # Right frame - Current grades
        right_frame = ttk.LabelFrame(main_frame, text="Current Semester Practical Grades", padding="15")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for right frame
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # Treeview for current practical grades
        columns = ("subject", "lab_copies", "viva", "practical_exam", "total", "grade", "status")
        self.practical_grades_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        headings = {
            "subject": "Subject",
            "lab_copies": "Lab Copies",
            "viva": "Viva",
            "practical_exam": "Practical Exam",
            "total": "Total",
            "grade": "Grade",
            "status": "Status"
        }
        
        for col, text in headings.items():
            self.practical_grades_tree.heading(col, text=text)
            self.practical_grades_tree.column(col, width=80)
        
        self.practical_grades_tree.column("subject", width=150)
        
        self.practical_grades_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.practical_grades_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.practical_grades_tree.configure(yscrollcommand=scrollbar.set)

    def setup_student_report_tab(self):
        """Setup student report tab with export functionality"""
        main_frame = ttk.Frame(self.student_report_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Student selection
        selection_frame = ttk.LabelFrame(main_frame, text="Select Student", padding="10")
        selection_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(selection_frame, text="Student:", font=('Arial', 11)).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.report_student_combo = ttk.Combobox(selection_frame, width=50, state="readonly", font=('Arial', 10))
        self.report_student_combo.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        self.report_student_combo.bind('<<ComboboxSelected>>', self.generate_student_report)
        
        # Export button
        ttk.Button(selection_frame, text="📤 Export Report", command=self.export_student_report).grid(row=0, column=2, padx=5)
        
        selection_frame.columnconfigure(1, weight=1)
        
        # Student info
        info_frame = ttk.LabelFrame(main_frame, text="Student Information", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.report_info_text = tk.Text(info_frame, height=4, width=80, font=('Arial', 10))
        self.report_info_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Academic performance
        performance_frame = ttk.LabelFrame(main_frame, text="Academic Performance", padding="10")
        performance_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create notebook for semester-wise results
        self.report_notebook = ttk.Notebook(performance_frame)
        self.report_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Summary frame
        summary_frame = ttk.Frame(performance_frame)
        summary_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(summary_frame, text="Overall CGPA:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=20)
        self.cgpa_label = ttk.Label(summary_frame, text="0.00", font=('Arial', 14, 'bold'), foreground="blue")
        self.cgpa_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(summary_frame, text="Total Credits Completed:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=20)
        self.total_credits_label = ttk.Label(summary_frame, text="0", font=('Arial', 14, 'bold'), foreground="green")
        self.total_credits_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(summary_frame, text="Current Semester:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=20)
        self.current_semester_label = ttk.Label(summary_frame, text="-", font=('Arial', 14, 'bold'), foreground="purple")
        self.current_semester_label.pack(side=tk.LEFT, padx=5)

    # [ALL THE REMAINING ORIGINAL METHODS STAY EXACTLY THE SAME]
    # Only the security system and admin management methods have been added

    # Section Management Methods
    def load_sections(self, department=None):
        """Load sections into treeview and comboboxes"""
        # Clear treeview
        for item in self.section_tree.get_children():
            self.section_tree.delete(item)
        
        # Build query based on filters
        query = '''
            SELECT section_name, department, semester, batch, class_teacher, room_number
            FROM sections
        '''
        params = []
        
        if department:
            dept_id = department.split(' - ')[0]
            query += ' WHERE department = ?'
            params.append(dept_id)
        
        query += ' ORDER BY department, batch, semester, section_name'
        
        self.cursor.execute(query, params)
        sections = self.cursor.fetchall()
        
        for section in sections:
            self.section_tree.insert("", tk.END, values=section)

    def add_section(self):
        """Add a new section"""
        section_name = self.sec_name_entry.get().strip()
        department_display = self.sec_dept_combo.get().strip()
        semester = self.sec_semester_combo.get().strip()
        batch = self.sec_batch_combo.get().strip()
        class_teacher = self.sec_teacher_entry.get().strip()
        room_number = self.sec_room_entry.get().strip()
        
        if not all([section_name, department_display, semester, batch]):
            messagebox.showerror("Error", "Please fill all required fields!")
            return
        
        department = department_display.split(' - ')[0]
        
        try:
            self.cursor.execute('''
                INSERT INTO sections 
                (section_name, department, semester, batch, class_teacher, room_number)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (section_name, department, int(semester), int(batch), class_teacher, room_number))
            
            self.conn.commit()
            messagebox.showinfo("Success", "Section added successfully!")
            self.load_sections()
            self.clear_section_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Section already exists for this department, semester, and batch!")

    def update_section(self):
        """Update section information"""
        section_name = self.sec_name_entry.get().strip()
        department_display = self.sec_dept_combo.get().strip()
        semester = self.sec_semester_combo.get().strip()
        batch = self.sec_batch_combo.get().strip()
        class_teacher = self.sec_teacher_entry.get().strip()
        room_number = self.sec_room_entry.get().strip()
        
        if not section_name:
            messagebox.showerror("Error", "Please select a section to update!")
            return
        
        department = department_display.split(' - ')[0]
        
        # Get original values to identify the section
        selected = self.section_tree.selection()
        if selected:
            original_values = self.section_tree.item(selected[0], 'values')
            original_section_name, original_department, original_semester, original_batch = original_values[:4]
            
            self.cursor.execute('''
                UPDATE sections SET section_name=?, department=?, semester=?, batch=?, class_teacher=?, room_number=?
                WHERE section_name=? AND department=? AND semester=? AND batch=?
            ''', (section_name, department, int(semester), int(batch), class_teacher, room_number,
                 original_section_name, original_department, int(original_semester), int(original_batch)))
            
            self.conn.commit()
            messagebox.showinfo("Success", "Section updated successfully!")
            self.load_sections()
            self.clear_section_form()

    def delete_section(self):
        """Delete section"""
        selected = self.section_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a section to delete!")
            return
        
        values = self.section_tree.item(selected[0], 'values')
        section_name, department, semester, batch = values[:4]
        
        # Check if section has students
        self.cursor.execute("SELECT COUNT(*) FROM students WHERE section=?", (section_name,))
        student_count = self.cursor.fetchone()[0]
        
        if student_count > 0:
            messagebox.showerror("Error", f"Cannot delete section! There are {student_count} students in this section.")
            return
        
        result = messagebox.askyesno("Confirm", "Are you sure you want to delete this section?")
        if result:
            self.cursor.execute('''
                DELETE FROM sections 
                WHERE section_name=? AND department=? AND semester=? AND batch=?
            ''', (section_name, department, semester, batch))
            
            self.conn.commit()
            messagebox.showinfo("Success", "Section deleted successfully!")
            self.load_sections()
            self.clear_section_form()

    def clear_section_form(self):
        """Clear section form"""
        self.sec_name_entry.delete(0, tk.END)
        self.sec_dept_combo.set('')
        self.sec_semester_combo.set('')
        self.sec_batch_combo.set('')
        self.sec_teacher_entry.delete(0, tk.END)
        self.sec_room_entry.delete(0, tk.END)

    def on_section_select(self, event):
        """Handle section selection"""
        selected = self.section_tree.selection()
        if selected:
            item = selected[0]
            values = self.section_tree.item(item, 'values')
            
            self.clear_section_form()
            
            self.sec_name_entry.insert(0, values[0])
            
            # Find department display string
            dept_id = values[1]
            self.cursor.execute("SELECT dept_name FROM departments WHERE dept_id=?", (dept_id,))
            dept_data = self.cursor.fetchone()
            if dept_data:
                dept_display = f"{dept_id} - {dept_data[0]}"
                self.sec_dept_combo.set(dept_display)
            
            self.sec_semester_combo.set(values[2])
            self.sec_batch_combo.set(values[3])
            self.sec_teacher_entry.insert(0, values[4])
            self.sec_room_entry.insert(0, values[5])

    def filter_sections(self, event=None):
        """Filter sections by department"""
        department = self.filter_sec_dept_combo.get()
        self.load_sections(department)

    # Data loading methods
    def load_departments(self):
        """Load departments into treeview and comboboxes"""
        # Clear treeview
        for item in self.dept_tree.get_children():
            self.dept_tree.delete(item)
        
        # Load departments
        self.cursor.execute('''
            SELECT d.dept_id, d.dept_name, d.hod_name, d.established_year, 
                   COUNT(s.student_id) as total_students
            FROM departments d
            LEFT JOIN students s ON d.dept_id = s.department
            GROUP BY d.dept_id
        ''')
        departments = self.cursor.fetchall()
        
        for dept in departments:
            self.dept_tree.insert("", tk.END, values=dept)
        
        # Update department comboboxes
        dept_list = [f"{dept[0]} - {dept[1]}" for dept in departments]
        
        # Update all department comboboxes
        comboboxes = [
            self.sec_dept_combo, self.filter_sec_dept_combo,
            self.sub_dept_combo, self.filter_sub_dept_combo,
            self.stu_dept_combo, self.filter_stu_dept_combo
        ]
        
        for combo in comboboxes:
            combo['values'] = dept_list
            if dept_list and combo.get() == '':
                combo.set(dept_list[0])

    def load_subjects(self, department=None, semester=None):
        """Load subjects into treeview and comboboxes"""
        # Clear treeview
        for item in self.subject_tree.get_children():
            self.subject_tree.delete(item)
        
        # Build query based on filters
        query = '''
            SELECT subject_code, subject_name, department, semester, credits, subject_type, max_marks
            FROM subjects
        '''
        params = []
        
        if department and department != 'All':
            dept_id = department.split(' - ')[0]
            query += ' WHERE department = ?'
            params.append(dept_id)
            
            if semester and semester != 'All':
                query += ' AND semester = ?'
                params.append(int(semester))
        elif semester and semester != 'All':
            query += ' WHERE semester = ?'
            params.append(int(semester))
        
        query += ' ORDER BY department, semester, subject_code'
        
        self.cursor.execute(query, params)
        subjects = self.cursor.fetchall()
        
        for subject in subjects:
            self.subject_tree.insert("", tk.END, values=subject)
        
        # Update subject comboboxes for grade entry
        theory_subjects = [f"{sub[0]} - {sub[1]}" for sub in subjects if sub[5] == 'Theory']
        practical_subjects = [f"{sub[0]} - {sub[1]}" for sub in subjects if sub[5] == 'Practical']
        
        self.theory_subject_combo['values'] = theory_subjects
        self.practical_subject_combo['values'] = practical_subjects

    def load_students(self, department=None):
        """Load students into treeview and comboboxes with section"""
        # Clear treeview
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        
        # Load students
        if department:
            dept_id = department.split(' - ')[0]
            self.cursor.execute("SELECT student_id, name, department, batch, current_semester, section, email, phone, status FROM students WHERE department=?", (dept_id,))
        else:
            self.cursor.execute("SELECT student_id, name, department, batch, current_semester, section, email, phone, status FROM students")
        
        students = self.cursor.fetchall()
        
        for student in students:
            self.student_tree.insert("", tk.END, values=student)
        
        # Update student comboboxes
        student_list = [f"{stu[0]} - {stu[1]}" for stu in students]
        
        self.theory_student_combo['values'] = student_list
        self.practical_student_combo['values'] = student_list
        self.report_student_combo['values'] = student_list
        
        # Clear filter when showing all
        if not department:
            self.filter_stu_dept_combo.set('')

    def load_theory_grades(self):
        """Load current semester theory grades for selected student"""
        for item in self.theory_grades_tree.get_children():
            self.theory_grades_tree.delete(item)
        
        student_display = self.theory_student_combo.get()
        semester = self.theory_semester_combo.get()
        
        if not student_display or not semester:
            return
        
        student_id = student_display.split(' - ')[0]
        
        self.cursor.execute('''
            SELECT s.subject_name, t.internal1_marks, t.internal2_marks, t.presentation_marks,
                   t.assignment1_marks, t.assignment2_marks, t.external_marks, t.total_marks,
                   t.grade, t.result_status
            FROM theory_grades t
            JOIN subjects s ON t.subject_code = s.subject_code
            WHERE t.student_id = ? AND t.semester = ?
        ''', (student_id, semester))
        
        grades = self.cursor.fetchall()
        for grade in grades:
            self.theory_grades_tree.insert("", tk.END, values=grade)

    def load_practical_grades(self):
        """Load current semester practical grades for selected student"""
        for item in self.practical_grades_tree.get_children():
            self.practical_grades_tree.delete(item)
        
        student_display = self.practical_student_combo.get()
        semester = self.practical_semester_combo.get()
        
        if not student_display or not semester:
            return
        
        student_id = student_display.split(' - ')[0]
        
        self.cursor.execute('''
            SELECT s.subject_name, p.lab_copies_marks, p.viva_marks, p.practical_exam_marks,
                   p.total_marks, p.grade, p.result_status
            FROM practical_grades p
            JOIN subjects s ON p.subject_code = s.subject_code
            WHERE p.student_id = ? AND p.semester = ?
        ''', (student_id, semester))
        
        grades = self.cursor.fetchall()
        for grade in grades:
            self.practical_grades_tree.insert("", tk.END, values=grade)

    # Database operations
    def add_department(self):
        """Add a new department"""
        dept_id = self.dept_id_entry.get().strip()
        dept_name = self.dept_name_entry.get().strip()
        hod_name = self.hod_entry.get().strip()
        est_year = self.est_year_entry.get().strip()
        
        if not dept_id or not dept_name:
            messagebox.showerror("Error", "Department ID and Name are required!")
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO departments (dept_id, dept_name, hod_name, established_year) VALUES (?, ?, ?, ?)",
                (dept_id, dept_name, hod_name, est_year)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Department added successfully!")
            self.load_departments()
            self.clear_department_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Department ID already exists!")

    def add_subject(self):
        """Add a new subject"""
        subject_code = self.sub_code_entry.get().strip()
        subject_name = self.sub_name_entry.get().strip()
        department_display = self.sub_dept_combo.get().strip()
        credits = self.sub_credits_combo.get().strip()
        semester = self.sub_semester_combo.get().strip()
        subject_type = self.sub_type_combo.get().strip()
        max_marks = self.sub_max_marks_entry.get().strip() or "100"
        min_marks = self.sub_min_marks_entry.get().strip() or "40"
        teaching_hours = self.sub_hours_entry.get().strip()
        
        if not all([subject_code, subject_name, department_display, credits, semester, subject_type]):
            messagebox.showerror("Error", "Please fill all required fields!")
            return
        
        department = department_display.split(' - ')[0]
        
        try:
            self.cursor.execute('''
                INSERT INTO subjects 
                (subject_code, subject_name, credits, semester, department, subject_type, max_marks, min_pass_marks, teaching_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (subject_code, subject_name, int(credits), int(semester), department, subject_type, 
                  int(max_marks), int(min_marks), teaching_hours))
            
            self.conn.commit()
            messagebox.showinfo("Success", "Subject added successfully!")
            self.load_subjects()
            self.clear_subject_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Subject code already exists!")

    def add_student(self):
        """Add a new student with section"""
        student_id = self.stu_id_entry.get().strip()
        name = self.stu_name_entry.get().strip()
        department_display = self.stu_dept_combo.get().strip()
        batch = self.stu_batch_combo.get().strip()
        semester = self.stu_semester_combo.get().strip()
        section = self.stu_section_combo.get().strip()
        email = self.stu_email_entry.get().strip()
        phone = self.stu_phone_entry.get().strip()
        address = self.stu_address_entry.get().strip()
        blood_group = self.stu_blood_combo.get().strip()
        status = self.stu_status_combo.get().strip()
        
        if not all([student_id, name, department_display, batch, semester]):
            messagebox.showerror("Error", "Please fill all required fields!")
            return
        
        department = department_display.split(' - ')[0]
        
        try:
            admission_date = datetime.now().strftime("%Y-%m-%d")
            
            self.cursor.execute('''
                INSERT INTO students 
                (student_id, name, department, batch, current_semester, section, email, phone, address, blood_group, admission_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, name, department, int(batch), int(semester), section, email, phone, address, blood_group, admission_date, status))
            
            self.conn.commit()
            messagebox.showinfo("Success", "Student added successfully!")
            self.load_students()
            self.clear_student_form()
            self.load_departments()  # Refresh department stats
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Student ID already exists!")

    # Grade calculation methods
    def calculate_theory_grade(self):
        """Calculate theory grade based on marks"""
        try:
            # Get marks from entries
            internal1 = float(self.theory_internal1_entry.get() or 0)
            internal2 = float(self.theory_internal2_entry.get() or 0)
            presentation = float(self.theory_presentation_entry.get() or 0)
            assignment1 = float(self.theory_assignment1_entry.get() or 0)
            assignment2 = float(self.theory_assignment2_entry.get() or 0)
            external = float(self.theory_external_entry.get() or 0)
            
            # Calculate internal total (average of two internals + presentation + assignments)
            internal_avg = (internal1 + internal2) / 2
            internal_total = internal_avg + presentation + assignment1 + assignment2
            
            total_marks = internal_total + external
            
            # Calculate grade based on total marks
            grade, grade_point = self.calculate_grade_and_point(total_marks)
            status = "Pass" if total_marks >= 40 else "Fail"
            
            # Update labels
            self.theory_internal_total_label.config(text=f"{internal_total:.2f}")
            self.theory_total_marks_label.config(text=f"{total_marks:.2f}")
            self.theory_grade_label.config(text=grade)
            self.theory_grade_point_label.config(text=f"{grade_point:.1f}")
            
            if status == "Fail":
                self.theory_status_label.config(text=status, foreground="red")
            else:
                self.theory_status_label.config(text=status, foreground="green")
            
            return total_marks, grade, grade_point, status
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for marks!")
            return None

    def calculate_practical_grade(self):
        """Calculate practical grade based on marks"""
        try:
            lab_copies = float(self.practical_lab_copies_entry.get() or 0)
            viva = float(self.practical_viva_entry.get() or 0)
            practical_exam = float(self.practical_exam_entry.get() or 0)
            
            total_marks = lab_copies + viva + practical_exam
            
            # Calculate grade based on total marks
            grade, grade_point = self.calculate_grade_and_point(total_marks)
            status = "Pass" if total_marks >= 40 else "Fail"
            
            # Update labels
            self.practical_total_marks_label.config(text=f"{total_marks:.2f}")
            self.practical_grade_label.config(text=grade)
            self.practical_grade_point_label.config(text=f"{grade_point:.1f}")
            
            if status == "Fail":
                self.practical_status_label.config(text=status, foreground="red")
            else:
                self.practical_status_label.config(text=status, foreground="green")
            
            return total_marks, grade, grade_point, status
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for marks!")
            return None

    def calculate_grade_and_point(self, total_marks):
        """Calculate grade and grade point based on marks"""
        if total_marks >= 90:
            return "O", 10.0
        elif total_marks >= 80:
            return "A+", 9.0
        elif total_marks >= 70:
            return "A", 8.0
        elif total_marks >= 60:
            return "B+", 7.0
        elif total_marks >= 55:
            return "B", 6.0
        elif total_marks >= 50:
            return "C", 5.0
        elif total_marks >= 45:
            return "P", 4.0
        elif total_marks >= 40:
            return "P", 4.0
        else:
            return "F", 0.0

    def save_theory_grade(self):
        """Save theory grade to database"""
        result = self.calculate_theory_grade()
        if not result:
            return
        
        total_marks, grade, grade_point, status = result
        
        student_display = self.theory_student_combo.get()
        semester = self.theory_semester_combo.get()
        subject_display = self.theory_subject_combo.get()
        
        if not student_display or not semester or not subject_display:
            messagebox.showerror("Error", "Please select student, semester and subject!")
            return
        
        student_id = student_display.split(' - ')[0]
        subject_code = subject_display.split(' - ')[0]
        
        try:
            internal1 = float(self.theory_internal1_entry.get() or 0)
            internal2 = float(self.theory_internal2_entry.get() or 0)
            presentation = float(self.theory_presentation_entry.get() or 0)
            assignment1 = float(self.theory_assignment1_entry.get() or 0)
            assignment2 = float(self.theory_assignment2_entry.get() or 0)
            external = float(self.theory_external_entry.get() or 0)
            
            back_paper = 1 if status == "Fail" else 0
            academic_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            
            # Insert or update grade
            self.cursor.execute('''
                INSERT OR REPLACE INTO theory_grades 
                (student_id, subject_code, semester, academic_year,
                 internal1_marks, internal2_marks, presentation_marks, assignment1_marks, assignment2_marks,
                 external_marks, total_marks, grade, grade_point, result_status, back_paper)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, subject_code, semester, academic_year,
                  internal1, internal2, presentation, assignment1, assignment2,
                  external, total_marks, grade, grade_point, status, back_paper))
            
            self.conn.commit()
            messagebox.showinfo("Success", "Theory grade saved successfully!")
            self.load_theory_grades()
            self.calculate_theory_sgpa()
            self.clear_theory_form()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for marks!")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

    def save_practical_grade(self):
        """Save practical grade to database"""
        result = self.calculate_practical_grade()
        if not result:
            return
        
        total_marks, grade, grade_point, status = result
        
        student_display = self.practical_student_combo.get()
        semester = self.practical_semester_combo.get()
        subject_display = self.practical_subject_combo.get()
        
        if not student_display or not semester or not subject_display:
            messagebox.showerror("Error", "Please select student, semester and subject!")
            return
        
        student_id = student_display.split(' - ')[0]
        subject_code = subject_display.split(' - ')[0]
        
        try:
            lab_copies = float(self.practical_lab_copies_entry.get() or 0)
            viva = float(self.practical_viva_entry.get() or 0)
            practical_exam = float(self.practical_exam_entry.get() or 0)
            
            back_paper = 1 if status == "Fail" else 0
            academic_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            
            # Insert or update grade
            self.cursor.execute('''
                INSERT OR REPLACE INTO practical_grades 
                (student_id, subject_code, semester, academic_year,
                 lab_copies_marks, viva_marks, practical_exam_marks, total_marks, grade, grade_point, result_status, back_paper)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, subject_code, semester, academic_year,
                  lab_copies, viva, practical_exam, total_marks, grade, grade_point, status, back_paper))
            
            self.conn.commit()
            messagebox.showinfo("Success", "Practical grade saved successfully!")
            self.load_practical_grades()
            self.clear_practical_form()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for marks!")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

    def calculate_theory_sgpa(self):
        """Calculate SGPA for theory subjects in current semester"""
        student_display = self.theory_student_combo.get()
        semester = self.theory_semester_combo.get()
        
        if not student_display or not semester:
            return
        
        student_id = student_display.split(' - ')[0]
        
        try:
            # Calculate SGPA for theory subjects
            self.cursor.execute('''
                SELECT SUM(s.credits * t.grade_point), SUM(s.credits)
                FROM theory_grades t
                JOIN subjects s ON t.subject_code = s.subject_code
                WHERE t.student_id = ? AND t.semester = ? AND t.result_status = 'Pass'
            ''', (student_id, semester))
            
            result = self.cursor.fetchone()
            if result and result[1] and result[1] > 0:
                total_grade_points, total_credits = result
                sgpa = total_grade_points / total_credits
                
                self.theory_credits_label.config(text=str(total_credits))
                self.theory_sgpa_label.config(text=f"{sgpa:.2f}")
            else:
                self.theory_credits_label.config(text="0")
                self.theory_sgpa_label.config(text="0.00")
                
        except sqlite3.Error:
            self.theory_credits_label.config(text="0")
            self.theory_sgpa_label.config(text="0.00")

    # Event handlers
    def on_department_select(self, event):
        """Handle department selection"""
        selected = self.dept_tree.selection()
        if selected:
            item = selected[0]
            values = self.dept_tree.item(item, 'values')
            
            self.clear_department_form()
            
            self.dept_id_entry.insert(0, values[0])
            self.dept_name_entry.insert(0, values[1])
            self.hod_entry.insert(0, values[2])
            self.est_year_entry.insert(0, values[3])

    def on_subject_select(self, event):
        """Handle subject selection"""
        selected = self.subject_tree.selection()
        if selected:
            item = selected[0]
            values = self.subject_tree.item(item, 'values')
            
            self.clear_subject_form()
            
            self.sub_code_entry.insert(0, values[0])
            self.sub_name_entry.insert(0, values[1])
            
            # Find department display string
            dept_id = values[2]
            self.cursor.execute("SELECT dept_name FROM departments WHERE dept_id=?", (dept_id,))
            dept_data = self.cursor.fetchone()
            if dept_data:
                dept_display = f"{dept_id} - {dept_data[0]}"
                self.sub_dept_combo.set(dept_display)
            
            self.sub_semester_combo.set(values[3])
            self.sub_credits_combo.set(values[4])
            self.sub_type_combo.set(values[5])
            self.sub_max_marks_entry.insert(0, values[6])

    def on_student_select(self, event):
        """Handle student selection with section"""
        selected = self.student_tree.selection()
        if selected:
            item = selected[0]
            values = self.student_tree.item(item, 'values')
            
            self.clear_student_form()
            
            self.stu_id_entry.insert(0, values[0])
            self.stu_name_entry.insert(0, values[1])
            
            # Find department display string
            dept_id = values[2]
            self.cursor.execute("SELECT dept_name FROM departments WHERE dept_id=?", (dept_id,))
            dept_data = self.cursor.fetchone()
            if dept_data:
                dept_display = f"{dept_id} - {dept_data[0]}"
                self.stu_dept_combo.set(dept_display)
            
            self.stu_batch_combo.set(values[3])
            self.stu_semester_combo.set(values[4])
            self.stu_section_combo.set(values[5])
            self.stu_email_entry.insert(0, values[6])
            self.stu_phone_entry.insert(0, values[7])
            self.stu_status_combo.set(values[8])
            
            # Update section combobox
            self.update_section_combobox()

    def on_theory_student_select(self, event):
        """Handle theory student selection"""
        student_display = self.theory_student_combo.get()
        if student_display:
            student_id = student_display.split(' - ')[0]
            
            # Get student info
            self.cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
            student_data = self.cursor.fetchone()
            
            if student_data:
                info_text = f"ID: {student_data[0]} | Name: {student_data[1]}\nDepartment: {student_data[2]} | Batch: {student_data[3]} | Semester: {student_data[4]}"
                self.theory_student_info.config(text=info_text)
                
                # Set current semester
                self.theory_semester_combo.set(student_data[4])
                self.load_theory_grades()
                self.calculate_theory_sgpa()

    def on_practical_student_select(self, event):
        """Handle practical student selection"""
        student_display = self.practical_student_combo.get()
        if student_display:
            student_id = student_display.split(' - ')[0]
            
            # Get student info
            self.cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
            student_data = self.cursor.fetchone()
            
            if student_data:
                info_text = f"ID: {student_data[0]} | Name: {student_data[1]}\nDepartment: {student_data[2]} | Batch: {student_data[3]} | Semester: {student_data[4]}"
                self.practical_student_info.config(text=info_text)
                
                # Set current semester
                self.practical_semester_combo.set(student_data[4])
                self.load_practical_grades()

    def on_theory_semester_select(self, event):
        """Handle theory semester selection"""
        self.load_theory_grades()
        self.calculate_theory_sgpa()

    def on_practical_semester_select(self, event):
        """Handle practical semester selection"""
        self.load_practical_grades()

    def on_student_dept_select(self, event=None):
        """Update sections when department is selected"""
        self.update_section_combobox()

    def on_student_batch_select(self, event=None):
        """Update sections when batch is selected"""
        self.update_section_combobox()

    def on_student_semester_select(self, event=None):
        """Update sections when semester is selected"""
        self.update_section_combobox()

    def update_section_combobox(self):
        """Update section combobox based on selected department, batch, and semester"""
        department = self.stu_dept_combo.get()
        batch = self.stu_batch_combo.get()
        semester = self.stu_semester_combo.get()
        
        if department and batch and semester:
            dept_id = department.split(' - ')[0]
            
            # Query sections for the selected department, batch, and semester
            self.cursor.execute('''
                SELECT section_name FROM sections 
                WHERE department = ? AND batch = ? AND semester = ?
            ''', (dept_id, int(batch), int(semester)))
            
            sections = [row[0] for row in self.cursor.fetchall()]
            self.stu_section_combo['values'] = sections
            
            if sections:
                self.stu_section_combo.set(sections[0])
            else:
                self.stu_section_combo.set('')

    def filter_subjects(self, event=None):
        """Filter subjects by department and semester"""
        department = self.filter_sub_dept_combo.get()
        semester = self.filter_sub_semester_combo.get()
        
        self.load_subjects(department, semester)

    def filter_students(self, event=None):
        """Filter students by department"""
        department = self.filter_stu_dept_combo.get()
        self.load_students(department)

    # Form clearing methods
    def clear_department_form(self):
        """Clear department form"""
        self.dept_id_entry.delete(0, tk.END)
        self.dept_name_entry.delete(0, tk.END)
        self.hod_entry.delete(0, tk.END)
        self.est_year_entry.delete(0, tk.END)

    def clear_subject_form(self):
        """Clear subject form"""
        self.sub_code_entry.delete(0, tk.END)
        self.sub_name_entry.delete(0, tk.END)
        self.sub_dept_combo.set('')
        self.sub_credits_combo.set('')
        self.sub_semester_combo.set('')
        self.sub_type_combo.set('')
        self.sub_max_marks_entry.delete(0, tk.END)
        self.sub_min_marks_entry.delete(0, tk.END)
        self.sub_hours_entry.delete(0, tk.END)
        
        # Set defaults
        self.sub_max_marks_entry.insert(0, "100")
        self.sub_min_marks_entry.insert(0, "40")

    def clear_student_form(self):
        """Clear student form including section"""
        self.stu_id_entry.delete(0, tk.END)
        self.stu_name_entry.delete(0, tk.END)
        self.stu_dept_combo.set('')
        self.stu_batch_combo.set('')
        self.stu_semester_combo.set('')
        self.stu_section_combo.set('')
        self.stu_email_entry.delete(0, tk.END)
        self.stu_phone_entry.delete(0, tk.END)
        self.stu_address_entry.delete(0, tk.END)
        self.stu_blood_combo.set('')
        self.stu_status_combo.set('Active')

    def clear_theory_form(self):
        """Clear theory grade form"""
        self.theory_internal1_entry.delete(0, tk.END)
        self.theory_internal2_entry.delete(0, tk.END)
        self.theory_presentation_entry.delete(0, tk.END)
        self.theory_assignment1_entry.delete(0, tk.END)
        self.theory_assignment2_entry.delete(0, tk.END)
        self.theory_external_entry.delete(0, tk.END)
        
        self.theory_internal_total_label.config(text="-")
        self.theory_total_marks_label.config(text="-")
        self.theory_grade_label.config(text="-")
        self.theory_grade_point_label.config(text="-")
        self.theory_status_label.config(text="-", foreground="black")

    def clear_practical_form(self):
        """Clear practical grade form"""
        self.practical_lab_copies_entry.delete(0, tk.END)
        self.practical_viva_entry.delete(0, tk.END)
        self.practical_exam_entry.delete(0, tk.END)
        
        self.practical_total_marks_label.config(text="-")
        self.practical_grade_label.config(text="-")
        self.practical_grade_point_label.config(text="-")
        self.practical_status_label.config(text="-", foreground="black")

    # Update and delete methods
    def update_department(self):
        """Update department information"""
        dept_id = self.dept_id_entry.get().strip()
        dept_name = self.dept_name_entry.get().strip()
        hod_name = self.hod_entry.get().strip()
        est_year = self.est_year_entry.get().strip()
        
        if not dept_id:
            messagebox.showerror("Error", "Please select a department to update!")
            return
        
        self.cursor.execute('''
            UPDATE departments SET dept_name=?, hod_name=?, established_year=?
            WHERE dept_id=?
        ''', (dept_name, hod_name, est_year, dept_id))
        
        self.conn.commit()
        messagebox.showinfo("Success", "Department updated successfully!")
        self.load_departments()
        self.clear_department_form()

    def update_subject(self):
        """Update subject information"""
        subject_code = self.sub_code_entry.get().strip()
        subject_name = self.sub_name_entry.get().strip()
        department_display = self.sub_dept_combo.get().strip()
        credits = self.sub_credits_combo.get().strip()
        semester = self.sub_semester_combo.get().strip()
        subject_type = self.sub_type_combo.get().strip()
        max_marks = self.sub_max_marks_entry.get().strip() or "100"
        min_marks = self.sub_min_marks_entry.get().strip() or "40"
        teaching_hours = self.sub_hours_entry.get().strip()
        
        if not subject_code:
            messagebox.showerror("Error", "Please select a subject to update!")
            return
        
        department = department_display.split(' - ')[0]
        
        self.cursor.execute('''
            UPDATE subjects SET subject_name=?, credits=?, semester=?, department=?, 
            subject_type=?, max_marks=?, min_pass_marks=?, teaching_hours=?
            WHERE subject_code=?
        ''', (subject_name, int(credits), int(semester), department, subject_type,
              int(max_marks), int(min_marks), teaching_hours, subject_code))
        
        self.conn.commit()
        messagebox.showinfo("Success", "Subject updated successfully!")
        self.load_subjects()
        self.clear_subject_form()

    def update_student(self):
        """Update student information with section"""
        student_id = self.stu_id_entry.get().strip()
        name = self.stu_name_entry.get().strip()
        department_display = self.stu_dept_combo.get().strip()
        batch = self.stu_batch_combo.get().strip()
        semester = self.stu_semester_combo.get().strip()
        section = self.stu_section_combo.get().strip()
        email = self.stu_email_entry.get().strip()
        phone = self.stu_phone_entry.get().strip()
        address = self.stu_address_entry.get().strip()
        blood_group = self.stu_blood_combo.get().strip()
        status = self.stu_status_combo.get().strip()
        
        if not student_id:
            messagebox.showerror("Error", "Please select a student to update!")
            return
        
        department = department_display.split(' - ')[0]
        
        self.cursor.execute('''
            UPDATE students SET name=?, department=?, batch=?, current_semester=?, section=?,
            email=?, phone=?, address=?, blood_group=?, status=?
            WHERE student_id=?
        ''', (name, department, int(batch), int(semester), section, email, phone, address, blood_group, status, student_id))
        
        self.conn.commit()
        messagebox.showinfo("Success", "Student updated successfully!")
        self.load_students()
        self.clear_student_form()
        self.load_departments()

    def delete_department(self):
        """Delete department"""
        dept_id = self.dept_id_entry.get().strip()
        
        if not dept_id:
            messagebox.showerror("Error", "Please select a department to delete!")
            return
        
        # Check if department has students
        self.cursor.execute("SELECT COUNT(*) FROM students WHERE department=?", (dept_id,))
        student_count = self.cursor.fetchone()[0]
        
        if student_count > 0:
            messagebox.showerror("Error", f"Cannot delete department! There are {student_count} students in this department.")
            return
        
        result = messagebox.askyesno("Confirm", "Are you sure you want to delete this department?")
        if result:
            self.cursor.execute("DELETE FROM departments WHERE dept_id=?", (dept_id,))
            self.conn.commit()
            messagebox.showinfo("Success", "Department deleted successfully!")
            self.load_departments()
            self.clear_department_form()

    def delete_subject(self):
        """Delete subject"""
        subject_code = self.sub_code_entry.get().strip()
        
        if not subject_code:
            messagebox.showerror("Error", "Please select a subject to delete!")
            return
        
        # Check if subject has grades
        self.cursor.execute("SELECT COUNT(*) FROM theory_grades WHERE subject_code=?", (subject_code,))
        theory_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM practical_grades WHERE subject_code=?", (subject_code,))
        practical_count = self.cursor.fetchone()[0]
        
        if theory_count > 0 or practical_count > 0:
            messagebox.showerror("Error", "Cannot delete subject! There are grades associated with this subject.")
            return
        
        result = messagebox.askyesno("Confirm", "Are you sure you want to delete this subject?")
        if result:
            self.cursor.execute("DELETE FROM subjects WHERE subject_code=?", (subject_code,))
            self.conn.commit()
            messagebox.showinfo("Success", "Subject deleted successfully!")
            self.load_subjects()
            self.clear_subject_form()

    def delete_student(self):
        """Delete student"""
        student_id = self.stu_id_entry.get().strip()
        
        if not student_id:
            messagebox.showerror("Error", "Please select a student to delete!")
            return
        
        # Check if student has grades
        self.cursor.execute("SELECT COUNT(*) FROM theory_grades WHERE student_id=?", (student_id,))
        theory_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM practical_grades WHERE student_id=?", (student_id,))
        practical_count = self.cursor.fetchone()[0]
        
        result = messagebox.askyesno("Confirm", 
                                   f"Are you sure you want to delete this student?\n"
                                   f"This will also delete {theory_count} theory grades and {practical_count} practical grades.")
        if result:
            # Delete grades first
            self.cursor.execute("DELETE FROM theory_grades WHERE student_id=?", (student_id,))
            self.cursor.execute("DELETE FROM practical_grades WHERE student_id=?", (student_id,))
            
            # Delete student
            self.cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
            self.conn.commit()
            messagebox.showinfo("Success", "Student deleted successfully!")
            self.load_students()
            self.clear_student_form()
            self.load_departments()

    def export_all_students(self):
        """Export all students data to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Students Data"
            )
            
            if filename:
                self.cursor.execute('''
                    SELECT s.student_id, s.name, s.department, d.dept_name, s.batch, s.current_semester, 
                           s.section, s.email, s.phone, s.address, s.blood_group, s.admission_date, s.status
                    FROM students s
                    LEFT JOIN departments d ON s.department = d.dept_id
                    ORDER BY s.department, s.batch, s.current_semester, s.student_id
                ''')
                
                students = self.cursor.fetchall()
                
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Write header
                    writer.writerow([
                        'Student ID', 'Name', 'Department Code', 'Department Name', 
                        'Batch', 'Current Semester', 'Section', 'Email', 'Phone', 
                        'Address', 'Blood Group', 'Admission Date', 'Status'
                    ])
                    
                    # Write data
                    for student in students:
                        writer.writerow(student)
                
                messagebox.showinfo("Success", f"Students data exported successfully to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

    def export_student_report(self):
        """Export detailed student report for selected student"""
        student_display = self.report_student_combo.get()
        if not student_display:
            messagebox.showinfo("Info", "Please select a student to export report!")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Student Report"
            )
            
            if filename:
                student_id = student_display.split(' - ')[0]
                
                # Get student basic info
                self.cursor.execute('''
                    SELECT s.*, d.dept_name 
                    FROM students s 
                    LEFT JOIN departments d ON s.department = d.dept_id 
                    WHERE s.student_id = ?
                ''', (student_id,))
                student_info = self.cursor.fetchone()
                
                # Get all theory grades
                self.cursor.execute('''
                    SELECT t.semester, s.subject_code, s.subject_name, s.credits, s.subject_type,
                           t.internal1_marks, t.internal2_marks, t.presentation_marks, 
                           t.assignment1_marks, t.assignment2_marks, t.external_marks,
                           t.total_marks, t.grade, t.grade_point, t.result_status
                    FROM theory_grades t
                    JOIN subjects s ON t.subject_code = s.subject_code
                    WHERE t.student_id = ?
                    ORDER BY t.semester, s.subject_code
                ''', (student_id,))
                theory_grades = self.cursor.fetchall()
                
                # Get all practical grades
                self.cursor.execute('''
                    SELECT p.semester, s.subject_code, s.subject_name, s.credits, s.subject_type,
                           p.lab_copies_marks, p.viva_marks, p.practical_exam_marks,
                           p.total_marks, p.grade, p.grade_point, p.result_status
                    FROM practical_grades p
                    JOIN subjects s ON p.subject_code = s.subject_code
                    WHERE p.student_id = ?
                    ORDER BY p.semester, s.subject_code
                ''', (student_id,))
                practical_grades = self.cursor.fetchall()
                
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Write student information
                    writer.writerow(["STUDENT INFORMATION"])
                    writer.writerow(["Student ID:", student_info[0]])
                    writer.writerow(["Name:", student_info[1]])
                    writer.writerow(["Department:", f"{student_info[2]} - {student_info[13]}"])
                    writer.writerow(["Batch:", student_info[3]])
                    writer.writerow(["Current Semester:", student_info[4]])
                    writer.writerow(["Section:", student_info[5]])
                    writer.writerow(["Email:", student_info[6]])
                    writer.writerow(["Phone:", student_info[7]])
                    writer.writerow(["Status:", student_info[11]])
                    writer.writerow([])
                    
                    # Write theory grades
                    writer.writerow(["THEORY GRADES"])
                    writer.writerow([
                        "Semester", "Subject Code", "Subject Name", "Credits", "Type",
                        "Internal 1", "Internal 2", "Presentation", "Assignment 1", "Assignment 2",
                        "External", "Total Marks", "Grade", "Grade Point", "Status"
                    ])
                    
                    for grade in theory_grades:
                        writer.writerow(grade)
                    
                    writer.writerow([])
                    
                    # Write practical grades
                    writer.writerow(["PRACTICAL GRADES"])
                    writer.writerow([
                        "Semester", "Subject Code", "Subject Name", "Credits", "Type",
                        "Lab Copies", "Viva", "Practical Exam", "Total Marks", "Grade", 
                        "Grade Point", "Status"
                    ])
                    
                    for grade in practical_grades:
                        writer.writerow(grade)
                
                messagebox.showinfo("Success", f"Student report exported successfully to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")

    def generate_student_report(self, event=None):
        """Generate comprehensive student report with section info"""
        student_display = self.report_student_combo.get()
        if not student_display:
            messagebox.showinfo("Info", "Please select a student to generate report!")
            return
        
        student_id = student_display.split(' - ')[0]
        
        # Get student info with section
        self.cursor.execute('''
            SELECT s.*, d.dept_name, sec.class_teacher 
            FROM students s 
            LEFT JOIN departments d ON s.department = d.dept_id 
            LEFT JOIN sections sec ON s.section = sec.section_name AND s.department = sec.department 
                                   AND s.batch = sec.batch AND s.current_semester = sec.semester
            WHERE s.student_id = ?
        ''', (student_id,))
        student_data = self.cursor.fetchone()
        
        if student_data:
            info_text = f"Student ID: {student_data[0]}\n"
            info_text += f"Name: {student_data[1]}\n"
            info_text += f"Department: {student_data[2]} - {student_data[13]}\n"
            info_text += f"Batch: {student_data[3]}\n"
            info_text += f"Current Semester: {student_data[4]}\n"
            info_text += f"Section: {student_data[5]}\n"
            if student_data[14]:  # Class teacher
                info_text += f"Class Teacher: {student_data[14]}\n"
            info_text += f"Email: {student_data[6]}\n"
            info_text += f"Phone: {student_data[7]}\n"
            info_text += f"Status: {student_data[11]}"
            
            self.report_info_text.delete(1.0, tk.END)
            self.report_info_text.insert(1.0, info_text)
        
        # Clear existing tabs
        for tab in self.report_notebook.tabs():
            self.report_notebook.forget(tab)
        
        # Calculate overall statistics
        total_credits_all = 0
        total_grade_points_all = 0
        current_semester = student_data[4] if student_data else 1
        
        # Generate semester-wise reports
        semesters_with_data = []
        
        # Check theory grades for semesters
        self.cursor.execute("SELECT DISTINCT semester FROM theory_grades WHERE student_id=? ORDER BY semester", (student_id,))
        theory_semesters = [row[0] for row in self.cursor.fetchall()]
        
        # Check practical grades for semesters  
        self.cursor.execute("SELECT DISTINCT semester FROM practical_grades WHERE student_id=? ORDER BY semester", (student_id,))
        practical_semesters = [row[0] for row in self.cursor.fetchall()]
        
        # Combine and get unique semesters
        all_semesters = sorted(set(theory_semesters + practical_semesters))
        
        for semester in all_semesters:
            semesters_with_data.append(semester)
            
            # Create frame for this semester
            semester_frame = ttk.Frame(self.report_notebook)
            self.report_notebook.add(semester_frame, text=f"Semester {semester}")
            
            # Create treeview for this semester
            columns = ("type", "subject", "credits", "total", "grade", "grade_point", "status")
            tree = ttk.Treeview(semester_frame, columns=columns, show="headings", height=12)
            
            headings = {
                "type": "Type",
                "subject": "Subject",
                "credits": "Credits",
                "total": "Total",
                "grade": "Grade",
                "grade_point": "Grade Point",
                "status": "Status"
            }
            
            for col, text in headings.items():
                tree.heading(col, text=text)
                tree.column(col, width=80)
            
            tree.column("subject", width=150)
            tree.column("type", width=80)
            
            tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            semester_credits = 0
            semester_grade_points = 0
            
            # Add theory grades
            self.cursor.execute('''
                SELECT s.subject_name, s.credits, t.total_marks, t.grade, t.grade_point, t.result_status
                FROM theory_grades t
                JOIN subjects s ON t.subject_code = s.subject_code
                WHERE t.student_id = ? AND t.semester = ?
            ''', (student_id, semester))
            
            theory_grades = self.cursor.fetchall()
            for grade in theory_grades:
                subject_name, credits, total, grade_val, grade_point, status = grade
                tree.insert("", tk.END, values=("Theory", subject_name, credits, total, grade_val, grade_point, status))
                
                if status == "Pass":
                    semester_credits += credits
                    semester_grade_points += credits * grade_point
                    total_credits_all += credits
                    total_grade_points_all += credits * grade_point
            
            # Add practical grades
            self.cursor.execute('''
                SELECT s.subject_name, s.credits, p.total_marks, p.grade, p.grade_point, p.result_status
                FROM practical_grades p
                JOIN subjects s ON p.subject_code = s.subject_code
                WHERE p.student_id = ? AND p.semester = ?
            ''', (student_id, semester))
            
            practical_grades = self.cursor.fetchall()
            for grade in practical_grades:
                subject_name, credits, total, grade_val, grade_point, status = grade
                tree.insert("", tk.END, values=("Practical", subject_name, credits, total, grade_val, grade_point, status))
                
                if status == "Pass":
                    semester_credits += credits
                    semester_grade_points += credits * grade_point
                    total_credits_all += credits
                    total_grade_points_all += credits * grade_point
            
            # Calculate semester SGPA
            if semester_credits > 0:
                sgpa = semester_grade_points / semester_credits
                
                sgpa_frame = ttk.Frame(semester_frame)
                sgpa_frame.pack(fill=tk.X, pady=5)
                
                ttk.Label(sgpa_frame, text=f"Semester {semester} SGPA: {sgpa:.2f}", 
                         font=('Arial', 12, 'bold'), foreground="blue").pack()
        
        # Update overall statistics
        if total_credits_all > 0:
            cgpa = total_grade_points_all / total_credits_all
            self.cgpa_label.config(text=f"{cgpa:.2f}")
            self.total_credits_label.config(text=str(total_credits_all))
        else:
            self.cgpa_label.config(text="0.00")
            self.total_credits_label.config(text="0")
        
        self.current_semester_label.config(text=str(current_semester))
        
        if not semesters_with_data:
            messagebox.showinfo("Info", "No grade data found for the selected student!")

def main():
    root = tk.Tk()
    app = ProfessionalCollegeGradeSystem(root)
    root.mainloop() 

if __name__ == "__main__":
    main()