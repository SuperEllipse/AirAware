# AirAware Project

## Overview
This project focuses on leveraging Generative AI to address environmental challenges through a multi-agent workflow. Specifically, the application analyzes air quality and integrates it with meteorological data for a comprehensive understanding of environmental trends. The workflow emphasizes the use of open datasets and APIs to create actionable insights as part of the broader **"Data for Good"** initiative.

### Highlights:
1. **Open Data Sources**:
   - **Air Quality Data**: Utilizes the OpenAQ API for accessing air quality metrics.
   - **Geocoding**: Employs OpenStreetMap to extract bounding box coordinates for specified locations.
   - **Weather Data**: Integrates with Open-Meteo API to fetch weather details.

2. **Agentic Workflow**:
   - Combines multiple data sources seamlessly.
   - Facilitates a unified view of air quality and its correlation with weather conditions.
   - Employs CrewAI’s multi-agent framework to ensure robust and modular processing.

3. **Use Case Focus**:
   - Designed for environmental monitoring and analysis.
   - Aligns with global sustainability goals by providing actionable insights on air quality trends.

## Functional Components
### 1. Bounding Box Extraction
The application determines bounding box coordinates for a given location using OpenStreetMap. This enables fetching weather data for all points within a region.

### 2. Air Quality Analysis
Retrieves PM10 and PM2.5 levels, compares them with AQI standards, and identifies trends.

### 3. Weather Integration
Integrates historical weather data with air quality trends to offer context on meteorological influences.

### 4. Reporting
Generates detailed reports combining air quality and weather data for user-defined locations and timeframes.

## Example Report
--- Air Quality Analysis Report ---
### Comprehensive Air Quality and Weather Report

#### Introduction
This report provides a detailed analysis of air quality data, specifically focusing on PM2.5 levels, alongside corresponding historical weather conditions for New Delhi and Chennai, India during the period of March 23 to March 26, 2025. The aim is to identify trends in air quality, compute average values, and explore potential correlations with meteorological conditions.

---

### 1. Air Quality Analysis

#### 1.1 New Delhi, India

**PM2.5 Data:**
- **March 23:** 78.50 µg/m³
- **March 24:** 92.60 µg/m³
- **March 25:** 106.83 µg/m³
- **March 26:** 99.07 µg/m³

**Average PM2.5 Level:**  
\[
\text{Average} = \frac{78.50 + 92.60 + 106.83 + 99.07}{4} = 94.00 \, \text{µg/m³}
\]

**Weather Data:**
- **March 23:** Mean Temp: 29.6°C, Wind Speed: 11.3 km/h, Humidity: 71%, Precipitation: 0.2 mm
- **March 24:** Mean Temp: 29.0°C, Wind Speed: 9.0 km/h, Humidity: 75%, Precipitation: 0.6 mm
- **March 25:** Mean Temp: 28.8°C, Wind Speed: 8.2 km/h, Humidity: 73%, Precipitation: 0.0 mm
- **March 26:** Mean Temp: 29.0°C, Wind Speed: 9.8 km/h, Humidity: 71%, Precipitation: 0.0 mm

**Observations:**
- The PM2.5 levels in New Delhi exhibited a significant increase over the analyzed period, peaking at 106.83 µg/m³ on March 25.
- There is a noticeable correlation between decreasing wind speed and increasing PM2.5 concentrations, suggesting that stagnant air may contribute to pollutant accumulation.
- The highest PM2.5 concentration aligns with the lowest wind speeds and moderate humidity levels.

---

#### 1.2 Chennai, India

**PM2.5 Data:**
- **March 23:** 18.84 µg/m³
- **March 24:** 25.24 µg/m³
- **March 25:** 31.04 µg/m³
- **March 26:** 30.38 µg/m³

**Average PM2.5 Level:**  
\[
\text{Average} = \frac{18.84 + 25.24 + 31.04 + 30.38}{4} = 26.15 \, \text{µg/m³}
\]

**Weather Data:**
- **March 23:** Mean Temp: 29.4°C, Wind Speed: 7.3 km/h, Humidity: 78%, Precipitation: 0.1 mm
- **March 24:** Mean Temp: 29.9°C, Wind Speed: 6.8 km/h, Humidity: 76%, Precipitation: 0.0 mm
- **March 25:** Mean Temp: 30.1°C, Wind Speed: 6.5 km/h, Humidity: 75%, Precipitation: 0.0 mm
- **March 26:** Mean Temp: 30.3°C, Wind Speed: 6.9 km/h, Humidity: 74%, Precipitation: 0.0 mm

**Observations:**
- PM2.5 levels in Chennai showed a gradual increase from March 23 to March 25, with a slight decrease on March 26.
- Despite lower PM2.5 levels compared to New Delhi, the trend indicates increasing pollution levels which may be influenced by lower wind speeds.
- The humidity remained relatively high but did not significantly alter the PM2.5 concentrations, suggesting that other local sources of pollution could be at play.

---

### Conclusion

The analysis highlights distinct differences in air quality trends between New Delhi and Chennai during the specified dates:

- **New Delhi** experienced significantly higher PM2.5 levels with an alarming peak due to stagnant meteorological conditions (lower wind speeds).
- **Chennai**, while having lower PM2.5 concentrations overall, also showed an upward trend in pollution levels which warrants further monitoring.

Overall, this report underscores the critical need for continued air quality monitoring in conjunction with meteorological data to inform public health strategies and policy-making