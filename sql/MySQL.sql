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

-- LawyerDetails table - stores lawyer-specific information
-- Photo is stored as file path rather than binary data to prevent connection issues
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
    FOREIGN KEY (UserId) REFERENCES Users(id),
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
    FOREIGN KEY (UserId) REFERENCES Users(id)
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

-- Insert default admin account
INSERT INTO Users (FirstName, LastName, Email, Password, Phone, UserType)
VALUES ('Admin', 'User', 'admin@legalaid.com', 'scrypt:32768:8:1$0ML0s4MlZJT7ZW5k$64870d670f18ce0c304daab61aaf090e7840933073cc79325431b29d76db2afbf8a6680c1716b31d6cf892b5892ffe5467aa85d2576a9ad16a55d88acf482f91', '0000000000', 'Admin');
