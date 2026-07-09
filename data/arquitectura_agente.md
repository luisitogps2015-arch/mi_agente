# Arquitectura Agente IA

## Sprint 1 - Agent Loop

Estado: COMPLETADO

### Arquitectura

Telegram
↓
app.py
↓
mcp_server.py
↓
agent_loop.py
↓
mcp_client.py
↓
plugin_registry.py
↓
plugins

### Pruebas exitosas

* /agente listar archivos ✅
* /agente leer archivo config ✅
* /agente enviar alerta de prueba ✅

### Mejoras implementadas

* PROJECT_ROOT centralizado
* Compatibilidad Docker / Host
* Plugins corregidos
* Agent Loop integrado a Telegram

## Próximo Sprint

1. Chunking
2. Context Builder
3. BM25
4. Reranking
5. Memoria contextual
6. Autocuración segura
