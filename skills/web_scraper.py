import requests
from bs4 import BeautifulSoup

def obtener_titulo(url):
    """
    Realiza una petición GET a la URL proporcionada y extrae el contenido de la etiqueta <title>.
    Retorna una cadena de texto con el título o un mensaje de error.
    """
    try:
        # Realizamos la petición con un timeout para evitar bloqueos
        response = requests.get(url, timeout=10)
        
        # Verificamos si la petición fue exitosa
        response.raise_for_status()
        
        # Parseamos el HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraemos el título
        if soup.title and soup.title.string:
            return str(soup.title.string.strip())
        else:
            return "La página no tiene título."
            
    except requests.exceptions.RequestException as e:
        return f"Error en la conexión: {str(e)}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"
