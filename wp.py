import streamlit as st
import requests
from PIL import Image

# This is very dynamic process because it is adapting on the conditionals having a rigid prior experience (initial state of a system) and
# also with the conditionals injected by the user. 
# It then infers and gives the probability

class WeatherPredictor:
    def __init__(self, conditional_probs):
        self.conditional_probs = conditional_probs
        # Internal prior probabilities (fixed, based on general weather patterns)
        self.prior_probs = {"Rain": 0.15, "No Rain": 0.85}

    def predict(self, evidence, user_confidence):
        # Calculate the posterior probabilities using Bayes' theorem
        posterior_probs = {}
        evidence_sum = sum(self.conditional_probs.get(evidence, {}).values())

        if evidence_sum == 0:  # If condition not in the dictionary, assume neutral prediction
            return {"Rain": 0.5, "No Rain": 0.5}

        for outcome in self.prior_probs:
            likelihood = self.conditional_probs.get(evidence, {}).get(outcome, 0) / evidence_sum
            posterior_probs[outcome] = self.prior_probs[outcome] * likelihood

        # Normalize the posterior probabilities
        total_prob = sum(posterior_probs.values())
        for outcome in posterior_probs:
            posterior_probs[outcome] /= total_prob

        # Adjust prediction based on user confidence (this acts as a weight)
        adjusted_probs = {
            "Rain": posterior_probs["Rain"] * (1 + user_confidence * 0.3),  # Apply a subtle weight
            "No Rain": posterior_probs["No Rain"] * (1 - user_confidence * 0.3)
        }

        # Normalize the adjusted posterior probabilities
        total_adjusted_prob = sum(adjusted_probs.values())
        for outcome in adjusted_probs:
            adjusted_probs[outcome] /= total_adjusted_prob

        return adjusted_probs


# Function to fetch weather data using OpenWeatherMap API
def fetch_weather_data(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            weather = data['weather'][0]['description']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            cloudiness = data['clouds']['all']  # Cloud cover in percentage
            wind_speed = data['wind']['speed']  # Wind speed in m/s
            icon_code = data['weather'][0]['icon']  # Icon code for weather condition
            return weather, temp, feels_like, cloudiness, wind_speed, icon_code
        else:
            error_message = data.get('message', 'Error fetching weather data')
            return error_message
    except Exception as e:
        return f"An error occurred: {str(e)}"


# Function to display weather icons
def get_weather_icon(icon_code):
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}.png"
    return icon_url


# Streamlit user interface
def main():
    st.title('Sky Sense 🌤️')

    # Input: City name for dynamic weather data
    city = st.text_input("Enter city name:", "")

    # Only fetch weather data if city is provided
    if city:
        api_key = "0dea85a9d70a0f814fb544d1b910bf33"  # need to be a environment variable / using it for quick deployment
        weather_data = fetch_weather_data(city, api_key)

        if isinstance(weather_data, str):  # In case of error fetching weather data
            st.write(weather_data)
            return

        # Extract weather data
        weather_condition, temp, feels_like, cloudiness, wind_speed, icon_code = weather_data

        # Display weather data
        st.image(get_weather_icon(icon_code), width=100)  # Display weather icon
        st.subheader(f"Current weather in {city}: {weather_condition.capitalize()}")
        st.write(f"🌡️ Temperature: {temp}°C, Feels Like: {feels_like}°C")
        st.write(f"☁️ Cloudiness: {cloudiness}%, 💨 Wind Speed: {wind_speed} m/s")

        # Input for confidence in rain prediction
        st.subheader("How confident are you that it will rain today?")
        rain_confidence = st.selectbox(
            "Select your confidence in rain today:",
            ["Very Unlikely", "Unlikely", "Neutral", "Likely", "Very Likely"]
        )

        # Mapping the confidence to a rough likelihood factor
        confidence_map = {
            "Very Unlikely": 0.05,
            "Unlikely": 0.2,
            "Neutral": 0.5,
            "Likely": 0.8,
            "Very Likely": 1.0
        }

        # Set the user's confidence level
        user_confidence = confidence_map[rain_confidence]

        # Set conditional probabilities for different weather conditions
        conditional_probs = {
            "Clear": {"Rain": 0.05, "No Rain": 0.95},
            "Partly Cloudy": {"Rain": 0.30, "No Rain": 0.70},
            "Cloudy": {"Rain": 0.80, "No Rain": 0.20},
            "Rainy": {"Rain": 0.90, "No Rain": 0.10},
            "Stormy": {"Rain": 0.95, "No Rain": 0.05},
            "few clouds": {"Rain": 0.30, "No Rain": 0.70},  # Added condition for 'few clouds'
        }

        # Initialize Bayesian predictor with internal prior probabilities
        predictor = WeatherPredictor(conditional_probs)

        # Trigger prediction button
        if st.button("Predict Rain"):
            # Make prediction based on the user's inputs
            posterior_probs = predictor.predict(weather_condition, user_confidence)

            # Display the prediction results
            st.subheader("Rain Prediction")
            st.write(f"🌧️ Rain Probability: {posterior_probs['Rain'] * 100:.2f}%")
            st.write(f"🌤️ No Rain Probability: {posterior_probs['No Rain'] * 100:.2f}%")

            # Provide advice based on the prediction
            if posterior_probs["Rain"] > posterior_probs["No Rain"]:
                st.write("🌂 Advice: It is likely to rain today. You might want to carry an umbrella.")
            else:
                st.write(
                    "☀️ Advice: It is not likely to rain today. You can proceed with your plans without worrying about rain.")


    # Footer with copyright notice
    st.markdown("""
        <p style="text-align:center; font-size:12px;">© Developed by Janak Adhikari | 2024</p>
    """, unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
