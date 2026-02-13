import requests
import logging
import json

class EvolutionService:
    """
    Service wrapper for Evolution API (WhatsApp).
    Handles sending messages and fetching chat history/status.
    """
    def __init__(self, base_url, api_token, instance_name="cactvs"):
        self.base_url = base_url.rstrip('/') if base_url else ""
        self.api_token = api_token
        self.instance_name = instance_name
        self.headers = {
            "apikey": self.api_token,
            "Content-Type": "application/json"
        }

    def is_configured(self):
        """Checks if the service has necessary configuration."""
        return bool(self.base_url and self.api_token)

    def check_connection(self):
        """Checks if the Evolution API instance is connected."""
        if not self.is_configured():
            return False, "Evolution API URL or Token is missing."

        url = f"{self.base_url}/instance/connectionState/{self.instance_name}"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                state = data.get('instance', {}).get('state') or data.get('state')
                if state == 'open':
                     return True, "Connected"
                return False, f"Status: {state}"
            else:
                return False, f"API Error: {response.status_code}"
        except Exception as e:
            logging.error(f"Error checking connection: {e}")
            return False, str(e)

    def send_message(self, phone, message):
        """Sends a text message to a specific number."""
        if not self.is_configured():
            logging.warning("Evolution API not configured.")
            return None

        url = f"{self.base_url}/message/sendText/{self.instance_name}"
        payload = {
            "number": phone,
            "text": message
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error sending message to {phone}: {e}")
            return None

    def get_recent_messages(self, count=10):
        """
        Fetches recent messages. 
        Note: This uses the /chat/findMessages endpoint which is common in Evolution API v2.
        Required for polling mechanism.
        """
        if not self.is_configured():
            return []

        url = f"{self.base_url}/chat/findMessages/{self.instance_name}"
        payload = {
            "count": count,
            "page": 1
        }
        try:
            # Evolution API often uses POST for findMessages to pass options
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                 # Instance might not exist or endpoint unavailable
                 logging.warning("Evolution API findMessages endpoint not found (404).")
                 return []
            
            response.raise_for_status()
            return response.json() # Returns list of messages objects
        except Exception as e:
            logging.error(f"Error fetching messages: {e}")
            return []
