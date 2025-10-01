import sqlite3

def setup_database(DB_PATH):
    """Initialize the team database with sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            email TEXT,
            hire_date DATE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            status TEXT,
            assigned_to INTEGER,
            due_date DATE,
            FOREIGN KEY (assigned_to) REFERENCES employees (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            project_id INTEGER,
            assignee_id INTEGER,
            status TEXT,
            created_date DATE,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (assignee_id) REFERENCES employees (id)
        )
    ''')
    
    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        sample_employees = [
            (1, "Alice Johnson", "Development", "alice@company.com", "2023-01-15"),
            (2, "Bob Smith", "Design", "bob@company.com", "2023-03-20"),
            (3, "Carol Brown", "Marketing", "carol@company.com", "2022-11-10"),
            (4, "David Wilson", "Development", "david@company.com", "2023-05-05")
        ]
        cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", sample_employees)
        
        sample_projects = [
            (1, "Website Redesign", "Complete company website overhaul", "In Progress", 1, "2024-12-31"),
            (2, "Mobile App", "Develop mobile application", "Planning", 2, "2025-03-15"),
            (3, "Marketing Campaign", "Q4 marketing push", "Active", 3, "2024-11-30")
        ]
        cursor.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", sample_projects)
        
        sample_tasks = [
            (1, "Setup development environment", 1, 1, "Completed", "2024-09-01"),
            (2, "Design mockups", 2, 2, "In Progress", "2024-09-15"),
            (3, "Content creation", 3, 3, "Active", "2024-09-10")
        ]
        cursor.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)", sample_tasks)
    
    conn.commit()
    conn.close()
    print("Database setup completed!")