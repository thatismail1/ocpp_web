import aiohttp
import logging
from typing import Dict, Any
import json
import time
from performance_metrics import PerformanceMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default API configuration
DEFAULT_API_ENDPOINT = 'http://144.122.166.37:3005/api/readings/'
DEFAULT_API_KEY = 'None'

class ApiSender:
    def __init__(self, api_url: str = DEFAULT_API_ENDPOINT, api_key: str = DEFAULT_API_KEY):
        self.api_url = api_url
        self.api_key = api_key
        self.metrics = PerformanceMetrics()
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        } if api_key else {'Content-Type': 'application/json'}
        
    def configure(self, api_url: str, api_key: str = None):
        """Configure the API endpoint and key."""
        self.api_url = api_url
        self.api_key = api_key
        if api_key:
            self.headers['X-API-Key'] = api_key
            logger.info(f"API configured with URL: {api_url}")
        else:
            logger.warning("No API key provided")

    async def send_meter_data(self, data: Dict[str, Any]) -> bool:
        """Send meter data to configured API endpoint."""
        if not self.api_url:
            logger.error("[API] URL not configured")
            return False

        if 'X-API-Key' not in self.headers:
            logger.error("[API] No API key configured")
            return False

        start_time = time.time()
        try:
            # Log the complete formatted JSON data
            logger.info("[API] Sending formatted JSON data to endpoint:")
            logger.info(json.dumps(data, indent=4))
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=data, headers=self.headers) as response:
                    response_text = await response.text()
                    
                    if response.status in (200, 201, 202):
                        logger.info(f"[API] Successfully sent meter data")
                        if response.status == 202:
                            logger.info(f"[API] Request accepted for processing: {response_text}")
                        logger.debug(f"[API] Response: {response_text}")
                        
                        # Add metrics before returning success
                        api_time = time.time() - start_time
                        self.metrics.update_api_timing(api_time, success=True)
                        self.metrics.log_metrics()
                        return True
                    elif response.status == 401:
                        logger.error(f"[API] Authentication failed - Invalid API key")
                        logger.error(f"[API] Response: {response_text}")
                        return False
                    else:
                        logger.error(f"[API] Failed to send data - Status: {response.status}")
                        logger.error(f"[API] Response: {response_text}")
                        
                        # Add metrics before returning failure
                        api_time = time.time() - start_time
                        self.metrics.update_api_timing(api_time, success=False)
                        self.metrics.log_metrics()
                        return False
                        
        except aiohttp.ClientError as e:
            logger.error(f"[API] Network error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"[API] Unexpected error: {str(e)}")
            
            # Add metrics before returning failure
            api_time = time.time() - start_time
            self.metrics.update_api_timing(api_time, success=False)
            self.metrics.log_metrics()
            return False