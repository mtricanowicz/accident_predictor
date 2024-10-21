import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import requests

# Set a starting location on the map (the Dubois Center)
lat_start = 35.22862041030688
lon_start = -80.83445778852331

# Define the openweathermaps.org API components
# Define the API key to use
API_KEY = "0a2f1b71c8591af7c64f8dd7b5a31323" # my API key

# Initialize the Streamlit app with a selectable map
st.title("Select a Point on the Map")

# Create a map centered on some initial location (e.g., San Francisco)
m = folium.Map(location=[lat_start, lon_start], zoom_start=20)

# Add a click event to the map to capture user-selected point
m.add_child(folium.LatLngPopup())

# Display the map in Streamlit and capture the click event
map_output = st_folium(m, width=900, height=600)

# Function to reverse geocode (get address from lat/lng)
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="accident_input")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.address
    return "Address not found"

# Function to fetch weather data from OpenWeatherMap
def get_weather_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Check if the user clicked on the map and retrieve the coordinates
if map_output['last_clicked'] is not None:
    lat = map_output['last_clicked']['lat']
    lon = map_output['last_clicked']['lng']

    # Display the selected latitude and longitude
    st.write(f"Selected Latitude: {lat}")
    st.write(f"Selected Longitude: {lon}")

    # Reverse geocode the selected lat/lng to get address details
    address = reverse_geocode(lat, lon)
    st.write(f"Address: {address}")

    # Fetch weather data based on the selected location
    weather_data = get_weather_data(lat, lon, API_KEY)

    if weather_data:
        # Display some basic weather information
        temp = weather_data['main']['temp']
        weather_desc = weather_data['weather'][0]['description']
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']

        st.write(f"Weather: {weather_desc.capitalize()}")
        st.write(f"Temperature: {temp} °C")
        st.write(f"Humidity: {humidity}%")
        st.write(f"Wind Speed: {wind_speed} m/s")
    else:
        st.write("Weather data could not be retrieved.")
else:
    st.write("Click on the map to select a point.")
