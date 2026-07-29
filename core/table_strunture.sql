CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id VARCHAR(30) NOT NULL,  
  user_name VARCHAR(50) NOT NULL,
  user_pass VARCHAR(255) NOT NULL,
  user_role VARCHAR(50) NOT NULL,
  email VARCHAR(100),
  mobile VARCHAR(20),
  profile_image VARCHAR(255) DEFAULT NULL,
  sync_code VARCHAR(50) DEFAULT NULL COMMENT 'Biometric/External Sync Code',
  sync_count INT DEFAULT 0 COMMENT 'Total sync iterations for mobile app or biometric device',
  fcm_token TEXT DEFAULT NULL COMMENT 'Push Notification Token for Mobile App',
  device_id VARCHAR(255) DEFAULT NULL COMMENT 'Bound Mobile Device ID for Security',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='System users (Admins & Mobile Users) for HRMS';



CREATE TABLE employees (
  id INT PRIMARY KEY AUTO_INCREMENT,
  emp_id VARCHAR(30) NOT NULL COMMENT 'Unique Employee Identification Number',
  emp_name VARCHAR(50) NOT NULL COMMENT 'Full name of the employee',
  card_number VARCHAR(30) DEFAULT NULL COMMENT 'RFID or Proximity Access Card Number',
  emp_type VARCHAR(20) DEFAULT 'PERMANENT' COMMENT 'Employment type: PERMANENT, PROBATIONARY, CONTRACTUAL, etc.',
  emp_department VARCHAR(100) DEFAULT NULL COMMENT 'Department name',
  emp_designation VARCHAR(100) DEFAULT NULL COMMENT 'Position or job title',
  emp_grade VARCHAR(30) DEFAULT NULL COMMENT 'Pay grade or scale level',
  current_posting_place VARCHAR(100) DEFAULT NULL COMMENT 'Current work location, branch, or station',
  current_posting_join_date DATE DEFAULT NULL COMMENT 'Joining date at current posting place',
  current_grade_join_date DATE DEFAULT NULL COMMENT 'Effective date of current pay grade',
  mobile VARCHAR(20) NOT NULL COMMENT 'Primary contact mobile number',
  email VARCHAR(100) NOT NULL COMMENT 'Official or primary email address',
  gender VARCHAR(10) DEFAULT NULL COMMENT 'Gender identification',
  dob DATE DEFAULT NULL COMMENT 'Date of birth',
  blood_group VARCHAR(10) DEFAULT NULL COMMENT 'Blood group (e.g., A+, O-, AB+)',
  join_date DATE NOT NULL COMMENT 'Initial joining date in the organization',
  confirmation_date DATE DEFAULT NULL COMMENT 'Date when job was confirmed / made permanent',
  retirement_date DATE DEFAULT NULL COMMENT 'Expected or actual date of retirement',
  edu_qualification VARCHAR(255) DEFAULT NULL COMMENT 'Highest educational qualification summary',
  home_district VARCHAR(50) DEFAULT NULL COMMENT 'Home district / Native district',
  present_address TEXT DEFAULT NULL COMMENT 'Current residential address',
  permanent_address TEXT DEFAULT NULL COMMENT 'Permanent residential address',
  nid_number VARCHAR(30) DEFAULT NULL COMMENT 'National Identity Number (NID)',
  photo_url VARCHAR(255) DEFAULT NULL COMMENT 'Path or URL of the employee photo',
  note TEXT DEFAULT NULL,
  status_type VARCHAR(20) DEFAULT 'ACTIVE' COMMENT 'ACTIVE, INACTIVE',
  created_on DATETIME DEFAULT CURRENT_TIMESTAMP(),
  created_by VARCHAR(50) DEFAULT NULL,
  updated_on DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(),
  updated_by VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB COMMENT='Employee primary records with extended professional and personal profile details';

CREATE TABLE employee_transfers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  emp_id VARCHAR(30) NOT NULL COMMENT 'FK referencing employees.emp_id',

  transfer_order_no VARCHAR(50) NOT NULL COMMENT 'Transfer order tracking / GO reference number',
  transfer_type VARCHAR(30) DEFAULT 'ADMINISTRATIVE' COMMENT 'ADMINISTRATIVE, ON_REQUEST, PROMOTION, DEPUTATION, MUTUAL',
  transfer_reason TEXT DEFAULT NULL COMMENT 'Reason for transfer',
  
  from_posting_place VARCHAR(100) NOT NULL COMMENT 'Previous posting location/branch',
  to_posting_place VARCHAR(100) NOT NULL COMMENT 'New target posting location/branch',
  
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
) ENGINE=InnoDB COMMENT='Employee transfer orders, grade upgrades, and deployment logs';