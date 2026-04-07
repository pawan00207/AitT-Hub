from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Airline(db.Model):
    __tablename__ = 'Airlines'
    airline_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    airline_code = db.Column(db.Text, nullable=False)
    airline_name = db.Column(db.Text, nullable=False)

    flights = db.relationship('Flight', backref='airline', lazy=True)


class Airport(db.Model):
    __tablename__ = 'Airports'
    airport_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    airport_code = db.Column(db.Text, nullable=False)
    airport_name = db.Column(db.Text, nullable=False)
    city = db.Column(db.Text)
    state = db.Column(db.Text)


class Flight(db.Model):
    __tablename__ = 'Flights'
    flight_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flight_number = db.Column(db.Text, nullable=False)
    airline_id = db.Column(db.Integer, db.ForeignKey('Airlines.airline_id'))
    origin_airport = db.Column(db.Integer, db.ForeignKey('Airports.airport_id'))
    dest_airport = db.Column(db.Integer, db.ForeignKey('Airports.airport_id'))
    scheduled_departure = db.Column(db.Text)
    scheduled_arrival = db.Column(db.Text)
    status = db.Column(db.Text, default='On Time')

    origin = db.relationship('Airport', foreign_keys=[origin_airport], backref='departing_flights')
    destination = db.relationship('Airport', foreign_keys=[dest_airport], backref='arriving_flights')
    delays = db.relationship('Delay', backref='flight', lazy=True)
    tickets = db.relationship('Ticket', backref='flight', lazy=True)


class Passenger(db.Model):
    __tablename__ = 'Passengers'
    passenger_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    phone = db.Column(db.Text)
    passport_number = db.Column(db.Text)

    tickets = db.relationship('Ticket', backref='passenger', lazy=True)


class Ticket(db.Model):
    __tablename__ = 'Tickets'
    ticket_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('Passengers.passenger_id'))
    flight_id = db.Column(db.Integer, db.ForeignKey('Flights.flight_id'))
    seat_number = db.Column(db.Text)
    booking_date = db.Column(db.Text)
    ticket_class = db.Column(db.Text, default='Economy')
    price = db.Column(db.Float)
    status = db.Column(db.Text, default='Confirmed')


class Delay(db.Model):
    __tablename__ = 'Delays'
    delay_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('Flights.flight_id'))
    delay_minutes = db.Column(db.Integer)
    delay_reason = db.Column(db.Text)
    weather_delay = db.Column(db.Integer, default=0)
    carrier_delay = db.Column(db.Integer, default=0)
    nas_delay = db.Column(db.Integer, default=0)
    security_delay = db.Column(db.Integer, default=0)
    late_aircraft_delay = db.Column(db.Integer, default=0)


class User(db.Model, UserMixin):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, default='passenger')

    def get_id(self):
        return str(self.user_id)
