import os
import requests
import streamlit as st
import random
from PIL import Image
from dotenv import load_dotenv

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

# When Override Occupancy is checked, uncheck Simulate Random Occupancy
if manual_override:
    simulate_occupancy = False

# Conditionally hide checkboxes based on the state of the other checkbox
if manual_override:
    is_room_occupied = st.sidebar.checkbox("Room is Occupied", value=True)
    room_status = "Room Occupied" if is_room_occupied else "Room Unoccupied"
    st.sidebar.write(f"Override: {room_status}")
elif simulate_occupancy:
    manual_override = False
    st.session_state.random_occupancy = random.choice([True, False])
    is_room_occupied = st.session_state.random_occupancy
else:
    is_room_occupied = st.sidebar.checkbox("Room is Occupied", value=True)

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
image_dir = "images"  # Use relative path

def get_weather_image(temp):
    # Check the image directory path
    st.write(f"Image directory path: {image_dir}")  # This will print the path to your Streamlit app

    if temp < 15:
        weather_image_path = os.path.join(image_dir, "cold_weather.png")
    elif temp > 30:
        weather_image_path = os.path.join(image_dir, "hot_weather.png")
    elif 15 <= temp <= 20 or 26 <= temp <= 30:
        weather_image_path = os.path.join(image_dir, "mild_weather.png")
    else:
        weather_image_path = os.path.join(image_dir, "energy_saving.png")  # Updated to 'energy_saving.png'

    try:
        weather_image = Image.open(weather_image_path)
        weather_image = weather_image.resize((300, 300))  # Resize to 300x300 (you can adjust this size)
        return weather_image
    except FileNotFoundError:
        st.error(f"Image {weather_image_path} not found. Please check your image paths.")
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

            # Get weather image based on the temperature
            weather_image = get_weather_image(temp)

            st.success(f"Temperature: {temp}°C | Humidity: {humidity}% | Season: {season} | AQI: {aqi}")
            st.info(f"Room Occupied: {'Yes' if is_room_occupied else 'No'}")

            # Layout: Display Devices (AC, Humidifier, Dehumidifier, Air Purifier) and Weather Image in Two Columns
            col1, col2 = st.columns([2, 1])  # Two columns: AC and Devices in left, weather image in right

            with col1:
                st.subheader("Devices")
                # Display device statuses with color only for ON/OFF
                ac_text = f"<span style='color:{'green' if ac_status == 'ON' else 'red'};'>{ac_status}</span>"
                st.markdown(f"**AC**: {ac_text}", unsafe_allow_html=True)

                humidifier_text = f"<span style='color:{'green' if humidifier_status == 'ON' else 'red'};'>{humidifier_status}</span>"
                st.markdown(f"**Humidifier**: {humidifier_text}", unsafe_allow_html=True)

                dehumidifier_text = f"<span style='color:{'green' if dehumidifier_status == 'ON' else 'red'};'>{dehumidifier_status}</span>"
                st.markdown(f"**Dehumidifier**: {dehumidifier_text}", unsafe_allow_html=True)

                air_purifier_text = f"<span style='color:{'green' if air_purifier_status == 'ON' else 'red'};'>{air_purifier_status}</span>"
                st.markdown(f"**Air Purifier**: {air_purifier_text}", unsafe_allow_html=True)

            with col2:
                if weather_image:
                    st.image(weather_image, use_container_width=True)
                else:
                    st.warning("Could not load weather image.")

else:
    # Manual Input for Weather Data
    st.header("Enter Weather Data Manually")
    manual_temp = st.number_input("Enter the outdoor temperature (°C)", min_value=-50, max_value=50, value=22)
    manual_humidity = st.number_input("Enter the outdoor humidity (%)", min_value=0, max_value=100, value=50)
    manual_aqi = st.number_input("Enter the AQI", min_value=0, max_value=500, value=75)  # AQI input field added
    
    season = determine_season(manual_temp)
    aqi = manual_aqi  # Manual input now uses the entered AQI value

    ac_status, humidifier_status, dehumidifier_status, air_purifier_status = determine_actions(
        manual_temp, manual_humidity, aqi, preferred_min_temp, preferred_max_temp, outdoor_temp_threshold, season, is_room_occupied
    )

    # Get weather image based on the temperature
    weather_image = get_weather_image(manual_temp)

    # Show the results based on manual input
    st.success(f"Manual Input - Temperature: {manual_temp}°C | Humidity: {manual_humidity}% | AQI: {aqi}")
    st.info(f"Room Occupied: {'Yes' if is_room_occupied else 'No'}")

    # Display devices in two columns
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Devices")
        ac_text = f"<span style='color:{'green' if ac_status == 'ON' else 'red'};'>{ac_status}</span>"
        st.markdown(f"**AC**: {ac_text}", unsafe_allow_html=True)

        humidifier_text = f"<span style='color:{'green' if humidifier_status == 'ON' else 'red'};'>{humidifier_status}</span>"
        st.markdown(f"**Humidifier**: {humidifier_text}", unsafe_allow_html=True)

        dehumidifier_text = f"<span style='color:{'green' if dehumidifier_status == 'ON' else 'red'};'>{dehumidifier_status}</span>"
        st.markdown(f"**Dehumidifier**: {dehumidifier_text}", unsafe_allow_html=True)

        air_purifier_text = f"<span style='color:{'green' if air_purifier_status == 'ON' else 'red'};'>{air_purifier_status}</span>"
        st.markdown(f"**Air Purifier**: {air_purifier_text}", unsafe_allow_html=True)

    with col2:
        if weather_image:
            st.image(weather_image, use_container_width=True)
        else:
            st.warning("Could not load weather image.")
