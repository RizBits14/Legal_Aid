CREATE DATABASE Legal_Aid;

USE Legal_Aid;

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

CREATE TABLE LawyerDetails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    LicenseNumber VARCHAR(50) NOT NULL UNIQUE,
    LicenseProof VARCHAR(255) NOT NULL,  -- Path to uploaded license document
    Specialization VARCHAR(100) NOT NULL,
    YearsOfExperience INT NOT NULL,
    VerificationStatus ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    VerifiedBy INT,  -- References Admin who verified
    VerificationDate TIMESTAMP NULL,
    FOREIGN KEY (UserId) REFERENCES Users(id),
    FOREIGN KEY (VerifiedBy) REFERENCES Users(id)
);

CREATE TABLE ClientDetails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    Address TEXT NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(50) NOT NULL,
    FOREIGN KEY (UserId) REFERENCES Users(id)
);

-- Insert default admin account
INSERT INTO Users (UserType, FirstName, LastName, Email, Password, Phone)
VALUES ('Admin', 'System', 'Administrator', 'admin@legalaid.com', 'pbkdf2:sha256:600000$VxZUzHAF$7a1b65a7f68406d0b2574fe7407c89fd6284c5c9c750db292d087ac5305e9fdb', '1234567890');


