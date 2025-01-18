# smart-hvac-system

Overview

This Smart HVAC System optimizes indoor comfort, energy efficiency, and air quality by using real-time weather data and environmental conditions. It automatically adjusts heating, cooling, humidity levels, and air purification based on outdoor weather and air quality (AQI) data.




Features:

Real-time Weather Data Integration: Fetches live weather conditions using the OpenWeatherMap API.

Automatic Device Control:
Air Conditioner: Automatically turns ON when the outdoor temperature exceeds a user-defined threshold.

Humidifier/Dehumidifier: Activates based on outdoor humidity and season (Winter/Summer).

Air Purifier: Turns ON when the AQI surpasses a defined threshold.

Seasonal Adaptation: Detects the season based on the temperature and adjusts device actions accordingly.

Room Occupancy Simulation: Simulate room occupancy to control devices based on whether the room is occupied or not.

Energy Saving: Devices turn OFF when the room is unoccupied to save energy.





Prerequisites

Python 3.x

Libraries: requests, streamlit, PIL, base64

OpenWeatherMap API Key: Sign up for an API key






Installation

Clone the repository:
git clone https://github.com/hemant6939/smart-hvac-system.git

Navigate to your project folder:
cd smart-hvac-system

Install the required dependencies:
pip install -r requirements.txt






Configuration

Set up OpenWeatherMap API:
Replace "65f75041ea97dba3775e87a53acf8307" in the code with your own OpenWeatherMap API key.

Weather Images:
Make sure to include the following images in your project folder:

cold_weather.png
hot_weather.png
mild_weather.png
energy_saving.png






Usage

Run the Streamlit App:
After installing the dependencies, run the app using:
streamlit run smart_hvac_system.py

Interact with the App:

Real-time Weather Data: Enter your city and country to fetch live weather and AQI data.
Manual Input: Set outdoor temperature, humidity, and AQI manually to simulate different conditions.

Adjust Preferences: Use the sidebar to set your preferred temperature range, AC threshold, and AQI threshold for the air purifier.

Simulate Room Occupancy: Simulate random room occupancy or manually control the status of the room.

Apply Best Settings

Click the "Apply Best Settings" button to automatically apply the recommended settings for temperature, AC threshold, and AQI.



License

This project is open-source and available under the MIT License. See the LICENSE file for more information.


Example of How the App Works

Once deployed, users can see live data on:

Indoor Temperature: Shows if the room needs heating or cooling.

Humidity Level: Provides information about the need for a humidifier or dehumidifier.

Air Quality Index (AQI): Displays whether the air purifier should be ON based on air quality.

Device Status: Real-time ON/OFF status of devices like AC, humidifier, dehumidifier, and air purifier.



Future Improvements

Integrate more IoT devices for home automation.

Implement predictive algorithms for energy-saving optimization.

Add voice control or smart home assistant integration (e.g., Alexa, Google Home).
