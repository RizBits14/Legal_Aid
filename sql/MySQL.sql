-- Create and configure database with proper settings
CREATE DATABASE Legal_Aid;

USE Legal_Aid;

-- Configure MySQL session variables to prevent timeout issues
SET GLOBAL wait_timeout=600;
SET GLOBAL interactive_timeout=600;
SET GLOBAL max_allowed_packet=16777216; -- 16MB

-- Users table - stores basic account information
CREATE TABLE Users (
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
CREATE TABLE LawyerDetails (
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
    
    -- New profile fields for enhanced lawyer profiles
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
CREATE TABLE ClientDetails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    Address TEXT NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(50) NOT NULL,
    Photo VARCHAR(255) NOT NULL,  
    FOREIGN KEY (UserId) REFERENCES Users(id) ON DELETE CASCADE
);

-- ContactMessages table - stores contact form submissions
CREATE TABLE ContactMessages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    subject VARCHAR(200),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('New', 'Pending', 'Solved', 'Rejected') DEFAULT 'New'
);

-- New table for lawyer reviews and ratings
CREATE TABLE LawyerReviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    LawyerId INT NOT NULL,
    ClientId INT NOT NULL,
    Rating TINYINT NOT NULL CHECK (Rating >= 1 AND Rating <= 5),
    ReviewText TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    IsVerified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (LawyerId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_review (LawyerId, ClientId)
);

-- New table for consultation bookings
CREATE TABLE Consultations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    LawyerId INT NOT NULL,
    ClientId INT NOT NULL,
    ConsultationDate DATETIME NOT NULL,
    Duration INT DEFAULT 30, -- in minutes
    Status ENUM('Scheduled', 'Completed', 'Cancelled', 'No-Show') DEFAULT 'Scheduled',
    ConsultationType ENUM('In-Person', 'Video Call', 'Phone Call') DEFAULT 'Video Call',
    Notes TEXT,
    Fee DECIMAL(10,2),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (LawyerId) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (ClientId) REFERENCES Users(id) ON DELETE CASCADE
);

-- Insert default admin account (only admin, no dummy lawyers)
INSERT INTO Users (FirstName, LastName, Email, Password, Phone, UserType)
VALUES ('Admin', 'User', 'admin@legalaid.com', 'scrypt:32768:8:1$0ML0s4MlZJT7ZW5k$64870d670f18ce0c304daab61aaf090e7840933073cc79325431b29d76db2afbf8a6680c1716b31d6cf892b5892ffe5467aa85d2576a9ad16a55d88acf482f91', '0000000000', 'Admin');

-- Create indexes for better performance
CREATE INDEX idx_lawyer_specialization ON LawyerDetails(Specialization);
CREATE INDEX idx_lawyer_experience ON LawyerDetails(YearsOfExperience);
CREATE INDEX idx_lawyer_rating ON LawyerDetails(Rating);
CREATE INDEX idx_lawyer_verification ON LawyerDetails(VerificationStatus);
CREATE INDEX idx_consultation_date ON Consultations(ConsultationDate);
CREATE INDEX idx_review_rating ON LawyerReviews(Rating);
