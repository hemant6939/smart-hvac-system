from dotenv import load_dotenv
import os
import requests
import streamlit as st
import random
from PIL import Image

# Configuration
CONFIG = {
    "DEFAULT_CITY": "London",
    "DEFAULT_COUNTRY": "UK",
    "RECOMMENDED_TEMP": (20, 26),
    "AQI_THRESHOLD": 100,
    "IMAGE_MAPPING": {
        "cold": "cold_weather.png",
        "hot": "hot_weather.png",
        "mild": "mild_weather.png",
        "optimal": "energy_saving.png"
    }
}

# Initialize environment
load_dotenv(dotenv_path='env')
API_KEY = os.getenv("API_KEY") or st.secrets.get("general", {}).get("API_KEY")

if not API_KEY:
    st.error("❌ Missing API Key. Please configure your OpenWeatherMap API key.")
    st.stop()

# Helper functions
def get_weather_image(temp):
    """Get appropriate weather image based on temperature"""
    image_dir = "images"
    
    if temp < 15:
        image_key = "cold"
    elif temp > 30:
        image_key = "hot"
    elif 15 <= temp <= 20 or 26 <= temp <= 30:
        image_key = "mild"
    else:
        image_key = "optimal"

    try:
        return Image.open(os.path.join(image_dir, CONFIG["IMAGE_MAPPING"][image_key])).resize((300, 300))
    except (FileNotFoundError, KeyError) as e:
        st.error(f"⚠️ Image not found: {str(e)}")
        return None

def handle_api_error(response, service_name):
    """Handle API response errors"""
    if response.status_code == 401:
        st.error("🔑 Invalid API Key. Please check your OpenWeatherMap credentials.")
    elif response.status_code == 404:
        st.error("🌍 Location not found. Please check city/country names.")
    else:
        st.error(f"⚠️ Error fetching {service_name} data: {response.status_code}")
    return None

# Data fetching functions
def fetch_weather_data(city, country):
    """Fetch current weather data from OpenWeatherMap"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    
    if response.status_code != 200:
        return handle_api_error(response, "weather")
        
    data = response.json()
    return {
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "lat": data["coord"]["lat"],
        "lon": data["coord"]["lon"]
    }

def fetch_aqi_data(lat, lon):
    """Fetch air quality data from OpenWeatherMap"""
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return handle_api_error(response, "air quality")
        
    return response.json()["list"][0]["main"]["aqi"]

# Core logic
def determine_climate_actions(weather_data, aqi_data, user_prefs, occupancy):
    """Determine HVAC system actions based on environmental conditions"""
    actions = {
        "ac": "OFF",
        "humidifier": "OFF",
        "dehumidifier": "OFF",
        "air_purifier": "OFF",
        "heater": "OFF"
    }

    if not occupancy:
        return actions

    # Temperature-based actions
    if weather_data["temp"] > user_prefs["ac_threshold"]:
        actions["ac"] = "ON"
    elif weather_data["temp"] < 15:
        actions["heater"] = "ON"

    # Humidity management
    humidity = weather_data["humidity"]
    if humidity < 30:
        actions["humidifier"] = "ON"
    elif humidity > 60:
        actions["dehumidifier"] = "ON"

    # Air quality control
    if aqi_data and aqi_data > user_prefs["aqi_threshold"]:
        actions["air_purifier"] = "ON"

    return actions

# UI Components
def create_device_status(device, status):
    """Create styled device status display"""
    color = "green" if status == "ON" else "red"
    return f"<span style='color: {color}; font-weight: bold;'>{status}</span>"

def show_results_panel(actions, weather_data, aqi_data, image):
    """Display results in a organized layout"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🏠 Device Status")
        for device, status in actions.items():
            st.markdown(
                f"**{device.title()}:** {create_device_status(device, status)}", 
                unsafe_allow_html=True
            )
            
    with col2:
        if image:
            st.image(image, use_container_width=True)
            
    st.write(f"""
    ### 🌡️ Environmental Conditions
    - Temperature: {weather_data['temp']:.1f}°C
    - Humidity: {weather_data['humidity']}%
    - Air Quality Index: {aqi_data or 'N/A'}
    """)

# Main app
def main():
    st.title("🌍 Smart Climate Control System")
    st.markdown("Optimize your indoor environment based on real-time weather conditions")
    
    # User preferences sidebar
    with st.sidebar:
        st.header("⚙️ Preferences")
        user_prefs = {
            "temp_range": st.slider("Ideal Temperature Range (°C)", 15, 30, (20, 26)),
            "ac_threshold": st.slider("AC Activation Threshold (°C)", 20, 35, 27),
            "aqi_threshold": st.slider("Air Quality Alert Level", 50, 300, 100)
        }
        
        st.header("🏠 Room Status")
        occupancy = st.radio("Occupancy:", ["Occupied", "Vacant"], index=0)
        
        if st.button("🔄 Apply Recommended Settings"):
            user_prefs.update({
                "temp_range": CONFIG["RECOMMENDED_TEMP"],
                "ac_threshold": 27,
                "aqi_threshold": CONFIG["AQI_THRESHOLD"]
            })
            st.success("✅ Best practices applied!")

    # Main interface
    weather_source = st.radio(
        "Select input method:", 
        ["🌐 Real-time Weather Data", "✍️ Manual Input"]
    )

    if weather_source.startswith("🌐"):
        city = st.text_input("City", CONFIG["DEFAULT_CITY"])
        country = st.text_input("Country Code", CONFIG["DEFAULT_COUNTRY"])
        
        if st.button("⛅ Get Weather Data"):
            weather_data = fetch_weather_data(city, country)
            if weather_data:
                aqi_data = fetch_aqi_data(weather_data["lat"], weather_data["lon"])
                actions = determine_climate_actions(
                    weather_data, 
                    aqi_data,
                    user_prefs,
                    occupancy == "Occupied"
                )
                show_results_panel(
                    actions,
                    weather_data,
                    aqi_data,
                    get_weather_image(weather_data["temp"])
                )
    else:
        weather_data = {
            "temp": st.number_input("Temperature (°C)", -20, 50, 22),
            "humidity": st.number_input("Humidity (%)", 0, 100, 50)
        }
        aqi_data = st.number_input("Air Quality Index", 0, 500, 50)
        
        if st.button("💡 Analyze Conditions"):
            actions = determine_climate_actions(
                weather_data, 
                aqi_data,
                user_prefs,
                occupancy == "Occupied"
            )
            show_results_panel(
                actions,
                weather_data,
                aqi_data,
                get_weather_image(weather_data["temp"])
            )

if __name__ == "__main__":
    main()
