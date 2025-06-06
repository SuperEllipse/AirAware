"""
input_parser_tool.py

Author: Vish Rajagopalan
Company: Cloudera
Date: 2025-06-05

Description:
This module provides a tool to parse and validate input for air quality analysis.
The input includes location names, date ranges, and parameters for analysis.
"""

import json
import argparse
from pydantic import BaseModel, Field
from typing import List, Optional, Any


class UserParameters(BaseModel):
    """
    Parameters used to configure a tool. This may include API keys,
    database connections, environment variables, etc.
    """
    pass  # This tool does not require user-specific parameters.


class ToolParameters(BaseModel):
    """
    Arguments of a tool call. These arguments are passed to this tool whenever
    an Agent calls this tool. The descriptions below are also provided to agents
    to help them make informed decisions of what to pass to the tool.
    """
    locations: List[str] = Field(..., description="List of location names for air quality analysis.")
    start_date: str = Field(..., description="Start date for the analysis in YYYY-MM-DD format.")
    end_date: str = Field(..., description="End date for the analysis in YYYY-MM-DD format.")
    aq_parameters: List[str] = Field(..., description="List of air quality parameters to analyze (e.g., pm10, pm25).")


def run_tool(config: UserParameters, args: ToolParameters) -> Any:
    """
    Main tool code logic. Anything returned from this method is returned
    from the tool back to the calling agent.
    """
    # Basic input validation
    if not args.locations:
        return {"error": "At least one location must be specified."}
    if not args.aq_parameters:
        return {"error": "At least one air quality parameter must be specified."}
    if args.start_date >= args.end_date:
        return {"error": "The start date must be before the end date."}

    # Construct the summary of inputs
    input_summary = {
        "locations": args.locations,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "parameters": args.aq_parameters,
    }

    return {"validated_input": input_summary}


OUTPUT_KEY = "tool_output"
"""
When an agent calls a tool, technically the tool's entire stdout can be passed back to the agent.
However, if an OUTPUT_KEY is present in a tool's main file, only stdout content *after* this key is
passed to the agent. This allows us to return structured output to the agent while still retaining
the entire stdout stream from a tool! By default, this feature is enabled, and anything returned
from the run_tool() method above will be the structured output of the tool.
"""


if __name__ == "__main__":
    """
    Tool entrypoint. 
    
    The only two things that are required in a tool are the
    ToolConfiguration and ToolArguments classes. Then, the only two arguments that are
    passed to a tool entrypoint are "--tool-config" and "--tool-args", respectively. The rest
    of the implementation is up to the tool builder - feel free to customize the entrypoint to your 
    choosing!
    """
    
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
    
    # Run the tool.
    output = run_tool(config, params)
    print(OUTPUT_KEY, output)
