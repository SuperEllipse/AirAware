from typing import Optional
import requests
from crewai.tools import BaseTool
from math import cos, radians

class BoundingBoxExtractorTool(BaseTool):
    """Tool to create a bounding box around the centroid of a given location."""

    name: str = "bounding_box_extractor"
    description: str = (
        "Generates a bounding box as [south, west, north, east] around the center "
        "of a given location using Nominatim's lat/lon."
    )
    parameters: Optional[list[dict]] = [
        {
            "name": "location",
            "type": "string",
            "description": "The name of the location to find the bounding box for.",
            "required": True,
        },
        {
            "name": "radius_km",
            "type": "number",
            "description": "Radius in kilometers around the location center.",
            "required": False,
        }
    ]
    return_direct: bool = False

    def _create_bbox_from_point(self, lat, lon, radius_km=10):
        """Create a bounding box around a lat/lon with a radius in km."""
        lat_offset = radius_km / 111  # 1 degree latitude ≈ 111 km
        lon_offset = radius_km / (111 * cos(radians(lat)))

        return [
            lat - lat_offset,  # South
            lon - lon_offset,  # West
            lat + lat_offset,  # North
            lon + lon_offset   # East
        ]

    def _run(self, location: str, radius_km: int = 10) -> list[str] | str:
        """Executes the tool to retrieve the bounding box around a location center."""
        url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
        headers = {"User-Agent": "CrewAI Tool (vishrajagopalan@gmx.com)"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                display_name = data[0]['display_name']

                bbox = self._create_bbox_from_point(lat, lon, radius_km=radius_km)

                print(f"Location: {display_name}")
                print(f"Center: lat={lat}, lon={lon}")
                print(f"Generated Bounding Box (±{radius_km}km): {bbox}")
                return bbox
            else:
                return f"Location not found: {location}"
        except requests.exceptions.RequestException as e:
            return f"Error fetching location {location}: {e}"

# ==============================================================================
# Main function for testing the BoundingBoxExtractorTool
# ==============================================================================
if __name__ == "__main__":
    bbox_tool = BoundingBoxExtractorTool()

    locations_to_test = [
        "Tokyo, Japan",
        "Melbourne, Australia",
        "New York, USA",
        "New Delhi, India"
    ]

    print("--- Starting BoundingBoxExtractorTool Test ---")
    for location in locations_to_test:
        print(f"\n>>> Testing with location: '{location}'")
        try:
            result = bbox_tool._run(location=location, radius_km=15)  # 15 km radius
            print(f"<<< Result for '{location}': {result}")
        except Exception as e:
            print(f"Error for '{location}': {e}")
    print("\n--- Test complete ---")
