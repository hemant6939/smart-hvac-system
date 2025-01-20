import streamlit as st
from dotenv import load_dotenv
import requests
import os

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
preferred_min_temp = int(os.getenv("PREFERRED_MIN_TEMP", 22))
preferred_max_temp = int(os.getenv("PREFERRED_MAX_TEMP", 25))
outdoor_temp_threshold = int(os.getenv("OUTDOOR_TEMP_THRESHOLD", 28))
AQI_THRESHOLD = int(os.getenv("AQI_THRESHOLD", 100))

# Function to fetch weather data
def fetch_weather(city, country, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]
        return temp, humidity, lat, lon
    else:
        st.error("Error fetching weather data. Please check the city and country inputs.")
        return None, None, None, None

# Function to fetch AQI
def fetch_aqi(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["list"][0]["main"]["aqi"]
    else:
        st.warning("Could not fetch AQI data.")
        return None

# Determine the season based on temperature
def determine_season(temp):
    if temp < 15:
        return "Winter"
    elif temp < 30:
        return "Spring/Fall"
    else:
        return "Summer"

# Determine device actions
def determine_actions(outdoor_temp, outdoor_humidity, aqi, preferred_min, preferred_max, outdoor_threshold, season, is_room_occupied):
    ac_status = "OFF"
    heater_status = "OFF"
    humidifier_status = "OFF"
    dehumidifier_status = "OFF"
    air_purifier_status = "OFF"

    if is_room_occupied:
        # AC logic
        if outdoor_temp > outdoor_threshold:
            ac_status = "ON"

        # Heater logic
        if outdoor_temp < 15:
            if outdoor_temp < 8:
                heater_status = "FULL SPEED"
            else:
                heater_status = "NORMAL SPEED"

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

    return ac_status, heater_status, humidifier_status, dehumidifier_status, air_purifier_status

# Get weather image
def get_weather_image(temp):
    base_path = "/Users/hemantchaudhary/Desktop/smart-hvac-system/"
    if temp < 15:
        return base_path + "cold.png"
    elif temp < 30:
        return base_path + "mild.png"
    else:
        return base_path + "hot.png"

# Main app
st.title("Smart HVAC System")
st.sidebar.title("Settings")
weather_source = st.sidebar.selectbox("Choose Weather Source", ["Real-time Weather Data", "Manual Input"])
is_room_occupied = st.sidebar.checkbox("Is the room occupied?", value=True)

if weather_source == "Real-time Weather Data":
    st.header("Real-time Weather Data")
    city = st.text_input("Enter your city")
    country = st.text_input("Enter your country")

    if st.button("Fetch Weather and AQI"):
        temp, humidity, lat, lon = fetch_weather(city, country, API_KEY)
        if temp is not None:
            aqi = fetch_aqi(lat, lon, API_KEY)
            season = determine_season(temp)

            # Determine device statuses
            ac_status, heater_status, humidifier_status, dehumidifier_status, air_purifier_status = determine_actions(
                temp, humidity, aqi, preferred_min_temp, preferred_max_temp, outdoor_temp_threshold, season, is_room_occupied
            )

            # Get weather image based on the temperature
            weather_image = get_weather_image(temp)

            st.success(f"Temperature: {temp}°C | Humidity: {humidity}% | Season: {season} | AQI: {aqi}")
            st.info(f"Room Occupied: {'Yes' if is_room_occupied else 'No'}")

            # Display Devices and Weather Image
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Devices")

                ac_text = f"<span style='color:{'green' if ac_status == 'ON' else 'red'};'>{ac_status}</span>"
                st.markdown(f"**AC**: {ac_text}", unsafe_allow_html=True)

                heater_text = f"<span style='color:{'green' if heater_status != 'OFF' else 'red'};'>{heater_status}</span>"
                st.markdown(f"**Heater**: {heater_text}", unsafe_allow_html=True)

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
    st.header("Enter Weather Data Manually")
    manual_temp = st.number_input("Enter the outdoor temperature (°C)", min_value=-50, max_value=50, value=22)
    manual_humidity = st.number_input("Enter the outdoor humidity (%)", min_value=0, max_value=100, value=50)
    manual_aqi = st.number_input("Enter the AQI", min_value=0, max_value=500, value=75)

    season = determine_season(manual_temp)
    aqi = manual_aqi

    # Determine device statuses
    ac_status, heater_status, humidifier_status, dehumidifier_status, air_purifier_status = determine_actions(
        manual_temp, manual_humidity, aqi, preferred_min_temp, preferred_max_temp, outdoor_temp_threshold, season, is_room_occupied
    )

    # Get weather image based on the temperature
    weather_image = get_weather_image(manual_temp)

    st.success(f"Manual Input - Temperature: {manual_temp}°C | Humidity: {manual_humidity}% | AQI: {manual_aqi} | Season: {season}")
    st.info(f"Room Occupied: {'Yes' if is_room_occupied else 'No'}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Devices")

        ac_text = f"<span style='color:{'green' if ac_status == 'ON' else 'red'};'>{ac_status}</span>"
        st.markdown(f"**AC**: {ac_text}", unsafe_allow_html=True)

        heater_text = f"<span style='color:{'green' if heater_status != 'OFF' else 'red'};'>{heater_status}</span>"
        st.markdown(f"**Heater**: {heater_text}", unsafe_allow_html=True)

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
