import os
from typing import List, Optional
from crewai import LLM, Crew, Agent, Task
from agent_tools.bounding_box_extractor_tool import BoundingBoxExtractorTool
from agent_tools.air_quality_analysis_tool import AirQualityAnalysisTool
from agent_tools.weather_tools import HistoricalWeatherTool # Assuming weather_tools.py contains HistoricalWeatherTool
from agent_tools.utils import get_openai_api_key, get_serper_api_key # Import specific functions you use
MODEL_NAME=os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
# LLM Configuration
llm = LLM(
    model=MODEL_NAME,  # call model by provider/model_name
    temperature=0.7,  # Slightly lower temperature for more focused analysis
    max_tokens=1000,  # Increased max tokens for a more comprehensive report
    top_p=0.9,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    stop=["END"],
    seed=42
)


# Load API Keys (ensure these are set as environment variables or securely managed)
openai_api_key = os.environ.get("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# Initialize Tools
bounding_box_extractor_tool = BoundingBoxExtractorTool()
air_quality_tool = AirQualityAnalysisTool()
weather_tool = HistoricalWeatherTool()



def create_air_quality_analysis_crew(locations: List[str], start_date: str, end_date: str, aq_parameters: Optional[List[str]] = None):
    """Creates and runs the air quality analysis crew."""

    # Agent 1: Bounding Box Retriever
    bounding_box_retriever = Agent(
        role="Geospatial Data Specialist",
        goal="Retrieve bounding box coordinates for the specified locations.",
        backstory="Expert in geographical information retrieval and spatial data analysis.",
        verbose=True,
        allow_delegation=False,
        tools=[bounding_box_extractor_tool],
    )

    # Task 1: Get Bounding Boxes
    get_bounding_boxes_task = Task(
        description=f"For each of the following locations: {locations}, use the 'bounding_box_extractor' tool to find their bounding box coordinates. Return the bounding boxes associated with each location.",
        agent=bounding_box_retriever,
        expected_output="A dictionary or list containing the bounding box coordinates (south, west, north, east) for each specified location.",
    )

    # Agent 2: Weather Data Integrator
    weather_data_integrator = Agent(
        role="Historical Weather Data Specialist",
        goal="Retrieve concise historical weather summaries for the specified locations and dates.",
        backstory="Expert in accessing and summarizing historical meteorological data relevant to environmental analysis.",
        verbose=True,
        allow_delegation=False,
        tools=[weather_tool],
    )

    # Task 2: Get Weather Data
    get_weather_data_task = Task(
        description=f"For each of the following locations: {locations}, use the bounding boxes (south, west, north, east) to query the weather tool to find a concise summary of relevant historical weather conditions between {start_date} and {end_date}. Focus on key weather aspects that might influence air quality (e.g., temperature, wind, precipitation).",
        agent=weather_data_integrator,
        expected_output="A dictionary or list containing concise summaries of historical weather conditions for each specified city.",
        context=[get_bounding_boxes_task], 
    )

    # Agent 3: Air Quality Data Retriever
    air_quality_retriever = Agent(
        role="Air Quality Data Retriever",
        goal="Fetch air quality data from OpenAQ for the specified locations and date range.",
        backstory="Specialized in accessing and retrieving air quality data from the OpenAQ database.",
        verbose=True,
        allow_delegation=False,
        tools=[air_quality_tool],
    )
    
    # Task 3: Get Air Quality Data
    get_air_quality_data_task = Task(
        description=f"Fetch air quality data using the air_quality_tool for the following locations: {locations} from {start_date} to {end_date} using the bounding boxes for each location. If specific parameters are provided ({aq_parameters}), focus on those. Return the data as a pandas DataFrame.",
        agent=air_quality_retriever,
        expected_output="A pandas DataFrame containing the air quality data for the specified locations, dates, and parameters.",
        context=[get_bounding_boxes_task],  # The AirQualityAnalysisTool needs the locations
    )

    # Agent 4: Air Quality Analyst
    air_quality_analyst = Agent(
        role="Air Quality Analyst",
        goal="Analyze the collected air quality data and the corresponding weather information to generate a comprehensive report on the air quality situation.",
        backstory="Experienced environmental scientist specializing in air pollution analysis and its relationship with meteorological conditions.",
        verbose=True,
        allow_delegation=False,
        llm=llm,  # Use the configured LLM
        context=[get_air_quality_data_task] + [get_weather_data_task],
    )

    # Task 4: Analyze and Report
    analysis_task = Task(
        description="Analyze the provided air quality data (including parameters like pm10, value, units, date, and location) for the specified locations and dates. Consider the historical weather information (temperature, wind, precipitation, humidity) for the same period. Identify any trends in air quality, calculate average values where relevant, and discuss any potential correlations or influences of weather conditions on the air quality. Provide a detailed report summarizing the air quality situation for each city, including the key findings and any notable observations related to weather patterns.",
        agent=air_quality_analyst,
        expected_output="A comprehensive report detailing the air quality analysis for each city, including trends, averages, and a discussion of potential relationships with the historical weather conditions.",
    )


    # Instantiate the Crew
    agents = [bounding_box_retriever, weather_data_integrator, air_quality_retriever, air_quality_analyst]
    tasks = [get_bounding_boxes_task, get_weather_data_task, get_air_quality_data_task, analysis_task]


    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
    )

    # Run the crew and get the analysis report
    report = crew.kickoff()
    return report


# For Testing just the workflow
# if __name__ == "__main__":
#     locations = ["New Delhi, India", "Chennai, India"]
#     analysis_start_date = "2024-12-31"
#     analysis_end_date = "2025-01-02"
#     parameters_of_interest = ["pm25, pm10"]  # Optional

#     try:
#         analysis_report = create_air_quality_analysis_crew(
#             locations=locations,
#             start_date=analysis_start_date,
#             end_date=analysis_end_date,
#             aq_parameters=parameters_of_interest
#         )
#         print("\n--- Air Quality Analysis Report ---")
#         print(analysis_report)
#     except ValueError as e:
#         print(f"Error: {e}")
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")