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

CREATE TABLE ClientDetails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    Address TEXT NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(50) NOT NULL,
    Photo VARCHAR(255) NOT NULL,  
    FOREIGN KEY (UserId) REFERENCES Users(id)
);

-- Insert default admin account
INSERT INTO Users (FirstName, LastName, Email, Password, Phone, UserType)
VALUES ('Admin', 'User', 'admin@legalaid.com', 'scrypt:32768:8:1$0ML0s4MlZJT7ZW5k$64870d670f18ce0c304daab61aaf090e7840933073cc79325431b29d76db2afbf8a6680c1716b31d6cf892b5892ffe5467aa85d2576a9ad16a55d88acf482f91', '0000000000', 'Admin');
