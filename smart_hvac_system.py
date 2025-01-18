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
    simulate_occupancy = False
    is_room_occupied = st.sidebar.checkbox("Room is Occupied", value=True)
else:
    is_room_occupied = random.choice([True, False]) if simulate_occupancy else st.sidebar.checkbox("Room is Occupied", value=True)

# Apply Best Settings
if st.sidebar.button("Apply Best Settings"):
    st.session_state["preferred_min_temp"] = RECOMMENDED_MIN_TEMP
    st.session_state["preferred_max_temp"] = RECOMMENDED_MAX_TEMP
    st.session_state["outdoor_temp_threshold"] = RECOMMENDED_OUTDOOR_THRESHOLD
    st.session_state["aqi_threshold"] = AQI_THRESHOLD
    st.sidebar.success("Best settings applied!")

# Main App: Real-Time Weather or Manual Input
st.header("Weather Source")
weather_source = st.radio(
    "Choose how to provide weather data:",
    ("Real-time Weather Data", "Manual Input")
)

# Path for images directory
image_dir = "images"  # Use relative path for images

def get_weather_image(temp):
    if temp < 15:
        weather_image_path = os.path.join(image_dir, "cold_weather.png")
    elif temp > 30:
        weather_image_path = os.path.join(image_dir, "hot_weather.png")
    elif 15 <= temp <= 20 or 26 <= temp <= 30:
        weather_image_path = os.path.join(image_dir, "mild_weather.png")
    else:
        weather_image_path = os.path.join(image_dir, "energy_saving.png")

    try:
        return Image.open(weather_image_path)
    except FileNotFoundError:
        st.error(f"Image {weather_image_path} not found. Please ensure the images folder is properly set up.")
        return None

if weather_source == "Real-time Weather Data":
    city = st.text_input("Enter your city", DEFAULT_CITY)
    country = st.text_input("Enter your country code (e.g., 'US', 'UK')", DEFAULT_COUNTRY)

    if st.button("Fetch Weather and AQI"):
        temp, humidity, lat, lon = fetch_weather(city, country, API_KEY)
        if temp is not None:
            aqi = fetch_aqi(lat, lon, API_KEY)
            season = determine_season(temp)

            ac_status, humidifier_status, dehumidifier_status, air_purifier_status = determine_actions(
                temp, humidity, aqi, preferred_min_temp, preferred_max_temp, outdoor_temp_threshold, season, is_room_occupied
            )

            weather_image = get_weather_image(temp)

            st.success(f"Temperature: {temp}°C | Humidity: {humidity}% | Season: {season} | AQI: {aqi}")
            st.info(f"Room Occupied: {'Yes' if is_room_occupied else 'No'}")

            # Display the image and statuses
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Devices")
                st.markdown(f"**AC**: {'ON' if ac_status == 'ON' else 'OFF'}")
                st.markdown(f"**Humidifier**: {'ON' if humidifier_status == 'ON' else 'OFF'}")
            with col2:
                if weather_image:
                    st.image(weather_image)
else:
    manual_temp = st.number_input("Enter outdoor temperature:", -50, 50, value=25)
    season = determine_season(manual_temp)
    st.write(f"Season: {season}")
