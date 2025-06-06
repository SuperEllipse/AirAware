"""
Air Quality Analysis Tool

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-05-21

Description:
Fetch and aggregate historical air quality data for specified locations and dates
using the OpenAQ API, AWS S3 OpenAQ data archive, and a BoundingBoxExtractorTool
for geographical lookup.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
import requests
import pandas as pd
import gzip
import json
import argparse
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from .utils import get_openaq_api_key

# Constants
URL = "https://api.openaq.org/v3/locations?limit=100&page=1&order_by=id&sort_order=asc"
SOURCE_BUCKET_NAME = "openaq-data-archive"
ANONYMOUS_SESSION = boto3.Session()

class UserParameters(BaseModel):
    api_key: str = Field(description="API key for OpenAQ access")


class ToolParameters(BaseModel):
    bounding_boxes: List[List[float]] = Field(description="List of bounding boxes as [south, north, west, east]")
    locations: List[str] = Field(description="List of location names corresponding to bounding boxes")
    start_date: str = Field(description="Start date for the analysis in YYYY-MM-DD format")
    end_date: str = Field(description="End date for the analysis in YYYY-MM-DD format")
    aq_parameters: Optional[List[str]] = Field(
        default=None,
        description="Optional list of air quality parameters to filter (e.g., ['pm25', 'o3'])",
    )

def run_tool(config: UserParameters, args: ToolParameters) -> Any:
    def get_location_ids(bbox: List[float]) -> List[dict]:
        params = {"bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"}
        headers = {"X-API-Key": config.api_key}
        response = requests.get(URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("results", [])

    def fetch_sensor_data(location_ids: List[int], start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        consolidated_df = pd.DataFrame()
        s3_client = ANONYMOUS_SESSION.client("s3", region_name="us-east-1", config=Config(signature_version=UNSIGNED))

        for location_id in location_ids:
            for date in pd.date_range(start=start_date, end=end_date):
                year, month, day = date.strftime("%Y"), date.strftime("%m"), date.strftime("%d")
                prefix = f"records/csv.gz/locationid={location_id}/year={year}/month={month}/"
                try:
                    response = s3_client.list_objects_v2(Bucket=SOURCE_BUCKET_NAME, Prefix=prefix)
                    if "Contents" in response:
                        for obj in response["Contents"]:
                            key = obj["Key"]
                            if key.endswith(f"{year}{month}{day}.csv.gz"):
                                obj_data = s3_client.get_object(Bucket=SOURCE_BUCKET_NAME, Key=key)
                                with gzip.GzipFile(fileobj=obj_data["Body"]) as gz_file:
                                    daily_df = pd.read_csv(gz_file)
                                    consolidated_df = pd.concat([consolidated_df, daily_df], ignore_index=True)
                except Exception as e:
                    print(f"Error fetching data for location ID {location_id}: {e}")

        return consolidated_df

    def aggregate_data(df: pd.DataFrame, parameters: Optional[List[str]]) -> pd.DataFrame:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime")

        if parameters:
            df = df[df["parameter"].isin(parameters)]

        daily_data = (
            df.reset_index()
            .groupby(["parameter", pd.Grouper(key="datetime", freq="D")])
            .agg(value=("value", "mean"), units=("units", "first"))
            .dropna()
            .reset_index()
        )

        daily_data["date"] = daily_data["datetime"].dt.date
        del daily_data["datetime"]
        return daily_data

    all_data = []
    for bbox, location in zip(args.bounding_boxes, args.locations):
        bbox_openaq_format = [bbox[1], bbox[0], bbox[3], bbox[2]]
        location_data = get_location_ids(bbox_openaq_format)
        location_ids = [loc["id"] for loc in location_data]

        consolidated_df = fetch_sensor_data(location_ids, args.start_date, args.end_date)
        if not consolidated_df.empty:
            aggregated_daily_data = aggregate_data(consolidated_df, args.aq_parameters)
            aggregated_daily_data["location"] = location
            all_data.append(aggregated_daily_data)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame(columns=["date", "parameter", "unit", "value", "location"])

OUTPUT_KEY = "tool_output"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-params", required=True, help="User configuration in JSON format")
    parser.add_argument("--tool-params", required=True, help="Tool arguments in JSON format")
    args = parser.parse_args()

    user_dict = json.loads(args.user_params)
    tool_dict = json.loads(args.tool_params)

    config = UserParameters(**user_dict)
    params = ToolParameters(**tool_dict)

    output = run_tool(config, params)
    print(OUTPUT_KEY, output)
