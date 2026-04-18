import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'airtrack-secret-key-2024')

# Use absolute path for SQLite to work correctly on Vercel
import os
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'airtrack.db')
if not os.path.exists(os.path.join(basedir, 'instance')):
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, Airline, Airport, Flight, Passenger, Ticket, Delay, User
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not username or not password:
            flash('Username and password are required.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
        else:
            user = User(username=username, password=generate_password_hash(password), role='passenger')
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_flights = Flight.query.count()
    total_tickets = Ticket.query.filter_by(status='Confirmed').count()
    total_revenue = db.session.query(db.func.sum(Ticket.price)).filter_by(status='Confirmed').scalar() or 0
    avg_delay = db.session.query(db.func.avg(Delay.delay_minutes)).scalar() or 0
    total_passengers = Passenger.query.count()

    recent_flights = Flight.query.order_by(Flight.flight_id.desc()).limit(5).all()
    recent_tickets = Ticket.query.order_by(Ticket.ticket_id.desc()).limit(5).all()

    delayed_count = Flight.query.filter_by(status='Delayed').count()
    cancelled_count = Flight.query.filter_by(status='Cancelled').count()
    ontime_count = Flight.query.filter_by(status='On Time').count()

    return render_template('dashboard.html',
        total_flights=total_flights,
        total_tickets=total_tickets,
        total_revenue=round(total_revenue, 2),
        avg_delay=round(avg_delay, 1),
        total_passengers=total_passengers,
        recent_flights=recent_flights,
        recent_tickets=recent_tickets,
        delayed_count=delayed_count,
        cancelled_count=cancelled_count,
        ontime_count=ontime_count,
    )


@app.route('/flights')
@login_required
def flights():
    all_flights = db.session.query(Flight, Airline, Airport, Airport).join(
        Airline, Flight.airline_id == Airline.airline_id
    ).join(
        Airport, Flight.origin_airport == Airport.airport_id, isouter=True
    ).all()

    flights_data = Flight.query.all()
    airlines = Airline.query.all()
    airports = Airport.query.all()
    return render_template('flights.html', flights=flights_data, airlines=airlines, airports=airports)


@app.route('/flights/add', methods=['POST'])
@login_required
@admin_required
def add_flight():
    f = Flight(
        flight_number=request.form['flight_number'],
        airline_id=int(request.form['airline_id']),
        origin_airport=int(request.form['origin_airport']),
        dest_airport=int(request.form['dest_airport']),
        scheduled_departure=request.form['scheduled_departure'],
        scheduled_arrival=request.form['scheduled_arrival'],
        status=request.form.get('status', 'On Time'),
    )
    db.session.add(f)
    db.session.commit()
    flash('Flight added successfully.', 'success')
    return redirect(url_for('flights'))


@app.route('/flights/edit/<int:flight_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_flight(flight_id):
    f = Flight.query.get_or_404(flight_id)
    airlines = Airline.query.all()
    airports = Airport.query.all()
    if request.method == 'POST':
        f.flight_number = request.form['flight_number']
        f.airline_id = int(request.form['airline_id'])
        f.origin_airport = int(request.form['origin_airport'])
        f.dest_airport = int(request.form['dest_airport'])
        f.scheduled_departure = request.form['scheduled_departure']
        f.scheduled_arrival = request.form['scheduled_arrival']
        f.status = request.form.get('status', 'On Time')
        db.session.commit()
        flash('Flight updated.', 'success')
        return redirect(url_for('flights'))
    return render_template('edit_flight.html', flight=f, airlines=airlines, airports=airports)


@app.route('/flights/delete/<int:flight_id>', methods=['POST'])
@login_required
@admin_required
def delete_flight(flight_id):
    f = Flight.query.get_or_404(flight_id)
    Ticket.query.filter_by(flight_id=flight_id).delete()
    Delay.query.filter_by(flight_id=flight_id).delete()
    db.session.delete(f)
    db.session.commit()
    flash('Flight deleted.', 'success')
    return redirect(url_for('flights'))


@app.route('/search_flights', methods=['GET', 'POST'])
@login_required
def search_flights():
    airports = Airport.query.all()
    airlines = Airline.query.all()
    results = []
    if request.method == 'POST':
        origin = request.form.get('origin')
        dest = request.form.get('dest')
        date = request.form.get('date', '')
        query = Flight.query
        if origin:
            query = query.filter(Flight.origin_airport == int(origin))
        if dest:
            query = query.filter(Flight.dest_airport == int(dest))
        if date:
            query = query.filter(Flight.scheduled_departure.like(f"{date}%"))
        results = query.all()
    return render_template('search_flights.html', airports=airports, airlines=airlines, results=results)


@app.route('/book_ticket/<int:flight_id>', methods=['GET', 'POST'])
@login_required
def book_ticket(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        passport = request.form.get('passport_number', '')
        ticket_class = request.form.get('ticket_class', 'Economy')
        seat = request.form.get('seat_number', 'Auto')

        prices_map = {'Economy': 199.99, 'Business': 599.99, 'First': 1199.99}
        price = prices_map.get(ticket_class, 199.99)

        passenger = Passenger.query.filter_by(email=email).first()
        if not passenger:
            passenger = Passenger(full_name=full_name, email=email, phone=phone, passport_number=passport)
            db.session.add(passenger)
            db.session.flush()

        ticket = Ticket(
            passenger_id=passenger.passenger_id,
            flight_id=flight_id,
            seat_number=seat,
            booking_date=datetime.now().strftime('%Y-%m-%d'),
            ticket_class=ticket_class,
            price=price,
            status='Confirmed',
        )
        db.session.add(ticket)
        db.session.commit()
        flash(f'Ticket booked! Ticket ID: {ticket.ticket_id}', 'success')
        return redirect(url_for('my_bookings'))

    return render_template('book_ticket.html', flight=flight)


@app.route('/my_bookings')
@login_required
def my_bookings():
    if current_user.role == 'admin':
        tickets = Ticket.query.order_by(Ticket.ticket_id.desc()).all()
    else:
        passenger = Passenger.query.filter_by(email=current_user.username + '@example.com').first()
        tickets = []
        if passenger:
            tickets = Ticket.query.filter_by(passenger_id=passenger.passenger_id).all()
        else:
            tickets = Ticket.query.order_by(Ticket.ticket_id.desc()).limit(10).all()
    return render_template('my_bookings.html', tickets=tickets)


@app.route('/cancel_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def cancel_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = 'Cancelled'
    db.session.commit()
    flash('Ticket cancelled.', 'info')
    return redirect(url_for('my_bookings'))


@app.route('/passengers')
@login_required
@admin_required
def passengers():
    all_passengers = Passenger.query.all()
    return render_template('passengers.html', passengers=all_passengers)


@app.route('/delays')
@login_required
@admin_required
def delays():
    all_delays = Delay.query.all()
    return render_template('delays.html', delays=all_delays)


@app.route('/predict_delay', methods=['GET', 'POST'])
@login_required
def predict_delay():
    from ml_model import predict_delay as ml_predict, AIRLINE_CODES, AIRPORT_CODES
    result = None
    if request.method == 'POST':
        airline_code = request.form.get('airline_code', 'AA')
        origin_code = request.form.get('origin_code', 'JFK')
        dest_code = request.form.get('dest_code', 'LAX')
        month = int(request.form.get('month', 7))
        day_of_week = int(request.form.get('day_of_week', 1))
        departure_hhmm = int(request.form.get('departure_hhmm', 800))
        distance = int(request.form.get('distance', 2475))
        result = ml_predict(airline_code, origin_code, dest_code, month, day_of_week, departure_hhmm, distance)
        result['airline'] = airline_code
        result['origin'] = origin_code
        result['dest'] = dest_code
        result['distance'] = distance
    return render_template('predict_delay.html',
        result=result,
        airline_codes=AIRLINE_CODES,
        airport_codes=AIRPORT_CODES,
    )


@app.route('/reports')
@login_required
def reports():
    top_delayed_sql = """
        SELECT a.airline_name, a.airline_code, AVG(d.delay_minutes) as avg_delay, COUNT(d.delay_id) as delay_count
        FROM Airlines a
        JOIN Flights f ON f.airline_id = a.airline_id
        JOIN Delays d ON d.flight_id = f.flight_id
        GROUP BY a.airline_id
        ORDER BY avg_delay DESC
        LIMIT 5
    """
    top_delayed = db.session.execute(db.text(top_delayed_sql)).fetchall()

    busiest_routes_sql = """
        SELECT ao.airport_code as origin_code, ad.airport_code as dest_code,
               ao.city as origin_city, ad.city as dest_city,
               COUNT(t.ticket_id) as ticket_count
        FROM Flights f
        JOIN Airports ao ON f.origin_airport = ao.airport_id
        JOIN Airports ad ON f.dest_airport = ad.airport_id
        JOIN Tickets t ON t.flight_id = f.flight_id
        WHERE t.status = 'Confirmed'
        GROUP BY f.origin_airport, f.dest_airport
        ORDER BY ticket_count DESC
        LIMIT 5
    """
    busiest_routes = db.session.execute(db.text(busiest_routes_sql)).fetchall()

    revenue_sql = """
        SELECT a.airline_name, a.airline_code, SUM(t.price) as total_revenue, COUNT(t.ticket_id) as tickets_sold
        FROM Airlines a
        JOIN Flights f ON f.airline_id = a.airline_id
        JOIN Tickets t ON t.flight_id = f.flight_id
        WHERE t.status = 'Confirmed'
        GROUP BY a.airline_id
        ORDER BY total_revenue DESC
    """
    revenue_data = db.session.execute(db.text(revenue_sql)).fetchall()

    monthly_sql = """
        SELECT SUBSTR(booking_date, 1, 7) as month, COUNT(ticket_id) as bookings, SUM(price) as revenue
        FROM Tickets
        WHERE status = 'Confirmed'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """
    monthly_data = db.session.execute(db.text(monthly_sql)).fetchall()

    long_delays_sql = """
        SELECT f.flight_number, a.airline_name, ao.airport_code as origin,
               ad.airport_code as dest, d.delay_minutes, d.delay_reason
        FROM Delays d
        JOIN Flights f ON d.flight_id = f.flight_id
        JOIN Airlines a ON f.airline_id = a.airline_id
        JOIN Airports ao ON f.origin_airport = ao.airport_id
        JOIN Airports ad ON f.dest_airport = ad.airport_id
        WHERE d.delay_minutes > 60
        ORDER BY d.delay_minutes DESC
    """
    long_delays = db.session.execute(db.text(long_delays_sql)).fetchall()

    return render_template('reports.html',
        top_delayed=top_delayed,
        busiest_routes=busiest_routes,
        revenue_data=revenue_data,
        monthly_data=monthly_data,
        long_delays=long_delays,
        top_delayed_sql=top_delayed_sql.strip(),
        busiest_routes_sql=busiest_routes_sql.strip(),
        revenue_sql=revenue_sql.strip(),
        monthly_sql=monthly_sql.strip(),
        long_delays_sql=long_delays_sql.strip(),
    )


def init_db():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            from seed_data import seed
            seed()


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
