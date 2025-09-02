"""
Bounding Box Extractor Tool

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
This tool retrieves geographical bounding box coordinates (south, north, west, east)
for a given location name by querying the Nominatim OpenStreetMap API.
"""
"""
Bounding Box Extractor Tool

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
This tool retrieves a custom geographical bounding box around the city center
for a given location name using Nominatim to get the center coordinates.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
import json
import argparse
import requests
from math import cos, radians


class UserParameters(BaseModel):
    """Parameters used to configure the tool. This may include API keys, user agents, etc."""
    pass


class ToolParameters(BaseModel):
    """Arguments passed to the tool by an Agent."""
    location: str = Field(description="The name of the location to find the bounding box for.")
    radius_km: Optional[float] = Field(default=15, description="Radius in km around city center for bounding box.")


class BoundingBoxExtractor:
    @staticmethod
    def create_bbox_from_center(lat, lon, radius_km=15):
        """Create a bounding box around a lat/lon with a given radius in km."""
        lat_offset = radius_km / 111  # 1 degree latitude ≈ 111 km
        lon_offset = radius_km / (111 * cos(radians(lat)))  # Adjust longitude by latitude

        return [
            lat - lat_offset,  # South
            lon - lon_offset,  # West
            lat + lat_offset,  # North
            lon + lon_offset   # East
        ]

    @staticmethod
    def run_tool(config: UserParameters, args: ToolParameters) -> Any:
        """Generate bounding box around city center."""
        url = f"https://nominatim.openstreetmap.org/search?q={args.location}&format=json&limit=1"
        headers = {"User-Agent": "AirAware Data For Good (vishrajagopalan@gmx.com)"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                display_name = data[0]['display_name']

                bbox = BoundingBoxExtractor.create_bbox_from_center(lat, lon, radius_km=args.radius_km)
                return {
                    "location": display_name,
                    "center": {"lat": lat, "lon": lon},
                    "radius_km": args.radius_km,
                    "bounding_box": bbox
                }
            else:
                return {"error": f"Location not found: {args.location}"}

        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching location {args.location}: {e}"}


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
