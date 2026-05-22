import streamlit as st
import requests
import random


# Bayesian Weather Predictor
class WeatherPredictor:
    def __init__(self, conditional_probs, dynamic_prior):
        self.conditional_probs = conditional_probs
        self.prior_probs = dynamic_prior

    def predict(self, evidence, user_confidence):
        posterior_probs = {}

        if evidence not in self.conditional_probs:
            return self.prior_probs

        evidence_sum = sum(
            self.conditional_probs[evidence].values()
        )

        if evidence_sum == 0:
            return self.prior_probs

        # Bayes update
        for outcome in self.prior_probs:
            likelihood = (
                self.conditional_probs[evidence].get(outcome, 0)
                / evidence_sum
            )

            posterior_probs[outcome] = (
                self.prior_probs[outcome] * likelihood
            )

        total_prob = sum(posterior_probs.values())

        if total_prob == 0:
            return self.prior_probs

        # Normalize
        for outcome in posterior_probs:
            posterior_probs[outcome] /= total_prob

        # User confidence adjustment
        adjusted_probs = {
            "Rain": posterior_probs["Rain"]
            * (1 + user_confidence * 0.3),

            "No Rain": posterior_probs["No Rain"]
            * (1 - user_confidence * 0.3)
        }

        total_adjusted_prob = sum(adjusted_probs.values())

        if total_adjusted_prob == 0:
            return posterior_probs

        # Final normalization
        for outcome in adjusted_probs:
            adjusted_probs[outcome] /= total_adjusted_prob

        return adjusted_probs


# Dynamic Prior Calculation
def calculate_dynamic_prior(cloudiness, humidity, temp):

    cloud_factor = cloudiness / 100.0
    humidity_factor = humidity / 100.0

    base_rain_prior = (
        (cloud_factor * 0.6)
        + (humidity_factor * 0.4)
    )

    rain_prior = max(
        0.05,
        min(0.95, base_rain_prior)
    )

    return {
        "Rain": rain_prior,
        "No Rain": 1.0 - rain_prior
    }


# Fetch Weather Data
def fetch_weather_data(
        city,
        api_key,
        simulate_offline=False
):

    # Offline Simulator
    if simulate_offline:

        mock_conditions = [
            "clear sky",
            "few clouds",
            "scattered clouds",
            "broken clouds",
            "overcast clouds",
            "light rain"
        ]

        chosen_condition = random.choice(mock_conditions)

        return (
            chosen_condition,
            round(random.uniform(12.0, 28.0), 1),
            round(random.uniform(10.0, 26.0), 1),
            random.randint(10, 100),
            round(random.uniform(1.5, 8.5), 1),
            "02d",
            random.randint(40, 95)
        )

    # REAL API ENDPOINT
    url = "https://api.openweathermap.org/data/2.5/weather"

    payload = {
        "q": city.strip(),
        "appid": api_key.strip(),
        "units": "metric"
    }

    try:
        response = requests.get(
            url,
            params=payload,
            timeout=8
        )

        # Error Handling
        if response.status_code != 200:

            try:
                error_json = response.json()

                return error_json.get(
                    "message",
                    "Error fetching weather data"
                ).capitalize()

            except Exception:
                return (
                    f"Server error "
                    f"status code: {response.status_code}"
                )

        data = response.json()

        return (
            data["weather"][0]["description"],
            data["main"]["temp"],
            data["main"]["feels_like"],
            data["clouds"]["all"],
            data["wind"]["speed"],
            data["weather"][0]["icon"],
            data["main"]["humidity"]
        )

    except requests.exceptions.Timeout:
        return "Request timed out."

    except requests.exceptions.ConnectionError:
        return "Connection failed."

    except Exception as e:
        return f"Unexpected error: {str(e)}"


# Streamlit UI
def main():

    st.set_page_config(
        page_title="Sky Sense",
        page_icon="🌤️",
        layout="centered"
    )

    st.title("Sky Sense 🌤️")

    # Sidebar
    st.sidebar.header("🔧 Environment Settings")

    offline_mode = st.sidebar.toggle(
        "Simulate Offline Mode",
        value=False,
        help=(
            "Generate mock weather states "
            "without internet access."
        )
    )

    # User Input
    city = st.text_input(
        "Enter city name:"
    )

    if city:
        api_key = st.secrets["OPENWEATHER_API_KEY"]

        weather_data = fetch_weather_data(
            city,
            api_key,
            simulate_offline=offline_mode
        )

        # Handle Errors
        if isinstance(weather_data, str):
            st.error(weather_data)
            return

        (
            weather_condition,
            temp,
            feels_like,
            cloudiness,
            wind_speed,
            icon_code,
            humidity
        ) = weather_data

        # Weather Icon
        st.image(
            f"https://openweathermap.org/img/wn/{icon_code}@2x.png",
            width=100
        )

        # Weather Info
        st.subheader(
            f"Current weather in {city}"
        )

        st.write(
            f"🌥️ Condition: "
            f"{weather_condition.capitalize()}"
        )

        st.write(
            f"🌡️ Temperature: {temp}°C"
        )

        st.write(
            f"🥵 Feels Like: {feels_like}°C"
        )

        st.write(
            f"💧 Humidity: {humidity}%"
        )

        st.write(
            f"☁️ Cloudiness: {cloudiness}%"
        )

        st.write(
            f"💨 Wind Speed: {wind_speed} m/s"
        )

        # Dynamic Prior
        dynamic_prior = calculate_dynamic_prior(
            cloudiness,
            humidity,
            temp
        )

        # User Confidence
        st.subheader(
            "How confident are you that it will rain today?"
        )

        rain_confidence = st.selectbox(
            "Select confidence level:",
            [
                "Very Unlikely",
                "Unlikely",
                "Neutral",
                "Likely",
                "Very Likely"
            ]
        )

        confidence_map = {
            "Very Unlikely": -0.5,
            "Unlikely": -0.2,
            "Neutral": 0.0,
            "Likely": 0.2,
            "Very Likely": 0.5
        }

        user_confidence = confidence_map[
            rain_confidence
        ]

        # Conditional Probabilities
        conditional_probs = {
            "clear sky": {
                "Rain": 0.05,
                "No Rain": 0.95
            },

            "few clouds": {
                "Rain": 0.15,
                "No Rain": 0.85
            },

            "scattered clouds": {
                "Rain": 0.30,
                "No Rain": 0.70
            },

            "broken clouds": {
                "Rain": 0.50,
                "No Rain": 0.50
            },

            "overcast clouds": {
                "Rain": 0.80,
                "No Rain": 0.20
            },

            "light rain": {
                "Rain": 0.90,
                "No Rain": 0.10
            },

            "moderate rain": {
                "Rain": 0.95,
                "No Rain": 0.05
            }
        }

        predictor = WeatherPredictor(
            conditional_probs,
            dynamic_prior
        )

        # Predict Button
        if st.button("Predict Rain"):

            clean_condition = (
                weather_condition
                .lower()
                .strip()
            )

            posterior_probs = predictor.predict(
                clean_condition,
                user_confidence
            )

            st.subheader(
                "Rain Prediction Engine"
            )

            st.write(
                f"📊 Dynamic Prior Rain Likelihood: "
                f"{dynamic_prior['Rain'] * 100:.1f}%"
            )

            st.write(
                f"🌧️ Final Rain Probability: "
                f"{posterior_probs['Rain'] * 100:.2f}%"
            )

            st.write(
                f"☀️ Final No Rain Probability: "
                f"{posterior_probs['No Rain'] * 100:.2f}%"
            )

            # Final Advice
            if (
                posterior_probs["Rain"]
                >
                posterior_probs["No Rain"]
            ):

                st.success(
                    "🌂 Advice: "
                    "Rain is likely today. "
                    "Carry an umbrella."
                )

            else:

                st.info(
                    "☀️ Advice: "
                    "Rain is unlikely today."
                )

        # Footer
        st.markdown(
            """
            <hr>
            <p style='text-align:center; font-size:12px;'>
            © Developed by Janak Adhikari | 2026
            </p>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()