-- =====================================================
-- COMPLETE LEGAL AID DATABASE SCHEMA
-- Enhanced version with client dashboard functionality
-- =====================================================

-- Create and configure database with proper settings
CREATE DATABASE IF NOT EXISTS Legal_Aid;

USE Legal_Aid;

-- Configure MySQL session variables to prevent timeout issues
SET GLOBAL wait_timeout=600;
SET GLOBAL interactive_timeout=600;
SET GLOBAL max_allowed_packet=16777216; -- 16MB

-- =====================================================
-- CORE USER MANAGEMENT TABLES
-- =====================================================

-- Users table - stores basic account information
CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserType ENUM('Admin', 'Lawyer', 'Client') NOT NULL,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL,
    Phone VARCHAR(15) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Enhanced LawyerDetails table with additional profile information
CREATE TABLE IF NOT EXISTS LawyerDetails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    LicenseNumber VARCHAR(50) NOT NULL UNIQUE,
    LicenseProof VARCHAR(255) NOT NULL,
    Photo VARCHAR(255) NOT NULL, 
    Specialization VARCHAR(100) NOT NULL,
    YearsOfExperience INT NOT NULL,
    VerificationStatus ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    VerifiedBy INT,  
    VerificationDate TIMESTAMP NULL,
    
    -- Enhanced profile fields for lawyer profiles
    Bio TEXT DEFAULT 'Experienced legal professional dedicated to providing excellent service and achieving the best outcomes for clients.',
    Education TEXT DEFAULT 'Legal education details will be updated by the lawyer.',
    BarAssociation VARCHAR(100) DEFAULT 'State Bar Association',
    OfficeAddress TEXT DEFAULT 'Office address to be updated.',
    ConsultationFee DECIMAL(10,2) DEFAULT 150.00,
    Languages VARCHAR(255) DEFAULT 'English',
    Rating DECIMAL(3,2) DEFAULT 4.5,
    TotalReviews INT DEFAULT 0,
    
    -- Practice areas (JSON format for multiple specializations)
    PracticeAreas TEXT DEFAULT '[]',
    
    -- Achievements and certifications (JSON format)
    Achievements TEXT DEFAULT '[]',
    
    -- Availability and contact preferences
    AvailableHours VARCHAR(100) DEFAULT 'Mon-Fri: 9AM-6PM',
    PreferredContactMethod ENUM('Email', 'Phone', 'Both') DEFAULT 'Both',
    
    FOREIGN KEY (UserId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (VerifiedBy) REFERENCES Users(id)
);

-- ClientDetails table - stores client-specific information
CREATE TABLE IF NOT EXISTS ClientDetails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    Address TEXT NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(50) NOT NULL,
    Photo VARCHAR(255) NOT NULL,  
    FOREIGN KEY (UserId) REFERENCES Users(id) ON DELETE CASCADE
);

-- =====================================================
-- CASE MANAGEMENT SYSTEM
-- =====================================================

-- Cases table - manages legal cases
CREATE TABLE IF NOT EXISTS Cases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ClientId INT NOT NULL,
    LawyerId INT NULL,
    Title VARCHAR(255) NOT NULL,
    Category VARCHAR(100) NOT NULL,
    Description TEXT NOT NULL,
    Status ENUM('Pending', 'Active', 'In Progress', 'Completed', 'Closed') DEFAULT 'Pending',
    Priority ENUM('Low', 'Medium', 'High', 'Urgent') DEFAULT 'Medium',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CompletedAt TIMESTAMP NULL,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (LawyerId) REFERENCES Users(id) ON DELETE SET NULL
);

-- Case Updates table - tracks case progress and communications
CREATE TABLE IF NOT EXISTS CaseUpdates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    CaseId INT NOT NULL,
    UpdatedBy INT NOT NULL,
    UpdateType ENUM('Status Change', 'Note', 'Document Added', 'Appointment Scheduled', 'Payment Received', 'Court Date Set') DEFAULT 'Note',
    UpdateText TEXT NOT NULL,
    IsClientVisible BOOLEAN DEFAULT TRUE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (CaseId) REFERENCES Cases(id) ON DELETE CASCADE,
    FOREIGN KEY (UpdatedBy) REFERENCES Users(id) ON DELETE CASCADE
);

-- =====================================================
-- APPOINTMENT SYSTEM
-- =====================================================

-- Appointments table - manages consultations and meetings
CREATE TABLE IF NOT EXISTS Appointments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ClientId INT NOT NULL,
    LawyerId INT NOT NULL,
    CaseId INT NULL,
    Title VARCHAR(255) DEFAULT 'Legal Consultation',
    AppointmentDate DATE NOT NULL,
    AppointmentTime TIME NOT NULL,
    Duration INT DEFAULT 60, -- in minutes
    MeetingType ENUM('In-Person', 'Video Call', 'Phone Call') DEFAULT 'In-Person',
    Location TEXT,
    Description TEXT,
    Status ENUM('Scheduled', 'Rescheduled', 'Completed', 'Cancelled', 'No-Show') DEFAULT 'Scheduled',
    MeetingLink VARCHAR(500), -- for video calls
    Notes TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (LawyerId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (CaseId) REFERENCES Cases(id) ON DELETE SET NULL
);

-- =====================================================
-- DOCUMENT MANAGEMENT SYSTEM
-- =====================================================

-- Documents table - manages case files and legal documents
CREATE TABLE IF NOT EXISTS Documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ClientId INT NOT NULL,
    LawyerId INT NULL,
    CaseId INT NULL,
    Name VARCHAR(255) NOT NULL,
    Description TEXT,
    FileName VARCHAR(255) NOT NULL,
    FilePath VARCHAR(500) NOT NULL,
    FileSize VARCHAR(50),
    FileType VARCHAR(10),
    Category ENUM('Legal Document', 'Evidence', 'Contract', 'Court Filing', 'Personal Document', 'Other') DEFAULT 'Other',
    IsConfidential BOOLEAN DEFAULT FALSE,
    UploadedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (LawyerId) REFERENCES Users(id) ON DELETE SET NULL,
    FOREIGN KEY (CaseId) REFERENCES Cases(id) ON DELETE SET NULL
);

-- =====================================================
-- LEGAL AID SYSTEM
-- =====================================================

-- Legal Aid Requests table - manages requests for free legal assistance
CREATE TABLE IF NOT EXISTS LegalAidRequests (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ClientId INT NOT NULL,
    CaseType VARCHAR(100) NOT NULL,
    Urgency ENUM('Low', 'Medium', 'High') NOT NULL,
    Income VARCHAR(50) NOT NULL,
    HouseholdSize INT DEFAULT 1,
    Description TEXT NOT NULL,
    SupportingDocuments TEXT, -- JSON array of document paths
    Status ENUM('Pending', 'Under Review', 'Approved', 'Rejected', 'Assigned') DEFAULT 'Pending',
    ReviewedBy INT NULL,
    AssignedLawyerId INT NULL,
    ReviewNotes TEXT,
    SubmittedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ReviewedAt TIMESTAMP NULL,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (ReviewedBy) REFERENCES Users(id) ON DELETE SET NULL,
    FOREIGN KEY (AssignedLawyerId) REFERENCES Users(id) ON DELETE SET NULL
);

-- =====================================================
-- COMMUNICATION SYSTEM
-- =====================================================

-- Contact Messages table - stores contact form submissions
CREATE TABLE IF NOT EXISTS ContactMessages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    subject VARCHAR(200),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('New', 'Pending', 'Solved', 'Rejected') DEFAULT 'New',
    responded_by INT NULL,
    response_notes TEXT,
    FOREIGN KEY (responded_by) REFERENCES Users(id) ON DELETE SET NULL
);

-- Notifications table - system notifications for users
CREATE TABLE IF NOT EXISTS Notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    UserId INT NOT NULL,
    Title VARCHAR(255) NOT NULL,
    Message TEXT NOT NULL,
    Type ENUM('Info', 'Success', 'Warning', 'Error', 'Appointment', 'Case Update', 'Document') DEFAULT 'Info',
    IsRead BOOLEAN DEFAULT FALSE,
    ActionUrl VARCHAR(500), -- URL for clickable notifications
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserId) REFERENCES Users(id) ON DELETE CASCADE
);

-- =====================================================
-- REVIEW AND RATING SYSTEM
-- =====================================================

-- Lawyer Reviews table - client reviews for lawyers
CREATE TABLE IF NOT EXISTS LawyerReviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    LawyerId INT NOT NULL,
    ClientId INT NOT NULL,
    CaseId INT NULL,
    Rating TINYINT NOT NULL CHECK (Rating >= 1 AND Rating <= 5),
    ReviewTitle VARCHAR(200),
    ReviewText TEXT,
    IsAnonymous BOOLEAN DEFAULT FALSE,
    IsVerified BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (LawyerId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (CaseId) REFERENCES Cases(id) ON DELETE SET NULL,
    UNIQUE KEY unique_review (LawyerId, ClientId, CaseId)
);

-- =====================================================
-- PAYMENT AND BILLING SYSTEM
-- =====================================================

-- Payments table - tracks payments and billing
CREATE TABLE IF NOT EXISTS Payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ClientId INT NOT NULL,
    LawyerId INT NOT NULL,
    CaseId INT NULL,
    AppointmentId INT NULL,
    Amount DECIMAL(10,2) NOT NULL,
    Currency VARCHAR(3) DEFAULT 'USD',
    PaymentType ENUM('Consultation Fee', 'Legal Fee', 'Court Costs', 'Document Fee', 'Other') DEFAULT 'Legal Fee',
    PaymentMethod ENUM('Credit Card', 'Bank Transfer', 'PayPal', 'Cash', 'Check') DEFAULT 'Credit Card',
    PaymentStatus ENUM('Pending', 'Completed', 'Failed', 'Refunded') DEFAULT 'Pending',
    TransactionId VARCHAR(100),
    PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Description TEXT,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (LawyerId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (CaseId) REFERENCES Cases(id) ON DELETE SET NULL,
    FOREIGN KEY (AppointmentId) REFERENCES Appointments(id) ON DELETE SET NULL
);

-- =====================================================
-- SYSTEM LOGS AND AUDIT TRAIL
-- =====================================================

-- Activity Logs table - tracks user activities for security and auditing
CREATE TABLE IF NOT EXISTS ActivityLogs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    ActivityType ENUM('Login', 'Logout', 'Case Created', 'Case Updated', 'Document Uploaded', 'Appointment Scheduled', 'Profile Updated', 'Payment Made') NOT NULL,
    ActivityDescription TEXT,
    IPAddress VARCHAR(45),
    UserAgent TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserId) REFERENCES Users(id) ON DELETE CASCADE
);

-- =====================================================
-- DEFAULT DATA INSERTION
-- =====================================================

-- Insert default admin account
INSERT IGNORE INTO Users (FirstName, LastName, Email, Password, Phone, UserType)
VALUES ('Admin', 'User', 'admin@legalaid.com', 'scrypt:32768:8:1$0ML0s4MlZJT7ZW5k$64870d670f18ce0c304daab61aaf090e7840933073cc79325431b29d76db2afbf8a6680c1716b31d6cf892b5892ffe5467aa85d2576a9ad16a55d88acf482f91', '0000000000', 'Admin');

-- Insert sample legal categories for cases
INSERT IGNORE INTO Cases (id, ClientId, LawyerId, Title, Category, Description, Status) VALUES 
(0, 1, NULL, 'Sample Case Categories', 'Reference', 'Available categories: Family Law, Criminal Law, Civil Law, Corporate Law, Personal Injury, Real Estate, Immigration, Labor Law, Intellectual Property, Tax Law', 'Closed');

-- =====================================================
-- DATABASE INDEXES FOR PERFORMANCE
-- =====================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON Users(Email);
CREATE INDEX IF NOT EXISTS idx_users_type ON Users(UserType);

-- LawyerDetails table indexes
CREATE INDEX IF NOT EXISTS idx_lawyer_specialization ON LawyerDetails(Specialization);
CREATE INDEX IF NOT EXISTS idx_lawyer_experience ON LawyerDetails(YearsOfExperience);
CREATE INDEX IF NOT EXISTS idx_lawyer_rating ON LawyerDetails(Rating);
CREATE INDEX IF NOT EXISTS idx_lawyer_verification ON LawyerDetails(VerificationStatus);

-- Cases table indexes
CREATE INDEX IF NOT EXISTS idx_cases_client ON Cases(ClientId);
CREATE INDEX IF NOT EXISTS idx_cases_lawyer ON Cases(LawyerId);
CREATE INDEX IF NOT EXISTS idx_cases_status ON Cases(Status);
CREATE INDEX IF NOT EXISTS idx_cases_category ON Cases(Category);
CREATE INDEX IF NOT EXISTS idx_cases_created ON Cases(CreatedAt);

-- Appointments table indexes
CREATE INDEX IF NOT EXISTS idx_appointments_client ON Appointments(ClientId);
CREATE INDEX IF NOT EXISTS idx_appointments_lawyer ON Appointments(LawyerId);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON Appointments(AppointmentDate);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON Appointments(Status);

-- Documents table indexes
CREATE INDEX IF NOT EXISTS idx_documents_client ON Documents(ClientId);
CREATE INDEX IF NOT EXISTS idx_documents_case ON Documents(CaseId);
CREATE INDEX IF NOT EXISTS idx_documents_type ON Documents(FileType);

-- Notifications table indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user ON Notifications(UserId);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON Notifications(IsRead);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON Notifications(Type);

-- Reviews table indexes
CREATE INDEX IF NOT EXISTS idx_reviews_lawyer ON LawyerReviews(LawyerId);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON LawyerReviews(Rating);
CREATE INDEX IF NOT EXISTS idx_reviews_verified ON LawyerReviews(IsVerified);

-- Legal Aid Requests indexes
CREATE INDEX IF NOT EXISTS idx_legal_aid_client ON LegalAidRequests(ClientId);
CREATE INDEX IF NOT EXISTS idx_legal_aid_status ON LegalAidRequests(Status);
CREATE INDEX IF NOT EXISTS idx_legal_aid_urgency ON LegalAidRequests(Urgency);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for active cases with lawyer information
CREATE OR REPLACE VIEW ActiveCasesView AS
SELECT 
    c.id,
    c.Title,
    c.Category,
    c.Description,
    c.Status,
    c.Priority,
    c.CreatedAt,
    c.UpdatedAt,
    CONCAT(client.FirstName, ' ', client.LastName) AS ClientName,
    client.Email AS ClientEmail,
    CONCAT(lawyer.FirstName, ' ', lawyer.LastName) AS LawyerName,
    lawyer.Email AS LawyerEmail,
    ld.Specialization,
    ld.ConsultationFee
FROM Cases c
JOIN Users client ON c.ClientId = client.id
LEFT JOIN Users lawyer ON c.LawyerId = lawyer.id
LEFT JOIN LawyerDetails ld ON lawyer.id = ld.UserId
WHERE c.Status IN ('Pending', 'Active', 'In Progress');

-- View for lawyer profiles with ratings
CREATE OR REPLACE VIEW LawyerProfilesView AS
SELECT 
    u.id,
    u.FirstName,
    u.LastName,
    u.Email,
    u.Phone,
    ld.LicenseNumber,
    ld.Specialization,
    ld.YearsOfExperience,
    ld.Bio,
    ld.Education,
    ld.OfficeAddress,
    ld.ConsultationFee,
    ld.Languages,
    ld.AvailableHours,
    ld.VerificationStatus,
    ld.Rating,
    ld.TotalReviews,
    ld.Photo
FROM Users u
JOIN LawyerDetails ld ON u.id = ld.UserId
WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Approved';

-- =====================================================
-- STORED PROCEDURES FOR COMMON OPERATIONS
-- =====================================================

DELIMITER //

-- Procedure to update lawyer rating after a new review
CREATE PROCEDURE UpdateLawyerRating(IN lawyer_id INT)
BEGIN
    DECLARE avg_rating DECIMAL(3,2);
    DECLARE review_count INT;
    
    SELECT AVG(Rating), COUNT(*) 
    INTO avg_rating, review_count
    FROM LawyerReviews 
    WHERE LawyerId = lawyer_id AND IsVerified = TRUE;
    
    UPDATE LawyerDetails 
    SET Rating = COALESCE(avg_rating, 4.5),
        TotalReviews = review_count
    WHERE UserId = lawyer_id;
END //

-- Procedure to create a notification
CREATE PROCEDURE CreateNotification(
    IN user_id INT,
    IN title VARCHAR(255),
    IN message TEXT,
    IN notification_type ENUM('Info', 'Success', 'Warning', 'Error', 'Appointment', 'Case Update', 'Document'),
    IN action_url VARCHAR(500)
)
BEGIN
    INSERT INTO Notifications (UserId, Title, Message, Type, ActionUrl)
    VALUES (user_id, title, message, notification_type, action_url);
END //

DELIMITER ;

-- =====================================================
-- DATABASE TRIGGERS
-- =====================================================

DELIMITER //

-- Trigger to create notification when case status changes
CREATE TRIGGER case_status_notification
AFTER UPDATE ON Cases
FOR EACH ROW
BEGIN
    IF OLD.Status != NEW.Status THEN
        CALL CreateNotification(
            NEW.ClientId,
            'Case Status Updated',
            CONCAT('Your case "', NEW.Title, '" status has been changed to: ', NEW.Status),
            'Case Update',
            CONCAT('/client/case/', NEW.id)
        );
    END IF;
END //

-- Trigger to create notification when appointment is scheduled
CREATE TRIGGER appointment_notification
AFTER INSERT ON Appointments
FOR EACH ROW
BEGIN
    -- Notify client
    CALL CreateNotification(
        NEW.ClientId,
        'Appointment Scheduled',
        CONCAT('Your appointment has been scheduled for ', NEW.AppointmentDate, ' at ', NEW.AppointmentTime),
        'Appointment',
        CONCAT('/client/appointment/', NEW.id)
    );
    
    -- Notify lawyer
    CALL CreateNotification(
        NEW.LawyerId,
        'New Appointment',
        CONCAT('New appointment scheduled for ', NEW.AppointmentDate, ' at ', NEW.AppointmentTime),
        'Appointment',
        CONCAT('/lawyer/appointment/', NEW.id)
    );
END //

-- Trigger to update lawyer rating when review is added
CREATE TRIGGER update_rating_after_review
AFTER INSERT ON LawyerReviews
FOR EACH ROW
BEGIN
    CALL UpdateLawyerRating(NEW.LawyerId);
END //

DELIMITER ;

-- =====================================================
-- SECURITY SETTINGS
-- =====================================================

-- Set proper character set and collation
ALTER DATABASE Legal_Aid CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Enable event scheduler for automated tasks
SET GLOBAL event_scheduler = ON;

-- =====================================================
-- FINAL VERIFICATION
-- =====================================================

-- Display created tables
SHOW TABLES;

-- Display table structures for verification
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'Legal_Aid'
ORDER BY TABLE_NAME;

-- Success message
SELECT 'Legal Aid database setup completed successfully!' AS Status;