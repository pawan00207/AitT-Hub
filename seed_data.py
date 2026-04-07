from app import app
from models import db, Airline, Airport, Flight, Passenger, Ticket, Delay, User
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        airlines = [
            Airline(airline_code='AA', airline_name='American Airlines'),
            Airline(airline_code='DL', airline_name='Delta Air Lines'),
            Airline(airline_code='UA', airline_name='United Airlines'),
            Airline(airline_code='WN', airline_name='Southwest Airlines'),
            Airline(airline_code='AS', airline_name='Alaska Airlines'),
        ]
        db.session.add_all(airlines)
        db.session.flush()

        airports = [
            Airport(airport_code='JFK', airport_name='John F. Kennedy International', city='New York', state='NY'),
            Airport(airport_code='LAX', airport_name='Los Angeles International', city='Los Angeles', state='CA'),
            Airport(airport_code='ORD', airport_name="O'Hare International", city='Chicago', state='IL'),
            Airport(airport_code='ATL', airport_name='Hartsfield-Jackson Atlanta International', city='Atlanta', state='GA'),
            Airport(airport_code='DFW', airport_name='Dallas/Fort Worth International', city='Dallas', state='TX'),
            Airport(airport_code='MIA', airport_name='Miami International', city='Miami', state='FL'),
            Airport(airport_code='SEA', airport_name='Seattle-Tacoma International', city='Seattle', state='WA'),
            Airport(airport_code='SFO', airport_name='San Francisco International', city='San Francisco', state='CA'),
            Airport(airport_code='LAS', airport_name='Harry Reid International', city='Las Vegas', state='NV'),
            Airport(airport_code='BOS', airport_name='Logan International', city='Boston', state='MA'),
        ]
        db.session.add_all(airports)
        db.session.flush()

        statuses = ['On Time', 'Delayed', 'Cancelled', 'On Time', 'On Time']
        flight_routes = [
            (1, 1, 2), (2, 2, 1), (3, 3, 4), (4, 4, 5), (5, 5, 6),
            (1, 6, 7), (2, 7, 8), (3, 8, 9), (4, 9, 10), (5, 10, 1),
            (1, 2, 3), (2, 3, 4), (3, 4, 1), (4, 1, 5), (5, 5, 2),
            (1, 7, 1), (2, 8, 2), (3, 6, 3), (4, 9, 4), (5, 10, 5),
        ]

        base_date = datetime(2024, 3, 1, 6, 0)
        flights = []
        for i, (al_idx, orig_idx, dest_idx) in enumerate(flight_routes):
            dep = base_date + timedelta(days=i % 10, hours=i % 12)
            arr = dep + timedelta(hours=random.randint(2, 6))
            f = Flight(
                flight_number=f"{airlines[al_idx-1].airline_code}{1000+i}",
                airline_id=airlines[al_idx-1].airline_id,
                origin_airport=airports[orig_idx-1].airport_id,
                dest_airport=airports[dest_idx-1].airport_id,
                scheduled_departure=dep.strftime('%Y-%m-%d %H:%M'),
                scheduled_arrival=arr.strftime('%Y-%m-%d %H:%M'),
                status=random.choice(statuses),
            )
            flights.append(f)
        db.session.add_all(flights)
        db.session.flush()

        passengers = [
            Passenger(full_name='Alice Johnson', email='alice@example.com', phone='555-0101', passport_number='P1001001'),
            Passenger(full_name='Bob Smith', email='bob@example.com', phone='555-0102', passport_number='P1001002'),
            Passenger(full_name='Carol White', email='carol@example.com', phone='555-0103', passport_number='P1001003'),
            Passenger(full_name='David Brown', email='david@example.com', phone='555-0104', passport_number='P1001004'),
            Passenger(full_name='Eva Martinez', email='eva@example.com', phone='555-0105', passport_number='P1001005'),
            Passenger(full_name='Frank Lee', email='frank@example.com', phone='555-0106', passport_number='P1001006'),
            Passenger(full_name='Grace Kim', email='grace@example.com', phone='555-0107', passport_number='P1001007'),
            Passenger(full_name='Henry Davis', email='henry@example.com', phone='555-0108', passport_number='P1001008'),
            Passenger(full_name='Irene Wilson', email='irene@example.com', phone='555-0109', passport_number='P1001009'),
            Passenger(full_name='James Taylor', email='james@example.com', phone='555-0110', passport_number='P1001010'),
        ]
        db.session.add_all(passengers)
        db.session.flush()

        classes = ['Economy', 'Business', 'First']
        prices = {'Economy': 199.99, 'Business': 599.99, 'First': 1199.99}
        ticket_statuses = ['Confirmed', 'Confirmed', 'Confirmed', 'Cancelled']

        tickets = []
        for i in range(15):
            p = passengers[i % len(passengers)]
            f = flights[i % len(flights)]
            cls = random.choice(classes)
            t = Ticket(
                passenger_id=p.passenger_id,
                flight_id=f.flight_id,
                seat_number=f"{random.randint(1,35)}{random.choice('ABCDEF')}",
                booking_date=(base_date - timedelta(days=random.randint(5, 30))).strftime('%Y-%m-%d'),
                ticket_class=cls,
                price=prices[cls] + random.uniform(-20, 50),
                status=random.choice(ticket_statuses),
            )
            tickets.append(t)
        db.session.add_all(tickets)
        db.session.flush()

        reasons = ['Weather', 'Carrier', 'NAS', 'Security', 'Late Aircraft']
        delays = []
        for i in range(10):
            f = flights[i]
            reason = random.choice(reasons)
            mins = random.randint(15, 180)
            d = Delay(
                flight_id=f.flight_id,
                delay_minutes=mins,
                delay_reason=reason,
                weather_delay=mins if reason == 'Weather' else 0,
                carrier_delay=mins if reason == 'Carrier' else 0,
                nas_delay=mins if reason == 'NAS' else 0,
                security_delay=mins if reason == 'Security' else 0,
                late_aircraft_delay=mins if reason == 'Late Aircraft' else 0,
            )
            delays.append(d)
        db.session.add_all(delays)

        users = [
            User(username='admin', password=generate_password_hash('admin123'), role='admin'),
            User(username='alice', password=generate_password_hash('alice123'), role='passenger'),
            User(username='bob', password=generate_password_hash('bob123'), role='passenger'),
        ]
        db.session.add_all(users)

        db.session.commit()
        print("Database seeded successfully!")
        print("Admin login: admin / admin123")
        print("Passenger login: alice / alice123")


if __name__ == '__main__':
    seed()
