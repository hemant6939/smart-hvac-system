from dotenv import load_dotenv  # To load variables from the env file
import os  # To access the environment variables
import requests
import streamlit as st
import random
from PIL import Image

# Load environment variables from the '.env' file
load_dotenv()  # Automatically looks for .env in the project root directory

# Access the API key from the environment variables
API_KEY = os.getenv("API_KEY")  # Get the API key value from the '.env' file

# If the API_KEY is not found in the env file, you can provide an error message or fallback value
if not API_KEY:
    st.error("API Key not found. Please check your '.env' file.")

# OpenWeatherMap API details
DEFAULT_CITY = "London"
DEFAULT_COUNTRY = "UK"

# Recommended settings
RECOMMENDED_MIN_TEMP = 20  # Preferred Minimum Indoor Temperature
RECOMMENDED_MAX_TEMP = 26  # Preferred Maximum Indoor Temperature
RECOMMENDED_OUTDOOR_THRESHOLD = 27  # Turn ON AC if Outdoor Temp is Above
AQI_THRESHOLD = 100  # AQI threshold to turn ON the Air Purifier

# Path for images directory (relative path for cloud and local)
image_dir = "images"  # Folder 'images' should be in the same directory as this script

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
    return "Winter" if temperature < 15 else "Summer"

# Determine AC, humidifier, dehumidifier, and air purifier actions
def determine_actions(outdoor_temp, outdoor_humidity, aqi, preferred_min, preferred_max, outdoor_threshold, season, is_room_occupied):
    ac_status = "OFF"
    humidifier_status = "OFF"
    dehumidifier_status = "OFF"
    air_purifier_status = "OFF"

    if is_room_occupied:  # Check if the room is occupied
        # AC logic
        if outdoor_temp > outdoor_threshold:
            ac_status = "ON"

        # Humidity logic
        if season == "Winter":
            if outdoor_humidity < 30:
                humidifier_status = "ON"
            elif outdoor_humidity > 50:
                dehumidifier_status = "ON"
        elif season == "Summer":
            if outdoor_humidity < 40:
                humidifier_status = "ON"
            elif outdoor_humidity > 60:
                dehumidifier_status = "ON"

        # Air Purifier logic
        if aqi and aqi > AQI_THRESHOLD:
            air_purifier_status = "ON"
    else:
        st.warning("Room is unoccupied. Devices are OFF to save energy.")

    return ac_status, humidifier_status, dehumidifier_status, air_purifier_status

# Load weather images based on temperature
def get_weather_image(temp):
    try:
        if temp < 15:
            weather_image_path = os.path.join(image_dir, "cold_weather.png")
        elif temp > 30:
            weather_image_path = os.path.join(image_dir, "hot_weather.png")
        elif 15 <= temp <= 20 or 26 <= temp <= 30:
            weather_image_path = os.path.join(image_dir, "mild_weather.png")
        else:
            weather_image_path = os.path.join(image_dir, "energy_saving.png")

        weather_image = Image.open(weather_image_path)
        return weather_image
    except FileNotFoundError:
        st.error(f"Image {weather_image_path} not found. Please check your image paths.")
        return None

# Main Streamlit App
st.title("SMART HVAC SYSTEM")
st.subheader("Optimize comfort, energy savings, and air quality using real-time data!")

# Weather source selection
st.header("Weather Source")
weather_source = st.radio(
    "Choose how to provide weather data:",
    ("Real-time Weather Data", "Manual Input")
)

if weather_source == "Real-time Weather Data":
    city = st.text_input("Enter your city", DEFAULT_CITY)
    country = st.text_input("Enter your country code (e.g., 'US', 'UK')", DEFAULT_COUNTRY)

    if st.button("Fetch Weather and AQI"):
        temp, humidity, lat, lon = fetch_weather(city, country, API_KEY)
        if temp is not None:
            aqi = fetch_aqi(lat, lon, API_KEY)
            st.success(f"Temperature: {temp}°C, Humidity: {humidity}%, AQI: {aqi}")
else:
    manual_temp = st.number_input("Enter the outdoor temperature (°C)", -50, 50, 22)
    manual_humidity = st.number_input("Enter the outdoor humidity (%)", 0, 100, 50)
    manual_aqi = st.number_input("Enter the AQI", 0, 500, 75)
