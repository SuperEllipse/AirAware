"""
weather_tools.py

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
This module provides tools for retrieving historical weather data.
It includes a Pydantic model for weather tool input and a tool to
fetch daily historical weather information from Open-Meteo.com based
on a bounding box and date range.
"""

from typing import Type
import requests
from pydantic import BaseModel, Field
from crewai.tools import BaseTool 
from typing import List, Optional



class OpenMeteoWeatherInput(BaseModel):
    """Input for the OpenMeteoHistoricalWeatherTool using a bounding box."""
    # Bounding box format: [south_latitude, west_longitude, north_latitude, east_longitude]
    bounding_box: List[float] = Field(..., description="Bounding box coordinates in [south_lat, west_lon, north_lat, east_lon] format.")
    start_date: str = Field(..., description="The start date for historical weather data in YYYY-MM-DD format.")
    end_date: str = Field(..., description="The end date for historical weather data in YYYY-MM-DD format.")

# A bounding box, or bbox, is a rectangular area defined by four coordinates: 
# two representing the southwest corner (minimum longitude, minimum latitude) and 
# two representing the northeast corner (maximum longitude, maximum latitude). 
# It's essentially a way to define a geographical area on a map or within a dataset. 

class HistoricalWeatherTool(BaseTool):
    name: str = "HistoricalWeatherTool"
    description: str = (
        "Retrieves DAILY historical weather data (mean temperature, max temperature, min temperature, "
        "sum of precipitation, mean wind speed, mean relative humidity) for a location "
        "defined by a bounding box and a date range from Open-Meteo.com (no API key required for non-commercial use). "
        "The tool internally calculates the center point of the bounding box for the API query."
    )
    args_schema: Type[BaseModel] = OpenMeteoWeatherInput

    def _run(self, bounding_box: List[float], start_date: str, end_date: str) -> str:
        if len(bounding_box) != 4:
            return "Error: Bounding box must contain exactly 4 float values: [south_lat, west_lon, north_lat, east_lon]."

        # bounding_box is in [south_lat, west_lon, north_lat, east_lon]
        south_lat, west_lon, north_lat, east_lon = bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]
        
        # Calculate the center point of the bounding box
        center_latitude = (south_lat + north_lat) / 2
        center_longitude = (west_lon + east_lon) / 2

        base_url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": center_latitude,
            "longitude": center_longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_mean,relative_humidity_2m_mean",
            "timezone": "auto" # It's good practice to specify timezone for daily data
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            if "daily" not in data:
                return f"No daily weather data found for the bounding box {bounding_box} between {start_date} and {end_date}. API response: {data}"

            daily_data = data["daily"]
            times = daily_data.get("time", [])
            temp_means = daily_data.get("temperature_2m_mean", [])
            temp_maxs = daily_data.get("temperature_2m_max", [])
            temp_mins = daily_data.get("temperature_2m_min", [])
            precipitations = daily_data.get("precipitation_sum", [])
            wind_speeds_mean = daily_data.get("wind_speed_10m_mean", [])
            humidities_mean = daily_data.get("relative_humidity_2m_mean", [])

            weather_summary = []
            for i in range(len(times)):
                summary = {
                    "date": times[i],
                    "temperature_mean_2m": temp_means[i] if i < len(temp_means) else "N/A",
                    "temperature_max_2m": temp_maxs[i] if i < len(temp_maxs) else "N/A",
                    "temperature_min_2m": temp_mins[i] if i < len(temp_mins) else "N/A",
                    "precipitation_sum": precipitations[i] if i < len(precipitations) else "N/A",
                    "wind_speed_10m_mean": wind_speeds_mean[i] if i < len(wind_speeds_mean) else "N/A",
                    "relative_humidity_2m_mean": humidities_mean[i] if i < len(humidities_mean) else "N/A"
                }
                weather_summary.append(summary)

            return str(weather_summary) # Return as string for LLM processing
        except requests.exceptions.RequestException as e:
            return f"Error fetching weather data from Open-Meteo for bounding box {bounding_box}: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"
        
# Only for Testing
# def main(location: str, start_date: str, end_date: str):
#     """
#     Main function to get the bounding box for a location and then fetch historical weather details.

#     Args:
#         location (str): The name of the location.
#         start_date (str): The start date for weather data in YYYY-MM-DD format.
#         end_date (str): The end date for weather data in YYYY-MM-DD format.
#     """
#     bbox_extractor = BoundingBoxExtractorTool()
#     weather_tool = HistoricalWeatherTool()

#     print(f"Getting bounding box for {location}...")
#     bounding_box = bbox_extractor.run(location=location)

#     if isinstance(bounding_box, str):
#         print(f"Error: {bounding_box}")
#         return

#     print(f"Bounding box for {location}: {bounding_box}")
#     print(f"Fetching weather details for {location} from {start_date} to {end_date}...")
#     weather_details = weather_tool.run(bounding_box=bounding_box, start_date=start_date, end_date=end_date)
    
#     print("\nWeather Details:")
#     print(weather_details)

# if __name__ == "__main__":
#     # Example usage:
#     location_name = "Chennai"
#     start = "2023-01-01"
#     end = "2023-01-03"
#     main(location_name, start, end)

#     print("\n" + "="*50 + "\n")

#     location_name_2 = "London"
#     start_2 = "2024-05-15"
#     end_2 = "2024-05-17"
#     main(location_name_2, start_2, end_2)