import requests
import json

base_url = "http://localhost:8080"
instance = "cactvs"
apikey = "B6D6574D-3932-491A-850E-1649911D0C4F"

headers = {
    "apikey": apikey
}

def delete_instance():
    url = f"{base_url}/instance/delete/{instance}"
    try:
        print(f"Deleting instance at {url}...")
        response = requests.delete(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

delete_instance()
