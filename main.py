#
# Project: Air Aware
# Author: Vish Rajagopala
# Company: Cloudera
# Version: 1.0
#
# General Commentary:
# This script serves as the main entry point for the "Air Aware" project,
# a comprehensive air quality analysis workflow. The purpose of Air Aware
# is to provide accessible and actionable insights into air quality data
# for various locations and timeframes. It achieves this by orchestrating
# an intelligent agent system (referred to as a "crew") responsible for
# fetching raw air quality measurements, processing them, and generating
# analytical reports. The goal is to empower users with a clear understanding
# of air quality trends, potential health implications, and environmental
# factors.
#
# Example Usage (assuming this file is named `main.py`):
#
# To run the analysis for London and Paris, focusing on PM2.5 and Ozone (O3)
# for the first week of May 2024, you would call:
# python main.py --locations "London, UK" "Paris, France" --start_date 2024-05-01 --end_date 2024-05-07 --parameters pm25 o3
#
# To run with default settings (New Delhi & Chennai, PM2.5 as the primary parameter,
# covering the last 2 days up to today's date), simply execute:
# python main.py
#
# For more options and help, use:
# python main.py --help

import argparse
from datetime import datetime, timedelta
from workflows.airquality_analysis  import create_air_quality_analysis_crew

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run an air quality analysis for specified locations and parameters."
    )

    parser.add_argument(
        "-l",
        "--locations",
        nargs="+",  # This allows multiple arguments (e.g., "New Delhi, India" "Chennai, India")
        default=["New Delhi, India", "Chennai, India"],
        help="Space-separated list of locations to analyze (e.g., 'New York, USA' 'London, UK')."
             "Default: 'New Delhi, India', 'Chennai, India'"
    )

    parser.add_argument(
        "-s",
        "--start_date",
        type=str,
        default=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"), # Default to 2 days ago
        help="Analysis start date in YYYY-MM-DD format. Default: 60 days ago."
    )

    parser.add_argument(
        "-e",
        "--end_date",
        type=str,
        # Set default to None initially, we'll calculate it later if not provided by user
        default=None,
        help="Analysis end date in YYYY-MM-DD format. Default: start_date + 3 days."
    )

    parser.add_argument(
        "-p",
        "--parameters",
        nargs="+", # This allows multiple arguments (e.g., "pm25" "o3")
        default=["pm25"], # Default to pm25 if nothing is provided
        help="Space-separated list of air quality parameters to analyze (e.g., 'pm25' 'pm10' 'o3')."
             "Default: 'pm25'."
    )

    args = parser.parse_args()

    # Accessing the parsed arguments
    locations = args.locations
    analysis_start_date = args.start_date
    analysis_end_date = args.end_date
    parameters_of_interest = args.parameters # Already defaults to ["pm25"]
    # --- Logic to determine end_date ---
    if args.end_date:
        # User provided an end_date
        analysis_end_date = args.end_date
    else:
        # Calculate end_date based on (default or user-provided) start_date
        try:
            start_dt_obj = datetime.strptime(analysis_start_date, "%Y-%m-%d")
            end_dt_obj = start_dt_obj + timedelta(days=3)
            analysis_end_date = end_dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            print("Warning: Could not calculate default end_date due to invalid start_date format. Setting end_date to today.")
            analysis_end_date = datetime.now().strftime("%Y-%m-%d")
    # --- End of end_date logic ---

    # Basic validation for dates
    try:
        start_dt = datetime.strptime(analysis_start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(analysis_end_date, "%Y-%m-%d")
        if start_dt > end_dt:
            raise ValueError("Start date cannot be after end date.")
    except ValueError as e:
        print(f"Error: Invalid date format or date range. Please use YYYY-MM-DD. {e}")
        parser.print_help()
        exit(1)


    print(f"Running analysis with:")
    print(f"  Locations: {locations}")
    print(f"  Start Date: {analysis_start_date}")
    print(f"  End Date: {analysis_end_date}")
    print(f"  Parameters: {parameters_of_interest}")


    try:
        analysis_report = create_air_quality_analysis_crew(
            locations=locations,
            start_date=analysis_start_date,
            end_date=analysis_end_date,
            aq_parameters=parameters_of_interest
        )
        print("\n--- Air Quality Analysis Report ---")
        print(analysis_report)
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")