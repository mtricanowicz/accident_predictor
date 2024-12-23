import streamlit as st
import os
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

# Link to presentation document
presentation = st.secrets["Documents"]["presentation"] # Random Forest Model

# Set custom page configuration including the "About" section
st.set_page_config(
    page_title="Traffic Impact Predictor",  # Custom title in the browser tab
    page_icon=":vertical_traffic_light:",  # Custom icon for the browser tab
    layout="wide",  # Set the defaul layout for the app
    initial_sidebar_state="auto",  # Sidebar state when app loads
    menu_items={
        "About": f"""
        ## Traffic Impact Predictor App
        This app was created to satisfy the project requirement of DSBA-6156 ([accompanying presentation]({presentation})) as part of the MS degree program in Data Science and Business Analytics at The University of North Carolina at Charlotte.\n
        - **Author:** Michael Tricanowicz
        - **GitHub:** [accident_predictor](https://github.com/mtricanowicz/accident_predictor)
        """
    }
)

# Import the optimized model features                                   
model_features = pd.read_csv("model_features.csv")
model_features = model_features[model_features["Feature"] != "Severity"]

# Load the prediction log
prediction_log = pd.read_csv("prediction_log.csv") # Loads a persistent prediction log

tab1, tab2 = st.tabs(["Traffic Impact Predictor", "Prediction Log"])

with tab1:
    # Set page title
    st.header("Traffic Impact Predictor", divider="gray")

    ##### RETRIEVE AND LOAD MODEL #####

    # Specify the Google Drive file url to enable download and retrieval of the model .pkl file from Google Drive 
    # Model file IDs from Google Drive
    randomforest_id = st.secrets["Model_pkl_IDs"]["randomforest_id"] # Random Forest Model
    xgboost_id = st.secrets["Model_pkl_IDs"]["xgboost_id"] # XGBoost Model
    blended_id = st.secrets["Model_pkl_IDs"]["blended_id"] # Blended RF+XGB Model
    file_id = blended_id
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

    ##### RETRIEVE AND LOAD MODEL COMPLETE ##### 


    # Display explanation of the app
    with st.expander(label="About this app."):
        st.write("The purpose of this app is to use a pretrained machine learning model to predict how severe the traffic impact will be as a result of an accident.") 
        st.write(f"""The current version of this app uses a {model.__class__.__name__} model {'with constituent models' if model.__class__.__name__=='VotingClassifier' else ''} {' and '.join([estimator.__class__.__name__ for _, estimator in model.estimators]) if model.__class__.__name__=='VotingClassifier' else ''} trained on the following features: {', '.join(model_features["Feature"].astype(str))}.
            The model was developed around the ['US Accidents (2016-2023)'](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents) dataset found on kaggle.
            The dataset contains approximately 7.7 million accident records from the continental United States between the years 2016-2023 with 46 original features.
            Undersampling, data cleaning, and feature selection was performed on the original dataset to prepare it for model development.
        """)
        st.write("""This app provides a means for a user to input an accident location. The location and time of the input, as well as accompanying geographic and weather data, is fed into the model to generate a prediction. 
            This app is designed to require as little user intervention as possible. A single click should be sufficient to obtain a prediction.
                This is accomplished by processing the user input as follows:
                \n1. The user click generates a latitude and longitude value.
                \n2. The lat/lon is processed by timzonefinder and pytz to determine the local time zone.
                \n3. A timestamp is applied at time of click with the local timezone to generate local time of the event.
                \n4. The lat/lon is processed by the Nominatim geocoder of geopy to generate the nearest address to the event location.
                \n5. The lat/lon is processed by the OpenWeatherMap API to fetch the weather conditions for the location and time of the event.
                \n6. The lat/lon is processed by the OpenStreetMap Overpass API to fetch whether a traffic signal is present within 400 m (approx 1/4 mile) of the event location.
                \n7. The lat/lon is processed by the OpenStreetMap Overpass API to confirm whether it is a road to ensure it is a valid location to make a traffic impact prediction.
                \n8. The processed data is then compiled into a dataframe as the input variables for the model.
                \n9. The input dataframe is fed to the model to generate a severity prediction between 1 (least severe) and 4 (most severe).
                \n10. The prediction and input variables are displayed by the app in a user friendly format. 
        """)
        st.write("Identify accident location by selecting a point on the map.")
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)


    ##### DEFINE FUNCTIONS #####

    # Define the openweathermaps.org API key to use
    API_KEY_owm = st.secrets["API_Keys"]["API_KEY_owm"] # my API key

    # Define function to reverse geocode (get address from lat/lng)
    def reverse_geocode(lat, lon):
        geolocator = Nominatim(user_agent="accident_input")
        try:
            location = geolocator.reverse((lat, lon), exactly_one=True)
            if location:
                return location.raw['address']
            else:
                return None
        except Exception as e: # Handle errors
            return "Error: An unexpected error occurred. Please try again."

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

    ##### DEFINE FUNCTIONS COMPLETE #####


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
        map_output = st_folium(m, width=1350, height=850)

        ##### PROCESS USER'S ACCIDENT INPUT #####
        start_time = datetime.now()
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
        if isinstance(reverse_geocode(lat, lon), str) and "Error" in reverse_geocode(lat, lon):
            address = reverse_geocode(lat, lon)
        elif reverse_geocode(lat, lon):
            house_number = reverse_geocode(lat, lon).get('house_number')
            street = reverse_geocode(lat, lon).get('road')
            city = reverse_geocode(lat, lon).get('city')
            state = reverse_geocode(lat, lon).get('state')
            zipcode = reverse_geocode(lat, lon).get('postcode')
            address = f"{house_number} {street}, {city}, {state} {zipcode}"
        else:
            address = "Address data could not be retrieved."
        
        # Fetch weather data based on the selected location
        weather_data = get_weather_data(lat, lon, API_KEY_owm)
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

        ##### USE OPENSTREETMAPS OVERPASS API TO MAKE CERTAIN CHECKS #####
        # Define OSM's Overpass API URL
        url_osm = "http://overpass-api.de/api/interpreter"
        ## Determine traffic signal presence ##
        # Define Overpass query to retrieve traffic signals within 400 meters (about 1/4 mile) from the selected accident location
        query_signal = f"""
        [out:json];
        node["highway"="traffic_signals"](around:400,{lat},{lon});
        out body;
        """
        # Send the request
        response_signal = requests.get(url_osm, params={'data': query_signal})
        # Parse response JSON
        traffic_presence = response_signal.json()
        # Define the traffic_signal variable. An empty set returned from the OSM query implies no traffic signals within the 1/4 mile radius
        if traffic_presence['elements']==[]:
            traffic_signal = False
        else:
            traffic_signal = True
        ## Perform check to determine if the selected location is a road ##
        # Define Overpass query to retrieve roads within 15 meters (about 50 feet) from the selected accident location
        query_roads = f"""
        [out:json];
        way["highway"](around:15,{lat},{lon});
        out ids;
        """
        # Send the request
        response_roads = requests.get(url_osm, params={'data': query_roads})
        # Parse response JSON
        roads_presence = response_roads.json()
        # Define the is_road variable. An empty set returned from the OSM query implies that the selected location is not within 50 feet of a road
        if roads_presence['elements']==[]:
            is_road = False
        else:
            is_road = True

        ##### Store accident conditions in a DataFrame #####
        if weather_data is not None and reverse_geocode(lat, lon) is not None:
            columns = ["Start_Month", "Start_Day", "Start_Hour", "Start_Lat", "Start_Lng", "Temperature(F)", "Pressure(in)", "Visibility(mi)", "Humidity(%)", "Wind_Speed(mph)", "Traffic_Signal"]
            inputs = [[local_time.month, local_time.dayofweek, local_time.hour, lat, lon, temp, pressure, visibility, humidity, wind_speed, traffic_signal]]
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
        # If user input is detected generate and display prediction
        elif map_output['last_clicked'] is not None and weather_data is not None and reverse_geocode(lat, lon) is not None and is_road==True:
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
        # Otherwise return prompts if the location does not meet necessary requirements for a prediction 
        elif map_output['last_clicked'] is not None and is_road==False:
            st.divider()
            st.header("Selected location is not a road.")
            st.header("Please try again.")
            st.divider()
        elif map_output['last_clicked'] is not None and weather_data is None and reverse_geocode(lat, lon) is not None:
            st.divider()
            st.header("Failed to retrieve weather data.")
            st.header("Please try again.")
            st.divider()
        elif map_output['last_clicked'] is not None and weather_data is not None and reverse_geocode(lat, lon) is None:
            st.divider()
            st.header("Address not valid.")
            st.header("Please try again.")
            st.divider()
        elif map_output['last_clicked'] is not None:
            st.divider()
            st.header("Prediction cannot be generated")
            st.header("Please try again.")
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
        with st.expander("Location Conditions", expanded=True):
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
            if weather_data is not None:
                # Display weather information (not displayed in production app)
                st.write(f"🌡️ Temperature: {temp} °F")
                st.write(f"🌥️ Pressure: {np.round(pressure, 2)} inHg")
                st.write(f"🌫️ Visibility: {np.round(visibility, 2)} miles")
                st.write(f"☀️ Humidity: {humidity} %")
                st.write(f"☁️ Wind Speed: {wind_speed} mph")
                st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            if traffic_signal is not None:
                # Display traffic signal presence
                st.write(f"🚦 Traffic Signal within 1/4 mile: {traffic_signal}")
                st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        end_time = datetime.now()
        st.write("")
        st.write(f"Processing time: {(np.timedelta64((end_time-start_time), "s")/np.timedelta64(1, "s")):.0f} seconds")

# Log the prediction
with tab2:
    st.header("Prediction Log", divider="gray")
    with st.expander(label="About this log."):
        st.write("This tab records the log of predictions for the current session. It initializes with a few previous predictions shown as examples of what to expect.") 
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    # prediction_log = pd.DataFrame(columns=["Traffic Impact Prediction", "Local Time", "Latitude", "Longitude", "Temperature (°F)", "Pressure (inHg)", "Visibility (mi)", "Humidity (%)", "Wind Speed (mph)", "Traffic Signal"]) # This line can be used to reset the log
    if "severity_prediction" in locals() or 'severity_prediction' in globals():
        prediction_latest = [severity_prediction[0], local_time, decimal_to_dms(lat), decimal_to_dms(lon), temp, np.round(pressure, 2), np.round(visibility, 2), humidity, wind_speed, traffic_signal]
        prediction_log.loc[len(prediction_log)] = prediction_latest
        prediction_log.to_csv("prediction_log.csv", index=False)
    st.dataframe(prediction_log)

