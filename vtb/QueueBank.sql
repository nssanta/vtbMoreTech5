CREATE TABLE QueueData (
    id INT AUTO_INCREMENT PRIMARY KEY,
    branch_id INT,
    category_id INT,
    start_time DATETIME,
    end_time DATETIME,
    FOREIGN KEY (branch_id) REFERENCES Branches(id),
    FOREIGN KEY (category_id) REFERENCES ServiceCategories(id)
);
