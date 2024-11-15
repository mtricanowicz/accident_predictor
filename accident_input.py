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
        The purpose of this app is to use a pretrained machine learning model to predict how severe the traffic impact will be as a result of an accident. This app provides a means for a user to input an accident location. The location and time of the input, as well as accompanying geographic and weather data, is fed into the model to generate a prediction. This app is designed to require as little user intervention as possible. A single click should be sufficient to obtain a prediction.\n
        - **Version:** 1.0.0
        - **Author:** Michael Tricanowicz
        - **License:** MIT
        - **GitHub:** [airline_financials](https://github.com/mtricanowicz/airline_financials)
        """
    }
)

# Define the openweathermaps.org API key to use
API_KEY = "0a2f1b71c8591af7c64f8dd7b5a31323" # my API key

# Function to reverse geocode (get address from lat/lng)
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="accident_input")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.raw['address']
    else:
        return None

# Function to fetch weather data from OpenWeatherMap
def get_weather_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Define variable that will get the timezone name based on latitude and longitude
tf = timezonefinder.TimezoneFinder()

st.header("Traffic Impact Predictor", divider="gray")
with st.expander(label="About"):
    st.write("The purpose of this app is to use a pretrained machine learning model to predict how severe the traffic impact will be as a result of an accident. This app provides a means for a user to input an accident location. The location and time of the input, as well as accompanying geographic and weather data, is fed into the model to generate a prediction. This app is designed to require as little user intervention as possible. A single click should be sufficient to obtain a prediction.")
    st.write("Identify accident location by selecting a point on the map.")

# Set columns
col1, col2 = st.columns([2, 1])

with col1:

    # Set a starting location on the map (the Dubois Center)
    lat_start = 35.22862041030688
    lon_start = -80.83445778852331

    # Initialize the Streamlit app with a selectable map
    # Create a map centered on some initial location
    m = folium.Map(location=[lat_start, lon_start], zoom_start=15)
    # Add a click event to the map to capture user-selected point
    m.add_child(folium.LatLngPopup())
    # Display the map in Streamlit and capture the click event
    map_output = st_folium(m, width=1200, height=800)

with col2:
    ##### PROCESS USER'S ACCIDENT INPUT #####
    # Check if the user clicked on the map and retrieve the coordinates
    if map_output['last_clicked'] is None:
        st.header("Navigate to and click on accident location on map.")
        # Instantiate the location to the default starting location
        lat = lat_start
        lon = lon_start
        zipcode = reverse_geocode(lat, lon).get('postcode')
        
        # Instantiate the current time
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        local_timezone = pytz.timezone(timezone_str)
        local_time = datetime.now(local_timezone)
        local_time = pd.to_datetime(local_time, format='ISO8601')
        # Retrieve the weather information for the default starting location
        weather_data = get_weather_data(lat, lon, API_KEY)
        temp = weather_data['main']['temp']
        wind_chill = weather_data['main']['feels_like']
        pressure = weather_data['main']['pressure'] * 0.2953 # convert API data from hPA to inHg
        visibility = weather_data['visibility'] / 1609.34 # convert API data from meters to miles
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        

    elif map_output['last_clicked'] is not None:
        lat = map_output['last_clicked']['lat']
        lon = map_output['last_clicked']['lng']
        timezone_str = tf.timezone_at(lat=lat, lng=lon)

        # Apply the timezone
        if timezone_str:
            local_timezone = pytz.timezone(timezone_str)
            local_time = datetime.now(local_timezone)
            local_time = pd.to_datetime(local_time, format='ISO8601')
            # Display time of click
            st.write(f"Accident Time: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
            #st.write(f"Accident Time: {local_time}")
        else:
            st.write("Timezone could not be determined for the given coordinates.")
        
        # Display the selected latitude and longitude
        st.write(f"Accident Latitude: {lat}")
        st.write(f"Accident Longitude: {lon}")
        
        # Reverse geocode the selected lat/lng to get address details and display address
        if reverse_geocode(lat, lon):
            house_number = reverse_geocode(lat, lon).get('house_number')
            street = reverse_geocode(lat, lon).get('road')
            city = reverse_geocode(lat, lon).get('city')
            state = reverse_geocode(lat, lon).get('state')
            zipcode = reverse_geocode(lat, lon).get('postcode')
            address = f"{house_number} {street}, {city}, {state} {zipcode}"
            st.write(f"Nearest Address: {address}")
        else:
            st.write("Address data could not be retrieved.")
        
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
    # Import the optimized model features                                   
    model_features = pd.read_csv("model_features.csv")
    model_features = model_features[model_features["Feature"] != "Severity"]
    if weather_data is not None and reverse_geocode(lat, lon) is not None:
        columns = ["Start_Month", "Start_Day", "Start_Hour", "Start_Lat", "Start_Lng", "Temperature(F)", "Pressure(in)", "Visibility(mi)", "Humidity(%)", "Wind_Speed(mph)", "Traffic_Signal"]
        inputs = [[local_time.month, local_time.day, local_time.hour, lat, lon, temp, pressure, visibility, humidity, wind_speed, traffic_signal]]
        user_input = pd.DataFrame(inputs, columns=columns)
        # Reorder the input features to match what the model expects to see     
        user_input = user_input[model_features["Feature"].values] 
        # Display model input DataFrame (not displayed in production app)
        #st.write("Features to load into model:")
        #st.write(user_input) 


    ##### Test loading the model ##### [UNUSED]
    #st.title("Test load model.")
    #try:
    #    with open('applet_model.pkl', 'rb') as file:
    #            model = pickle.load(file)
    #    st.write("Model loaded successfully.")
    #except Exception as e1:
    #    st.write("Error loading model:", e1)


    # Model file IDs from Google Drive
    # Random Forest Model - https://drive.google.com/file/d/143EKAWRozG165zuVP54h5MJdW40Pw1ls/view?usp=drive_link
    # XGBoost Model - https://drive.google.com/file/d/1_0kDivpnBZRuoSnYWgiG1z1Xln7oFf1D/view?usp=drive_link
    # Blended RF+XGB Model - https://drive.google.com/file/d/1Q4b62ys0ooYfElCBZHn8M-u38ykzLkDL/view?usp=drive_link

    ##### Generate predictions #####
    #st.title("Attempt to generate prediction.")
    # Retrieve model .pkl file from Google Drive by specifying the Google Drive file url and downloading the file
    file_id = "1_0kDivpnBZRuoSnYWgiG1z1Xln7oFf1D"
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, "applet_model.pkl", quiet=False)
    # Define the model
    with open('applet_model.pkl', 'rb') as file:
        model = pickle.load(file)
    # Define callable prediction function to invoke the model on input data
    def severity_predictor(input):
        # Generate prediction    
        prediction = model.predict(input)
        return prediction


    ##### Run and display prediction #####
    if map_output['last_clicked'] is not None and weather_data is not None and reverse_geocode(lat, lon) is not None:
        try:
            severity_prediction = severity_predictor(user_input)
            if severity_prediction==1:
                message = "Minor"
                color = "green"
                size = 32
            elif severity_prediction==2:
                message = "Moderate"
                color = "yellow"
                size = 34
            elif severity_prediction==3:
                message = "Major"
                color = "orange"
                size = 36
            elif severity_prediction==4:
                message = "SEVERE"
                color = "red"
                size = 38
            st.header("Accident traffic impact severity:")
            st.markdown(f"<h1 style='color: {color}; font-size: {size}px;'>{severity_prediction[0]} | {message}</h1>", unsafe_allow_html=True)
            #st.markdown(f"<h1 style='color: {color}; font-size: {size}px;'>{message}</h1>", unsafe_allow_html=True)    
        except Exception as e2:
            st.write("Error running model:", e2)
    elif map_output['last_clicked'] is not None:
        st.write("Prediction cannot be generated. Please try again.")
