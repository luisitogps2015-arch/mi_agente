# Análisis inicial del proyecto para integración de CrewAI

> [!IMPORTANT]
> **Contexto histórico:** el contenido original de este documento es una fotografía
> previa a Sprint 0 y Sprint 1.1. En ese momento, el proyecto utilizaba Python 3.9
> y CrewAI no estaba instalado. El estado actual validado es Python 3.11.16,
> CrewAI 1.14.7, Docker build exitoso, `/health` HTTP 200 y `/api/status` HTTP 200.
> Las observaciones históricas deben interpretarse dentro de ese contexto. Las
> recomendaciones arquitectónicas que no dependan de versiones siguen siendo
> válidas, salvo que hayan sido superadas explícitamente.

## 1. Rama Git activa

La rama activa durante el análisis es:

```text
feature/crewai-core
```

El árbol de trabajo estaba limpio al iniciar la inspección. `HEAD`, `main` y `origin/main` apuntaban al commit `914d2c1`, con el mensaje `Backup inicial plataforma agentes PM Copilot`.

## 2. Arquitectura general del proyecto

El proyecto es una plataforma de agentes en Python con dos canales principales de entrada: una aplicación Flask con dashboard y un bot de Telegram. El flujo operativo predominante es:

```text
Telegram / Dashboard Flask
          |
          v
        app.py
          |
          v
     mcp_server.py
          |
   enrutamiento textual
          |
          v
   plugin_registry.py
      |           |
      v           v
  plugins/     skills/
```

Alrededor de ese núcleo existen tres subsistemas adicionales que todavía no forman una única arquitectura integrada:

1. Un pipeline RAG local formado por ingesta, chunking, recuperación híbrida, construcción de contexto y generación con Groq.
2. Dos aproximaciones multiagente propias: clases bajo `agents/` coordinadas por `multi_agent_router.py`, y motores funcionales coordinados por `orchestrator_engine.py`.
3. Un flujo PM independiente basado en LangGraph, dedicado al procesamiento documental y expuesto mediante un plugin.

La aplicación principal no usa de forma efectiva `MultiAgentRouter` ni `orchestrator_engine.py`. El dashboard presenta estados de RAG, planner y self-healing, pero la ejecución principal termina llamando directamente a `procesar_agente()` en `mcp_server.py`. Parte de la visualización multiagente representa estados simulados y no la ejecución real de esos motores.

## 3. Módulos principales relacionados con agentes

### Agentes orientados a objetos

- `agents/base_agent.py`: clase base y persistencia JSON del último trabajo de cada agente.
- `agents/planner_agent.py`: adaptador sobre `planner_engine.crear_plan`.
- `agents/executor_agent.py`: recibe un plan, pero todavía no lo ejecuta.
- `agents/critic_agent.py`: evaluación genérica sin lógica crítica profunda.
- `agents/reflection_agent.py`: reflexión textual fija.
- `agents/self_healing_agent.py`: respuesta fija; no realiza reparaciones.
- `agents/memory_agent.py`: adaptador para leer el resumen de memoria.
- `multi_agent_router.py`: secuencia los agentes anteriores.
- `multi_agent_router_local.py`: simulador local reducido.

### Motores funcionales

- `planner_engine.py`: planificación con Groq y contexto RAG.
- `task_decomposer.py`: conversión de planes generados por LLM en tareas JSON.
- `executor_engine.py`: creación, activación, validación y prueba de plugins.
- `critic_engine.py`: ejecución y evaluación del resultado mediante Groq.
- `reflection_engine.py`: reflexión basada en la salida del critic.
- `self_healing_engine.py`: reparación especializada del plugin `leer_logs.py`.
- `orchestrator_engine.py`: pipeline planner, decomposer, executor, critic, reflection, self-healing y memoria.
- `agent_loop.py`: bucle simple de ejecución, evaluación y reintento.
- `reasoning_engine.py`: razonamiento controlado sobre contexto RAG.

### Infraestructura relacionada

- `app.py`: entrada Flask, dashboard y Telegram.
- `mcp_server.py`: enrutamiento textual y fachada de ejecución.
- `mcp_client.py`: mapeo adicional entre texto y acciones.
- `plugin_registry.py`: descubrimiento, validación y ejecución dinámica de plugins y skills.
- `pm_langgraph.py`: grafo PM de procesamiento documental.
- `memory_manager.py`: registro de eventos y resumen operativo.
- `goal_manager.py`: persistencia y seguimiento de objetivos.

## 4. Estado actual de:

### RAG

El pipeline principal está compuesto por:

```text
document_ingestion.py
        |
        v
chunk_manager.py
        |
        v
retrieval_manager.py
        |
        v
context_builder.py
        |
        v
rag_engine.py -> Groq
```

La ingesta genera metadata y chunks. La recuperación combina BM25 y TF-IDF, normaliza puntuaciones y aplica reranking heurístico. No hay embeddings semánticos externos ni una base vectorial real. Existe además una implementación paralela más básica en `retrieval_engine.py` y `search_engine.py`.

### Plugins

Los plugins viven principalmente en `plugins/`, se descubren dinámicamente y deben exponer `run(params)`. `plugins_activos.json` declara activación, pero `plugin_registry.py` no consulta ese archivo al ejecutar: cualquier módulo de primer nivel encontrado por nombre puede ejecutarse.

Los subdirectorios con `server.py` o `manifest.json` no son descubiertos por el registry actual, porque este solo recorre archivos `.py` en el primer nivel.

### Skills

Los archivos de `skills/` son scripts Python heterogéneos. No constituyen un sistema declarativo equivalente al concepto de skills de CrewAI. El registry los carga mediante el mismo contrato de plugins. Algunos contienen efectos en el nivel del módulo, rutas rígidas o incluso contenido JavaScript guardado con extensión `.py`.

### Memoria

La memoria está fragmentada entre varias fuentes:

- `memory/events.jsonl` y `memory/summary.json`: eventos operativos.
- `agents/state/*.json`: último trabajo y contador de cada agente.
- `agente_data.db`: SQLite de herramientas y aplicación.
- `agente_memoria.db`: SQLite usado por algunos skills.
- `historial.json` y `data/historial.json`: historiales distintos.
- `proyectos/*/memoria/`: memoria específica por proyecto.
- `goals.json`: objetivos persistentes.

`memory_manager.py` implementa un registro append-only y un resumen, pero no memoria semántica ni recuperación conversacional. Además, el endpoint `/api/memory` busca `memory/events.json`, mientras el manager escribe `memory/events.jsonl`.

### Planner

`planner_engine.py` es la implementación real: usa Groq, consulta el RAG y genera planes especializados en la arquitectura de plugins. `PlannerAgent` es un adaptador funcional sobre ese motor. El modelo está fijado en código y el flujo depende de `GROQ_API_KEY`.

### Executor

`executor_engine.py` puede crear archivos de plugin, activar plugins, validar sintaxis y ejecutar pruebas. Su conjunto de acciones es limitado y usa `subprocess.run(..., shell=True)`, protegido únicamente mediante una lista básica de cadenas bloqueadas. `ExecutorAgent`, en cambio, solo confirma que recibió un plan y no llama al engine.

### Critic

Existen tres implementaciones no unificadas:

- `critic_engine.py`: evaluación con Groq.
- `agents/critic_agent.py`: placeholder genérico.
- `orchestrator_engine.py`: evaluación heurística cacheada.

LangGraph añade además un critic específico que valida la longitud del texto extraído. No comparten contrato ni criterios comunes.

### Reflection

`reflection_engine.py` genera reflexión con Groq; `ReflectionAgent` devuelve un texto genérico; y `orchestrator_engine.py` contiene otra reflexión heurística. No existe persistencia estructurada del aprendizaje ni una realimentación general al planner.

### Self-healing

`self_healing_engine.py` puede modificar y probar únicamente `plugins/leer_logs.py`. `SelfHealingAgent` no realiza una reparación real. `orchestrator_engine.py` contiene otra variante especializada del mismo caso, y existen plugins adicionales de autocuración. Es una prueba funcional específica, no un sistema general de recuperación.

### LangGraph

`pm_langgraph.py` implementa este flujo:

```text
START
  -> intake_agent
  -> document_agent
       |-- error -> delivery_agent
       `-- éxito -> critic_agent -> delivery_agent
  -> END
```

Se expone mediante `plugins/grafo_pm.py`. Es un grafo funcional para procesamiento documental PM, pero no usa checkpointer, persistencia nativa del grafo, reanudación ni retries, y no está integrado con el router multiagente general.

## 5. Archivos candidatos para integrar CrewAI

Los candidatos naturales, en orden aproximado de relevancia, son:

1. `multi_agent_router.py`: punto conceptual más directo para sustituir el encadenamiento manual por una Crew y tareas coordinadas.
2. `agents/planner_agent.py`, `agents/executor_agent.py`, `agents/critic_agent.py`, `agents/reflection_agent.py` y `agents/self_healing_agent.py`: sus roles pueden mapearse a agentes CrewAI.
3. `orchestrator_engine.py`: posible fachada estable para invocar CrewAI conservando el contrato `orquestar(objetivo)`.
4. `app.py`: punto de entrada desde el cual seleccionar ejecución directa, CrewAI o LangGraph; no debería contener las definiciones de la Crew.
5. `mcp_server.py`: posible ruta o acción nueva para exponer la orquestación CrewAI a Telegram y dashboard.
6. `plugin_registry.py`: capa existente que debería adaptarse como fuente de tools para CrewAI.
7. `rag_engine.py`, `context_builder.py` y `memory_manager.py`: servicios compartidos que pueden exponerse como herramientas o dependencias de los agentes.
8. `pm_langgraph.py`: punto de integración si se decide invocar una Crew desde un nodo o delimitar responsabilidades entre LangGraph y CrewAI.

## 6. Componentes existentes que deberían reutilizarse

- El contrato `run(params)` de plugins.
- El descubrimiento y ejecución del registry, después de reforzar activación y seguridad.
- Los plugins PM ya implementados.
- La ingesta documental, chunking y recuperación híbrida local.
- `context_builder.py` y `rag_engine.py` como servicio RAG compartido.
- La configuración y acceso existentes a Groq, centralizados en lugar de repetidos.
- `memory_manager.py`, una vez normalizados rutas y formatos.
- `goal_manager.py` para objetivos persistentes.
- Los endpoints Flask, el bot de Telegram y el dashboard.
- El estado tipado y la lógica documental de `pm_langgraph.py`.
- Las funciones existentes de OCR, PDF y DOCX.
- La estructura de artefactos bajo `proyectos/`.

## 7. Componentes que no deberían duplicarse

- Un segundo pipeline RAG sin decidir si sustituye o complementa BM25/TF-IDF.
- Una memoria propia de CrewAI paralela a todas las memorias actuales sin definir una fuente de verdad.
- Nuevas implementaciones separadas de planner, executor, critic, reflection y self-healing.
- Otra capa de tools que replique el catálogo de plugins.
- Otro router de intención textual.
- Un segundo workflow PM que compita con LangGraph por el mismo estado.
- Otro almacenamiento independiente de estados por agente.
- Clientes LLM y configuración duplicados en cada agente.
- Lógica CrewAI incrustada directamente en `app.py` o en cada plugin.

## 8. Riesgos técnicos antes de integrar CrewAI

1. La versión Python del Dockerfile es incompatible con las versiones actuales de CrewAI.
2. Existen varias orquestaciones paralelas sin una autoridad clara: `agent_loop`, router, orchestrator, LangGraph y el flujo simulado del dashboard.
3. El router actual no pasa correctamente los resultados entre todos los agentes; executor y critic reciben el objetivo en lugar del artefacto producido por la etapa anterior.
4. Algunos motores vuelven a ejecutar etapas completas, lo que puede duplicar costes, escrituras y efectos externos.
5. Los plugins pueden escribir archivos, ejecutar shell, acceder a red o enviar mensajes.
6. `shell=True` y una lista de palabras bloqueadas no constituyen un sandbox suficiente para tools autónomas.
7. La importación dinámica puede ejecutar efectos en el nivel del módulo incluso durante validación.
8. Flask, Telegram y threads comparten diccionarios y archivos sin sincronización explícita.
9. JSON, JSONL y dos bases SQLite fragmentan la persistencia y dificultan establecer una fuente de verdad.
10. Se mezclan rutas relativas, rutas bajo `/app` y `PROJECT_ROOT`.
11. `requirements.txt` no fija versiones, por lo que las reconstrucciones no son reproducibles.
12. No se identificó una suite automatizada coherente para validar el pipeline completo.
13. El dashboard puede marcar etapas como completadas aunque no haya invocado sus motores reales.
14. No hay una política general de idempotencia para reintentos de tareas con efectos.
15. El contenido documental recuperado por RAG puede introducir instrucciones hostiles o prompt injection.
16. El almacenamiento en archivos y el estado global en memoria no escalan de forma segura a múltiples workers.

## 9. Dependencias y compatibilidad técnica

### Python y Docker

El Dockerfile usa:

```dockerfile
FROM python:3.9-slim
```

Esto confirma la línea Python 3.9. El parche exacto depende del momento en que Docker resuelva esa etiqueta no fijada.

Las versiones actuales de CrewAI requieren Python `>=3.10,<3.14`. Por ello, CrewAI actual no es compatible con la imagen base del repositorio y no debería agregarse antes de actualizar y validar la versión de Python.

### Dependencias actuales

`requirements.txt` declara, sin versiones fijadas, Flask, Groq, DDGS, Tavily, pandas, Telegram, BeautifulSoup, requests, dotenv, librerías documentales/OCR y LangGraph. CrewAI no está declarado.

Riesgos de compatibilidad identificados:

- `langgraph`: no implica necesariamente un conflicto de paquetes, pero sí solapamiento de responsabilidades de orquestación.
- `groq`: CrewAI puede introducir su propia abstracción de proveedores, posiblemente mediante LiteLLM, duplicando clientes y configuración.
- `pydantic`: CrewAI depende intensamente de modelos tipados; versiones transitivas de CrewAI y LangGraph deben resolverse y fijarse conjuntamente.
- `openai` y `litellm`: no están declarados actualmente, pero pueden aparecer como dependencias transitivas de CrewAI.
- `pandas`, `requests` y `python-dotenv`: son dependencias potencialmente compartidas que deben quedar sujetas a restricciones reproducibles.
- `crewai[tools]`: añadiría un grafo de dependencias mucho mayor, incluyendo posibles herramientas de embeddings y parsers que duplicarían capacidades existentes.
- `python:slim`: ciertos extras pueden requerir ruedas binarias, compiladores o Rust, especialmente en dependencias de tokenización.

No puede confirmarse el conjunto exacto de conflictos sin resolver las dependencias en un entorno aislado. Esa validación debe hacerse después de decidir y fijar una versión concreta de CrewAI y de actualizar Python, no durante esta fase de análisis.

## 10. Clasificación de componentes

| Componente | Clasificación | Motivo |
|---|---|---|
| Entrada Flask/Telegram | Implementado | Es el flujo principal ejecutable. |
| MCP server y router textual | Implementado | Traduce texto a acciones y ejecuta plugins. |
| Plugin registry | Parcial | Ejecuta módulos, pero no aplica activación ni descubre subdirectorios. |
| Catálogo de plugins | Implementado | Existe un catálogo amplio, aunque de calidad heterogénea. |
| Skills | Prototipo | Son scripts heterogéneos tratados como plugins. |
| Ingesta documental | Implementado | Genera metadata y chunks. |
| RAG local | Implementado | Incluye BM25, TF-IDF, reranking y generación con Groq. |
| RAG vectorial semántico | Pendiente | No existen embeddings ni una base vectorial real. |
| Memoria de eventos | Parcial | Funciona, pero rutas y lectura desde dashboard no están alineadas. |
| Memoria por agente | Prototipo | Solo conserva contador, último task y último resultado. |
| Memoria semántica | Pendiente | No está implementada. |
| Goal manager | Implementado | Proporciona CRUD y seguimiento persistente. |
| Planner engine | Implementado | Usa Groq y RAG, aunque está especializado en plugins. |
| PlannerAgent | Parcial | Es un wrapper funcional del engine. |
| Task decomposer | Parcial | Depende de extraer JSON generado por el LLM. |
| Executor engine | Parcial | Tiene acciones reales, pero limitadas y con riesgos de shell. |
| ExecutorAgent | Prototipo | Solo confirma recepción del plan. |
| Critic engine | Parcial | Evalúa con LLM, pero puede relanzar la ejecución. |
| CriticAgent | Prototipo | Devuelve una evaluación genérica. |
| Reflection engine | Parcial | Genera reflexión sin aprendizaje persistente. |
| ReflectionAgent | Prototipo | Devuelve texto fijo. |
| Self-healing engine | Prototipo | Solo atiende el caso `leer_logs.py`. |
| SelfHealingAgent | Prototipo | No realiza reparación real. |
| Orchestrator engine | Prototipo | Pipeline completo pero especializado y cacheado. |
| MultiAgentRouter | Prototipo | Encadena agentes con contratos incompletos. |
| Agent loop | Parcial | Implementa evaluación y reintento simples. |
| LangGraph PM | Parcial | Grafo funcional sin persistencia ni integración general. |
| CrewAI | Pendiente | No existe dependencia, configuración ni implementación. |
| Integración CrewAI con plugins | Pendiente | Faltan adaptadores de tools. |
| Integración CrewAI con RAG | Pendiente | El servicio es reutilizable, pero no está conectado. |
| Integración CrewAI con memoria | Pendiente | Falta decidir una fuente de verdad. |
| Compatibilidad operativa CrewAI | No confirmado | La incompatibilidad de Python es conocida, pero no se resolvió el grafo de paquetes. |
| Suite automatizada de integración | No confirmado | No se encontró una suite coherente para el pipeline completo. |

## 11. Recomendación para el siguiente Sprint

### Objetivo

Construir y validar un núcleo mínimo de orquestación CrewAI que coordine Planner, Executor y Critic reutilizando los servicios existentes, sin sustituir todavía el flujo principal de producción ni LangGraph PM.

### Alcance técnico

1. Actualizar la base técnica a una versión de Python compatible con CrewAI y fijar una versión concreta del paquete base, sin incluir inicialmente `crewai[tools]`.
2. Definir una única fachada de orquestación que preserve un contrato similar a `orquestar(objetivo)` y mantenga CrewAI desacoplado de `app.py`.
3. Crear una Crew mínima con tres roles: Planner, Executor y Critic.
4. Adaptar `plugin_registry.run_plugin` como tool controlada, con lista explícita de plugins permitidos y sin habilitar acciones destructivas o shell autónomo.
5. Adaptar el RAG existente como herramienta de solo lectura para el Planner.
6. Registrar el resultado del flujo mediante `memory_manager.py`, sin activar todavía la memoria nativa de CrewAI.
7. Definir modelos de entrada y salida estructurados para evitar contratos ambiguos entre tareas.
8. Añadir pruebas aisladas del flujo mínimo con tools simuladas y una prueba de integración sin efectos externos.
9. Mantener `pm_langgraph.py` sin cambios funcionales durante el Sprint y documentar el límite entre LangGraph y CrewAI.
10. No conectar la Crew al endpoint principal ni a Telegram hasta que las pruebas demuestren ejecución determinista, control de permisos e idempotencia.

El resultado esperado del Sprint es un núcleo CrewAI mínimo, reproducible y probado, disponible detrás de una interfaz interna, sin migrar aún la operación principal del sistema.
