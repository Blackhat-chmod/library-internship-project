# Week 3 Authentication Concepts

## Authentication vs Authorization

Authentication means proving who the user is.

Example:
A user enters an email and password and the system checks whether those credentials are correct.

Authorization means deciding what an authenticated user is allowed to do.

Example:
An Admin may be allowed to delete books, while a normal User may only be allowed to view them.

Authentication = Who are you?

Authorization = What are you allowed to do?

## Why Passwords Should Not Be Stored as Plain Text

Passwords should never be stored directly as readable text.

If a database is leaked, plain-text passwords can immediately be read and misused.

Instead, the application should store a secure hash of the password.

## Password Hashing

Password hashing converts a password into a one-way value.

When a user logs in, the entered password is checked against the stored hash.

The original password should not need to be recovered from the database.

## JWT

JWT stands for JSON Web Token.

A JWT is a signed token that can be issued after a successful login.

A JWT has three main parts:

1. Header
2. Payload
3. Signature

The payload can contain claims such as:

- User ID
- Email
- Role

The signature helps the server verify that the token has not been changed.

## JWT Authentication Flow

1. The user sends login credentials.
2. The server checks the password hash.
3. The server issues a JWT.
4. The client stores the JWT.
5. The client sends the JWT with the next request.
6. The server validates the JWT.
7. The server allows or rejects access.

## Claims

Claims are pieces of information about the authenticated user.

Examples:

- User ID
- Email
- Name
- Role

Claims can be used when deciding what a user is allowed to access.

## Role-Based Authorization

Role-based authorization restricts access based on a user's role.

Example roles:

- Admin
- Librarian
- User

Example:

- Admin can add, update, and delete books.
- Librarian can add and update books.
- User can only view books.

## What Could Go Wrong With Plain-Text Passwords

If passwords were stored as plain text and the database was leaked, anyone with access to the database could immediately read every user's password.

This could also affect the user's accounts on other websites if they reused the same password.

## Simple Authentication Sequence

Login request
→ server checks password hash
→ server issues JWT
→ client stores JWT
→ client sends JWT with the next request
→ server validates JWT
→ protected request continues

## Summary

Authentication proves identity.

Authorization controls permissions.

Passwords should be hashed.

JWTs can be used to authenticate API requests.

Claims contain user information.

Roles can restrict what each user is allowed to do.

This week focuses on understanding these concepts. Full authentication implementation will be done later.