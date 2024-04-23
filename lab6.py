# Standard library imports
import os
import time
import socket
from datetime import datetime

# Third-party imports for data handling and database
import pandas as pd
from IPython.display import display
import sqlite3

# Third-party imports for web development
from flask import Flask, session, request, render_template, redirect, url_for, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

# Third-party imports for geolocation and weather web API and LLM
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderInsufficientPrivileges
from geopy.distance import geodesic
import requests
from retry_requests import retry
import openmeteo_requests
import requests_cache
import json

#######################################################################
# Start up sqlite3 database
DBname = 'serverDB1.db'

# Establish the connection to the database
con = sqlite3.connect(DBname)

if os.path.isfile(DBname):
    pass
else:
    # Execute the script from the file
    with open("database.sql") as f:
        con.executescript(f.read())

def dbConnection():
    con = sqlite3.connect(DBname)
    return con

def initialize_db():
    with dbConnection() as con:
        cur = con.cursor()
        # Create the 'credentials' table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                username TEXT PRIMARY KEY,
                hashed_pw TEXT NOT NULL
            )
        """)

        # Create the 'reports' table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                user_id TEXT,    
                latitude FLOAT,
                longitude FLOAT,
                state TEXT,
                country TEXT,
                description TEXT,
                category TEXT,
                temperature FLOAT,
                humidity FLOAT,
                rain FLOAT,
                date TEXT,
                time TEXT,
                filepath TEXT
            )
        """)

        # Check if the admin user already exists
        cur.execute("SELECT * FROM credentials WHERE username = 'admin'")
        rows = cur.fetchall()
        if not rows:
            # If the admin user does not exist, create it
            hashed_password = generate_password_hash('admin')
            cur.execute("INSERT INTO credentials (username, hashed_pw) VALUES (?, ?)", ('admin', hashed_password))

#######################################################################
# Create a Flask application
auth = HTTPBasicAuth()

app = Flask(__name__,static_folder="data")
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
app.secret_key = 'lab6_key' # delete if it works without it

CORS(app)
#######################################################################

# root: Login Form
@app.route("/", methods = ["GET", "POST"])
def getform():
    if request.method == 'POST':
        action = request.form['action']
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Handle login
        if action == 'Login':
            with dbConnection() as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM credentials WHERE username = ?", (username,))
                rows = cur.fetchall() # Fetch all rows from the query result

                if rows and check_password_hash(rows[0][1], password):
                    session['username'] = username
                    return redirect(url_for('home', username=username))
                else:
                    return render_template('login.html', message="Invalid username or password!", form_action="/")
        
        # Handle registration
        elif action == 'Register':
            reg_df = pd.DataFrame({ # Registration data frame
                'username': username,
                'hashed_pw': generate_password_hash(password),
            }, index=[0])

            with dbConnection() as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM credentials WHERE username = ?", (username,))
                rows = cur.fetchall()

                if rows:
                    return render_template('login.html', message=f"User {username} already exists!", form_action="/")
                else:
                    cur.execute("INSERT INTO credentials (username, hashed_pw) VALUES (?, ?)", 
                                (reg_df['username'].values[0],
                                 reg_df['hashed_pw'].values[0]))
                    return render_template('login.html', message=f"User {username} registered successfully!", form_action="/")
    else:
        return render_template("login.html", title="Login Form")

#######################################################################
# home:

def get_location(ip_address):
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

    data = response.json()
    
    try:
        loc = data['loc']  # 'loc' contains the latitude and longitude
    except KeyError:
        print("Error: 'loc' not found in response")
        loc = None
        return loc
    return loc

def get_hashed_pw(username):
    con = sqlite3.connect(DBname)
    cur = con.cursor()
    cur.execute("SELECT hashed_pw FROM credentials WHERE username=?", (username,))

    result = cur.fetchone()
    if result is None:
        return None
    else:
        return result[0]

@app.route('/home/<username>', methods=['GET', 'POST'])
def home(username):
    # Check if the user is logged in
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('getform'))
    
    hashed_pw = get_hashed_pw(username)
    api_key = hashed_pw

    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip_address = request.environ['REMOTE_ADDR']
        print(f"IP address with REMOTE_ADDR_2: {ip_address}")
    else:
        ip_address = request.environ['HTTP_X_FORWARDED_FOR']
        print(f"IP address with HTTP_X_FORWARDED_FOR: {ip_address}")


    # Different approaches to get the IP address of the client

    # Works
    # ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    # print(f"IP address X_Forwarded: {ip_address}")

    # Doesn't work
    # ip_address = request.environ['REMOTE_ADDR']
    # print(f"IP address REMOTE_ADDR: {ip_address}")

    # Works
    # ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr) 
    # print(f"IP address X_REAL_IP: {ip_address}")

    # Doesn't work
    # ip_address = request.remote_addr # Get the IP address of the client, doesn't work in local host
    # print(f"IP address remote_addr: {ip_address}")
    
    #ip_address = "174.78.194.22" # For testing purposes, IP from Macon Georgia
    

    gps_lat, gps_long = None, None
    loc = get_location(ip_address)
    if loc is None:
        gps_lat = "Can't read your location. Please enter it manually."
        gps_long = "Can't read your location. Please enter it manually."
    else:
        gps_lat, gps_long = loc.split(',')

    return render_template("home.html", username=username, gps_lat=gps_lat, gps_long=gps_long, api_key=api_key, user_ip = ip_address)


#######################################################################

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('getform'))

#######################################################################
# Report Form

def save_file(file):
    path = ""
    if file:
        path = f"files/{time.strftime('%Y%m%d-%H%M%S')}_{secure_filename(file.filename)}"
        file.save(path)
    else:
        print("No file uploaded")
    return path

def get_username(api_key):
    with dbConnection() as con:
        cur = con.cursor()
        cur.execute("SELECT username FROM credentials WHERE hashed_pw=?", (api_key,)) # Generate the api_key from the hashed password

        result = cur.fetchone()
        print(f"Results: {result}")
        if result is None:
            return None
        else:
            return result[0]
    
# Code from: https://open-meteo.com/en/docs#current=temperature_2m&hourly= and adapted to my needs
def get_weather_data(lat, long):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": long,
        "current": ["temperature_2m", "relative_humidity_2m", "rain"]
    }

    responses = openmeteo.weather_api(url, params=params) # Request the data
    response = responses[0] # Process first location. Add a for-loop for multiple locations or weather models

    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temp = current.Variables(0).Value()
    current_temp = round(current_temp, ndigits=1) # round to one digit after coma
    current_rain = current.Variables(2).Value()
    current_humidity = current.Variables(1).Value() 
    current_time = datetime.fromtimestamp(current.Time()) # Convert the time to a readable format

    date = current_time.date()
    time = current_time.time()

    return current_temp, current_rain, current_humidity, date, time 

def get_address(gps_coordinates): # Format of the gps_coordinates: "32.8407, -83.6324", must be a string
    
    geolocator = Nominatim(user_agent="UGA_23", timeout=10) # Use a unique user_agent
   
    try: # Get the address from the GPS coordinates with the geopy library
        location = geolocator.reverse(gps_coordinates)

    except GeocoderInsufficientPrivileges:
        # If a 403 error occurs, wait for a while before making the next request
        time.sleep(1)
        location = geolocator.reverse(gps_coordinates)

    location_raw = location.raw # Get the raw location data

    # Extract the state and country
    state = location_raw['address']['state']
    country = location_raw['address']['country']

    return state, country

def get_category(description):

    apikey = "AIzaSyCemhnpQn1qgLq6Mf_m7NLzCiuXZyfTMQg" # API key for the Google API
    host = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    params = {"key": apikey}
    body = {"contents": [{"parts": [{"text": f"Category the following string as dangerous, offensive or normal. Only return one word. String: {description}"}]}]}
    res = requests.post(host, params=params, json=body)
    res = res.text # Convert the response to a readable format
    data = json.loads(res) # Convert for easier processing

    # Check if the finish reason is "SAFETY" because then there is no valid response
    if data['candidates'][0]['finishReason'] == "SAFETY":
        category = "Dangerous"
    else:
        text = data['candidates'][0]['content']['parts'][0]['text']
        category = text
    
    return category
    
    

@app.route("/report", methods = ["POST"])
def report():
    man_gps_lat = request.form.get("man_gps_lat", "")
    man_gps_long = request.form.get("man_gps_long", "")

    
    api_key = request.form.get("api_key", "")
    username = get_username(api_key) # Get the username from the API key
    hashed_pw = get_hashed_pw(username) # Get the hashed password from the username

    # Check if the API key matches the hashed password
    # api_key = "wrong_for_testing" # For testing purpose to simulate a wrong API key
    if api_key == hashed_pw:
        print("API key matches the hashed password.")
    else:

        return(render_template('login.html', message="Invalid API key! Please log in again.", form_action="/"))

    # If the user manually entered GPS coordinates, use those
    if man_gps_lat != "" and man_gps_long != "":
        gps_lat = man_gps_lat
        gps_long = man_gps_long
    
    # Otherwise, use the GPS coordinates from the IP address
    else:
        gps_lat = request.form.get("gps_lat", "")
        gps_long = request.form.get("gps_long", "")
    
    user_ip = request.form.get("user_ip", "")
    description = request.form.get("description", "")
    file = request.files.get("file", None)
    file_path = save_file(file)

    gps_coordinates = str(gps_lat + ", " + str(gps_long)) # Don't change order of coordinates

    # Get the address for the GPS coordinates
    try:
        state, country = get_address(gps_coordinates)
    except Exception as e:
        print(f"Error: {e}")
        state = None
        country = None

    # Get the weather data and the time for the GPS coordinates
    try:
        current_temp, current_rain, current_humidity, date, time  = get_weather_data(gps_lat, gps_long)
    except Exception as e:
        print(f"Error: {e}")
        current_temp = None
        current_rain = None
        current_humidity = None
        date = None
        time = None    
    
    # Convert date and time to strings
    date = str(date)
    time = str(time)

    # Create a string with the current weather data
    weather_data = f"Temperature: {current_temp} °C, Rain: {current_rain} mm, Humidity: {current_humidity} %, Sampled at: {date}, {time}."

    # Get the category of the description
    category = get_category(description)

    with dbConnection() as con:
        cur = con.cursor()

        # Insert the data into the reports table
        cur.execute("""
            INSERT INTO reports (user_id, latitude, longitude, state, country, description, category, temperature, humidity, rain, date, time, filepath)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, gps_lat, gps_long, state, country, description, category, current_temp, current_humidity, current_rain, date, time, file_path))

    return render_template('report.html', user_ip=user_ip,
                           gps_coordinates=gps_coordinates, state=state, country=country,
                           weather_data = weather_data, 
                           description=description, category=category,
                           username = username, file_path=file_path)

#######################################################################

@app.route('/data', methods=['GET'])
def data():
    try:
        output = request.args.get('output', 'html')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        dist = request.args.get('dist')
        max_reports = request.args.get('max')
        sort = request.args.get('sort', 'newest')

        # Convert dates to datetime objects
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Get the data from the database
        with dbConnection() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM reports")
            rows = cur.fetchall()

            columns = [desc[0] for desc in cur.description]

            df = pd.DataFrame(rows, columns=columns)
            df.dropna(inplace=True)
            df['date'] = pd.to_datetime(df['date'])
            df['time'] = pd.to_datetime(df['time']).dt.time

        # Filter by start_date and end_date
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['date'] >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['date'] <= end_date]    

        # Limit the number of reports
        if max_reports:
            max_reports = int(max_reports)
            df = df.head(max_reports)
            
        # Sort the reports
        if sort == 'newest':
            df = df.sort_values(['date', 'time'], ascending=False)
        elif sort == 'oldest':
            df = df.sort_values(['date', 'time'], ascending=True)        

        
        # Filter by lat, lng, dist
        if lat and lng and dist:
            lat = float(lat)
            lng = float(lng)
            dist = float(dist)
            print(f"Lat: {lat}, Lng: {lng}, Dist: {dist}")
            
            df = df[df.apply(lambda row: geodesic((lat, lng), (row['latitude'], row['longitude'])).km <= dist, axis=1)]

        display(df)

        df['date'] = df['date'].astype(str)
        df['time'] = df['time'].astype(str)

        # Output the data in the requested format
        if output == 'csv':
            return df.to_csv(index=False) # Convert the DataFrame to CSV and return it
        elif output == 'json':
            return jsonify(df.to_dict(orient='records')) # Convert the DataFrame to JSON and return it
        else:
            # Create clickable links in the DataFrame
            df['filepath'] = '<a href="' + df['filepath'] + '">' + df['filepath'] + '</a>'
            return df.to_html(index=False, escape=False) # Convert the DataFrame to an HTML table and return it
    except Exception as e:
        message = f"Error: {e}\nYour input is not valid! See /data/help for more information."
        return message
    
#######################################################################

# Get the file from the 'files' directory
@app.route('/files/<path:filename>', methods=['GET', 'POST'])
def get_files(filename):
    return send_from_directory('files', filename)

#######################################################################

# Help page
@app.route('/data/help', methods=['GET'])
def help():
    return render_template('help.html', url=request.url_root)

#######################################################################

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True, host='0.0.0.0', port=5000)