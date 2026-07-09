import requests
from bs4 import BeautifulSoup

def analizar_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        texto = ' '.join([p.text for p in soup.find_all('p')]).lower()
        
        # Lista de palabras con pesos distintos
        positivas = ['innovación', 'revolucionario', 'potente', 'mejor', 'increíble', 'futuro']
        negativas = ['problema', 'fallo', 'costoso', 'lento', 'queja']
        
        score = 5 + sum(1 for p in positivas if p in texto) - sum(1 for n in negativas if n in texto)
        score = max(0, min(score * 2, 10)) # Normalizar de 0 a 10
        
        sentimiento = '✅ POSITIVO' if score > 5 else '⚠ MODERADO/CAUTELOSO'
        return f'--- REPORTE DE MERCADO ---\nURL: {url}\nSentimiento: {sentimiento}\nImpacto: {score}/10\nResumen: {texto[:180].strip()}...'
    except Exception as e:
        return f'Error: {str(e)}'