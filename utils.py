"""
Utility functions for the Bizim Transfer MCP server.
"""
from datetime import datetime
from typing import Dict, Union, Optional, Any, List

# Currency mapping
CURRENCY_MAP = {
    "TRY": 1,
    "EUR": 2,
    "USD": 3,
    "GBP": 4,
    "RUB": 6
}

def validate_date(date_str: str) -> bool:
    """
    Validate a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not date_str:
            return True  # Empty string is valid (for optional dates)
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_time(time_str: str) -> bool:
    """
    Validate a time string in HH:MM format.
    
    Args:
        time_str: Time string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not time_str:
            return True  # Empty string is valid (for optional times)
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def format_transfer_results(result: Dict[str, Any]) -> str:
    """
    Format transfer search results into a readable string.
    
    Args:
        result: API response from search_transfers
        
    Returns:
        Formatted string with transfer options
    """
    if result.get("status") != "success":
        return f"Error: {result.get('description', 'Unknown error occurred')}"
    
    response_parts = []
    
    # Add header
    currency_symbol = result.get("currencysembol", "")
    response_parts.append(f"Transfer options from {result.get('pickup')} to {result.get('dropoff')}")
    response_parts.append(f"Total passengers: {result.get('adult')} adults, {result.get('child')} children, {result.get('infant')} infants")
    response_parts.append("")  # Empty line
    
    # Add UUID for later use in booking
    response_parts.append(f"Booking reference (UUID): {result.get('uuid')}")
    response_parts.append("")  # Empty line
    
    # Process each way
    ways = result.get("ways", [])
    for way in ways:
        way_type = "Outbound" if way.get("type", "").startswith("yon1") else "Return"
        response_parts.append(f"## {way_type} Journey")
        response_parts.append(f"From: {way.get('from')}")
        response_parts.append(f"To: {way.get('to')}")
        response_parts.append(f"Date: {way.get('date')}")
        response_parts.append("")
        
        # Process transfer options
        options = way.get("list", [])
        for i, option in enumerate(options, 1):
            response_parts.append(f"### Option {i}: {option.get('carname')}")
            response_parts.append(f"Type: {option.get('extramessage', 'Standard')}")
            response_parts.append(f"Pickup Time: {option.get('pickup')}")
            response_parts.append(f"Duration: {option.get('duration')} minutes")
            response_parts.append(f"Price: {option.get('price')} {currency_symbol}")
            response_parts.append(f"Max Passengers: {option.get('kisihakki')} with {option.get('bavulhakki')} luggage items")
            
            # Add extras if available
            extras = option.get("extraurunler", [])
            if extras:
                response_parts.append("Available Extras:")
                for extra in extras:
                    response_parts.append(f"- {extra.get('UrunTanimi')}: {extra.get('BirimFiyat')} {currency_symbol}")
            
            # Add booking reference IDs
            response_parts.append(f"Route ID: {option.get('routeid')}")
            response_parts.append(f"Subroute ID: {option.get('subrouteid')} (needed for booking)")
            response_parts.append("")
    
    return "\n".join(response_parts)

def format_reservation_results(result: Dict[str, Any]) -> str:
    """
    Format reservation confirmation into a readable string.
    
    Args:
        result: API response from make_reservation
        
    Returns:
        Formatted string with reservation details
    """
    if result.get("status") != "success":
        return f"Error: {result.get('description', 'Unknown error occurred')}"
    
    response = [
        "✅ Reservation successfully created!",
        f"Reservation Number: {result.get('rezid')}",
        "",
        "Please keep this reservation number for your records.",
        "You should receive a confirmation email with your booking details."
    ]
    
    return "\n".join(response)

def format_reservation_list(result: Dict[str, Any]) -> str:
    """
    Format reservation list into a readable string.
    
    Args:
        result: API response from list_reservations
        
    Returns:
        Formatted string with reservation list
    """
    if result.get("status") != "success":
        return f"Error: {result.get('description', 'Unknown error occurred')}"
    
    reservations = result.get("list", [])
    if not reservations:
        return "No reservations found matching your criteria."
    
    response_parts = [f"Found {len(reservations)} reservation(s):"]
    
    for i, res in enumerate(reservations, 1):
        response_parts.append(f"\n## Reservation {i}")
        response_parts.append(f"Reservation Number: {res.get('reservationnumber')}")
        response_parts.append(f"Customer: {res.get('customername')} {res.get('customersurname')}")
        response_parts.append(f"Contact: {res.get('customeremail')}, {res.get('customertel')}")
        response_parts.append(f"Passengers: {res.get('adult')} adults, {res.get('child')} children, {res.get('infant')} infants")
        response_parts.append(f"Amount: {res.get('Amount')} {res.get('currency')}")
        response_parts.append(f"Status: {res.get('status')}")
        response_parts.append(f"Payment: {res.get('paymenttype')}")
        response_parts.append(f"Created: {res.get('createat')}")
        
        # Show transfer ways
        ways = res.get("ways", [])
        response_parts.append("\nTransfers:")
        for j, way in enumerate(ways, 1):
            dir_text = "Outbound" if j == 1 else "Return"
            response_parts.append(f"- {dir_text}: {way.get('pickupadres')} → {way.get('returnadres')}")
            response_parts.append(f"  Date: {way.get('flightdate')}, Pickup time: {way.get('pickuptime')}")
            response_parts.append(f"  Vehicle: {way.get('car')}, Duration: {way.get('duration')} min")
            if way.get('flightnumber'):
                response_parts.append(f"  Flight: {way.get('flightnumber')}, Terminal: {way.get('terminal')}")
        
        # Show passengers
        passengers = res.get("passangers", [])
        if passengers:
            response_parts.append("\nPassengers:")
            for passenger in passengers:
                response_parts.append(f"- {passenger.get('namesurname')} ({passenger.get('country')})")
    
    return "\n".join(response_parts)

def format_places_results(places: List[Dict[str, str]]) -> str:
    """
    Format places search results into a readable string.
    
    Args:
        places: API response from search_places
        
    Returns:
        Formatted string with places list
    """
    if not places:
        return "No places found matching your query."
    
    response_parts = ["Found locations:"]
    
    for i, place in enumerate(places, 1):
        response_parts.append(f"{i}. {place.get('description')} (ID: {place.get('place_id')})")
    
    return "\n".join(response_parts)

def format_place_details(details: Dict[str, Any]) -> str:
    """
    Format place details into a readable string.
    
    Args:
        details: API response from get_place_details
        
    Returns:
        Formatted string with place details
    """
    response_parts = ["Location Details:"]
    
    response_parts.append(f"Name: {details.get('name', 'N/A')}")
    response_parts.append(f"Address: {details.get('formatted_address', 'N/A')}")
    
    # Get coordinates if available
    location = details.get('geometry', {}).get('location', {})
    if location:
        response_parts.append(f"Latitude: {location.get('lat', 'N/A')}")
        response_parts.append(f"Longitude: {location.get('lng', 'N/A')}")
    
    # Get place types if available
    types = details.get('types', [])
    if types:
        response_parts.append(f"Type: {', '.join(types)}")
    
    return "\n".join(response_parts)