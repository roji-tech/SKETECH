# Attendance API Documentation

This document provides detailed information about the Attendance API endpoints, request/response formats, and usage examples.

## Table of Contents
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [List Attendance Records](#list-attendance-records)
  - [Check In](#check-in)
  - [Check Out](#check-out)
  - [Today's Attendance](#todays-attendance)
  - [Attendance Reports](#attendance-reports)
  - [Overtime Management](#overtime-management)
- [Error Handling](#error-handling)
- [Pagination](#pagination)
- [Filtering](#filtering)

## Authentication

All API endpoints require authentication using JWT (JSON Web Tokens). Include the token in the `Authorization` header:

```
Authorization: JWT <your_token_here>
```

## Base URL

All API endpoints are prefixed with `/api/`.

## Endpoints

### List Attendance Records

Retrieve a paginated list of attendance records.

```
GET /api/attendance/
```

**Query Parameters:**
- `employee_id` (optional): Filter by employee ID
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `status` (optional): Filter by status (e.g., 'present', 'absent', 'late')
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of items per page (default: 20)

**Example Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "employee_id": 1,
      "employee_name": "John Doe",
      "attendance_date": "2023-06-15",
      "attendance_clock_in": "09:00:00",
      "attendance_clock_out": "17:00:00",
      "status": "present",
      "attendance_validated": true
    }
  ]
}
```

### Check In

Record an employee's check-in time.

```
POST /api/attendance/check_in/
```

**Request Body:**
```json
{
  "employee_id": 1,
  "notes": "Starting work",
  "location": "Office"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Checked in successfully"
}
```

### Check Out

Record an employee's check-out time.

```
POST /api/attendance/check_out/
```

**Request Body:**
```json
{
  "employee_id": 1,
  "notes": "Ending work",
  "location": "Office"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Checked out successfully"
}
```

### Today's Attendance

Get today's attendance status for the current user.

```
GET /api/attendance/today/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "employee_id": 1,
  "employee_name": "John Doe",
  "attendance_date": "2023-06-15",
  "attendance_clock_in": "09:00:00",
  "attendance_clock_out": null,
  "status": "present"
}
```

### Attendance Reports

Generate attendance reports.

```
GET /api/reports/attendance/
```

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `employee_id` (optional): Filter by employee ID
- `department_id` (optional): Filter by department ID

**Response (200 OK):**
```json
[
  {
    "employee_id": 1,
    "employee_name": "John Doe",
    "date": "2023-06-15",
    "check_in": "09:00:00",
    "check_out": "17:00:00",
    "status": "present",
    "total_hours": "08:00:00",
    "overtime": "01:30:00"
  }
]
```

### Overtime Management

#### List Overtime Records

```
GET /api/overtime/
```

#### Approve Overtime

```
POST /api/overtime/{id}/approve/
```

## Error Handling

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "status": "error",
  "message": "Detailed error message"
}
```

## Pagination

List endpoints support pagination using the following query parameters:
- `page`: Page number (starts from 1)
- `page_size`: Number of items per page (default: 20)

Pagination response includes metadata:
- `count`: Total number of items
- `next`: URL to the next page (null if last page)
- `previous`: URL to the previous page (null if first page)
- `results`: Array of items

## Filtering

Most list endpoints support filtering using query parameters. For example:

```
GET /api/attendance/?employee_id=1&status=present&start_date=2023-06-01&end_date=2023-06-30
```

## Rate Limiting

- 1000 requests per hour per user
- 10000 requests per hour per IP address
