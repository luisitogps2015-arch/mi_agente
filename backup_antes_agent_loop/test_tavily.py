import requests

def probar_busqueda():
    tavily_key = "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"
    query = "noticias tecnología 2026"
    url = "https://api.tavily.com/search"
    payload = {"api_key": tavily_key, "query": query, "search_depth": "basic", "max_results": 1}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Código de respuesta: {response.status_code}")
        print(f"Respuesta: {response.text}")
    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    probar_busqueda()
