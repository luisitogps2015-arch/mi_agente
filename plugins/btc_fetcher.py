import requests

def run(p):
    return requests.get('https://api.coindesk.com/v1/bpi/currentprice.json').json()['bpi']['USD']['rate']