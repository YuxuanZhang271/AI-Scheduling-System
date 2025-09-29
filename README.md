# AI-powered Scheduling Systems

Assignments: <br>
Frontend: sycccccccccccccc, zhaooo1166, KathyKo <br>
Database & Backend: JKnightY, YuxuanZhang271 <br>
Schedular: zhaooo1166, YuxuanZhang271 <br>
Task Evaluation Model: sycccccccccccccc, JKnightY, KathyKo

## Table of Content
- [Database](#database)
- [Frontend](#frontend)
- [Backend](#backend)
- [Scheduler](#scheduler)
- [Task Evaluation Model](#task-evaluation-model)

## Database
Framework: 

## Frontend
Framework: ReactJS

## Backend
Framework: 

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