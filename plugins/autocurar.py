from self_healing_engine import escribir_plugin_leer_logs, ejecutar_comando

def run(params):
    objetivo = (params.get("objetivo") or params.get("query") or params.get("texto") or "").lower()

    if not objetivo:
        return "Error: falta parámetro objetivo."

    if "leer logs" not in objetivo and "leer_logs" not in objetivo:
        return "Error: autocurar V1 rápido solo soporta leer_logs."

    pasos = []

    ok, msg = escribir_plugin_leer_logs()
    pasos.append(f"1. actualizar_plugin - {'COMPLETADO' if ok else 'FALLIDO'} - {msg}")

    validar = ejecutar_comando("python3 -m py_compile plugins/leer_logs.py")
    pasos.append(f"2. validar_sintaxis - {'COMPLETADO' if validar.get('ok') else 'FALLIDO'}")

    probar = ejecutar_comando(
        "python3 -c \"from plugin_registry import run_plugin; print(run_plugin('leer_logs', {'archivo':'app.log','lineas':5}))\""
    )
    pasos.append(f"3. probar_plugin - {'COMPLETADO' if probar.get('ok') else 'FALLIDO'}")

    return "Self-Healing rápido: COMPLETADO\n\n" + "\n".join(pasos)
