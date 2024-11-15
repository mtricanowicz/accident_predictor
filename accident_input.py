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
import gdown
import xgboost

# Set custom page configuration including the "About" section
st.set_page_config(
    page_title="Traffic Impact Predictor",  # Custom title in the browser tab
    page_icon=":vertical_traffic_light:",  # Custom icon for the browser tab
    layout="wide",  # Set the defaul layout for the app
    initial_sidebar_state="auto",  # Sidebar state when app loads
    menu_items={
        "About": """
        ## Traffic Impact Predictor App
        This app was created to satisfy the project requirement of DSBA-6156 as part of the MS degree program in Data Science and Business Analytics at the University of North Carolina at Charlotte.\n
        - **Version:** 1.0.0
        - **Author:** Michael Tricanowicz
        - **License:** MIT
        - **GitHub:** [accident_predictor](https://github.com/mtricanowicz/accident_predictor)
        """
    }
)

# Import the optimized model features                                   
model_features = pd.read_csv("model_features.csv")
model_features = model_features[model_features["Feature"] != "Severity"]

# Set page title
st.header("Traffic Impact Predictor", divider="gray")
with st.expander(label="About this app."):
    st.write("The purpose of this app is to use a pretrained machine learning model to predict how severe the traffic impact will be as a result of an accident.") 
    st.write(f"The current version of this app uses an XGBoost model trained on the following features: {', '.join(model_features["Feature"].astype(str))}")
    st.write("""This app provides a means for a user to input an accident location. The location and time of the input, as well as accompanying geographic and weather data, is fed into the model to generate a prediction. 
             This app is designed to require as little user intervention as possible. A single click should be sufficient to obtain a prediction.\n
             This is accomplished by processing the user input as follows:
             1. The user click generates a latitude and longitude value.<br>
             2. The lat/lon is processed by timzonefinder and pytz to determine the local time zone.
             3. A timestamp is applied at time of click with the local timezone to generate local time of the event.
             4. The lat/lon is processed by the Nominatim geocoder of geopy to generate the nearest address to the event location.
             5. The lat/lon is processed by the OpenWeatherMap API to fetch the weather conditions for the location and time of the event.
             6. The lat/lon is processed by the OpenStreetMap Overpass API to fetch whether a traffic signal is present within 400 m (approx 1/4 mile) of the event location.
             7. The processed data is then compiled into a dataframe as the input variables for the model.
             8. The input dataframe is fed to the model to generate a severity prediction.
             9. The prediction and input variables are displayed by the app in a user friendly format. 
             """)
    st.write("Identify accident location by selecting a point on the map.")
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

##### BEGIN FUNCTION DEFINITION SECTION #####

# Define the openweathermaps.org API key to use
API_KEY = "0a2f1b71c8591af7c64f8dd7b5a31323" # my API key

# Define function to reverse geocode (get address from lat/lng)
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="accident_input")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.raw['address']
    else:
        return None

# Define function to fetch weather data from OpenWeatherMap
def get_weather_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Define variable that will get the timezone name based on latitude and longitude
tf = timezonefinder.TimezoneFinder()

# Specify the Google Drive file url to enable download and retrieval of the model .pkl file from Google Drive 
# Model file IDs from Google Drive
# Random Forest Model - https://drive.google.com/file/d/143EKAWRozG165zuVP54h5MJdW40Pw1ls/view?usp=drive_link
# XGBoost Model - https://drive.google.com/file/d/1_0kDivpnBZRuoSnYWgiG1z1Xln7oFf1D/view?usp=drive_link
# Blended RF+XGB Model - https://drive.google.com/file/d/1Q4b62ys0ooYfElCBZHn8M-u38ykzLkDL/view?usp=drive_link
file_id = "1_0kDivpnBZRuoSnYWgiG1z1Xln7oFf1D"
url = f"https://drive.google.com/uc?id={file_id}"

# Define function to download and load model, caching the result
@st.cache_resource
def load_model():
    gdown.download(url, "applet_model.pkl", quiet=False)
    # Define the model
    with open('applet_model.pkl', 'rb') as file:
        model = pickle.load(file)
    return model

# Load the model
model = load_model()

# Define callable prediction function to invoke the model on input data
def severity_predictor(input):
    # Generate prediction    
    prediction = model.predict(input)
    return prediction

# Define function to convert latitude and longitude values from decimal to degrees/minutes/seconds format
def decimal_to_dms(decimal_coord):
    # Determine if it's negative (for W or S)
    is_negative = decimal_coord < 0
    decimal_coord = abs(decimal_coord)
    # Calculate degrees, minutes, and seconds
    degrees = int(decimal_coord)
    minutes_float = (decimal_coord - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    # Return as a formatted string with N/S or E/W direction
    direction = ''
    if is_negative:
        direction = 'S' if degrees >= 0 else 'W'
    else:
        direction = 'N' if degrees >= 0 else 'E'
    return f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"

##### END FUNCTION DEFINITION SECTION #####

# Set columns
col1, col2 = st.columns([2, 1])

with col1: # map and user interaction area
    # Set a starting location on the map (the Dubois Center)
    lat_start = 35.2286
    lon_start = -80.8348

    # Create a map centered on the starting location
    m = folium.Map(location=[lat_start, lon_start], zoom_start=15)
    # Add a click event to the map to capture user-selected point
    m.add_child(folium.LatLngPopup())
    # Display the map in Streamlit and capture the click event
    map_output = st_folium(m, width=1200, height=800)

    ##### PROCESS USER'S ACCIDENT INPUT #####
    # Check if the user clicked on the map and retrieve the coordinates
    if map_output['last_clicked'] is None:
        # Instantiate the location to the default starting location
        lat = lat_start
        lon = lon_start
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
    elif map_output['last_clicked'] is not None:
        # Instantiate the location to the user selection
        lat = map_output['last_clicked']['lat']
        lon = map_output['last_clicked']['lng']
        timezone_str = tf.timezone_at(lat=lat, lng=lon)

    # Apply the timezone and generate local time
    if timezone_str:
        local_timezone = pytz.timezone(timezone_str)
        local_time = datetime.now(local_timezone)
        local_time = pd.to_datetime(local_time, format='ISO8601')
    else:
        local_time = "Timezone could not be determined for the given coordinates."
    
    # Reverse geocode the selected lat/lng to get address details and display address
    if reverse_geocode(lat, lon):
        house_number = reverse_geocode(lat, lon).get('house_number')
        street = reverse_geocode(lat, lon).get('road')
        city = reverse_geocode(lat, lon).get('city')
        state = reverse_geocode(lat, lon).get('state')
        zipcode = reverse_geocode(lat, lon).get('postcode')
        address = f"{house_number} {street}, {city}, {state} {zipcode}"
    else:
        address = "Address data could not be retrieved."
    
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
    else:
        temp = "Weather data could not be retrieved."
        wind_chill = "Weather data could not be retrieved."
        pressure = "Weather data could not be retrieved."
        visibility = "Weather data could not be retrieved."
        humidity = "Weather data could not be retrieved."
        wind_speed = "Weather data could not be retrieved."

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

    # Determine traffic signal presence 
    # Define OSM's Overpass API URL
    url_osm = "http://overpass-api.de/api/interpreter"
    # Define Overpass query to retrieve traffic signals within 400 meters (about 1/4 mile) from the selected accident location
    query = f"""
    [out:json];
    node["highway"="traffic_signals"](around:400,{lat},{lon});
    out body;
    """
    # Send the request
    response = requests.get(url_osm, params={'data': query})
    # Parse response JSON
    traffic_presence = response.json()
    # Define the traffic_signal variable. An empty set returned from the OSM query implies no traffic signals within the 1/4 mile radius
    if traffic_presence['elements']==[]:
        traffic_signal = False
    else:
        traffic_signal = True

    ##### Store accident conditions in a DataFrame #####
    if weather_data is not None and reverse_geocode(lat, lon) is not None:
        columns = ["Start_Month", "Start_Day", "Start_Hour", "Start_Lat", "Start_Lng", "Temperature(F)", "Pressure(in)", "Visibility(mi)", "Humidity(%)", "Wind_Speed(mph)", "Traffic_Signal"]
        inputs = [[local_time.month, local_time.day, local_time.hour, lat, lon, temp, pressure, visibility, humidity, wind_speed, traffic_signal]]
        user_input = pd.DataFrame(inputs, columns=columns)   
        user_input = user_input[model_features["Feature"].values] # Reorder the input features to match what the model expects to see
        # Display model input DataFrame (not displayed in production app)
        #st.write("Features to load into model:")
        #st.write(user_input) 

with col2: # output area
    # Display prompt if no user input detected
    if map_output['last_clicked'] is None:
        st.divider()
        st.header("Navigate to and click on accident location on map.")
        st.divider()
    # Otherwise generate and display prediction
    elif map_output['last_clicked'] is not None and weather_data is not None and reverse_geocode(lat, lon) is not None:
        try:
            severity_prediction = severity_predictor(user_input)
            if severity_prediction==1:
                message = "Minor"
                color = "green"
                size = 52
            elif severity_prediction==2:
                message = "Moderate"
                color = "yellow"
                size = 54
            elif severity_prediction==3:
                message = "Major"
                color = "orange"
                size = 56
            elif severity_prediction==4:
                message = "SEVERE"
                color = "red"
                size = 58
            st.divider()
            st.header("Accident traffic impact:")
            st.markdown(f"<h1 style='color: {color}; font-size: {size}px;'>{severity_prediction[0]} | {message}</h1>", unsafe_allow_html=True)
            #st.markdown(f"<h1 style='color: {color}; font-size: {size}px;'>{message}</h1>", unsafe_allow_html=True)
            st.divider()  
        except Exception as e2:
            st.write("Error running model:", e2)
    elif map_output['last_clicked'] is not None:
        st.divider()
        st.write("Prediction cannot be generated. Please try again.")
        st.divider()
    
    # Display input variables in an expandable area for review
    st.markdown("""
        <style>
        .custom-divider {
            border-top: 1px solid #e0e0e0;
            margin-top: 2px;   /* Adjusts the space above */
            margin-bottom: 2px; /* Adjusts the space below */
        }
        </style>
    """, unsafe_allow_html=True)
    with st.expander("Location Conditions"):
        if local_time is not None:
            # Display the time
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            st.write(f"🕔 Local Time: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        if lat is not None and lon is not None:
            # Display the selected latitude and longitude
            st.write(f"🌐 Latitude: {decimal_to_dms(lat)}")
            st.write(f"🌐 Longitude: {decimal_to_dms(lon)}")
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        if address is not None:
            # Display the nearest address
            st.write(f"🏪 Nearest Address: {address}")
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        if temp is not None and wind_chill is not None and pressure is not None and visibility is not None and humidity is not None and wind_speed is not None:
            # Display weather information (not displayed in production app)
            st.write(f"🌡️ Temperature: {temp} °F")
            st.write(f"🌥️ Pressure: {np.round(pressure, 2)} inHg")
            st.write(f"🌫️ Visibility: {np.round(visibility, 2)} miles")
            st.write(f"☀️ Humidity: {humidity} %")
            st.write(f"☁️ Wind Speed: {wind_speed} mph")
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        if address is not None:
            # Display traffic signal presence
            st.write(f"🚦 Traffic Signal within 1/4 mile: {traffic_signal}")
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

