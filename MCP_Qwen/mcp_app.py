#!/usr/bin/env python3
"""
FastMCP HTTP Server - Weather Service
Runs as HTTP server instead of stdio for Docker deployment
"""

from fastmcp import FastMCP
import json

# Create server instance
mcp = FastMCP("Weather Server HTTP")

# Weather data
WEATHER_DATA = {
    "new_york": {"temp": 72, "condition": "Sunny", "humidity": 60},
    "london": {"temp": 65, "condition": "Cloudy", "humidity": 80},
    "tokyo": {"temp": 75, "condition": "Rainy", "humidity": 85},
    "paris": {"temp": 68, "condition": "Partly Cloudy", "humidity": 70}
}

@mcp.prompt() #("What is the weather in {city}?")
def get_weather_prompt(city: str) -> dict:
    """Prompt template for getting weather information."""
    print(f"Generating prompt for city: {city}")
    return f"What is the weather in {city}?"

#not used    
#return {
#    "role": "user",
#    "content": f"What is the weather in {city}?"
#}
    
@mcp.tool()
def get_weather(city: str) -> str:
    """Get weather information for a city.    
    Args:
        city: City name (lowercase, underscore for spaces like 'new_york')
    """
    city = city.lower().strip()
    print(f"Fetching weather for: {city}")
    if city in WEATHER_DATA:
        weather = WEATHER_DATA[city]
        result = f"Weather in {city.replace('_', ' ').title()}:\n"
        result += f"Temperature: {weather['temp']}°F\n"
        result += f"Condition: {weather['condition']}\n"
        result += f"Humidity: {weather['humidity']}%"
        return result
    else:
        available = ", ".join(city.replace('_', ' ').title() for city in WEATHER_DATA.keys())
        return f"Sorry, weather data for '{city}' is not available. Available cities: {available}"

@mcp.tool()
def list_cities() -> str:    
    """List all cities with available weather data."""
    print("Listing available cities...")
    cities = list(WEATHER_DATA.keys())
    return ", ".join(city.replace('_', ' ').title() for city in cities)

@mcp.tool()
def add_city(city: str, temp: int, condition: str, humidity: int) -> str:
    """Add weather data for a new city."""
    print(f"Adding weather data for: {city}")
    city = city.lower().strip()    
    WEATHER_DATA[city] = {
        "temp": temp,
        "condition": condition,
        "humidity": humidity
    }
    return f"Added weather data for {city.replace('_', ' ').title()}"

@mcp.resource("weather://current_data")
def get_current_weather_data() -> str:
    print("Providing current weather data in JSON format")
    """All current weather data in JSON format."""    
    return json.dumps(WEATHER_DATA, indent=2)

if __name__ == "__main__":
    # Run as HTTP server on port 5000
    mcp.run(transport="streamable-http", host="0.0.0.0", port=5000)
    #mcp.run(transport="stdio")