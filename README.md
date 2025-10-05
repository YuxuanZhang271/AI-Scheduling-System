# AI-powered Scheduling Systems

Assignments: <br>
Frontend: Yuchen SUN (sycccccccccccccc), Jiahui Zhao (zhaooo1166), Ko Hung-Chi (KathyKo) <br>
Database & Backend: Keyi JIN (JKnightY), Yuxuan Zhang (YuxuanZhang271) <br>
Schedular: Jiahui Zhao (zhaooo1166), Yuxuan Zhang (YuxuanZhang271) <br>
Task Evaluation Model: Yuchen SUN (sycccccccccccccc), Keyi JIN (JKnightY), Ko Hung-Chi (KathyKo)

## Table of Content
- [Database](#database)
- [Frontend](#frontend)
- [Backend](#backend)
- [Scheduler](#scheduler)
- [Task Evaluation Model](#task-evaluation-model)

## Database

**Framework:** MongoDB

**Collections:**
### Fixed Tasks Table

| Name        | Type      | Range                           | Description |
|-------------|-----------|---------------------------------|-------------|
| task_id     | int       | —                               | Unique task identifier |
| user_id     | int       | —                               | ID of the user |
| task_type   | int       | ["work", "rest", "food", "fun"] | Type of task |
| start_time  | datetime  | —                               | Fixed start time, format: `%Y%m%d%H%M` |
| end_time    | datetime  | —                               | Fixed end time, format: `%Y%m%d%H%M` |
| difficulty  | int       | [1, 2, 3, 4, 5]                 | Self-assessed difficulty |
| energy      | float     | —                               | Energy level |
| pressure    | float     | —                               | Pressure level |
| description | string    | —                               | Description or notes |
| location    | string    | —                               | Task location |
---

### Flexible Tasks Table
| Name        | Type      | Range                           | Description             |
|-------------|-----------|---------------------------------|-------------------------|
| task_id     | int       | —                               | Identifier              |
| user_id     | int       | —                               | User ID                 |
| task_type   | int       | ["work", "rest", "food", "fun"] | Type                    |
| start_time  | datetime  | —                               | Start time (%Y%m%d%H%M) |
| duration    | int       | —                               | Duration (minutes)      |
| difficulty  | int       | [1, 2, 3, 4, 5]                 | Difficulty              |
| energy      | float     | —                               | Energy level            |
| pressure    | float     | —                               | Pressure level          |
| deadline    | datetime  | —                               | End time (%Y%m%d%H%M)   |
| priority    | int       | [1, 2, 3]                       | Priority                |
| description | string    | —                               | Description             |
| location    | string    | —                               | Location                |
---

### Users Table
| Name        | Type      | Range                                   | Description |
|-------------|-----------|-----------------------------------------|-------------|
| user_id     | int       | —                                       | User ID     |
| username    | string    | ≤ 15 characters, only letters & numbers | Username    |
| password    | string    | ≤ 20 characters, must uppercase, lowercase & numbers simultaneously | Password (encrypted)  |
---

### User_stats Table
| Name      | Type      | Range | Description     |
|-----------|-----------|-------|-----------------|
| user_id   | int       | —     | User ID         |
| time      | datetime  | —     | Current time    |
| energy    | float     | 0 ~ 5 | Energy level    |
| pressure  | float     | 0 ~ 5 | Pressure level  |
---
     
## Frontend
Framework: ReactJS <br>
Fragments: Timetable, Task Modify Window, AI Chatbot, Daily / Weekly Report Window

## Backend
**Framework:** FastAPI  
**Language:** Python 3.10  
**Environment:** Conda

**Main Components:**

- 🧾 **Task Management API**  
  - Handles CRUD operations for both fixed and flexible tasks.  
  - Interacts with MongoDB to store and retrieve task data.

- ⚡ **AI Scheduling Engine**  
  - Automatically generates daily or weekly timetables based on tasks and user status.  
  - Can integrate machine learning models or rule-based logic for optimization.

## Scheduler
Strategy: 
1. Sort unassigned tasks by firstly deadline, secondly priority. <br>
2. Pick the top task and attempt to assign it.  <br>
3. Travesal time windows between current time and deadline, if not exceed the proportion of work-rest time, put it inside. <br>
4. Shifting, swapping and evaluating. 

## Task Evaluation Model
Training Model: Evolution Algorithm <br>
Options: <br>
1. Functions: Logistic, Gompertz<br>
2. Paramters: Verticle Scale Parameter, Verticle offset, Time Scale Parameter, Time offset <br>

Evaluation Method: MSE