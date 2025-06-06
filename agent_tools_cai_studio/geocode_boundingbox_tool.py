"""
Bounding Box Extractor Tool

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
This tool retrieves geographical bounding box coordinates (south, north, west, east)
for a given location name by querying the Nominatim OpenStreetMap API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
import json
import argparse
import requests
from math import cos, radians


class UserParameters(BaseModel):
    """
    Parameters used to configure the tool. This may include API keys, user agents, etc.
    """
    pass


class ToolParameters(BaseModel):
    """
    Arguments of the tool call. These arguments are passed to this tool whenever
    an Agent calls this tool.
    """
    location: str = Field(description="The name of the location to find the bounding box for.")


class BoundingBoxExtractor:
    @staticmethod
    def expand_bounding_box(south_lat, west_lon, north_lat, east_lon, km_expansion=50):
        """Expand the bounding box by a fixed distance (in kilometers)."""
        lat_offset = km_expansion / 111  # 1 degree latitude ≈ 111 km
        lon_offset = km_expansion / (111 * cos(radians((south_lat + north_lat) / 2)))  # Adjust longitude by latitude

        return [
            south_lat - lat_offset,  # South
            west_lon - lon_offset,  # West
            north_lat + lat_offset,  # North
            east_lon + lon_offset   # East
        ]

    @staticmethod
    def run_tool(config: UserParameters, args: ToolParameters) -> Any:
        """Main tool code logic."""
        url = f"https://nominatim.openstreetmap.org/search?q={args.location}&format=json&addressdetails=1"
        headers = {"User-Agent": "AirAware Data For Good (vishrajagopalan@gmx.com) "}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data:
                bbox = data[0]['boundingbox']
                south_lat = float(bbox[0])
                north_lat = float(bbox[1])
                west_lon = float(bbox[2])
                east_lon = float(bbox[3])

                expanded_bbox = BoundingBoxExtractor.expand_bounding_box(south_lat, west_lon, north_lat, east_lon, km_expansion=15)
                return {"expanded_bounding_box": expanded_bbox}
            else:
                return {"error": f"Bounding box not found for location: {args.location}"}

        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching bounding box for {args.location}: {e}"}


OUTPUT_KEY = "tool_output"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-params", required=True, help="Tool configuration")
    parser.add_argument("--tool-params", required=True, help="Tool arguments")
    args = parser.parse_args()

    # Parse JSON into dictionaries
    user_dict = json.loads(args.user_params)
    tool_dict = json.loads(args.tool_params)

    # Validate dictionaries against Pydantic models
    config = UserParameters(**user_dict)
    params = ToolParameters(**tool_dict)

    # Run the tool
    output = BoundingBoxExtractor.run_tool(config, params)
    print(OUTPUT_KEY, output)
