import os
from crewai import LLM, Crew, Agent, Task
from agent_tools.bounding_box_extractor_tool import BoundingBoxExtractorTool
from agent_tools.air_quality_analysis_tool import AirQualityAnalysisTool
from agent_tools.weather_tools import HistoricalWeatherTool
from agent_tools.input_parser_tool_v2 import InputParserTool  #Version 2 - Author addition

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")


class AirQualityAnalysisCrew:
    """Class-based implementation of the air quality analysis workflow."""

    def __init__(self, user_input: str):
        self.user_input = user_input
        self.llm = self._configure_llm()
        self.tools = self._initialize_tools()
        self.agents = {}
        self.tasks = {}
        self.crew = None

        self._setup_agents()
        self._setup_tasks()
        self._initialize_crew()

    @staticmethod
    def _configure_llm() -> LLM:
        """Configure and return the LLM."""
        return LLM(
            model=MODEL_NAME,
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            stop=["END"],
            seed=42,
        )

    @staticmethod
    def _initialize_tools():
        """Initialize and return tools."""
        return {
            "input_parser_tool": InputParserTool(),
            "bounding_box_extractor_tool": BoundingBoxExtractorTool(),
            "air_quality_tool": AirQualityAnalysisTool(),
            "weather_tool": HistoricalWeatherTool(),
        }

# Note LAB WORK Begins here: Enter the details from the Lab Guide
    def _setup_agents(self):
        """Set up all agents."""
        # Step 1: Define agents individually
        input_parser_agent = Agent(
            role="Input Data Parser", #Lab Work : Enter Details here from LAB Guide
            goal="Efficient assistant for extracting structured information from user queries.", #Lab Work : Enter Details here from LAB Guide
            backstory="Parse user-provided natural language input into structured parameters required for air quality analysis.", #Lab Work : Enter Details here
            verbose=True,
            allow_delegation=False,
            tools=[self.tools["input_parser_tool"]], #Lab Work : Enter Details here
        )
        bounding_box_retriever = Agent(
            role="Geospatial Data Specialist", #Lab Work : Enter Details here from LAB Guide
            goal="Expert in geographical information retrieval and spatial data analysis.", #Lab Work : Enter Details here from LAB Guide
            backstory="Retrieve bounding box coordinates for the specified locations.", #Lab Work : Enter Details here from LAB Guide
            verbose=True,
            allow_delegation=False,
            tools=[self.tools["bounding_box_extractor_tool"]], #Lab Work : Enter Details here from LAB Guide
        )
        weather_data_integrator = Agent(
            role="Historical Weather Data Specialist",
            goal="Retrieve concise historical weather summaries for the specified locations and dates.",
            backstory="Expert in historical meteorological data analysis.",
            verbose=True,
            allow_delegation=False,
            tools=[self.tools["weather_tool"]],
        )
        air_quality_retriever = Agent(
            role="Air Quality Data Retriever",
            goal="Fetch air quality data from OpenAQ for the specified locations and date range.",
            backstory="Specialized in accessing and retrieving air quality data.",
            verbose=True,
            allow_delegation=False,
            tools=[
                self.tools["bounding_box_extractor_tool"],
                self.tools["air_quality_tool"]
    ],
        )
        air_quality_analyst = Agent(
            role="Air Quality Analyst",
            goal="Analyze air quality data and historical weather data to generate a report.",
            backstory="Experienced in air quality analysis and meteorological research.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Step 2: Add agents to self.agents
        self.agents = {
            "input_parser_agent": input_parser_agent,
            "bounding_box_retriever": bounding_box_retriever,
            "weather_data_integrator": weather_data_integrator,
            "air_quality_retriever": air_quality_retriever,
            "air_quality_analyst": air_quality_analyst,
        }

    def _setup_tasks(self):
        """Set up all tasks."""
        # Step 1: Define tasks individually
        parse_user_input_task = Task(
            description=f"Parse the user input: {self.user_input}. Extract locations, start date, end date, and air quality parameters using the InputParserTool.", #Lab Work : Enter Details here from LAB Guide,
            agent=self.agents["input_parser_agent"], #Lab Work : Enter Details here from LAB Guide,
            expected_output=(
                "A dictionary containing parsed 'locations', 'start_date', 'end_date','aq_parameters', and author from the user input." #version 2 #Lab Work : Enter Details here from LAB Guide,
            ),
        )
        get_bounding_boxes_task = Task(
            description="For each of the following locations, use the 'bounding_box_extractor' tool to find their bounding box coordinates. Return the bounding boxes associated with each location.",#Lab Work : Enter Details here from LAB Guide,
            agent=self.agents["bounding_box_retriever"], #Lab Work : Enter Details here from LAB Guide,
            expected_output="A list containing the bounding box coordinates (south, west, north, east) for each specified location.", #Lab Work : Enter Details here from LAB Guide,
            context=[parse_user_input_task],
        )
        get_weather_data_task = Task(
            description="For each of the following locations, use the bounding boxes (south, west, north, east), and the start_date and end_date in the context,  to query the weather tool to find a concise summary of relevant historical weather conditions between provided  start_date and end_date. Focus on key weather aspects that might influence air quality (e.g., temperature, wind, precipitation).",
            agent=self.agents["weather_data_integrator"],
            expected_output="A dictionary or list containing aggregate of historical weather conditions for each specified location.",
            context=[parse_user_input_task, get_bounding_boxes_task],
        )
        get_air_quality_data_task = Task(
            description="Fetch air quality data using the air_quality_tool for the eacj location: from start_date to end_date ONLY using the bounding boxes for each location. If specific parameters are provided by the aq_parameters attribute, focus on those. Return the data as a pandas DataFrame.",
            agent=self.agents["air_quality_retriever"],
            expected_output="A pandas DataFrame containing the air quality data for the specified locations, dates, and parameters.",
            context=[parse_user_input_task, get_bounding_boxes_task],
        )
        analysis_task = Task(
            description="Analyze the provided air quality data (including parameters like pm10, value, units, date, and location) for the specified locations and dates. Consider the historical weather information (temperature, wind, precipitation, humidity) for the same period. Identify any trends in air quality, calculate average values where relevant, and discuss any potential correlations or influences of weather conditions on the air quality. Provide a detailed report summarizing the air quality situation for each location, including the key findings and any notable observations related to weather patterns. Include facts and observations to compare the provided locations, as well as your own reliable knowledge base sources to comment on the overall Airquality. Add the author of the report", #Version 2 
            agent=self.agents["air_quality_analyst"],
            expected_output="A comprehensive report prepared by the Author of the Report ( obtain author from the context ),  detailing the air quality analysis for each location, including trends, averages, and a discussion of potential relationships with the historical weather conditions. Include a Summary at the top and Conclusion at the end.", # version 2
            context=[parse_user_input_task, get_air_quality_data_task, get_weather_data_task],
        )

        # Step 2: Add tasks to self.tasks
        self.tasks = {
            "parse_user_input_task": parse_user_input_task,
            "get_bounding_boxes_task": get_bounding_boxes_task,
            "get_weather_data_task": get_weather_data_task,
            "get_air_quality_data_task": get_air_quality_data_task,
            "analysis_task": analysis_task,
        
    }

    def _initialize_crew(self):
        """Initialize the Crew with agents and tasks."""
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            verbose=True,
        )

    def execute(self):
        """Execute the Crew workflow and return the report."""
        return self.crew.kickoff()


# For Testing
import argparse

# For Testing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run air quality analysis based on user input.")
    parser.add_argument(
        "--user-input",
        help="A natural language query for air quality analysis, e.g., 'Analyze air quality for New Delhi and Chennai between January 1 and January 3 2025, focusing on PM25 and PM10.'",
    )
    args = parser.parse_args()

    # Default value if no input is provided
    user_query = args.user_input or "Analyze air quality for New Delhi and Chennai between January 1 and January 3 2025, focusing on PM25 and PM10."

    try:
        analysis_crew = AirQualityAnalysisCrew(user_input=user_query)
        report = analysis_crew.execute()
        print("\n--- Air Quality Analysis Report ---")
        print(report)
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
