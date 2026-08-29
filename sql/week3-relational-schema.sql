CREATE DATABASE LibraryDb_Week3;
GO

USE LibraryDb_Week3;
GO

CREATE TABLE Authors
(
    AuthorId INT PRIMARY KEY IDENTITY(1,1),
    FullName NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE Books
(
    BookId INT PRIMARY KEY IDENTITY(1,1),
    Title NVARCHAR(150) NOT NULL,
    AuthorId INT NOT NULL,

    CONSTRAINT FK_Books_Authors
        FOREIGN KEY (AuthorId)
        REFERENCES Authors(AuthorId)
);
GO

INSERT INTO Authors (FullName)
VALUES
('Ali'),
('Hajra'),
('Hajra Ali');
GO

INSERT INTO Books (Title, AuthorId)
VALUES
('C# Fundamentals', 1),
('ASP.NET Core Basics', 1),
('Angular Essentials', 2),
('Frontend Development', 2),
('Database Design', 3),
('Software Architecture', 3);
GO

SELECT
    b.Title,
    a.FullName AS Author
FROM Books b
JOIN Authors a
    ON b.AuthorId = a.AuthorId
ORDER BY a.FullName;
GO

CREATE TABLE Categories
(
    CategoryId INT PRIMARY KEY IDENTITY(1,1),
    CategoryName NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE BookCategories
(
    BookId INT NOT NULL,
    CategoryId INT NOT NULL,

    CONSTRAINT PK_BookCategories
        PRIMARY KEY (BookId, CategoryId),

    CONSTRAINT FK_BookCategories_Books
        FOREIGN KEY (BookId)
        REFERENCES Books(BookId),

    CONSTRAINT FK_BookCategories_Categories
        FOREIGN KEY (CategoryId)
        REFERENCES Categories(CategoryId)
);
GO

INSERT INTO Categories (CategoryName)
VALUES
('Programming'),
('Web Development'),
('Database'),
('Software Engineering');
GO

INSERT INTO BookCategories (BookId, CategoryId)
VALUES
(1, 1),
(1, 4),
(2, 1),
(2, 2),
(3, 2),
(4, 2),
(4, 4),
(5, 3),
(6, 1),
(6, 4);
GO

SELECT
    b.Title,
    c.CategoryName
FROM BookCategories bc
JOIN Books b
    ON bc.BookId = b.BookId
JOIN Categories c
    ON bc.CategoryId = c.CategoryId
WHERE b.BookId = 1;
GO

DELETE FROM Authors
WHERE AuthorId = 1;
GO