from memory_manager import leer_resumen, leer_eventos

def run(params):
    modo = params.get("modo", "resumen")

    if modo == "eventos":
        resultado = leer_eventos(limite=10)

        if not resultado.get("ok"):
            return "Error leyendo eventos."

        eventos = resultado.get("eventos", [])

        if not eventos:
            return "No hay eventos registrados."

        salida = ["Últimos eventos:"]
        for e in eventos:
            salida.append(
                f"- {e.get('fecha')} | {e.get('tipo')} | {e.get('estado')} | {e.get('objetivo')}"
            )

        return "\n".join(salida)

    resultado = leer_resumen()

    if not resultado.get("ok"):
        return "Error leyendo resumen."

    resumen = resultado.get("resumen", {})

    return (
        f"Resumen de memoria:\n"
        f"Total eventos: {resumen.get('total_eventos')}\n"
        f"Por tipo: {resumen.get('por_tipo')}\n\n"
        f"Últimos eventos:\n"
        + "\n".join([
            f"- {e.get('tipo')} | {e.get('estado')} | {e.get('objetivo')}"
            for e in resumen.get('ultimos_eventos', [])
        ])
    )
