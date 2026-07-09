import os
import json
import importlib.util
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")


def _load_module(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def list_plugins():
    items = []

    for folder, tipo in [(PLUGINS_DIR, "plugin"), (SKILLS_DIR, "skill")]:
        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                path = os.path.join(folder, filename)
                items.append({
                    "name": filename[:-3],
                    "type": tipo,
                    "path": path
                })

    return items


def validate_plugin(name):
    for item in list_plugins():
        if item["name"] == name:
            try:
                module = _load_module(item["path"])
                if hasattr(module, "run") and callable(module.run):
                    return {"ok": True, "name": name, "type": item["type"]}
                return {"ok": False, "name": name, "error": "No tiene función run(params)"}
            except Exception as e:
                return {"ok": False, "name": name, "error": str(e)}

    return {"ok": False, "name": name, "error": "No encontrado"}


def run_plugin(name, params=None):
    params = params or {}

    for item in list_plugins():
        if item["name"] == name:
            try:
                module = _load_module(item["path"])
                if not hasattr(module, "run"):
                    return {"ok": False, "error": "El plugin no tiene run(params)"}

                result = module.run(params)
                return {
                    "ok": True,
                    "name": name,
                    "type": item["type"],
                    "result": result
                }

            except Exception as e:
                return {
                    "ok": False,
                    "name": name,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }

    return {"ok": False, "name": name, "error": "Plugin no encontrado"}


if __name__ == "__main__":
    print(json.dumps({
        "plugins": list_plugins()
    }, indent=2, ensure_ascii=False))
