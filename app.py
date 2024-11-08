import os
from flask import Flask, request, render_template, redirect, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from lib.user_repository import UserRepository
from lib.user import User
from lib.booking import *
from lib.database_connection import get_flask_database_connection
from lib.spaces_repository import SpaceRepository
from lib.booking_repository import *
from lib.availability_repository import *
from lib.availability import *
from lib.space import Space
from datetime import datetime, timedelta

# Create a new Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey(donttellanyoneorpirateswillGETyou)'

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    connection = get_flask_database_connection(app)
    userrepo = UserRepository(connection)
    return userrepo.get(user_id)

# == Your Routes Here ==

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    connection = get_flask_database_connection(app)
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pwd']
        userrepo = UserRepository(connection)
        user = userrepo.get_from_email(email)
        if not user:
            return render_template('invalid_login.html')
        if user and password == user.password:
            login_user(user)
            return redirect('/spaces', code = 302)
        else:
            return render_template('invalid_login.html')
    return render_template('login.html')

# Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        connection = get_flask_database_connection(app)
        new_user = User(None, request.form['name'], request.form['email'], request.form['password'])
        userrepo = UserRepository(connection)
        userrepo.add(new_user)
        new_user = userrepo.get_from_email(request.form['email'])
        login_user(new_user)
        return redirect("/spaces", code = 302)
    return render_template('signup.html')

# Returns the homepage
@app.route('/', methods=['GET'])
def get_index():
    return render_template('index.html')

# Returns the spaces page
@app.route('/spaces', methods=['GET'])
@login_required
def get_all_spaces():
    connection = get_flask_database_connection(app)
    repository = SpaceRepository(connection)
    spaces = repository.all()
    return render_template("/spaces.html", spaces=spaces)

# Returns the individual spaces page
@app.route('/spaces/<int:id>', methods=['GET'])
@login_required
def get_space(id):
    connection = get_flask_database_connection(app)
    space_repository = SpaceRepository(connection)
    availability_repository = AvailabilityRepository(connection)
    space = space_repository.find(id)
    availability = availability_repository.find_only_if_available(id)
    return render_template("show_space.html", space=space, availability=availability)


# Returns the individual user page
@app.route('/user/<int:id>', methods=['GET'])
@login_required
def get_user_dashboard(id):
    if current_user.id != id:
        id = current_user.id
        return redirect(f'/user/{id}', code = 302)
    connection = get_flask_database_connection(app)
    user_repository = UserRepository(connection)
    space_repository = SpaceRepository(connection)
    booking_repository = BookingRepository(connection)
    user = user_repository.find(id)
    spaces = space_repository.find_spaces_linked_to_id(id)
    bookings = booking_repository.find_spaces_linked_to_id(id)
    requests = booking_repository.find_pending_request_from_guest(id)
    print (requests)
    return render_template('user.html', user=user, spaces=spaces, bookings=bookings, requests=requests)


# Returns the individual add new space page  
@app.route('/new', methods=['GET'])
@login_required
def get_new_space_page():
    name = request.args.get('name')
    return render_template('new.html', name=name)


# Creates a new property/space and redirects to the add_availability page
@app.route('/spaces', methods=['POST'])
@login_required
def create_space():
    connection = get_flask_database_connection(app)
    repository = SpaceRepository(connection)
    title = request.form['title']
    location = request.form['location']
    headline_description = request.form['headline_description']
    description = request.form['description']
    price_per_night = request.form['price_per_night']
    user_id = current_user.id
    space = Space(None, title, location, headline_description, description, price_per_night, user_id)
    space = repository.create(space)
    return redirect (f"/add_availability")


# Returns page to allow hosts to add availability
@app.route('/add_availability', methods=['GET'])
@login_required
def create_availability_get():
    return render_template('add_availability.html')



# Creates new availability entries to the availabilities table in the database based on dates input in the "add availability" feature
@app.route('/add_availability', methods=['POST'])
@login_required
def create_availability_post():
    connection = get_flask_database_connection(app)
    availability_repo = AvailabilityRepository(connection)
    space = SpaceRepository(connection)
    
    start_available_nights = request.form['start_available_nights']
    end_available_nights = request.form['end_available_nights']
    start_available_nights_formatted = datetime.strptime(start_available_nights, "%Y-%m-%d")
    end_available_nights_formatted = datetime.strptime(end_available_nights, "%Y-%m-%d")
    available_dates_list = [(start_available_nights_formatted + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_available_nights_formatted - start_available_nights_formatted).days + 1)]
    
    current_user_id = current_user.id
    most_recent_space_added = space.find_most_recent_space_for_given_user_id(current_user_id)
    space_id = most_recent_space_added.id
    
    for item in available_dates_list:
        availability = Availability(None, space_id, item, True)
        availability_repo.create(availability)
    return redirect (f"/spaces")

# Requests a new booking from data input in the form on the space page
@app.route('/spaces/<int:id>', methods=['POST'])
@login_required
def create_booking(id):
    connection = get_flask_database_connection(app)
    booking_repository = BookingRepository(connection)
    space_repository = SpaceRepository(connection)
    price_per_night = space_repository.find_price_per_night(id)
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    status = "pending"
    total_nights = (end_date - start_date).days
    total_price = price_per_night * total_nights
    space_id = id
    user_id = session.get('id')
    booking = Booking(None, start_date, end_date, status, total_price, space_id, user_id)
    new_booking = booking_repository.create(booking)
    return render_template("/booking_confirmation.html")

# Confirms a booking and deletes appropriate availability data
# uses the new find pending booking function in booking repo to then delete availability
@app.route('/user/<int:id>', methods=['POST'])
@login_required
def confirm_booking(id):
    user_id = session.get('id')
    print(user_id)
    connection = get_flask_database_connection(app)
    booking_repository = BookingRepository(connection)
    availability_repository = AvailabilityRepository(connection)
    booking = booking_repository.find(id)
    print(booking)
    availability_repository.update_by_date_range(booking.space_id, booking.start_date, booking.end_date) #check if ranges include start and end date!
    booking.status = 'confirmed'
    booking_repository.confirm_booking(booking)
    return render_template("/user.html")

# cancels booking

# @app.route('/user/cancelled/<int:id>', methods=['POST'])
# @login_required
# def cancel_booking(id):
#     user_id = session.get('id')
#     connection = get_flask_database_connection(app)
#     booking_repository = BookingRepository(connection)
#     booking = booking_repository.find(id)
#     booking.status = 'cancelled'
#     print(booking)
#     booking_repository.update_status(booking)
#     return redirect (f"/user/2")
#     booking_repository.update_status(booking)
#     return redirect (f"/user/{user_id}")

# Rerouting /user to /user/<id>
@app.route('/user', methods=['GET'])
@login_required
def reroute_user():
    return redirect (f"/user/{current_user.id}")

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template("/logout.html")

# These lines start the server if you run this file directly
# They also start the server configured to use the test database
# if started in test mode.
if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5001)))