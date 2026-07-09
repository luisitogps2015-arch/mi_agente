def run(params):
    a = int(params.get("a", 0))
    b = int(params.get("b", 0))
    return f"Resultado: {a * b}"