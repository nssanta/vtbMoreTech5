CREATE TABLE Branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(255),
    name VARCHAR(255),
    category VARCHAR(255),
    address VARCHAR(255),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    work_time JSON
);
