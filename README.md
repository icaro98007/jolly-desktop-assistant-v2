# 🤖 JOLLY // AI-CORE v2.0 — Asistente Cyber-Pet Multimodal Local

Asistente de escritorio flotante y 100% local con capacidades de voz bidireccional (STT/TTS en GPU), visión artificial de pantalla y memoria persistente en PostgreSQL, orquestado mediante **n8n** y **Ollama**.

## 🏗️ Arquitectura del Sistema
- **Interfaz y Captura (`mascota_jolly.pyw`)**: Python 3.10 + Tkinter transparente sin bordes, captura de audio en tiempo real y captura de pantalla optimizada en memoria (`mss` + `Pillow`).
- **Oído Local (`F2` / 🎤)**: `faster-whisper` acelerado por CUDA (NVIDIA RTX 5060 Ti).
- **Voz Local (`Esc` para silenciar)**: Síntesis neuronal offline con Piper TTS.
- **Vista Local (`F3` / 👁️)**: Captura de escritorio enviada en Base64 a `qwen2.5vl:7b` vía Ollama.
- **Cerebro y Memoria (`workflow_jolly_v2.json`)**: Orquestación en **n8n** con bifurcación condicional (`If`), agente conversacional (`qwen2.5:14b`) y memoria/notas persistentes en **PostgreSQL** (`jolly_db`).

## ⌨️ Atajos Globales
- **`F2`**: Iniciar / detener grabación de voz.
- **`F3`**: Activar / desactivar Modo Visión (adjunta captura de pantalla en la siguiente consulta).
- **`Esc`**: Interrumpir inmediatamente el audio de respuesta.
- **`Alt + F4`**: Cerrar la aplicación.