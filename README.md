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
### Flexible Tasks Table

| Variable Name         | Variable Type | Variable Range (Optional)                                        | Description |
|-----------------------|---------------|-------------------------------------------------------------------|-------------|
| task_id              | int          | —                                                                 | Unique task identifier |
| user_id              | int          | —                                                                 | ID of the user who created the task |
| task_type            | int          | ["work", "rest", "food", "fun"]                                   | Type of task |
| task_deadline        | datetime     | —                                                                 | Task deadline |
| task_priority        | int          | [1, 2, 3]                                                         | Task priority level |
| expected_duration    | int          | —                                                                 | Expected duration in minutes |
| expected_difficulty  | int          | [1, 2, 3, 4, 5]                                                   | Self-assessed task difficulty |
| predicted_energy     | float        | —                                                                 | Predicted energy level at execution |
| predicted_pressure   | float        | —                                                                 | Predicted pressure level at execution |
| assigned_start_time  | datetime     | deadline - assigned_start_time > expected_duration                | AI-assigned start time |
| real_start_time      | datetime     | —                                                                 | Actual start time |
| real_duration        | int          | —                                                                 | Actual duration in minutes |
| real_energy          | float        | —                                                                 | Measured energy level during execution |
| real_pressure        | float        | —                                                                 | Measured pressure level during execution |
| status               | string       | [unassigned, assigned, processing, completed]                     | Task status |
| task_description     | string       | —                                                                 | Description or notes |
| task_location        | string       | —                                                                 | Task location |

---

### Fixed Tasks Table

| Variable Name        | Variable Type | Variable Range (Optional)                   | Description |
|----------------------|---------------|---------------------------------------------|-------------|
| task_id             | int          | —                                           | Unique task identifier |
| user_id             | int          | —                                           | ID of the user |
| task_type           | int          | ["work", "rest", "food", "fun"]            | Type of task |
| task_start_time     | datetime     | —                                           | Fixed start time |
| task_duration       | int          | —                                           | Task duration in minutes |
| expected_difficulty | int          | [1, 2, 3, 4, 5]                            | Self-assessed difficulty |
| predicted_energy    | float        | —                                           | Predicted energy level |
| predicted_pressure  | float        | —                                           | Predicted pressure level |
| real_energy         | float        | —                                           | Actual energy level |
| real_pressure       | float        | —                                           | Actual pressure level |
| status              | string       | [assigned, processing, completed]          | Task status |
| task_description    | string       | —                                           | Description or notes |
| task_location       | string       | —                                           | Task location |

---

### Users Table

| Variable Name   | Variable Type | Variable Range (Optional)                                                                     | Description |
|-----------------|---------------|-----------------------------------------------------------------------------------------------|-------------|
| user_id        | int          | —                                                                                             | Unique user ID |
| user_name      | string       | ≤ 15 characters                                                                               | Username |
| user_password  | string       | ≤ 20 characters, must contain uppercase, lowercase, and numbers simultaneously | User password (encrypted in practice) |

---

### User_stats Table

| Variable Name    | Variable Type | Variable Range (Optional) | Description |
|------------------|---------------|---------------------------|-------------|
| user_id         | int          | —                         | User ID |
| current_time    | datetime     | —                         | Time of the record |
| current_energy  | float        | 0 ~ 5                     | Reported energy level |
| current_pressure| float        | 0 ~ 5                     | Reported pressure level |

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