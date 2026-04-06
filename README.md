# AirTrack — Airline Reservation & Delay Prediction System

Full-stack DBMS academic project: Python Flask + SQLite + scikit-learn ML.

## Tech Stack
- **Backend**: Python 3.11 + Flask + SQLAlchemy ORM
- **Database**: SQLite (7 relational tables)
- **Frontend**: Jinja2 templates + CSS/JS (dark aviation theme)
- **ML Model**: Random Forest — Kaggle 2015 Flight Delays schema
- **Auth**: Flask-Login (admin / passenger roles)

## Features
- Admin Dashboard: flight CRUD, bookings, passengers, delay records
- Passenger Portal: search flights, book / cancel tickets
- Delay Prediction (ML): Random Forest on Kaggle 2015 schema
- SQL Reports: 5 raw queries shown on-screen

## Run Locally
```bash
pip install -r requirements.txt
python app.py
```
App at http://localhost:5000

## Demo Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Passenger | alice | alice123 |

## ML Features: MONTH, DAY_OF_WEEK, AIRLINE, ORIGIN_AIRPORT, DEST_AIRPORT, SCHEDULED_DEPARTURE, DISTANCE
