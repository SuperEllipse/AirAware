"""
air_quality_analysis_tool.py

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
This module defines the AirQualityAnalysisTool, which is designed to fetch
and aggregate historical air quality data for specified locations and dates
using a combination of OpenAQ API, AWS S3 OpenAQ data archive, and an
internal BoundingBoxExtractorTool for geographical lookup.
"""

from typing import Optional, List, Type
from datetime import datetime, date
import requests
import pandas as pd
import gzip
import os

from crewai.tools import BaseTool
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from .bounding_box_extractor_tool import BoundingBoxExtractorTool # Relative import if in same package
# Import the get_openaq_api_key function from your utils file
from .utils import get_openaq_api_key
from typing import List, Optional
anonymous_session = boto3.Session()  # For public bucket

class AirQualityAnalysisTool(BaseTool):
    name: str = "air_quality_analysis"
    description: str = "Fetch air quality data for specified locations and dates, returning aggregated results."
    parameters: Optional[List[dict]] = [
        {
            "name": "bounding_boxes",
            "type": "list[list[float]]",
            "description": (
                "List of bounding boxes (each as [south, north, west, east]) to analyze air quality for."
            ),
            "required": True,
        },      
        {
            "name": "locations",
            "type": "list[str]",
            "description": "List of location names to analyze air quality for.",
            "required": True,
        },          
        {
            "name": "start_date",
            "type": "str",
            "description": "Start date for the analysis in YYYY-MM-DD format.",
            "required": True,
        },
        {
            "name": "end_date",
            "type": "str",
            "description": "End date for the analysis in YYYY-MM-DD format.",
            "required": True,
        },
        {
            "name": "aq_parameters",
            "type": "Optional[list[str]]",
            "description": "Optional list of air quality parameters to filter (e.g., ['pm25', 'o3']). If None, all available parameters are used.",
            "required": False,
        },
    ]
    def _run(self, bounding_boxes: List[List[float]], locations: List[str], start_date: str, end_date: str, aq_parameters: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Args:
            bounding_boxes (list): List of bounding boxes as [south, north, west, east].
            locations (list): List of location names corresponding to bounding boxes.            
            start_date (str): Start date for the analysis in YYYY-MM-DD format.
            end_date (str): End date for the analysis in YYYY-MM-DD format.
            aq_parameters (list, optional): List of air quality parameters to filter. Defaults to None.

        Returns:
            pd.DataFrame: Aggregated air quality data with columns [date, parameter, unit, value, location_name].
        """
        

        # Convert start_date and end_date strings to datetime objects
        try:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        # Step 2: Fetch location IDs from OpenAQ
        def get_location_ids(bbox: List[str]) -> List[dict]:
            url = "https://api.openaq.org/v3/locations?limit=100&page=1&order_by=id&sort_order=asc"
            params = {
                "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            }
            headers = {"X-API-Key": get_openaq_api_key()}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("results", [])

        # Step 3: Fetch data from OpenAQ AWS bucket using boto3
        def fetch_sensor_data(location_ids: List[int], start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame: # Updated type hints
            consolidated_df = pd.DataFrame()
            failed_locations = []  # To track locations that fail to return data

            s3_client = anonymous_session.client('s3', region_name="us-east-1", config=Config(signature_version=UNSIGNED))
            source_bucket_name = "openaq-data-archive"

            for location_id in location_ids:
                for date in pd.date_range(start=start_date, end=end_date):
                    year, month, day = date.strftime("%Y"), date.strftime("%m"), date.strftime("%d")
                    prefix = f"records/csv.gz/locationid={location_id}/year={year}/month={month}/"
                    try:
                        response = s3_client.list_objects_v2(Bucket=source_bucket_name, Prefix=prefix)
                        if 'Contents' in response:
                            for obj in response['Contents']:
                                key = obj['Key']
                                if key.endswith(f"{year}{month}{day}.csv.gz"):
                                    print(f"Downloading: {key}")
                                    obj_data = s3_client.get_object(Bucket=source_bucket_name, Key=key)
                                    with gzip.GzipFile(fileobj=obj_data['Body']) as gz_file:
                                        daily_df = pd.read_csv(gz_file)
                                        consolidated_df = pd.concat([consolidated_df, daily_df], ignore_index=True)
                        else:
                            failed_locations.append(location_id)

                    except Exception as e:
                        print(f"Error fetching data for location ID {location_id}: {e}")
                        failed_locations.append(location_id)
            print("Sample Sensor Data from OPENAQ : \n", consolidated_df.head())
            if failed_locations:
                print(f"Locations with no data or errors: {failed_locations}")

            return consolidated_df

        # Step 4: Aggregate data
        def aggregate_data(df: pd.DataFrame, parameters: Optional[List[str]] = None) -> pd.DataFrame:
            df['datetime'] = pd.to_datetime(df['datetime'])  # Ensure datetime is parsed correctly
            df = df.set_index('datetime')  # Set 'datetime' as the index

            if parameters:
                df = df[df['parameter'].isin(parameters)]  
            try : 
                # Reset the index to avoid conflicts with 'parameter'
                df = df.reset_index()     
                print("DF :\n ", df.head())           
                daily_data = (
                    df.groupby(['parameter', pd.Grouper(key='datetime', freq='D')])
                    .agg(
                        value=('value', 'mean'),
                        units=('units', 'first')
                    )
                    .dropna()
                    .reset_index()
                )  
            except Exception as e : 
                print("Aggregation failed with Exception: ", e)
            daily_data['date'] = daily_data['datetime'].dt.date
            del daily_data['datetime']
            return daily_data

        # Main Workflow
        all_data = []
        for bbox, location in zip(bounding_boxes, locations):
            try:
                bbox_openaq_format  = [bbox[1], bbox[0], bbox[3], bbox[2]]         
                location_data = get_location_ids(bbox_openaq_format)
                location_ids = [loc['id'] for loc in location_data]
                # Open AQ accepts bounding box in the format west, south, east, north

                print(f"Found {len(location_ids)} locations for bounding box (per openAQ format) {bbox_openaq_format} (Location: {location}). Downloading data...")

                consolidated_df = fetch_sensor_data(location_ids, start_date_dt, end_date_dt)
                if not consolidated_df.empty:               
                    aggregated_daily_data = aggregate_data(consolidated_df, aq_parameters)
                    aggregated_daily_data["location"] = location  # Add the location column
                    all_data.append(aggregated_daily_data)

            except Exception as e:
                print(f"Error processing bounding box {bbox} for location {location}: {e}")

        # Combine all data
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            return result
        else:
            return pd.DataFrame(columns=["date", "parameter", "unit", "value", "location"])
        

tool = BoundingBoxExtractorTool()

if __name__ == '__main__':
    # Example usage:
    analysis_tool = AirQualityAnalysisTool()
    locations_to_analyze = [ "New Delhi, India"]
    parameters_to_analyze=["pm25"]
    bboxes=[]
    for location in locations_to_analyze : 
        bbox = tool.run(location=location)
        print(  "Bounding box : ", bbox)
        bboxes.append(bbox)


    start = "2023-01-01"
    end = "2023-01-03"
    parameters_to_analyze = ["pm25"]
    print(bboxes)
    try:
        
        results_df = analysis_tool.run(bounding_boxes = bboxes,locations=locations_to_analyze, start_date=start, end_date=end, aq_parameters=parameters_to_analyze)
        print("\nAggregated Air Quality Data:")
        print(results_df)
    except Exception as e:
        print(f"An error occurred during analysis: {e}")

