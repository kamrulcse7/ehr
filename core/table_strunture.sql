CREATE TABLE system_settings (
  id int PRIMARY KEY AUTO_INCREMENT,
  cid varchar(50) NOT NULL,
  s_group varchar(100) NOT NULL,
  s_key varchar(100) NOT NULL,
  s_value varchar(255) NOT NULL,
  note text DEFAULT NULL,
  status_type enum('active','inactive') DEFAULT 'active',
  created_on timestamp NOT NULL DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='System Configuration Table';

CREATE TABLE modules (
  id int PRIMARY KEY AUTO_INCREMENT,
  module_id varchar(30) NOT NULL UNIQUE COMMENT 'Unique code e.g. HR_EMP, HR_ATT',
  module_name varchar(100) NOT NULL COMMENT 'Display title in UI',
  parent_module_id varchar(30) DEFAULT NULL COMMENT 'NULL for Main Menu, parent module_id for Sub-menu',
  module_group varchar(100) DEFAULT NULL COMMENT 'HR, Finance, Office, Security',
  icon varchar(100) DEFAULT NULL COMMENT 'Frontend icon name',
  is_clickable tinyint(1) DEFAULT 1 COMMENT 'Whether this module is clickable in the UI',
  route_path varchar(255) DEFAULT NULL COMMENT 'Only set when is_clickable=TRUE',
  display_order int(11) DEFAULT 0 COMMENT 'UI ordering',
  note text DEFAULT NULL,
  status_type varchar(20) DEFAULT 'ACTIVE',
  created_on datetime DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on datetime DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Application modules and sub-modules for dynamic navigation & role-based access control';

CREATE TABLE roles (
  id int PRIMARY KEY AUTO_INCREMENT,
  role_id varchar(30) NOT NULL UNIQUE,
  role_name varchar(100) NOT NULL,
  note text DEFAULT NULL,
  status_type varchar(20) DEFAULT 'ACTIVE',
  created_on datetime DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on datetime DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='User roles or job titles';

CREATE TABLE role_module_permissions (
  id int PRIMARY KEY AUTO_INCREMENT,
  role_id varchar(30) NOT NULL COMMENT 'References roles.role_id',
  module_id varchar(30) NOT NULL COMMENT 'References modules.module_id',
  can_view tinyint(1) DEFAULT 1 COMMENT 'Permission to see in menu & view list/page',
  can_add tinyint(1) DEFAULT 0 COMMENT 'Permission to create new record',
  can_edit tinyint(1) DEFAULT 0 COMMENT 'Permission to update record',
  can_delete tinyint(1) DEFAULT 0 COMMENT 'Permission to delete record',
  can_export tinyint(1) DEFAULT 0 COMMENT 'Permission to export Excel/PDF/CSV',
  can_import tinyint(1) DEFAULT 0 COMMENT 'Permission to bulk import data from Excel/CSV',
  can_print tinyint(1) DEFAULT 0 COMMENT 'Permission to print report/voucher/document',
  can_approve tinyint(1) DEFAULT 0 COMMENT 'Permission to approve workflow/transaction (e.g. Leave, Salary, Transfer)',
  can_reject tinyint(1) DEFAULT 0 COMMENT 'Permission to reject workflow/transaction',
  can_upload tinyint(1) DEFAULT 0 COMMENT 'Permission to upload files/attachments',
  can_download tinyint(1) DEFAULT 0 COMMENT 'Permission to download files/attachments',
  note text DEFAULT NULL,
  status_type varchar(20) DEFAULT 'ACTIVE',
  created_on datetime DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on datetime DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Granular role-based permissions for modules and sub-modules';

CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cid VARCHAR(50) DEFAULT NULL COMMENT 'NULL for SYSTEM, required for COMPANY',
  user_id VARCHAR(30) NOT NULL UNIQUE COMMENT 'Unique system login ID',
  user_name VARCHAR(100) NOT NULL COMMENT 'Display name / Full name',
  user_pass VARCHAR(255) NOT NULL COMMENT 'Hashed password',
  role_id VARCHAR(30) NOT NULL COMMENT 'References roles.role_id',
  emp_id VARCHAR(30) DEFAULT NULL COMMENT 'Optional reference to employees.emp_id for self-service portal',
  email VARCHAR(150) DEFAULT NULL,
  mobile VARCHAR(20) DEFAULT NULL,
  profile_image VARCHAR(255) DEFAULT NULL,
  sync_code VARCHAR(50) DEFAULT NULL COMMENT 'Biometric/External Sync Code',
  sync_count INT DEFAULT 0 COMMENT 'Total sync iterations for mobile app or biometric device',
  fcm_token TEXT DEFAULT NULL COMMENT 'Push Notification Token for Mobile App',
  device_id VARCHAR(255) DEFAULT NULL COMMENT 'Bound Mobile Device ID for Security',
  must_change_pass TINYINT(1) DEFAULT 0 COMMENT '1 = Force password change on next login',
  last_login_on DATETIME DEFAULT NULL,
  last_login_ip VARCHAR(45) DEFAULT NULL,
  failed_login_attempts TINYINT DEFAULT 0,
  account_locked_until DATETIME DEFAULT NULL,
  note TEXT DEFAULT NULL,
  status_type VARCHAR(20) DEFAULT 'ACTIVE' COMMENT 'ACTIVE, INACTIVE, BLOCKED',
  created_on DATETIME DEFAULT CURRENT_TIMESTAMP(),
  created_by VARCHAR(50) DEFAULT NULL,
  updated_on DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(),
  updated_by VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='User accounts (both system and company-level)';

CREATE TABLE companies (
  id int PRIMARY KEY AUTO_INCREMENT,
  cid varchar(50) NOT NULL COMMENT 'Company reference',
  company_name varchar(255) NOT NULL COMMENT 'display name',
  legal_name varchar(255) DEFAULT NULL COMMENT 'Legal registered name',
  email varchar(150) DEFAULT NULL COMMENT 'Primary email',
  phone varchar(20) DEFAULT NULL COMMENT 'Phone number',
  website varchar(150) DEFAULT NULL COMMENT 'Website',
  address_line1 text DEFAULT NULL COMMENT 'Address line 1',
  address_line2 text DEFAULT NULL COMMENT 'Address line 2',
  city varchar(100) DEFAULT NULL COMMENT 'City',
  state varchar(100) DEFAULT NULL COMMENT 'State',
  country varchar(100) DEFAULT NULL COMMENT 'Country',
  postal_code varchar(20) DEFAULT NULL COMMENT 'Postal code',
  timezone varchar(50) DEFAULT 'UTC+06:00' COMMENT 'timezone',
  language_code varchar(10) DEFAULT NULL COMMENT 'Language code',
  fiscal_year_start_month tinyint(3) UNSIGNED NOT NULL DEFAULT 1 COMMENT '1=Jan, 7=July etc',
  favicon_url varchar(255) DEFAULT NULL COMMENT 'Company favicon URL',
  logo_url varchar(255) DEFAULT NULL COMMENT 'Company logo URL',
  banner_url varchar(255) DEFAULT NULL COMMENT 'Company banner image URL',
  status_type varchar(20) DEFAULT 'ACTIVE',
  note text DEFAULT NULL,
  created_on timestamp NOT NULL DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Company information master table';

CREATE TABLE company_settings (
  id int PRIMARY KEY AUTO_INCREMENT,
  cid varchar(50) NOT NULL,
  s_group varchar(100) NOT NULL,
  s_key varchar(100) NOT NULL,
  s_value varchar(255) NOT NULL,
  note text DEFAULT NULL,
  status_type enum('active','inactive') DEFAULT 'active',
  created_on timestamp NOT NULL DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Per-company configuration overrides for HR policies, attendance rules, payroll, etc.';

CREATE TABLE company_modules (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cid VARCHAR(50) NOT NULL COMMENT 'References companies.cid',
  module_id VARCHAR(30) NOT NULL COMMENT 'References modules.module_id',
  custom_name VARCHAR(100) DEFAULT NULL COMMENT 'Company specific custom menu title override',
  custom_icon VARCHAR(100) DEFAULT NULL COMMENT 'Company specific icon override',
  custom_route_path VARCHAR(255) DEFAULT NULL COMMENT 'Custom route for company specific feature',
  display_order INT DEFAULT 0 COMMENT 'Company specific menu sorting order',
  valid_until DATE DEFAULT NULL COMMENT 'Subscription/License expiration date (NULL for lifetime)',
  status_type VARCHAR(20) DEFAULT 'ACTIVE' COMMENT 'ACTIVE, INACTIVE, EXPIRED',
  note TEXT DEFAULT NULL,
  created_on DATETIME DEFAULT CURRENT_TIMESTAMP(),
  created_by VARCHAR(50) DEFAULT NULL,
  updated_on DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(),
  updated_by VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Company specific module subscriptions and custom feature overrides';

CREATE TABLE branches (
  id int PRIMARY KEY AUTO_INCREMENT,
  cid varchar(50) NOT NULL COMMENT 'Company reference',
  branch_id varchar(30) NOT NULL,
  branch_name varchar(100) NOT NULL,
  branch_address varchar(255) NOT NULL,
  mobile varchar(20) NOT NULL,
  email varchar(100) NOT NULL,
  note text DEFAULT NULL,
  status_type varchar(20) DEFAULT 'ACTIVE',
  created_on datetime DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on datetime DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Company branches or locations';

CREATE TABLE departments (
  id int PRIMARY KEY AUTO_INCREMENT,
  cid varchar(50) NOT NULL COMMENT 'Company reference',
  department_id varchar(30) NOT NULL,
  department_name varchar(100) NOT NULL,
  note text DEFAULT NULL,
  status_type varchar(20) DEFAULT 'ACTIVE',
  created_on datetime DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on datetime DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Company departments or functional areas';

CREATE TABLE designations (
  id int PRIMARY KEY AUTO_INCREMENT,
  cid varchar(50) NOT NULL COMMENT 'Company reference',
  designation_id varchar(30) NOT NULL,
  designation_name varchar(100) NOT NULL,
  depth int(11) DEFAULT 0 COMMENT '0=Top Level, 1=Subordinate',
  note text DEFAULT NULL,
  status_type varchar(20) DEFAULT 'ACTIVE',
  created_on datetime DEFAULT current_timestamp(),
  created_by varchar(50) DEFAULT NULL,
  updated_on datetime DEFAULT NULL ON UPDATE current_timestamp(),
  updated_by varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Employee designations or roles';

CREATE TABLE employees (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cid VARCHAR(50) NOT NULL COMMENT 'Company reference',
  emp_id VARCHAR(30) NOT NULL UNIQUE COMMENT 'Unique Employee Identification Number',
  emp_name VARCHAR(100) NOT NULL COMMENT 'Full name of the employee',
  card_number VARCHAR(50) DEFAULT NULL COMMENT 'RFID or Proximity Access Card Number',
  emp_type VARCHAR(30) DEFAULT 'PERMANENT' COMMENT 'Employment type: PERMANENT, PROBATIONARY, CONTRACTUAL, etc.',
  emp_department VARCHAR(100) DEFAULT NULL COMMENT 'Department name',
  emp_designation VARCHAR(100) DEFAULT NULL COMMENT 'Position or job title',
  emp_grade VARCHAR(30) DEFAULT NULL COMMENT 'Pay grade or scale level',
  current_branch_id VARCHAR(30) DEFAULT NULL COMMENT 'Current work location, branch, or station ID',
  current_branch_join_date DATE DEFAULT NULL COMMENT 'Joining date at current branch place',
  current_grade_join_date DATE DEFAULT NULL COMMENT 'Effective date of current pay grade',
  mobile VARCHAR(20) NOT NULL COMMENT 'Primary contact mobile number',
  email VARCHAR(150) NOT NULL COMMENT 'Official or primary email address',
  gender VARCHAR(10) DEFAULT NULL COMMENT 'Gender identification',
  dob DATE DEFAULT NULL COMMENT 'Date of birth',
  blood_group VARCHAR(10) DEFAULT NULL COMMENT 'Blood group (e.g., A+, O-, AB+)',
  join_date DATE NOT NULL COMMENT 'Initial joining date in the organization',
  confirmation_date DATE DEFAULT NULL COMMENT 'Date when job was confirmed / made permanent',
  retirement_date DATE DEFAULT NULL COMMENT 'Expected or actual date of retirement',
  edu_qualification VARCHAR(255) DEFAULT NULL COMMENT 'Highest educational qualification summary',
  home_district VARCHAR(100) DEFAULT NULL COMMENT 'Home district / Native district',
  present_address TEXT DEFAULT NULL COMMENT 'Current residential address',
  permanent_address TEXT DEFAULT NULL COMMENT 'Permanent residential address',
  nid_number VARCHAR(50) DEFAULT NULL COMMENT 'National Identity Number (NID / Smart Card / Passport)',
  photo_url VARCHAR(255) DEFAULT NULL COMMENT 'Path or URL of the employee photo',
  note TEXT DEFAULT NULL,
  status_type VARCHAR(20) DEFAULT 'ACTIVE' COMMENT 'ACTIVE, INACTIVE',
  created_on DATETIME DEFAULT CURRENT_TIMESTAMP(),
  created_by VARCHAR(50) DEFAULT NULL,
  updated_on DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(),
  updated_by VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Employee primary records with extended professional and personal profile details';

CREATE TABLE employee_transfers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cid VARCHAR(50) NOT NULL COMMENT 'Company reference',
  emp_id VARCHAR(30) NOT NULL COMMENT 'FK referencing employees.emp_id',

  transfer_order_no VARCHAR(50) NOT NULL COMMENT 'Transfer order tracking / GO reference number',
  transfer_type VARCHAR(30) DEFAULT 'ADMINISTRATIVE' COMMENT 'ADMINISTRATIVE, ON_REQUEST, PROMOTION, DEPUTATION, MUTUAL',
  transfer_reason TEXT DEFAULT NULL COMMENT 'Reason for transfer',
  
  from_branch_id VARCHAR(30) NOT NULL COMMENT 'Previous posting location/branch ID',
  to_branch_id VARCHAR(30) NOT NULL COMMENT 'New target posting location/branch ID',
  
  from_department VARCHAR(100) DEFAULT NULL COMMENT 'Previous department',
  to_department VARCHAR(100) DEFAULT NULL COMMENT 'New department',
  
  from_designation VARCHAR(100) DEFAULT NULL COMMENT 'Previous designation',
  to_designation VARCHAR(100) DEFAULT NULL COMMENT 'New designation',

  from_grade VARCHAR(30) DEFAULT NULL COMMENT 'Previous pay grade (e.g., Grade-9)',
  to_grade VARCHAR(30) DEFAULT NULL COMMENT 'New pay grade (e.g., Grade-6)',
  
  order_date DATE NOT NULL COMMENT 'Official order issued date',
  release_date DATE DEFAULT NULL COMMENT 'Expected/Actual date of release from current posting',
  expected_joining_date DATE DEFAULT NULL COMMENT 'Target date to join at new posting place',
  actual_joining_date DATE DEFAULT NULL COMMENT 'Actual date when employee submitted joining letter',
  joining_status VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING, RELEASED, JOINED, CANCELLED',
  
  attachment_url VARCHAR(255) DEFAULT NULL COMMENT 'Path or URL of scanned PDF/Image order copy',
  attachment_filename VARCHAR(150) DEFAULT NULL COMMENT 'Original file name for display/download',
  approved_on DATETIME DEFAULT NULL COMMENT 'Approval date and time',
  approved_by VARCHAR(100) DEFAULT NULL COMMENT 'Approving authority name or designation',
  
  note TEXT DEFAULT NULL COMMENT 'Additional notes',
  status_type VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING, PROCESSING, COMPLETED, CANCELLED',
  created_on DATETIME DEFAULT CURRENT_TIMESTAMP(),
  created_by VARCHAR(50) DEFAULT NULL,
  updated_on DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(),
  updated_by VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Employee transfer orders, grade upgrades, and deployment logs';


-- =================================================================
-- COMPLETE DEMO DATA FOR BADC (BANGLADESH AGRICULTURAL DEVELOPMENT CORP.)
-- =================================================================

-- 1. Company Information (BADC)
INSERT INTO companies (
  cid, company_name, legal_name, email, phone, website, address_line1, city, country, status_type, created_by
) VALUES (
  'BADC', 'Bangladesh Agricultural Development Corporation', 'Bangladesh Agricultural Development Corporation (BADC)', 'info@badc.gov.bd', '+88029556080', 'https://badc.gov.bd', 'Krishi Bhavan, 49-51 Dilkusha Commercial Area, Dhaka-1000', 'Dhaka', 'Bangladesh', 'ACTIVE', 'SYSTEM'
);

-- 2. Company Settings Overrides
INSERT INTO company_settings (cid, s_group, s_key, s_value, note, status_type, created_by) VALUES
('BADC', 'OFFICE_TIMING', 'START_TIME', '09:00 AM', 'Default office start time', 'active', 'SYSTEM'),
('BADC', 'OFFICE_TIMING', 'END_TIME', '05:00 PM', 'Default office end time', 'active', 'SYSTEM'),
('BADC', 'CALENDAR', 'WEEKEND_DAYS', 'Friday,Saturday', 'Official weekend days', 'active', 'SYSTEM');


-- 4. Branches / Regional Offices
INSERT INTO branches (cid, branch_id, branch_name, branch_address, mobile, email, status_type, created_by) VALUES
('BADC', 'HO_DHAKA', 'Head Office - Krishi Bhavan', '49-51 Dilkusha C/A, Dhaka-1000', '+88029556080', 'ho@badc.gov.bd', 'ACTIVE', 'SYSTEM'),
('BADC', 'REG_CTG', 'Chittagong Regional Office', 'Agrabad Commercial Area, Chittagong', '+88031710000', 'ctg@badc.gov.bd', 'ACTIVE', 'SYSTEM'),
('BADC', 'REG_RAJ', 'Rajshahi Regional Office', 'Natore Road, Rajshahi', '+880721770000', 'raj@badc.gov.bd', 'ACTIVE', 'SYSTEM'),
('BADC', 'REG_KHULNA', 'Khulna Regional Office', 'KDA Avenue, Khulna', '+88041720000', 'khulna@badc.gov.bd', 'ACTIVE', 'SYSTEM');

-- 5. Departments / Divisions
INSERT INTO departments (cid, department_id, department_name, status_type, created_by) VALUES
('BADC', 'DEP_ADMIN', 'Administration Division', 'ACTIVE', 'SYSTEM'),
('BADC', 'DEP_SEED', 'Seed Wing / Seed & Field Division', 'ACTIVE', 'SYSTEM'),
('BADC', 'DEP_IRRIG', 'Irrigation & Engineering Wing', 'ACTIVE', 'SYSTEM'),
('BADC', 'DEP_FINANCE', 'Finance & Accounts Division', 'ACTIVE', 'SYSTEM');

-- 6. Designations
INSERT INTO designations (cid, designation_id, designation_name, depth, status_type, created_by) VALUES
('BADC', 'DESIG_DG', 'Chairman / Director General', 0, 'ACTIVE', 'SYSTEM'),
('BADC', 'DESIG_GM', 'General Manager (GM)', 1, 'ACTIVE', 'SYSTEM'),
('BADC', 'DESIG_CE', 'Chief Engineer', 1, 'ACTIVE', 'SYSTEM'),
('BADC', 'DESIG_DGM', 'Deputy General Manager (DGM)', 2, 'ACTIVE', 'SYSTEM'),
('BADC', 'DESIG_XEN', 'Executive Engineer (XEN)', 3, 'ACTIVE', 'SYSTEM'),
('BADC', 'DESIG_SRENG', 'Assistant Engineer / Senior Officer', 4, 'ACTIVE', 'SYSTEM');


-- 9. Roles
INSERT INTO roles (role_id, role_name, note, status_type, created_by) VALUES
('COMPANY_ADMIN', 'Admin', 'Company Full administrative access', 'ACTIVE', 'SYSTEM'),
('COMPANY_HR_MANAGER', 'HR Manager', 'Manage personnel profiles, transfers, and postings', 'ACTIVE', 'SYSTEM'),
('COMPANY_OFFICER', 'Officer', 'General access to personal self-service portal', 'ACTIVE', 'SYSTEM');

-- 10. Global System Modules Catalog (User Defined Menu Architecture)
INSERT INTO modules (module_id, module_name, parent_module_id, module_group, icon, is_clickable, route_path, display_order, status_type) VALUES
-- 1. Dashboard
('DASHBOARD', 'Dashboard', NULL, 'General', 'dashboard', 1, '/dashboard', 1, 'ACTIVE'),

-- 2. Employee Management
('EMP_MGMT', 'Employee Management', NULL, 'HR', 'badge', 0, NULL, 2, 'ACTIVE'),
('EMPLOYEE_DIR', 'Employee Directory', 'EMP_MGMT', 'HR', 'badge', 1, '/staff/directory', 1, 'ACTIVE'),
('POSTING_TRANS', 'Postings & Transfers', 'EMP_MGMT', 'HR', 'swap_horiz', 1, '/staff/transfers', 2, 'ACTIVE'),

-- 3. Access & Security
('ACCESS_SECURITY', 'Access & Security', NULL, 'System', 'security', 0, NULL, 3, 'ACTIVE'),
('USER_MGMT', 'Users Management', 'ACCESS_SECURITY', 'System', 'manage_accounts', 1, '/admin/users', 1, 'ACTIVE'),
('ROLES_PERM', 'Roles & Permissions', 'ACCESS_SECURITY', 'System', 'key', 1, '/admin/roles', 2, 'ACTIVE'),
('AUDIT_LOGS', 'Audit / Activity Logs', 'ACCESS_SECURITY', 'System', 'history', 1, '/admin/audit-logs', 3, 'ACTIVE'),

-- 4. Reports & Analytics
('REPORTS_ANALYTICS', 'Reports & Analytics', NULL, 'Reports', 'analytics', 0, NULL, 4, 'ACTIVE'),
('EMP_REPORTS', 'Employee Reports', 'REPORTS_ANALYTICS', 'Reports', 'description', 1, '/reports/employees', 1, 'ACTIVE'),
('TRANSFER_LOGS', 'Movement / Transfer Logs', 'REPORTS_ANALYTICS', 'Reports', 'receipt_long', 1, '/reports/transfers', 2, 'ACTIVE'),
('CUSTOM_REPORTS', 'Export / Custom Reports', 'REPORTS_ANALYTICS', 'Reports', 'download', 1, '/reports/custom', 3, 'ACTIVE');

-- 11. Company Module Subscriptions (BADC Subscribed Modules & Optional Custom Overrides)
INSERT INTO company_modules (cid, module_id, custom_name, status_type, created_by) VALUES
('BADC', 'DASHBOARD', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'EMP_MGMT', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'EMPLOYEE_DIR', 'Personnel Directory', 'ACTIVE', 'SYSTEM'), -- Custom name override for BADC
('BADC', 'POSTING_TRANS', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'ACCESS_SECURITY', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'USER_MGMT', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'ROLES_PERM', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'AUDIT_LOGS', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'REPORTS_ANALYTICS', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'EMP_REPORTS', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'TRANSFER_LOGS', NULL, 'ACTIVE', 'SYSTEM'),
('BADC', 'CUSTOM_REPORTS', NULL, 'ACTIVE', 'SYSTEM');

-- 12. Role Permissions (COMPANY_ADMIN Full Access)
INSERT INTO role_module_permissions (
  role_id, module_id, can_view, can_add, can_edit, can_delete, can_export, can_import, can_print, can_approve, can_reject, can_upload, can_download, status_type, created_by
) VALUES
-- System Admin Full System Access Explicit Definitions
('SYSTEM_ADMIN', 'DASHBOARD', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'EMP_MGMT', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'EMPLOYEE_DIR', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'POSTING_TRANS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'ACCESS_SECURITY', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'USER_MGMT', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'ROLES_PERM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'AUDIT_LOGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'REPORTS_ANALYTICS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'EMP_REPORTS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'TRANSFER_LOGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'CUSTOM_REPORTS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'SYSTEM_SETTINGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'ORG_SETUP', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'APP_CONFIGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('SYSTEM_ADMIN', 'NOTIF_SETTINGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
-- Company Admin Standard Permissions
('COMPANY_ADMIN', 'DASHBOARD', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'EMP_MGMT', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'EMPLOYEE_DIR', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'POSTING_TRANS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'ACCESS_SECURITY', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'USER_MGMT', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'ROLES_PERM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'AUDIT_LOGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'REPORTS_ANALYTICS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'EMP_REPORTS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'TRANSFER_LOGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'CUSTOM_REPORTS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'SYSTEM_SETTINGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'ORG_SETUP', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'APP_CONFIGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM'),
('COMPANY_ADMIN', 'NOTIF_SETTINGS', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'ACTIVE', 'SYSTEM');

-- 13. Employees Demo Data
INSERT INTO employees (
  cid, emp_id, emp_name, card_number, emp_type, emp_department, emp_designation, emp_grade, current_branch_id, current_branch_join_date, mobile, email, gender, dob, join_date, status_type, created_by
) VALUES
('BADC', 'EMP-1001', 'Md. Ruhul Amin', 'CARD-001', 'PERMANENT', 'Administration Division', 'General Manager (GM)', 'Grade-3', 'HO_DHAKA', '2020-01-15', '+8801711111111', 'ruhul.amin@badc.gov.bd', 'MALE', '1975-04-12', '2002-06-10', 'ACTIVE', 'SYSTEM'),
('BADC', 'EMP-1002', 'Engr. Farhana Yasmin', 'CARD-002', 'PERMANENT', 'Irrigation & Engineering Wing', 'Executive Engineer (XEN)', 'Grade-6', 'REG_CTG', '2021-03-01', '+8801722222222', 'farhana.yasmin@badc.gov.bd', 'FEMALE', '1984-08-20', '2010-09-15', 'ACTIVE', 'SYSTEM'),
('BADC', 'EMP-1003', 'Tanvir Ahmed Chowdhury', 'CARD-003', 'PERMANENT', 'Seed Wing / Seed & Field Division', 'Assistant Engineer / Senior Officer', 'Grade-9', 'HO_DHAKA', '2022-07-10', '+8801733333333', 'tanvir.ahmed@badc.gov.bd', 'MALE', '1990-11-05', '2016-01-01', 'ACTIVE', 'SYSTEM');

-- 14. User Accounts Demo Data
INSERT INTO users (
  cid, user_id, user_name, user_pass, role_id, emp_id, email, mobile, status_type, created_by
) VALUES
(NULL, 'sysadmin', 'Super System Admin', '1234', 'SYSTEM_ADMIN', NULL, 'sysadmin@system.gov.bd', '+8801700000000', 'ACTIVE', 'SYSTEM'),
('BADC', 'badc_admin', 'BADC System Admin', '123456', 'COMPANY_ADMIN', 'EMP-1001', 'admin@badc.gov.bd', '+8801700000000', 'ACTIVE', 'SYSTEM'),
('BADC', 'badc_hr', 'BADC HR Officer', '123456', 'COMPANY_HR_MANAGER', 'EMP-1002', 'hr@badc.gov.bd', '+8801722222222', 'ACTIVE', 'SYSTEM'),
('BADC', 'badc_emp3', 'Tanvir Ahmed', '123456', 'COMPANY_OFFICER', 'EMP-1003', 'tanvir.ahmed@badc.gov.bd', '+8801733333333', 'ACTIVE', 'SYSTEM');

-- 15. Employee Transfers Demo Data
INSERT INTO employee_transfers (
  cid, emp_id, transfer_order_no, transfer_type, transfer_reason, from_branch_id, to_branch_id, from_department, to_department, from_designation, to_designation, from_grade, to_grade, order_date, expected_joining_date, joining_status, status_type, created_by
) VALUES (
  'BADC', 'EMP-1002', 'GO-BADC-2026/104', 'PROMOTION', 'Transferred to Head Office upon promotion to Executive Engineer', 'REG_CTG', 'HO_DHAKA', 'Irrigation & Engineering Wing', 'Irrigation & Engineering Wing', 'Assistant Engineer', 'Executive Engineer (XEN)', 'Grade-9', 'Grade-6', '2026-08-01', '2026-09-01', 'PENDING', 'PROCESSING', 'SYSTEM');