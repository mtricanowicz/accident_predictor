import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import requests

# Initialize the Streamlit app
st.title("Select a Point on the Map")

# Create a map centered on some initial location (e.g., San Francisco)
m = folium.Map(location=[37.7749, -122.4194], zoom_start=10)

# Add a click event to the map to capture user-selected point
m.add_child(folium.LatLngPopup())

# Display the map in Streamlit and capture the click event
map_output = st_folium(m, width=700, height=500)

# Function to reverse geocode (get address from lat/lng)
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="accident_input")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.address
    return "Address not found"

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
else:
    st.write("Click on the map to select a point.")


API_KEY = "0a2f1b71c8591af7c64f8dd7b5a31323"
LAT, LON = map_output['last_clicked']['lat'], map_output['last_clicked']['lng']  # location from map click

def get_weather(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    return response.json()

weather_data = get_weather(LAT, LON, API_KEY)
print(weather_data)

