"""
weather_tools.py

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
This tool retrieves DAILY historical weather data (mean temperature, max temperature, min temperature,
sum of precipitation, mean wind speed, mean relative humidity) for a location defined by a bounding box
and a date range from Open-Meteo.com. It internally calculates the center point of the bounding box for
the API query. No API key is required for non-commercial use.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
import json
import requests
import argparse


class UserParameters(BaseModel):
    """
    Parameters used to configure the tool. User-specific configuration
    such as API keys or environment settings can be defined here.
    """
    pass  # This tool does not require user-specific parameters.


class ToolParameters(BaseModel):
    """
    Arguments of a tool call. These arguments are passed to the tool whenever
    an Agent calls this tool. The descriptions below are provided to agents
    to help them make informed decisions about what to pass to the tool.
    """
    bounding_box: List[float] = Field(
        ..., description="Bounding box coordinates in [south_lat, west_lon, north_lat, east_lon] format."
    )
    start_date: str = Field(
        ..., description="The start date for historical weather data in YYYY-MM-DD format."
    )
    end_date: str = Field(
        ..., description="The end date for historical weather data in YYYY-MM-DD format."
    )


def run_tool(config: UserParameters, args: ToolParameters) -> Any:
    """
    Main tool code logic. Retrieves historical weather data from Open-Meteo.com
    for the specified bounding box and date range.
    """
    if len(args.bounding_box) != 4:
        return {"error": "Bounding box must contain exactly 4 float values: [south_lat, west_lon, north_lat, east_lon]."}

    # Calculate the center point of the bounding box
    south_lat, west_lon, north_lat, east_lon = args.bounding_box
    center_latitude = (south_lat + north_lat) / 2
    center_longitude = (west_lon + east_lon) / 2

    base_url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": center_latitude,
        "longitude": center_longitude,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_mean,relative_humidity_2m_mean",
        "timezone": "auto",
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if "daily" not in data:
            return {"error": f"No daily weather data found for the given parameters. Response: {data}"}

        # Extract weather data
        daily_data = data["daily"]
        weather_summary = []
        for i in range(len(daily_data.get("time", []))):
            summary = {
                "date": daily_data["time"][i],
                "temperature_mean_2m": daily_data.get("temperature_2m_mean", ["N/A"])[i],
                "temperature_max_2m": daily_data.get("temperature_2m_max", ["N/A"])[i],
                "temperature_min_2m": daily_data.get("temperature_2m_min", ["N/A"])[i],
                "precipitation_sum": daily_data.get("precipitation_sum", ["N/A"])[i],
                "wind_speed_10m_mean": daily_data.get("wind_speed_10m_mean", ["N/A"])[i],
                "relative_humidity_2m_mean": daily_data.get("relative_humidity_2m_mean", ["N/A"])[i],
            }
            weather_summary.append(summary)

        return weather_summary
    except requests.exceptions.RequestException as e:
        return {"error": f"HTTP error occurred: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}


OUTPUT_KEY = "tool_output"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-params", required=True, help="Tool configuration as JSON string")
    parser.add_argument("--tool-params", required=True, help="Tool arguments as JSON string")
    args = parser.parse_args()

    user_dict = json.loads(args.user_params)
    tool_dict = json.loads(args.tool_params)

    config = UserParameters(**user_dict)
    params = ToolParameters(**tool_dict)

    output = run_tool(config, params)
    print(OUTPUT_KEY, json.dumps(output))
