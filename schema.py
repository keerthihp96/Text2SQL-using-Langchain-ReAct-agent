# schema.py

TABLE_SCHEMA = """
You have access to a Snowflake database with the following tables:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLE 1: EMPLOYEES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLUMNS:
  - employee_id   (INT)      : Unique ID (Primary Key)
  - name          (VARCHAR)  : Full name
  - department    (VARCHAR)  : Department — values: Engineering, Marketing, HR, Finance
  - job_title     (VARCHAR)  : Job title
  - salary        (NUMBER)   : Annual salary in USD
  - location      (VARCHAR)  : Office — values: New York, London, Chicago
  - hire_date     (DATE)     : Hire date (YYYY-MM-DD)
  - is_active     (BOOLEAN)  : TRUE if employed, FALSE if not

SAMPLE DATA:
  (1, 'Alice Johnson', 'Engineering', 'Senior Engineer',  95000, 'New York', '2020-03-15', TRUE)
  (2, 'Bob Smith',     'Engineering', 'Junior Engineer',  65000, 'London',   '2022-07-01', TRUE)
  (9, 'Iris Taylor',   'Finance',     'CFO',             120000, 'New York', '2017-04-12', TRUE)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLE 2: DEPARTMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLUMNS:
  - department_id    (INT)      : Unique ID (Primary Key)
  - department_name  (VARCHAR)  : Department name
  - manager_id       (INT)      : FK → EMPLOYEES.employee_id
  - budget           (NUMBER)   : Annual budget in USD
  - location         (VARCHAR)  : Office location

SAMPLE DATA:
  (1, 'Engineering', 1, 500000, 'New York')
  (2, 'Marketing',   3, 300000, 'New York')
  (3, 'HR',          5, 200000, 'London')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLE 3: PROJECTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLUMNS:
  - project_id    (INT)      : Unique ID (Primary Key)
  - project_name  (VARCHAR)  : Project name
  - department_id (INT)      : FK → DEPARTMENTS.department_id
  - start_date    (DATE)     : Start date (YYYY-MM-DD)
  - end_date      (DATE)     : End date (YYYY-MM-DD)
  - budget        (NUMBER)   : Project budget in USD
  - status        (VARCHAR)  : values: active, completed

SAMPLE DATA:
  (1, 'Cloud Migration', 1, '2024-01-01', '2024-06-30', 150000, 'completed')
  (2, 'AI Integration',  1, '2024-03-01', '2024-12-31', 200000, 'active')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLE 4: EMPLOYEE_PROJECTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLUMNS:
  - employee_id      (INT)  : FK → EMPLOYEES.employee_id
  - project_id       (INT)  : FK → PROJECTS.project_id
  - role             (VARCHAR) : Role on project
  - assigned_date    (DATE)    : Date assigned
  - hours_allocated  (INT)     : Hours allocated

SAMPLE DATA:
  (1, 1, 'Tech Lead',    '2024-01-01', 500)
  (1, 2, 'Architect',    '2024-03-01', 600)
  (7, 2, 'Data Engineer','2024-03-01', 450)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RELATIONSHIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  EMPLOYEES.employee_id     → EMPLOYEE_PROJECTS.employee_id
  PROJECTS.project_id       → EMPLOYEE_PROJECTS.project_id
  DEPARTMENTS.department_id → PROJECTS.department_id
  EMPLOYEES.employee_id     → DEPARTMENTS.manager_id

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JOIN EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Employees with their projects
SELECT E.NAME, P.PROJECT_NAME, EP.ROLE
FROM EMPLOYEES E
JOIN EMPLOYEE_PROJECTS EP ON E.EMPLOYEE_ID = EP.EMPLOYEE_ID
JOIN PROJECTS P           ON EP.PROJECT_ID = P.PROJECT_ID;

-- Department budgets with manager names
SELECT D.DEPARTMENT_NAME, D.BUDGET, E.NAME AS MANAGER_NAME
FROM DEPARTMENTS D
JOIN EMPLOYEES E ON D.MANAGER_ID = E.EMPLOYEE_ID;

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULES FOR QUERYING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - Always use UPPERCASE for table and column names
  - Always qualify columns with table alias when joining
  - Use TRUE/FALSE for boolean filters (not 1/0)
  - Use 'YYYY-MM-DD' format for dates
  - Always add LIMIT 100 unless user asks for all records
  - Use INNER JOIN unless question implies optional data (then LEFT JOIN)
"""
