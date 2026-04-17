# Software Engineer Challenge

## Evaluation Criteria

We will evaluate:

- Best practices: validations, exception handling, intuitive naming, and OOP.
- SOLID principles: separation of concerns, abstraction and scalability, use of interfaces, and dependency inversion.
- Design patterns: one or more design patterns should be implemented to solve the main problem, including choosing the right channels and sending notifications.
- Architecture: good architecture design, well-defined folder structure, clear separation of concerns, scalability, and readiness for minimal changes to support new requirements in the future, such as Routes, Controllers, Services, Repositories, DTOs, and Interfaces.
- Unit testing: tests for each service and each function, with multiple scenarios per function.
- Database: migrations and seeders, foreign keys where applicable, indexing, correct data types and lengths, and loading all catalogs into the database is a plus.
- Challenge execution: fulfillment of requirements, performance and search methods, fault tolerance when sending notifications, and scalability to add more notification channels.

## Notification Test

It is required to create a system capable of receiving messages. Each message will have:

- A category
- A message body

These messages must be forwarded to pre-populated users in the system.

In addition to being subscribed to message categories, users will have specified the channels through which they would like to be notified, such as SMS, E-Mail, or Push Notification.

With this configuration, users should only receive notifications for messages that:

- Match categories they are subscribed to
- Use channels they have configured

## Message Categories

There will be three message categories:

- Sports
- Finance
- Movies

## Notification Channels

There will be three types of notifications, each requiring its own class to manage the sending logic independently:

- SMS
- E-Mail
- Push Notification

It is necessary to design the architecture for sending notifications through various channels. At a minimum, there should be one class for each channel, along with a strategy to select the appropriate channel.

Real messages do not need to be sent through third-party services. The focus is on establishing a structure that can support the sending logic in the future.

## Delivery Log Requirements

It is essential to store all relevant information required to verify that the notification has been successfully delivered to the respective subscriber. This includes:

- Message type
- Notification type
- User data
- Timestamp
- Any other pertinent information

## User Data

No user administration is required. You can use a mock of users in the source code.

Each user must include the following information:

- ID
- Name
- Email
- Phone number
- Subscribed categories: list of all categories the user is subscribed to
- Channels: list of notification channels (`SMS`, `E-Mail`, `Push Notification`)

## User Interface

The user interface must display two main elements:

### 1. Submission Form

A simple form to send a message containing:

- Category: list of available categories
- Message: text area with validation to confirm the message is not empty

### 2. Log History

A list of all log records, sorted from newest to oldest.
