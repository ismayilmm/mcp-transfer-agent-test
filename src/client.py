"""
Client for interacting with the Bizim Transfer API.
"""
import httpx
from typing import Dict, Any, List, Optional, Union


class BizimTransferClient:
    """Client for communicating with the Bizim Transfer REST API."""
    
    def __init__(
        self, 
        base_url: str = "http://test-api.bizimtransfer.com",
        username: str = "test", 
        password: str = "test"
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: API base URL
            username: API username for HTTP Basic Auth
            password: API password for HTTP Basic Auth
        """
        self.base_url = base_url
        self.auth = (username, password)
        self.client = httpx.AsyncClient(auth=self.auth)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def search_transfers(
        self,
        pickup: str,
        pickuplat: float,
        pickuplng: float,
        dropoff: str,
        dropofflat: float,
        dropofflng: float,
        adult: int,
        child: int = 0,
        infant: int = 0,
        pickupdate: str = "",
        pickuptime: str = "",
        dropoffdate: str = "",
        dropofftime: str = "",
        requesttype: int = 1,
        currencyid: int = 1,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Search for available transfers.
        
        Args:
            pickup: Pickup location address
            pickuplat: Pickup latitude
            pickuplng: Pickup longitude
            dropoff: Dropoff location address
            dropofflat: Dropoff latitude
            dropofflng: Dropoff longitude
            adult: Number of adults
            child: Number of children (0-16 years)
            infant: Number of infants (0-2 years)
            pickupdate: Pickup date (YYYY-MM-DD)
            pickuptime: Pickup time (HH:MM)
            dropoffdate: Return date for round trips (YYYY-MM-DD)
            dropofftime: Return time for round trips (HH:MM)
            requesttype: 1 for one-way, 2 for round-trip
            currencyid: Currency ID (1=TRY, 2=EUR, 3=USD, 4=GBP, 6=RUB)
            language: Language code (tr, en, de, ru)
            
        Returns:
            API response with available transfer options
        """
        payload = {
            "pickup": pickup,
            "pickuplat": pickuplat,
            "pickuplng": pickuplng,
            "dropoff": dropoff,
            "dropofflat": dropofflat,
            "dropofflng": dropofflng,
            "adult": adult,
            "child": child,
            "infant": infant,
            "pickupdate": pickupdate,
            "pickuptime": pickuptime,
            "dropoffdate": dropoffdate,
            "dropofftime": dropofftime,
            "requesttype": requesttype,
            "currencyid": currencyid,
            "language": language
        }
        
        response = await self.client.post(f"{self.base_url}/query", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def make_reservation(
        self,
        uuid: str,
        customername: str,
        customersurname: str,
        customeremail: str,
        customertelephone: Union[str, int],
        customercoutry: str,
        transferway: List[Dict[str, Any]],
        passangers: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Make a transfer reservation.
        
        Args:
            uuid: UUID from search results
            customername: Customer's first name
            customersurname: Customer's last name
            customeremail: Customer's email
            customertelephone: Customer's phone number with country code
            customercoutry: Customer's country code
            transferway: List of transfer details
            passangers: List of passenger details
            
        Returns:
            API response with reservation confirmation
        """
        payload = {
            "uuid": uuid,
            "customername": customername,
            "customersurname": customersurname,
            "customeremail": customeremail,
            "customertelephone": customertelephone,
            "customercoutry": customercoutry,
            "transferway": transferway,
            "passangers": passangers
        }
        
        response = await self.client.post(f"{self.base_url}/reservation", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def list_reservations(
        self,
        querytype: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        reservationnumber: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List existing reservations.
        
        Args:
            querytype: Type of query ('createdate', 'flightdate', 'reservationnumber')
            start: Start date for date-based queries (YYYY-MM-DD)
            end: End date for date-based queries (YYYY-MM-DD)
            reservationnumber: Reservation number for direct lookups
            
        Returns:
            API response with reservation list
        """
        if querytype in ["createdate", "flightdate"]:
            payload = {
                "querytype": querytype,
                "start": start,
                "end": end
            }
        else:  # reservationnumber
            payload = {
                "querytype": querytype,
                "reservationnumber": reservationnumber
            }
        
        response = await self.client.post(f"{self.base_url}/list", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def search_places(self, query: str, language: str = "en") -> List[Dict[str, str]]:
        """
        Search for places.
        
        Args:
            query: Search query
            language: Language code
            
        Returns:
            List of places matching the query
        """
        response = await self.client.get(
            f"{self.base_url}/places",
            params={"query": query, "language": language}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_place_details(self, place_id: str, language: str = "en") -> Dict[str, Any]:
        """
        Get details for a specific place.
        
        Args:
            place_id: Google Place ID
            language: Language code
            
        Returns:
            Place details
        """
        response = await self.client.get(
            f"{self.base_url}/places/detail",
            params={"place_id": place_id, "language": language}
        )
        response.raise_for_status()
        return response.json()