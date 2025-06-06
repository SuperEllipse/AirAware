"""
input_parser_tool.py

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-06-05

Description:
This module provides a tool to parse and validate input for air quality analysis.
The input includes location names, date ranges, and parameters for analysis.
"""

from typing import Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class AirQualityAnalysisInput(BaseModel):
    """Input schema for the AirQualityAnalysisTool."""
    locations: List[str] = Field(..., description="List of location names for air quality analysis.")
    start_date: str = Field(..., description="Start date for the analysis in YYYY-MM-DD format.")
    end_date: str = Field(..., description="End date for the analysis in YYYY-MM-DD format.")
    aq_parameters: List[str] = Field(..., description="List of air quality parameters to analyze (e.g., pm10, pm25).")


class InputParserTool(BaseTool):
    name: str = "InputParserTool"
    description: str = (
        "Parses LLM-provided input to validate and prepare parameters for air quality analysis. "
        "This includes extracting locations, date ranges, and air quality parameters."
    )
    args_schema: Type[BaseModel] = AirQualityAnalysisInput

    def _run(self, locations: List[str], start_date: str, end_date: str, aq_parameters: List[str]) -> str:
        """
        Process the input data and prepare it for further use in air quality analysis.

        Args:
            locations (List[str]): List of location names for the analysis.
            start_date (str): Start date for the analysis in YYYY-MM-DD format.
            end_date (str): End date for the analysis in YYYY-MM-DD format.
            parameters (List[str]): List of air quality parameters to analyze.

        Returns:
            str: A summary string of the parsed and validated input data.
        """
        # Basic input validation
        if not locations:
            return "Error: At least one location must be specified."
        if not aq_parameters:
            return "Error: At least one air quality parameter must be specified."
        if start_date >= end_date:
            return "Error: The start date must be before the end date."

        # Construct the summary of inputs
        input_summary = {
            "locations": locations,
            "start_date": start_date,
            "end_date": end_date,
            "parameters": aq_parameters,
        }

        return f"Validated Input: {input_summary}"


# Testing Example
if __name__ == "__main__":
    # Example LLM-provided input
    example_input = {
        "locations": ["New York, USA", "Los Angeles, USA"],
        "start_date": "2025-06-01",
        "end_date": "2025-06-03",
        "parameters": ["pm10", "pm25"],
    }

    tool = InputParserTool()
    result = tool.run(**example_input)
    print("\n--- Parsed and Validated Input ---")
    print(result)
