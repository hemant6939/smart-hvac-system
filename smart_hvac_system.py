from dotenv import load_dotenv  # To load variables from the env file
import os  # To access the environment variables
import requests
import streamlit as st
import random
from PIL import Image

# Load 'env' file locally
load_dotenv(dotenv_path='env')  # Specify the 'env' file explicitly

# Check if running locally or on Streamlit Cloud and load the API key accordingly
if "API_KEY" in os.environ:  # Local usage, load from 'env' file
    API_KEY = os.getenv("API_KEY")
else:  # Cloud usage, load from Streamlit secrets
    try:
        API_KEY = st.secrets["general"]["API_KEY"]
    except KeyError:
        API_KEY = None

# If the API_KEY is not found, display an error
if not API_KEY:
    st.error("API Key not found. Please check your API key configuration.")
    st.stop()

# OpenWeatherMap API details
DEFAULT_CITY = "London"
DEFAULT_COUNTRY = "UK"

# Recommended settings
RECOMMENDED_MIN_TEMP = 20  # Preferred Minimum Indoor Temperature
RECOMMENDED_MAX_TEMP = 26  # Preferred Maximum Indoor Temperature
RECOMMENDED_OUTDOOR_THRESHOLD = 27  # Turn ON AC if Outdoor Temp is Above
AQI_THRESHOLD = 100  # AQI threshold to turn ON the Air Purifier

# Fetch weather data from OpenWeatherMap
def fetch_weather(city, country, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        coord = data["coord"]  # Get latitude and longitude for AQI data
        return temp, humidity, coord["lat"], coord["lon"]
    else:
        return None, None, None, None

# Fetch AQI data from OpenWeatherMap
def fetch_aqi(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        aqi = data["list"][0]["main"]["aqi"]
        return aqi
    else:
        return None

# Determine season automatically based on temperature
def determine_season(temperature):
    if temperature < 15:
        return "Winter"
    elif 15 <= temperature <= 20 or 26 <= temperature <= 30:
        return "Mild"  # For temperature between 15-20°C or 26-30°C
    elif 20 <= temperature <= 26:
        return "Energy Saving"  # For temperature between 20-26°C
    else:
        return "Summer"  # For temperature greater than 30°C

# Determine device statuses
def determine_actions(outdoor_temp, outdoor_humidity, aqi, preferred_min, preferred_max, outdoor_threshold, season, is_room_occupied, aqi_threshold):
    ac_status = "OFF"
    humidifier_status = "OFF"
    dehumidifier_status = "OFF"
    air_purifier_status = "OFF"
    heater_status = "OFF"
    
    if is_room_occupied:  # Check if the room is occupied
        # AC logic
        if outdoor_temp > outdoor_threshold:
            ac_status = "ON"
        
        # Heater logic
        if season == "Winter" and outdoor_temp < 15:
            heater_status = "ON"

        # Humidity logic
        if season == "Winter" and outdoor_humidity < 30 and outdoor_temp < 15:
            humidifier_status = "ON"
        elif season == "Summer" and outdoor_humidity < 40 and outdoor_temp > 30:
            humidifier_status = "ON"
        elif outdoor_humidity > 60 and outdoor_temp > 30:
            dehumidifier_status = "ON"

        # Air Purifier logic
        if aqi and aqi > aqi_threshold:
            air_purifier_status = "ON"
    else:
        st.warning("Room is unoccupied. Devices are OFF to save energy.")

    return ac_status, humidifier_status, dehumidifier_status, air_purifier_status, heater_status

# Streamlit App
st.title("SMART HVAC SYSTEM")
st.subheader("Optimize comfort, energy savings, and air quality using real-time data!")

# Sidebar for user preferences
st.sidebar.header("User Preferences")
preferred_min_temp = st.sidebar.slider("Preferred Minimum Indoor Temperature (°C)", 18, 30, 22, key="min_temp_slider")
preferred_max_temp = st.sidebar.slider("Preferred Maximum Indoor Temperature (°C)", 20, 32, 26, key="max_temp_slider")
outdoor_temp_threshold = st.sidebar.slider("Turn ON AC if Outdoor Temp is Above (°C)", 15, 35, 25, key="ac_threshold_slider")
aqi_threshold = st.sidebar.slider("AQI Threshold for Air Purifier", 50, 300, AQI_THRESHOLD, key="aqi_threshold_slider")

# Room Occupancy Control
st.sidebar.header("Room Occupancy")
simulate_occupancy = st.sidebar.checkbox("Simulate Random Occupancy", value=False)
manual_override = st.sidebar.checkbox("Override Occupancy Manually", value=False)

if manual_override:
    is_room_occupied = st.sidebar.checkbox("Room is Occupied", value=True)
elif simulate_occupancy:
    is_room_occupied = random.choice([True, False])
else:
    is_room_occupied = st.sidebar.checkbox("Room is Occupied", value=True)

# Weather Data Input
st.header("Weather Source")
weather_source = st.radio("Choose how to provide weather data:", ("Real-time Weather Data", "Manual Input"))

if weather_source == "Real-time Weather Data":
    city = st.text_input("Enter your city", DEFAULT_CITY)
    country = st.text_input("Enter your country code (e.g., 'US', 'UK')", DEFAULT_COUNTRY)

    if st.button("Fetch Weather and AQI"):
        temp, humidity, lat, lon = fetch_weather(city, country, API_KEY)
        if temp is not None:
            aqi = fetch_aqi(lat, lon, API_KEY)
            season = determine_season(temp)
            actions = determine_actions(temp, humidity, aqi, preferred_min_temp, preferred_max_temp, outdoor_temp_threshold, season, is_room_occupied, aqi_threshold)

            st.success(f"Temperature: {temp}°C | Humidity: {humidity}% | Season: {season} | AQI: {aqi}")
            st.info(f"Room Occupied: {'Yes' if is_room_occupied else 'No'}")
            st.write(f"Device Status: {actions}")
        else:
            st.error("Failed to fetch weather data. Please check your inputs.")
else:
    temp = st.number_input("Outdoor Temperature (°C)", min_value=-50, max_value=50, value=22)
    humidity = st.number_input("Outdoor Humidity (%)", min_value=0, max_value=100, value=50)
    aqi = st.number_input("AQI", min_value=0, max_value=500, value=75)
    season = determine_season(temp)
    actions = determine_actions(temp, humidity, aqi, preferred_min_temp, preferred_max_temp, outdoor_temp_threshold, season, is_room_occupied, aqi_threshold)

    st.success(f"Temperature: {temp}°C | Humidity: {humidity}% | Season: {season} | AQI: {aqi}")
    st.info(f"Room Occupied: {'Yes' if is_room_occupied else 'No'}")
    st.write(f"Device Status: {actions}")
