# Bizim Transfer API Server

A Python-based server that provides a clean interface to the Bizim Transfer API, enabling users to search for transfers, get location details, make reservations, and more. The server can be run both as a standalone API client and as an MCP (Model Context Protocol) server.

## Features

- 🔍 **Location Search**: Search for hotels, airports, and other locations
- 🚕 **Transfer Search**: Find available transportation options between locations
- 📝 **Reservations**: Make and manage transfer reservations
- 🌐 **MCP Integration**: Run as an MCP server for AI model integration
- 🌍 **Multilingual Support**: Support for multiple languages (en, tr, de, ru)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/bizim-transfer-server.git
   cd bizim-transfer-server
   ```

2. Set up a virtual environment (recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. If you want to use MCP functionality, install the MCP package:
   ```
   pip install "mcp[cli]"
   ```

## API Client Usage

### Quick Test

Run the included `check_price.py` script to see an example of how to use the API:

```
python check_price.py
```

This will search for transfer options from Istanbul Airport to Osmanhan Hotel.

### Basic API Usage

```python
import asyncio
from client import BizimTransferClient

async def main():
    # Initialize the client
    client = BizimTransferClient()
    
    try:
        # Search for a location
        places = await client.search_places("Osmanhan Hotel", "en")
        
        # Get details about a location
        if places.get("status") == "success" and places.get("places"):
            place_id = places["places"][0]["place_id"]
            details = await client.get_place_details(place_id, "en")
        
        # Search for transfers
        transfers = await client.search_transfers(
            pickup="Istanbul Airport",
            pickuplat=41.2608,
            pickuplng=28.7425,
            dropoff="Taksim Square",
            dropofflat=41.0370,
            dropofflng=28.9850,
            adult=2,
            pickupdate="2023-06-15",
            pickuptime="14:00",
            requesttype=1,  # One-way
            currencyid=2,   # EUR
            language="en"
        )
        
    finally:
        # Always close the client
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## MCP Server Usage

The MCP (Model Context Protocol) server allows AI models to interact with the Bizim Transfer API in a structured way.

### Running the MCP Server

If you have the MCP package installed:

```
python -m mcp run server.py
```

For development with the inspector interface:

```
python -m mcp dev server.py
```

### Available MCP Tools

The MCP server exposes the following tools:

1. **search_places**: Search for locations
2. **get_place_details**: Get detailed information about a location
3. **search_transfers**: Search for available transfers between locations
4. **make_reservation**: Make a transfer reservation
5. **list_reservations**: List existing reservations

## API Reference

### BizimTransferClient

The main client for interacting with the Bizim Transfer API.

#### Methods

- **search_places(query, language)**: Search for locations
- **get_place_details(place_id, language)**: Get detailed information about a location
- **search_transfers(...)**: Search for available transfers between locations
- **make_reservation(...)**: Make a transfer reservation
- **list_reservations(...)**: List existing reservations

## Project Structure

- `client.py`: API client implementation
- `server.py`: MCP server implementation
- `utils.py`: Utility functions for formatting, validation, etc.
- `check_price.py`: Example script for checking transfer prices
- `requirements.txt`: Required Python packages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Bizim Transfer for providing the API
- The MCP team for the Model Context Protocol
