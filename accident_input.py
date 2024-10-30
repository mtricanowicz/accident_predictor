import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import requests
from datetime import datetime
import numpy as np
import pandas as pd
import math
import pickle
import sklearn
import pytz
import timezonefinder

# Set Streamlit layout
st.set_page_config(layout="wide")

# Set a starting location on the map (the Dubois Center)
lat_start = 35.22862041030688
lon_start = -80.83445778852331

# Define the openweathermaps.org API key to use
API_KEY = "0a2f1b71c8591af7c64f8dd7b5a31323" # my API key

# Initialize the Streamlit app with a selectable map
st.title("Identify accident location by selecting a point on the map.")

# Create a map centered on some initial location (e.g., San Francisco)
m = folium.Map(location=[lat_start, lon_start], zoom_start=15)
# Display the map in Streamlit and capture the click event
map_output = st_folium(m, width=1200, height=800)

# Add a click event to the map to capture user-selected point
m.add_child(folium.LatLngPopup())

# Function to reverse geocode (get address from lat/lng)
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="accident_input")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.raw['address']
    return "Address not found"

# Function to fetch weather data from OpenWeatherMap
def get_weather_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Instantiate the location to the default starting location
lat = lat_start
lon = lon_start
zipcode = reverse_geocode(lat, lon).get('postcode')
# Retrieve the weather information for the default starting location
weather_data = get_weather_data(lat, lon, API_KEY)
temp = weather_data['main']['temp']
wind_chill = weather_data['main']['feels_like']
pressure = weather_data['main']['pressure'] * 0.2953 # convert API data from hPA to inHg
visibility = weather_data['visibility'] / 1609.34 # convert API data from meters to miles
humidity = weather_data['main']['humidity']
wind_speed = weather_data['wind']['speed']

##### PROCESS USER'S ACCIDENT INPUT #####
# Check if the user clicked on the map and retrieve the coordinates
if map_output['last_clicked'] is not None:
    lat = map_output['last_clicked']['lat']
    lon = map_output['last_clicked']['lng']

    # Apply the timezone
    # Define variable that will get the timezone name based on latitude and longitude
    tf = timezonefinder.TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    if timezone_str:
        local_timezone = pytz.timezone(timezone_str)
        local_time = datetime.now(local_timezone)
        local_time = pd.to_datetime(local_time, format='ISO8601')
        # Display time of click
        st.write("Accident Time:", local_time.strftime('%Y-%m-%d %H:%M:%S'))
        #st.write(f"Accident Time: {local_time}")
    else:
        st.write("Timezone could not be determined for the given coordinates.")

    # Display the selected latitude and longitude
    st.write(f"Selected Latitude: {lat}")
    st.write(f"Selected Longitude: {lon}")

    # Reverse geocode the selected lat/lng to get address details
    house_number = reverse_geocode(lat, lon).get('house_number')
    street = reverse_geocode(lat, lon).get('road')
    city = reverse_geocode(lat, lon).get('city')
    state = reverse_geocode(lat, lon).get('state')
    zipcode = reverse_geocode(lat, lon).get('postcode')
    address = f"{house_number} {street}, {city}, {state} {zipcode}"
    st.write(f"Address: {address}")

    # Fetch weather data based on the selected location
    weather_data = get_weather_data(lat, lon, API_KEY)

    if weather_data:
        # Define weather information
        temp = weather_data['main']['temp']
        wind_chill = weather_data['main']['feels_like']
        pressure = weather_data['main']['pressure'] * 0.2953 # convert API data from hPA to inHg
        visibility = weather_data['visibility'] / 1609.34 # convert API data from meters to miles
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        # Display weather information (not displayed in production app)
        #st.write(f"Temperature: {temp} °F")
        #st.write(f"Wind Chill: {wind_chill} °F")
        #st.write(f"Pressure: {np.round(pressure, 2)} inHg")
        #st.write(f"Visibility: {np.round(visibility, 2)} miles")
        #st.write(f"Humidity: {humidity} %")
        #st.write(f"Wind Speed: {wind_speed} mph")        
    else:
        st.write("Weather data could not be retrieved.")
else:
    st.write("Click on the map to select a point.")


##### TRAFFIC SIGNAL INPUT ##### [UNUSED]
# Prompt user to specify whether or not a traffic signal is nearby (not used in production app, presence of traffic signal pulled from OpenStreetMaps API instead)
#st.title("Is there a traffic signal nearby?")
#user_response = st.radio("Is there a traffic signal nearby?", ("Yes", "No"))
# Store the response in a variable
#if user_response=="Yes":
#    traffic_signal = True
#elif user_response=="No":
#    traffic_signal = False
#else:
#    traffic_signal = True


##### TRAFFIC SIGNAL PRESENCE #####
# 
# Define OSM's Overpass API URL
url = "http://overpass-api.de/api/interpreter"
# Define Overpass query to retrieve traffic signals within 400 meters (about 1/4 mile) from the selected accident location
query = f"""
[out:json];
node["highway"="traffic_signals"](around:400,{lat},{lon});
out body;
"""
# Send the request
response = requests.get(url, params={'data': query})
# Parse response JSON
traffic_presence = response.json()
# Define the traffic_signal variable. An empty set returned from the OSM query implies no traffic signals within the 1/4 mile radius
if traffic_presence['elements']==[]:
    traffic_signal = False
else:
    traffic_signal = True


##### Store accident conditions in a DataFrame #####
#st.title("Input data for prediction model.")
columns = ["Start_Month", "Start_Day", "Start_Hour", "Start_Lat", "Start_Lng", "Zipcode", "Temperature(F)", "Wind_Chill(F)", "Pressure(in)", "Visibility(mi)", "Humidity(%)", "Wind_Speed(mph)", "Traffic_Signal"]
inputs = [[local_time.month, local_time.day, local_time.hour, lat, lon, zipcode, temp, wind_chill, pressure, visibility, humidity, wind_speed, traffic_signal]]
user_input = pd.DataFrame(inputs, columns=columns)
# Import the optimized model features                                   
model_features = pd.read_csv("model_features.csv")
model_features = model_features[model_features["Feature"] != "Severity"]
# Reorder the input features to match what the model expects to see     
user_input = user_input[model_features["Feature"].values] 
# Display model input DataFrame (not displayed in production app)
#st.write(user_input) 


##### Test loading the model ##### [UNUSED]
#st.title("Test load model.")
#try:
#    with open('applet_model.pkl', 'rb') as file:
#            model = pickle.load(file)
#    st.write("Model loaded successfully.")
#except Exception as e1:
#    st.write("Error loading model:", e1)


##### Generate predictions #####
#st.title("Attempt to generate prediction.")
# Define the model
with open('applet_model.pkl', 'rb') as file:
            model = pickle.load(file)
# Define callable prediction function to invoke the model on input data
def severity_predictor(input):
    # Generate prediction    
    prediction = model.predict(input)
    return prediction


##### Run and display prediction #####
try:
    severity_prediction = severity_predictor(user_input)
    if severity_prediction==1:
         message = "Minor"
         color = "green"
         size = 22
    elif severity_prediction==2:
         message = "Moderate"
         color = "yellow"
         size = 24
    elif severity_prediction==3:
         message = "Major"
         color = "orange"
         size = 26
    elif severity_prediction==4:
         message = "SEVERE"
         color = "red"
         size = 28
    st.title("Accident traffic impact severity:")
    st.markdown(f"<h1 style='color: {color}; font-size: {size}px;'>{severity_prediction[0]}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='color: {color}; font-size: {size}px;'>{message}</h1>", unsafe_allow_html=True)    
except Exception as e2:
    st.write("Error running model:", e2)

