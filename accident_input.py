import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import requests
from datetime import datetime
import numpy as np
import pandas as pd
from model import severity_predictor

# Set a starting location on the map (the Dubois Center)
lat_start = 35.22862041030688
lon_start = -80.83445778852331

# Define the openweathermaps.org API components
# Define the API key to use
API_KEY = "0a2f1b71c8591af7c64f8dd7b5a31323" # my API key

# Initialize the Streamlit app with a selectable map
st.title("Identify accident location by selecting a point on the map.")

# Create a map centered on some initial location (e.g., San Francisco)
m = folium.Map(location=[lat_start, lon_start], zoom_start=20)

# Add a click event to the map to capture user-selected point
m.add_child(folium.LatLngPopup())
timestamp = datetime.now()

# Display the map in Streamlit and capture the click event
map_output = st_folium(m, width=1000, height=700)

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

# Check if the user clicked on the map and retrieve the coordinates
if map_output['last_clicked'] is not None:
    lat = map_output['last_clicked']['lat']
    lon = map_output['last_clicked']['lng']

    # Display time of click
    st.write(timestamp)

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
        # Display weather information
        st.write(f"Temperature: {temp} °F")
        st.write(f"Wind Chill: {wind_chill} °F")
        st.write(f"Pressure: {np.round(pressure, 2)} inHg")
        st.write(f"Visibility: {np.round(visibility, 2)} miles")
        st.write(f"Humidity: {humidity} %")
        st.write(f"Wind Speed: {wind_speed} mph")        
    else:
        st.write("Weather data could not be retrieved.")
else:
    st.write("Click on the map to select a point.")

# Prompt user to specify whether or not a traffic signal is nearby
user_response = st.radio("Is there a traffic signal nearby?", ("Yes", "No"))
# Store the response in a variable
if user_response=="Yes":
    traffic_signal = True
elif user_response=="No":
    traffic_signal = False
else:
    traffic_signal = True

# Convert traffic_signal variable to a dummy variable
if traffic_signal==True:
    traffic_signal_true = 1
else:
    traffic_signal_true = 0

# Store accident conditions in a DataFrame
columns = ["Start_Year", "Start_Month", "Start_Day", "Start_Hour", "Start_Lat", "Start_Lng", "Zipcode", "Temperature(F)", "Wind_Chill(F)", "Pressure(in)", "Visibility(mi)", "Humidity(%)", "Wind_Speed(mph)", "Traffic_Signal_True"]
inputs = [[timestamp.year, timestamp.month, timestamp.day, timestamp.hour, lat, lon, zipcode, temp, wind_chill, pressure, visibility, humidity, wind_speed, traffic_signal_true]]
accident_input = pd.DataFrame(inputs, columns=columns)
st.write(accident_input)

# Call the prediction function
prediction = severity_predictor(accident_input)
st.write("Accident traffic impact severity:")
st.write(prediction)
