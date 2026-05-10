# Sistema de Rutas de Evacuación en Edificaciones Complejas

Sistema que modela edificaciones como grafos ponderados y genera rutas de evacuación óptimas desde cualquier punto hasta las salidas seguras. Permite simular emergencias, bloquear pasillos o escaleras, comparar alternativas y simular la evacuación de múltiples personas simultáneamente — todo desde una interfaz web interactiva.

---

## Tabla de contenidos

1. [Requisitos previos](#1-requisitos-previos)
2. [Instalación](#2-instalación)
3. [Ejecución](#3-ejecución)
4. [Uso de la interfaz web](#4-uso-de-la-interfaz-web)
   - [Cargar un edificio](#41-cargar-un-edificio)
   - [Bloquear nodos y conexiones](#42-bloquear-nodos-y-conexiones)
   - [Rutas de evacuación](#43-rutas-de-evacuación)
   - [Comparar rutas](#44-comparar-rutas)
   - [Ruta recomendada](#45-ruta-recomendada)
   - [Simulación de evacuación](#46-simulación-de-evacuación)
   - [Mapa del edificio](#47-mapa-del-edificio)
5. [Edificios incluidos](#5-edificios-incluidos)
6. [Estructura del proyecto](#6-estructura-del-proyecto)
7. [Arquitectura](#7-arquitectura)

---

## 1. Requisitos previos

Antes de instalar el proyecto asegúrate de tener lo siguiente:

| Requisito | Versión mínima | Cómo verificar |
|-----------|---------------|----------------|
| Python | 3.10 | `python3 --version` |
| pip | cualquiera | `pip3 --version` |
| Graphviz (sistema) | cualquiera | `dot -V` |

### Instalar Graphviz

Graphviz es necesario para generar los mapas visuales del edificio.

**macOS (Homebrew):**
```bash
brew install graphviz
```

**Ubuntu / Debian:**
```bash
sudo apt-get install graphviz
```

**Windows:**
Descarga el instalador desde [graphviz.org/download](https://graphviz.org/download/) y asegúrate de agregar `dot` al PATH del sistema.

---

## 2. Instalación

### Paso 1 — Clona o descarga el repositorio

```bash
git clone <url-del-repositorio>
cd Sistema-de-rutas-de-evacuaci-n-en-edificaciones-complejas
```

O descarga el ZIP desde GitHub y descomprímelo.

### Paso 2 — Instala las dependencias de Python

```bash
pip3 install -r requirements.txt
```

> **Nota en sistemas modernos (Ubuntu 23+, macOS con Python del sistema):** si `pip3` rechaza la instalación por PEP 668, agrega la bandera `--break-system-packages`:
> ```bash
> pip3 install -r requirements.txt --break-system-packages
> ```

Las dependencias son:
- `flask` — servidor web
- `graphviz` — generación de mapas PNG

---

## 3. Ejecución

Desde la raíz del proyecto ejecuta:

```bash
python3 web_app.py
```

Verás este mensaje en la terminal:

```
╔══════════════════════════════════════════════════════╗
║    SISTEMA DE RUTAS DE EVACUACIÓN — Interfaz Web    ║
╚══════════════════════════════════════════════════════╝

  Servidor en:  http://localhost:5000
  Detener con:  Ctrl+C
```

Abre tu navegador en **http://localhost:5000** y listo.

Para detener el servidor usa `Ctrl + C` en la terminal.

---

## 4. Uso de la interfaz web

### 4.1 Cargar un edificio

Al abrir la aplicación lo primero que verás es la tarjeta de **Configuración** en la parte superior.

1. Selecciona un edificio del menú desplegable (se muestran todos los archivos JSON de la carpeta `data/`).
2. Elige el modo:
   - **Normal** — el edificio carga sin ningún bloqueo.
   - **Emergencia** — se aplican bloqueos aleatorios al iniciar según la intensidad elegida.
3. Si elegiste Emergencia, selecciona la **intensidad**:
   - `leve` — 1 nodo y 1 conexión bloqueados.
   - `moderada` — 2 nodos y 2 conexiones bloqueados.
   - `crítica` — 3 nodos y 4 conexiones bloqueados.
4. Haz clic en **Cargar edificio**.

Una vez cargado aparecerá un panel lateral izquierdo con el selector de ubicación y los controles de bloqueo.

---

### 4.2 Bloquear nodos y conexiones

En el panel lateral puedes simular obstrucciones manualmente:

**Bloquear un nodo (habitación, pasillo, escalera):**
1. Selecciona el nodo en el selector "Bloquear nodo".
2. Haz clic en **Bloquear nodo**.

**Bloquear una conexión (arista entre dos nodos):**
1. En la sección "Bloquear conexión" selecciona el nodo origen y el nodo destino.
2. Haz clic en **Bloquear conexión**.

Los bloqueos activos aparecen como chips de color rojo en la sección "Bloqueos activos". Cada chip tiene una **×** para eliminarlo individualmente.

También puedes usar el botón **Restablecer todo** para quitar todos los bloqueos a la vez.

---

### 4.3 Rutas de evacuación

Pestaña: **Rutas**

1. Selecciona tu ubicación actual en el selector del panel lateral.
2. Haz clic en **Buscar rutas**.
3. Se mostrarán todas las rutas posibles ordenadas de menor a mayor costo, cada una con:
   - Los nodos del camino representados como chips de color según su tipo.
   - El costo total (suma de pesos de las aristas).
   - El número de pasos (aristas recorridas).
   - La salida a la que llega.
4. Al hacer clic en una ruta se genera automáticamente el mapa visual con esa ruta resaltada.

**Colores de los nodos:**
| Color | Tipo |
|-------|------|
| Azul | Habitación / sala |
| Amarillo | Pasillo |
| Morado | Escalera |
| Verde | Salida |
| Rojo tachado | Bloqueado |

---

### 4.4 Comparar rutas

Pestaña: **Comparar**

1. Selecciona tu ubicación y haz clic en **Comparar rutas**.
2. Se muestra una tabla con todas las rutas y sus métricas:
   - Costo total
   - Número de pasos
   - Cantidad de escaleras en el camino
   - Cantidad de pasillos en el camino
   - Eficiencia (costo / pasos)
   - Salida de destino

Útil para decidir qué ruta priorizar según las circunstancias (ej. personas con movilidad reducida evitarán escaleras).

---

### 4.5 Ruta recomendada

Pestaña: **Recomendar**

1. Selecciona tu ubicación.
2. Elige el criterio de recomendación:
   - **Costo mínimo** — la ruta con menor peso total (camino más rápido).
   - **Menos pasos** — la ruta con menos tramos (más directa).
3. Haz clic en **Recomendar**.

Se mostrará la ruta óptima según el criterio y, si hay más de una ruta disponible, una comparación de todas ellas por cada criterio.

---

### 4.6 Simulación de evacuación

Pestaña: **Simular**

Permite evacuar a varias personas al mismo tiempo y ver cómo se mueven paso a paso.

1. En la sección "Agregar persona" completa:
   - **ID** — identificador único (ej. `P1`).
   - **Nombre** — nombre de la persona.
   - **Ubicación** — nodo de inicio.
2. Haz clic en **+ Agregar** (puedes agregar tantas personas como quieras).
3. Selecciona el **criterio de asignación de rutas** (costo o pasos).
4. Haz clic en **Iniciar simulación**.

La simulación se reproduce automáticamente paso a paso (una tabla animada). Cada fila representa un paso de tiempo:
- La columna de cada persona muestra su posición actual.
- Los nodos con 2 o más personas simultáneas se marcan como **CONGESTIÓN**.
- Cuando una persona llega a una salida aparece **EVACUADO**.

Al terminar se muestra el resumen:
- Tiempo de evacuación individual.
- Nodos y conexiones con mayor congestión durante la simulación.

---

### 4.7 Mapa del edificio

Pestaña: **Mapa**

1. Haz clic en **Generar mapa** para ver el estado actual del edificio (bloqueos incluidos).
2. También puedes hacer clic en cualquier ruta desde la pestaña Rutas para generar el mapa con esa ruta resaltada.

El mapa se genera con Graphviz y muestra:
- Todos los nodos con su tipo (forma y color).
- Las conexiones con su peso.
- Los nodos bloqueados en rojo.
- La ruta seleccionada resaltada en naranja.

> Los mapas generados se guardan en la carpeta `output/maps/` con una marca de tiempo.

---

## 5. Edificios incluidos

El proyecto incluye tres edificios de ejemplo en la carpeta `data/`:

| Archivo | Edificio | Pisos | Nodos | Conexiones |
|---------|----------|-------|-------|------------|
| `building.json` | Edificio Académico Central | 2 | 16 | 16 |
| `hospital.json` | Hospital General | 3 | 19 | 20 |
| `centro_comercial.json` | Centro Comercial Plaza Mayor | 2 | 16 | 16 |

### Agregar un edificio propio

Crea un archivo `.json` en la carpeta `data/` con este formato:

```json
{
  "building": {
    "name": "Nombre del Edificio",
    "levels": 2
  },
  "nodes": [
    { "id": "N1", "label": "Recepción",  "type": "room",      "level": 1 },
    { "id": "N2", "label": "Pasillo 1",  "type": "hallway",   "level": 1 },
    { "id": "N3", "label": "Escalera 1", "type": "staircase", "level": 1 },
    { "id": "S1", "label": "Salida 1",   "type": "exit",      "level": 1 }
  ],
  "edges": [
    { "from": "N1", "to": "N2", "weight": 2 },
    { "from": "N2", "to": "N3", "weight": 3 },
    { "from": "N3", "to": "S1", "weight": 1 }
  ]
}
```

**Tipos de nodo válidos:** `room`, `hallway`, `staircase`, `exit`

La aplicación detecta el archivo automáticamente al recargar la página.

---

## 6. Estructura del proyecto

```
.
├── web_app.py                   # Punto de entrada — inicia el servidor web
├── requirements.txt             # Dependencias Python
├── data/                        # Edificios en formato JSON
│   ├── building.json
│   ├── hospital.json
│   └── centro_comercial.json
├── domain/                      # Entidades del dominio (grafo, nodos, aristas, estado)
│   ├── node.py
│   ├── edge.py
│   ├── graph.py
│   └── evacuation_state.py
├── application/                 # Casos de uso (lógica de negocio)
│   ├── find_routes.py           # DFS con backtracking — enumera todas las rutas
│   ├── recommend_route.py       # Selecciona la mejor ruta según criterio
│   ├── compare_routes.py        # Métricas comparativas entre rutas
│   ├── block_path.py            # Bloquear/desbloquear nodos y aristas
│   ├── simulate_evacuation.py   # Simulación paso a paso de múltiples personas
│   └── emergency_mode.py        # Bloqueos aleatorios para modo emergencia
├── infrastructure/
│   ├── persistence/
│   │   └── building_loader.py   # Carga el JSON y construye el grafo
│   └── visualization/
│       └── graph_plotter.py     # Genera el mapa PNG con Graphviz
├── interface/
│   └── web.py                   # API REST con Flask (todos los endpoints)
├── templates/
│   └── index.html               # Interfaz web (Bootstrap 5, JavaScript)
├── static/                      # Archivos estáticos (CSS/JS adicionales si los hay)
└── output/
    └── maps/                    # Mapas PNG generados
```

---

## 7. Arquitectura

El proyecto sigue **arquitectura limpia por capas**:

```
Interfaz web (Flask / HTML+JS)
        ↓ llamadas HTTP
Aplicación (casos de uso)
        ↓ usa
Dominio (entidades puras: grafo, nodos, aristas, estado)
        ↑ construye
Infraestructura (carga JSON, genera imágenes)
```

**Algoritmo central — DFS con backtracking** (`application/find_routes.py`):
- Explora todos los caminos posibles desde el nodo de inicio hasta cada salida.
- Evita ciclos con un conjunto `visited`.
- Considera bloqueados: si un nodo o arista está en `EvacuationState`, no se atraviesa.
- Retorna todas las rutas válidas ordenadas por costo ascendente.

**Estado de evacuación** (`domain/evacuation_state.py`):
- Mantiene dos conjuntos en memoria: `blocked_nodes` y `blocked_edges`.
- No modifica el grafo; el DFS lo consulta en cada paso.
- Se puede resetear sin recargar el edificio.
