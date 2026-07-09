import json
from plugin_registry import list_plugins, validate_plugin

resultados = []

for item in list_plugins():
    nombre = item["name"]
    validacion = validate_plugin(nombre)
    resultados.append({
        "name": nombre,
        "type": item["type"],
        "path": item["path"],
        "ok": validacion.get("ok"),
        "error": validacion.get("error", "")
    })

print(json.dumps(resultados, indent=2, ensure_ascii=False))
