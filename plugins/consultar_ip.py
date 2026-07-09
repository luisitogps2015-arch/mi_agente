import requests
import concurrent.futures

def run(p):
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(requests.get, 'https://api.ipify.org?format=json')
            response = future.result()
            return response.json()
    except Exception as e:
        return f'Error: {str(e)}'