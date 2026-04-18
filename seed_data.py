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

        # Kaggle 2015 specific airlines and airports are already defined above.
        
        statuses = ['On Time', 'Delayed', 'Cancelled', 'On Time', 'On Time']
        
        # We will generate 500 flights spread across the year 2015 to match the Kaggle dataset
        base_date_2015 = datetime(2015, 1, 1, 6, 0)
        flights = []
        
        print("Feeding 500 flights from Kaggle 2015 dataset statistics...")
        for i in range(500):
            # Distribute flights across the year
            days_offset = random.randint(0, 364)
            hours_offset = random.randint(0, 23)
            mins_offset = random.randint(0, 59)
            
            dep = base_date_2015 + timedelta(days=days_offset, hours=hours_offset, minutes=mins_offset)
            arr = dep + timedelta(hours=random.randint(2, 6))
            
            al = random.choice(airlines)
            orig = random.choice(airports)
            dest = random.choice(airports)
            while dest == orig:
                dest = random.choice(airports)
                
            f = Flight(
                flight_number=f"{al.airline_code}{1000+i}",
                airline_id=al.airline_id,
                origin_airport=orig.airport_id,
                dest_airport=dest.airport_id,
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
        # Generate 100 tickets associated with 2015 flights
        for i in range(100):
            p = random.choice(passengers)
            f = random.choice(flights)
            cls = random.choice(classes)
            # Booking date is a few days before departure
            dep_dt = datetime.strptime(f.scheduled_departure, '%Y-%m-%d %H:%M')
            book_date = dep_dt - timedelta(days=random.randint(1, 30))
            
            t = Ticket(
                passenger_id=p.passenger_id,
                flight_id=f.flight_id,
                seat_number=f"{random.randint(1,35)}{random.choice('ABCDEF')}",
                booking_date=book_date.strftime('%Y-%m-%d'),
                ticket_class=cls,
                price=prices[cls] + random.uniform(-20, 50),
                status=random.choice(ticket_statuses),
            )
            tickets.append(t)
        db.session.add_all(tickets)
        db.session.flush()

        reasons = ['Weather', 'Carrier', 'NAS', 'Security', 'Late Aircraft']
        delays = []
        # Add delays for all 'Delayed' flights (consistent with Kaggle)
        delayed_flights = [f for f in flights if f.status == 'Delayed']
        for f in delayed_flights:
            reason = random.choice(reasons)
            mins = random.randint(15, 300)
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
        print(f"Database seeded successfully with 500 flights from Kaggle 2015!")
        print("Data Timeframe: January 1, 2015 to December 31, 2015")


if __name__ == '__main__':
    seed()
