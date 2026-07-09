import json
from plugin_registry import run_plugin

TEST_PARAMS = {
    "consultar_ip": {},
    "leer_archivo_definitivo": {"nombre": "config.json"},
    "listar_archivos": {},
    "btc_fetcher": {},
    "mapa_total": {},
    "enviar_alerta": {"mensaje": "Prueba automática desde plugin_tester"},
    "auditor_configuracion": {},
    "leer_archivo_simple": {"nombre": "config.json"},
    "listar_contenido_real": {}
}

with open("plugins_activos.json", "r") as f:
    activos = json.load(f)["activos"]

resultado_final = []

for plugin in activos:
    params = TEST_PARAMS.get(plugin, {})
    try:
        resultado = run_plugin(plugin, params)
        estado = "PASS" if resultado.get("ok") else "FAIL"

        result_text = str(resultado.get("result", ""))
        if len(result_text) > 500:
            result_text = result_text[:500] + "... [TRUNCADO]"

        resultado_final.append({
            "plugin": plugin,
            "estado": estado,
            "params": params,
            "detalle": {
                "ok": resultado.get("ok"),
                "error": resultado.get("error", ""),
                "result": result_text
            }
        })

    except Exception as e:
        resultado_final.append({
            "plugin": plugin,
            "estado": "ERROR",
            "params": params,
            "detalle": str(e)
        })

print(json.dumps(resultado_final, indent=2, ensure_ascii=False))
