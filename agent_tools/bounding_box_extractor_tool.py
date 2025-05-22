"""
bounding_box_extractor_tool.py

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
This module defines the BoundingBoxExtractorTool, a specialized tool designed
to retrieve geographical bounding box coordinates (south, north, west, east)
for a given location name by querying the Nominatim OpenStreetMap API.
"""

from typing import Optional
import requests
from crewai.tools import BaseTool # Assuming BaseTool comes from crewai_tools or a similar library
from typing import List, Optional
from math import cos, radians
class BoundingBoxExtractorTool(BaseTool):
    """Tool to extract the bounding box coordinates (south, north, west, east) for a given location name using Nominatim."""

    name: str = "bounding_box_extractor"
    description: str = "Extracts the bounding box coordinates (south, north, west, east) for a given location name."
    parameters: Optional[list[dict]] = [
        {
            "name": "location",
            "type": "string",
            "description": "The name of the location to find the bounding box for.",
            "required": True,
        }
    ]
    return_direct: bool = False

    def _expand_bounding_box(self, south_lat, west_lon, north_lat, east_lon, km_expansion=50):
        """Expand the bounding box by a fixed distance (in kilometers)."""
        # Approximate degrees of latitude and longitude for the given expansion
        lat_offset = km_expansion / 111  # 1 degree latitude ≈ 111 km
        lon_offset = km_expansion / (111 * cos(radians((south_lat + north_lat) / 2)))  # Adjust longitude by latitude

        # Expand bounding box
        return [
            south_lat - lat_offset,  # South
            west_lon - lon_offset,  # West
            north_lat + lat_offset,  # North
            east_lon + lon_offset   # East
        ]
        
    def _run(self, location: str) -> list[str] | str:
        """Executes the tool to retrieve the bounding box."""
        url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&addressdetails=1"
        headers = {"User-Agent": "CrewAI Tool (vishrajagopalan@gmx.com)"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            print(data)
            if data:
                bbox = data[0]['boundingbox']
                print(f"Location: {location} ####### Bounding Box: {bbox}")
                south_lat = float(bbox[0])
                north_lat = float(bbox[1])
                west_lon = float(bbox[2])
                east_lon = float(bbox[3])

                # Expand the bounding box
                expanded_bbox = self._expand_bounding_box(south_lat, west_lon, north_lat, east_lon, km_expansion=15)
                print(f"Expanded Bounding Box: {expanded_bbox}")
                return expanded_bbox            
            else:
                return f"Bounding box not found for location: {location}"
        except requests.exceptions.RequestException as e:
            return f"Error fetching bounding box for {location}: {e}"

