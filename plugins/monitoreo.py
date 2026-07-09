import requests
from bs4 import BeautifulSoup
import json
# Importamos la función interna de ejecución de scripts
from mcp_server import ejecutar_script

def run(params):
    url = 'https://www.wikipedia.org'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    if 'Wikipedia' in soup.text:
        return ejecutar_script('enviar_alerta', {'mensaje': 'Alerta: Wikipedia encontrada en monitoreo automático'})
    return 'Sin alertas'