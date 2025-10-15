# 📘 AI Scheduling System - Full API Documentation

## Authentication

### **POST /register**  
Register a new user.  

**Parameters**  
- `user_name` (string)  
- `user_password` (string)  

**Response**
```json
{
  "user_id": 1,
  "message": "User registered successfully"
}
```

---

### **POST /login**  
Login and get authentication token.  

**Parameters**  
- `user_name` (string)  
- `user_password` (string)  

**Response**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user_id": 1
}
```

---

### **GET /me**  
Get current logged-in user info. Requires JWT.  

**Header**  
`Authorization: Bearer <token>`  

**Response**
```json
{
  "user_id": 1,
  "user_name": "Alice"
}
```

---

## Task Management

### **GET /tasks?user_id=xxx**  
Fetch all tasks (fixed + flexible) of a user.  

**Response (example)**
```json
[
  {
    "user_id": "68ef5144777e236fa2f89f8f",
    "task_mode": "fixed",
    "task_deadline": "2025-10-20T20:00:00",
    "task_priority": 2,
    "expected_duration": 1.0,
    "expected_difficulty": 3,
  }
]
```

---

### **POST /tasks**  
Create a new task.  

**Flexible Task required fields**  
- `task_type` (enum: work/rest/food/fun)  
- `task_deadline` (datetime)  
- `expected_duration` (int, minutes)  

**Fixed Task required fields**  
- `task_type` (enum: work/rest/food/fun)  
- `task_start_time` (datetime)  
- `task_duration` (int, minutes)  

**Optional fields for both**  
- `task_priority (1-3)`  
- `expected_difficulty (1-5)`  
- `task_description`  
- `task_location`  

**Response**
```json
{
  "task_id": 102,
  "message": "Task created successfully"
}
```

---

### **PUT /tasks/{task_id}**  
Update a task (fixed or flexible).  

**Parameters**  
Same as creation.  

**Response**
```json
{
  "message": "Task updated successfully"
}
```

---

### **DELETE /tasks/{task_id}**  
Delete a task.  

**Response**
```json
{
  "message": "Task deleted"
}
```

---

### **POST /tasks/{task_id}/feedback**  
Submit execution feedback.  

**Parameters**  
- `real_start_time` (datetime)  
- `real_duration` (int, minutes)  
- `real_energy` (float)  
- `real_pressure` (float)  
- `status` (string: unassigned/assigned/processing/completed)  

**Response**
```json
{
  "message": "Feedback submitted"
}
```

---

## AI Scheduling

### **POST /schedule/generate**  
Generate AI-powered recommended schedule.  

**Parameters**  
- `user_id` (int)  
- `date` (string, YYYY-MM-DD)  

**Response**
```json
[
  {
    "task_id": 103,
    "assigned_start_time": "2025-10-03T09:00:00",
    "task_description": "Research",
    "status": "assigned"
  }
]
```

---

### **POST /schedule/adjust**  
Adjust schedule based on user’s natural language command.  

**Parameters**  
- `user_id` (int)  
- `command` (string, e.g. "Move afternoon tasks to evening")  

**Response**
```json
[
  {
    "task_id": 104,
    "assigned_start_time": "2025-10-03T19:00:00",
    "task_description": "Meeting (moved to evening)"
  }
]
```

---

## Energy / Pressure Tracking

### **POST /user_stats**  
Upload user’s energy and pressure levels.  

**Parameters**  
- `user_id` (int)  
- `current_time` (datetime)  
- `current_energy` (float, range 0~5)  
- `current_pressure` (float, range 0~5)  

**Response**
```json
{
  "message": "Stats recorded"
}
```

---

### **GET /user_stats?user_id=xxx&range=week**  
Get historical energy/pressure data.  

**Response**
```json
[
  {
    "current_time": "2025-10-01T09:00:00",
    "current_energy": 4.5,
    "current_pressure": 1.5
  },
  {
    "current_time": "2025-10-01T18:00:00",
    "current_energy": 3.0,
    "current_pressure": 2.0
  }
]
```

---

## Reports

### **GET /reports/daily?user_id=xxx&date=YYYY-MM-DD**  
Get a daily productivity report.  

**Response**
```json
{
  "date": "2025-10-01",
  "completion_rate": 0.85,
  "avg_energy": 3.8,
  "avg_pressure": 2.1,
  "time_distribution": {
    "work": 300,
    "rest": 120,
    "fun": 90,
    "food": 60
  }
}
```

---

### **GET /reports/weekly?user_id=xxx&week=YYYY-W40**  
Get a weekly productivity report.  

**Response**
```json
{
  "week": "2025-W40",
  "completion_trend": [0.7, 0.8, 0.9, 0.85, 0.88, 0.9, 0.87],
  "time_distribution": {
    "work": 1500,
    "rest": 800,
    "fun": 400,
    "food": 300
  },
  "energy_trend": [4.2, 3.9, 4.0, 3.5, 4.1, 3.8, 4.0],
  "pressure_trend": [2.0, 2.1, 2.3, 1.8, 2.2, 2.0, 1.9]
}
```

---

## Database Alignment Notes

- **Flexible vs Fixed Tasks**  
  - Flexible tasks require: `task_deadline` + `expected_duration`  
  - Fixed tasks require: `task_start_time` + `task_duration`  

- **Status field**  
  - Flexible tasks: may include `unassigned`  
  - Fixed tasks: only `assigned`, `processing`, `completed`  

- **Task type (`task_type`)**  
  - API uses string enum: `"work"`, `"rest"`, `"food"`, `"fun"`  
  - DB may internally use integers, but mapping is handled in backend  

- **Energy/Pressure values**  
  - Strictly range: `0 ~ 5`  

- **User password**  
  - Must be ≤ 20 chars, contain uppercase, lowercase, and number  
