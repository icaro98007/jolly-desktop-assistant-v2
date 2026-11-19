# 🤖 JOLLY // AI-CORE v2.0 — Asistente Cyber-Pet Multimodal 100 % Local

**Jolly** es un asistente de escritorio flotante, reactivo y completamente privado diseñado para ejecutarse en hardware local sin depender de APIs en la nube. Integra **reconocimiento de voz en GPU**, **síntesis neuronal offline**, **visión artificial de pantalla en tiempo real** y **memoria persistente en PostgreSQL**, todo orquestado mediante flujos modulares en **n8n** y modelos locales en **Ollama**.

---

## ✨ Características Principales

- **🎙️ Voz Bidireccional en Tiempo Real (`F2` / `Esc`)**:
  - **STT (Speech-to-Text)**: Transcripción local ultrarrápida mediante `faster-whisper` acelerado por CUDA.
  - **TTS (Text-to-Speech)**: Síntesis de voz neuronal en español con **Piper TTS** totalmente offline y corte instantáneo de audio con la tecla `Esc`.
- **👁️ Visión Artificial de Escritorio (`F3`)**:
  - Captura de pantalla optimizada en memoria (`mss` + `Pillow`), redimensionada y codificada en Base64 para ser analizada por **`qwen2.5vl:7b`** sin guardar archivos temporales en disco.
- **🧠 Cerebro Conversacional y Memoria Persistente**:
  - Agente conversacional impulsado por **`qwen2.5:14b`** con historial de sesión y herramientas SQL (`Guardar_Nota` y `Consultar_Notas`) respaldadas en **PostgreSQL** (`jolly_db`).
- **🎭 Interfaz Cyber-Pet Reactiva**:
  - Ventana flotante sin bordes en **Tkinter** con animaciones de estado (`ACTIVO`, `ESCUCHANDO`, `PROCESANDO`, `HABLANDO`, `VISIÓN`, `ALERTA`) y cambio dinámico de expresiones faciales según la emoción devuelta por el modelo.

---

## 🏗️ Arquitectura del Sistema

```text
┌──────────────────────────────────────────────────────────────────────┐
│                     CLIENTE DE ESCRITORIO (Python)                   │
│  mascota_jolly.pyw (Tkinter UI + Faster-Whisper + Piper TTS + MSS)   │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │ HTTP POST (JSON: mensaje, session_id, imagen_base64)
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       ORQUESTACIÓN EN n8n (Docker)                   │
│                        Webhook Jolly (/webhook/jolly)                │
│                                  │                                   │
│                         [ Nodo IF: ¿Hay imagen? ]                    │
│                        /                         \                   │
│             (true) /                               \ (false)         │
│                   ▼                                 ▼                │
│   ┌───────────────────────────────┐   ┌───────────────────────────┐  │
│   │ Rama de Visión Artificial     │   │ Rama Conversacional       │  │
│   │ HTTP Request -> qwen2.5vl:7b  │   │ AI Agent -> qwen2.5:14b   │  │
│   │ Code JS (Parser JSON estricto)│   │ + Postgres Chat Memory    │  │
│   └───────────────┬───────────────┘   │ + Tools (Notas SQL)       │  │
│                   │                   └─────────────┬─────────────┘  │
│                   └────────────────┬────────────────┘                │
│                                    ▼                                 │
│                          [ Respond to Webhook ]                      │
│                      { "texto": "...", "emocion": "..." }            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Función |
| :--- | :--- | :--- |
| **Frontend / Agente Local** | Python 3.10+, Tkinter | Interfaz flotante, captura de audio/pantalla y reproducción |
| **STT (Oído)** | `faster-whisper` (CUDA) | Transcripción de voz local en GPU |
| **TTS (Voz)** | Piper TTS (`.onnx`) | Síntesis de voz neuronal local sin latencia de red |
| **Orquestación** | n8n (Self-Hosted Docker) | Enrutamiento condicional, parsing JSON y gestión de herramientas |
| **Modelos LLM / VLM** | Ollama (`qwen2.5:14b`, `qwen2.5vl:7b`) | Razonamiento conversacional y análisis visual multimodal |
| **Base de Datos** | PostgreSQL (`postgres_jolly`) | Memoria conversacional persistente y almacenamiento de notas |

---

## 📂 Estructura del Repositorio

```text
jolly-desktop-assistant-v2/
├── mascota_jolly.pyw              # Aplicación principal de escritorio (GUI, STT, TTS y Visión)
├── workflow_jolly_v2_vision.json  # Flujo completo de n8n listo para importar
├── docker-compose.example.yml     # Plantilla de contenedores para n8n y PostgreSQL
├── requirements.txt               # Dependencias de Python
├── .gitignore                     # Exclusión de modelos pesados, entornos y credenciales
└── README.md                      # Documentación técnica del proyecto
```

---

## 🚀 Instalación y Despliegue

### 1. Requisitos Previos
- **Python 3.10+** y GPU NVIDIA compatible con CUDA (probado en RTX 5060 Ti 16 GB).
- **Docker Desktop** (para ejecutar n8n y PostgreSQL).
- **Ollama** instalado y ejecutándose en el puerto `11434` con los modelos descargados:
  ```bash
  ollama pull qwen2.5:14b
  ollama pull qwen2.5vl:7b
  ```
- Binario y modelo de voz de **Piper TTS** ubicados en la carpeta local `voces/`.

### 2. Clonar e Instalar Dependencias de Python
```bash
git clone https://github.com/icaro98007/jolly-desktop-assistant-v2.git
cd jolly-desktop-assistant-v2
pip install -r requirements.txt
```

### 3. Configurar Infraestructura y Workflow en n8n
1. Copia `docker-compose.example.yml` a `docker-compose.yml`, define tus credenciales de PostgreSQL y levanta los servicios (`docker compose up -d`).
2. Accede a **n8n** (`http://localhost:6789`), crea un nuevo workflow e importa el archivo **`workflow_jolly_v2_vision.json`**.
3. Configura las credenciales de **PostgreSQL** (`host.docker.internal`, puerto `5432`, base de datos `jolly_db`) y **Ollama** (`http://host.docker.internal:11434`).
4. Guarda y activa (**Publish**) el workflow.

### 4. Ejecutar Jolly
```bash
pythonw mascota_jolly.pyw
```

---

## ⌨️ Atajos de Teclado Globales

| Atajo | Acción |
| :--- | :--- |
| **`F2`** | Iniciar o detener la grabación de voz por micrófono |
| **`F3`** | Activar / desactivar el **Modo Visión** para la siguiente consulta |
| **`Enter`** | Enviar consulta escrita desde la caja de texto |
| **`Esc`** | Interrumpir inmediatamente la reproducción de voz de Jolly |
| **`Alt + F4`** | Cerrar el asistente |

---

## 🔒 Privacidad y Seguridad
Todo el procesamiento de audio, capturas de pantalla, inferencia de lenguaje y almacenamiento de memoria ocurre **100 % en local**. Ningún dato sale hacia servidores externos.