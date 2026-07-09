def run(params):
    archivo = params.get('nombre')
    with open(f'/{archivo}', 'r') as f:
        return f.read()