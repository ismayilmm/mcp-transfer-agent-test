"""
MCP server implementation for the Bizim Transfer API.
"""
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from mcp.server.fastmcp import FastMCP, Context

from client import BizimTransferClient
from utils import (
    CURRENCY_MAP,
    validate_date,
    validate_time,
    format_transfer_results,
    format_reservation_results,
    format_reservation_list,
    format_places_results,
    format_place_details
)

# Create MCP server with a descriptive name
mcp = FastMCP("BizimTransfer")

@dataclass
class AppContext:
    client: BizimTransferClient


# Context setup for dependency injection
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    client = BizimTransferClient()
    try:
        yield AppContext(client=client)
    finally:
        # Cleanup on shutdown
        await client.close()

# Pass lifespan to server
mcp = FastMCP("BizimTransfer", lifespan=app_lifespan)

@mcp.tool()
async def search_transfers(
    pickup_address: str,
    pickup_lat: float,
    pickup_lng: float,
    dropoff_address: str,
    dropoff_lat: float,
    dropoff_lng: float,
    pickup_date: str,
    pickup_time: str,
    adults: int,
    children: int = 0,
    infants: int = 0,
    round_trip: bool = False,
    return_date: Optional[str] = None,
    return_time: Optional[str] = None,
    currency: str = "EUR",
    language: str = "en",
    ctx: Context = None
) -> str:
    """
    Search for available transfers between two locations.
    
    Args:
        pickup_address: Full address for pickup location
        pickup_lat: Latitude of pickup location
        pickup_lng: Longitude of pickup location
        dropoff_address: Full address for dropoff location
        dropoff_lat: Latitude of dropoff location
        dropoff_lng: Longitude of dropoff location
        pickup_date: Pickup date (YYYY-MM-DD format)
        pickup_time: Pickup time (HH:MM format, 24h)
        adults: Number of adults (minimum 1)
        children: Number of children (0-16 years)
        infants: Number of infants (0-2 years)
        round_trip: Whether this is a round trip
        return_date: Return date for round trips (YYYY-MM-DD format)
        return_time: Return time for round trips (HH:MM format, 24h)
        currency: Currency code (EUR, USD, GBP, TRY, RUB)
        language: Language for response (en, tr, de, ru)
    
    Returns:
        Formatted search results with available transfer options
    """
    # Input validation
    if not pickup_address or not dropoff_address:
        return "Error: Pickup and dropoff addresses are required"
    
    if adults < 1:
        return "Error: At least one adult passenger is required"
    
    if not validate_date(pickup_date):
        return "Error: Invalid pickup date format. Please use YYYY-MM-DD format"
    
    if not validate_time(pickup_time):
        return "Error: Invalid pickup time format. Please use HH:MM format (24h)"
    
    if round_trip:
        if not return_date or not return_time:
            return "Error: Return date and time are required for round trips"
        if not validate_date(return_date):
            return "Error: Invalid return date format. Please use YYYY-MM-DD format"
        if not validate_time(return_time):
            return "Error: Invalid return time format. Please use HH:MM format (24h)"
    
    # Get currency ID
    currency_id = CURRENCY_MAP.get(currency.upper(), 2)  # Default to EUR
    
    # Set request type (1 for one-way, 2 for round-trip)
    request_type = 2 if round_trip else 1
    
    try:
        # Get client from context
        client = ctx.request_context.lifespan_context
        
        # Log the request
        ctx.info(f"Searching transfers from {pickup_address} to {dropoff_address}")
        
        # Call the API
        result = await client.client.search_transfers(
            pickup=pickup_address,
            pickuplat=pickup_lat,
            pickuplng=pickup_lng,
            dropoff=dropoff_address,
            dropofflat=dropoff_lat,
            dropofflng=dropoff_lng,
            adult=adults,
            child=children,
            infant=infants,
            pickupdate=pickup_date,
            pickuptime=pickup_time,
            dropoffdate=return_date if round_trip else "",
            dropofftime=return_time if round_trip else "",
            requesttype=request_type,
            currencyid=currency_id,
            language=language
        )
        
        # Format and return the results
        return format_transfer_results(result)
    
    except Exception as e:
        return f"Error searching for transfers: {str(e)}"

@mcp.tool()
async def make_reservation(
    uuid: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    country_code: str,
    outbound_subroute_id: int,
    flight_number: Optional[str] = "",
    terminal: Optional[str] = "",
    notes: Optional[str] = "",
    return_subroute_id: Optional[int] = None,
    return_flight_number: Optional[str] = "",
    return_terminal: Optional[str] = "",
    return_notes: Optional[str] = "",
    passenger_names: List[str] = None,
    passenger_countries: List[str] = None,
    ctx: Context = None
) -> str:
    """
    Make a transfer reservation based on search results.
    
    Args:
        uuid: UUID from the search results
        first_name: Customer's first name
        last_name: Customer's last name
        email: Customer's email address
        phone: Customer's phone number with country code
        country_code: Customer's country code (2-letter ISO code)
        outbound_subroute_id: Subroute ID for the outbound journey
        flight_number: Flight number (optional)
        terminal: Terminal information (optional)
        notes: Additional notes for the driver
        return_subroute_id: Subroute ID for the return journey (round trips only)
        return_flight_number: Return flight number (optional)
        return_terminal: Return terminal information (optional)
        return_notes: Additional notes for the return driver
        passenger_names: List of passenger full names
        passenger_countries: List of passenger country codes (2-letter ISO codes)
    
    Returns:
        Reservation confirmation details
    """
    # Input validation
    if not uuid:
        return "Error: UUID is required from the search results"
    
    if not first_name or not last_name:
        return "Error: Customer name is required"
    
    if not email:
        return "Error: Email address is required"
    
    if not phone:
        return "Error: Phone number is required"
    
    if not country_code:
        return "Error: Country code is required"
    
    if not outbound_subroute_id:
        return "Error: Outbound subroute ID is required"
    
    # Prepare transfer ways
    transfer_ways = [
        {
            "subrouteid": outbound_subroute_id,
            "flightnumber": flight_number or "",
            "terminal": terminal or "",
            "notes": notes or ""
        }
    ]
    
    # Add return transfer if specified
    if return_subroute_id:
        transfer_ways.append({
            "subrouteid": return_subroute_id,
            "flightnumber": return_flight_number or "",
            "terminal": return_terminal or "",
            "notes": return_notes or ""
        })
    
    # Prepare passengers list
    passengers = []
    if passenger_names and passenger_countries:
        if len(passenger_names) != len(passenger_countries):
            return "Error: Number of passenger names and countries must match"
        
        for i, (name, country) in enumerate(zip(passenger_names, passenger_countries)):
            passengers.append({
                "name": name,
                "country": country.lower()
            })
    else:
        # Default to main customer if no specific passengers
        passengers.append({
            "name": f"{first_name} {last_name}",
            "country": country_code.lower()
        })
    
    try:
        # Get client from context
        client = ctx.request_context.lifespan_context
        
        # Log the request
        ctx.info(f"Making reservation for {first_name} {last_name}")
        
        # Call the API
        result = await client.client.make_reservation(
            uuid=uuid,
            customername=first_name,
            customersurname=last_name,
            customeremail=email,
            customertelephone=phone,
            customercoutry=country_code.lower(),
            transferway=transfer_ways,
            passangers=passengers
        )
        
        # Format and return the results
        return format_reservation_results(result)
    
    except Exception as e:
        return f"Error making reservation: {str(e)}"

@mcp.tool()
async def list_reservations(
    query_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    reservation_number: Optional[int] = None,
    ctx: Context = None
) -> str:
    """
    List existing reservations based on criteria.
    
    Args:
        query_type: Type of search ('createdate', 'flightdate', 'reservationnumber')
        start_date: Start date for date-based queries (YYYY-MM-DD)
        end_date: End date for date-based queries (YYYY-MM-DD)
        reservation_number: Specific reservation number to look up
    
    Returns:
        List of matching reservations
    """
    # Input validation
    if query_type not in ["createdate", "flightdate", "reservationnumber"]:
        return "Error: query_type must be 'createdate', 'flightdate', or 'reservationnumber'"
    
    if query_type in ["createdate", "flightdate"]:
        if not start_date or not end_date:
            return f"Error: start_date and end_date are required for {query_type} queries"
        if not validate_date(start_date) or not validate_date(end_date):
            return "Error: Invalid date format. Please use YYYY-MM-DD format"
    
    if query_type == "reservationnumber" and not reservation_number:
        return "Error: reservation_number is required for direct lookup"
    
    try:
        # Get client from context
        client = ctx.request_context.lifespan_context
        
        # Log the request
        ctx.info(f"Listing reservations with {query_type}")
        
        # Call the API
        if query_type in ["createdate", "flightdate"]:
            result = await client.client.list_reservations(
                querytype=query_type,
                start=start_date,
                end=end_date
            )
        else:  # reservationnumber
            result = await client.client.list_reservations(
                querytype=query_type,
                reservationnumber=reservation_number
            )
        
        # Format and return the results
        return format_reservation_list(result)
    
    except Exception as e:
        return f"Error listing reservations: {str(e)}"

@mcp.tool()
async def search_places(
    query: str,
    language: str = "en",
    ctx: Context = None
) -> str:
    """
    Search for locations using the Places API.
    
    Args:
        query: Search text (e.g., hotel name, airport, city)
        language: Language code (en, tr, de, ru)
    
    Returns:
        List of matching places with IDs for use with get_place_details
    """
    if not query:
        return "Error: Search query is required"
    if not ctx or not ctx.request_context.lifespan_context:
        return "Error: Server configuration error - missing context"
    try:
        # Get client from context
        client = ctx.request_context.lifespan_context
        
        # Log the request
        ctx.info(f"Searching places for '{query}'")
        
        # Call the API
        places = await client.client.search_places(query, language)
        
        # Format and return the results
        return format_places_results(places)
    
    except Exception as e:
        return f"Error searching places: {str(e)}"

@mcp.tool()
async def get_place_details(
    place_id: str,
    language: str = "en",
    ctx: Context = None
) -> str:
    """
    Get detailed information about a location.
    
    Args:
        place_id: Google Place ID from search_places results
        language: Language code (en, tr, de, ru)
    
    Returns:
        Detailed information about the location including coordinates
    """
    if not place_id:
        return "Error: Place ID is required"
    
    try:
        # Get client from context
        client = ctx.request_context.lifespan_context
        
        # Log the request
        ctx.info(f"Getting details for place ID {place_id}")
        
        # Call the API
        details = await client.client.get_place_details(place_id, language)
        
        # Format and return the results
        return format_place_details(details)
    
    except Exception as e:
        return f"Error getting place details: {str(e)}"


if __name__ == "__main__":
    import sys
        
    # Default to stdio transport if no arguments provided
    transport = "stdio"
    port = 8100
    
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--sse":
        transport = "sse"
        # Use port from command line if provided
        if len(sys.argv) > 2:
            port = int(sys.argv[2])
    
    # Run server with specified transport
    if transport == "sse":
        mcp.run(transport="sse", port=port, host="127.0.0.1")
    else:
        # At the beginning of the run method
        print(f"Starting MCP server with {transport} transport on port {port if transport == 'sse' else 'N/A'}")
        mcp.run()  # Default STDIO transport