import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim

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
    geolocator = Nominatim(user_agent="streamlit-app")
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
