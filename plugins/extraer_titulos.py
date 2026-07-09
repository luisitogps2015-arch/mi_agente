import requests
from bs4 import BeautifulSoup
def run(params):
    url = params.get('url')
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    titulos = [h1.text.strip() for h1 in soup.find_all('h1')]
    return {'url': url, 'titulos': titulos}