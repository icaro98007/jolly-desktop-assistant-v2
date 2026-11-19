import os
import sys
import site

# Registrar rutas DLL de NVIDIA CUDA/cuDNN para Faster-Whisper en Windows
for sp in site.getsitepackages():
    for sub in ("nvidia\\cublas\\bin", "nvidia\\cudnn\\bin"):
        ruta_dll = os.path.join(sp, sub)
        if os.path.isdir(ruta_dll):
            os.environ["PATH"] = ruta_dll + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(ruta_dll)

import tkinter as tk
import requests
import threading
import subprocess
import math
import time
import random
import wave
import tempfile
import numpy as np
import io
import base64
try:
    import mss
    from PIL import Image
    VISION_DISPONIBLE = True
except ImportError:
    VISION_DISPONIBLE = False

try:
    import keyboard
    KEYBOARD_DISPONIBLE = True
except ImportError:
    KEYBOARD_DISPONIBLE = False

# Dependencias opcionales de Voz Neuronal y Micrófono GPU
try:
    import sounddevice as sd
    AUDIO_DISPONIBLE = True
except ImportError:
    AUDIO_DISPONIBLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_DISPONIBLE = True
except ImportError:
    WHISPER_DISPONIBLE = False

try:
    from piper.voice import PiperVoice
    PIPER_DISPONIBLE = True
except ImportError:
    PIPER_DISPONIBLE = False

# ==========================================
# CONFIGURACIÓN PRINCIPAL
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBHOOK_URL = "http://localhost:6789/webhook/jolly"
SESSION_ID = "jolly_desktop"
COLOR_FONDO_TRANSPARENTE = "#010101"
RUTA_VOZ_PIPER = os.path.join(BASE_DIR, "voces", "es_MX-claude-high.onnx")

TEMAS_EMOCION = {
    "feliz": {
        "neon": "#00F5D4",
        "secundario": "#00BBF9",
        "visor": "#071318",
        "chasis": "#121824",
        "estado": "● EN LÍNEA"
    },
    "pensando": {
        "neon": "#FBBF24",
        "secundario": "#F59E0B",
        "visor": "#161208",
        "chasis": "#1A1822",
        "estado": "◌ PROCESANDO..."
    },
    "sorprendido": {
        "neon": "#FF2A85",
        "secundario": "#9B5DE5",
        "visor": "#180814",
        "chasis": "#1E1424",
        "estado": "⚡ ALERTA"
    },
    "cansado": {
        "neon": "#64748B",
        "secundario": "#475569",
        "visor": "#0B0E14",
        "chasis": "#11141C",
        "estado": "☾ REPOSO"
    },
    "neutral": {
        "neon": "#38BDF8",
        "secundario": "#818CF8",
        "visor": "#09111E",
        "chasis": "#131926",
        "estado": "● ACTIVO"
    },
    "escuchando": {
        "neon": "#F43F5E",
        "secundario": "#FB7185",
        "visor": "#1F0910",
        "chasis": "#22121A",
        "estado": "🎙️ ESCUCHANDO..."
    }
}


class JollyCyberPet:
    def __init__(self, root):
        self.root = root
        self.root.title("Jolly Cyber-Pet")
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", COLOR_FONDO_TRANSPARENTE)
        self.root.configure(bg=COLOR_FONDO_TRANSPARENTE)

        # Posición inicial (esquina inferior derecha)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.win_w = 340
        self.win_h = 415
        pos_x = screen_w - self.win_w - 35
        pos_y = screen_h - self.win_h - 65
        self.root.geometry(f"{self.win_w}x{self.win_h}+{pos_x}+{pos_y}")

        # Variables de estado y animación
        self.emocion = "feliz"
        self.hablando = False
        self.grabando = False
        self.voz_activa = True
        self.modo_vision = False
        self.cancelar_audio = False
        self.ultimo_f2 = 0.0
        self.proc_voz = None
        self.tiempo = 0.0
        self.parpadeo = False
        self.proximo_parpadeo = time.time() + 3.0
        self.drag_x = 0
        self.drag_y = 0

        # Motores de IA de Audio
        self.whisper_model = None
        self.piper_voice = None
        self.audio_frames = []
        self.stream_audio = None
        self.sample_rate = 16000

        # Canvas principal transparente
        self.canvas = tk.Canvas(
            self.root,
            width=self.win_w,
            height=220,
            bg=COLOR_FONDO_TRANSPARENTE,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.TOP)

        # Eventos de arrastre y menú contextual
        self.canvas.bind("<ButtonPress-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.mover_ventana)
        self.canvas.bind("<Button-3>", self.mostrar_menu)

        # Panel HUD de diálogo y entrada
        self.construir_hud()

        # Inicializar motores de voz y oído en segundo plano
        threading.Thread(target=self.cargar_motores_audio, daemon=True).start()

        # Saludo inicial
        self.mostrar_respuesta(
            "¡Sistemas v2.0 en línea! Pulsa 🎤 o [F2] para hablar, [Esc] para silenciar.",
            "feliz",
            hablar=False
        )

        # Bucle de animación a ~30 FPS
        self.animar()

    def cargar_motores_audio(self):
        if PIPER_DISPONIBLE and os.path.exists(RUTA_VOZ_PIPER):
            try:
                self.piper_voice = PiperVoice.load(RUTA_VOZ_PIPER)
            except Exception:
                self.piper_voice = None

        if WHISPER_DISPONIBLE:
            try:
                self.whisper_model = WhisperModel("small", device="cuda", compute_type="float16")
            except Exception:
                try:
                    self.whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
                except Exception:
                    self.whisper_model = None

    def construir_hud(self):
        self.hud_frame = tk.Frame(
            self.root,
            bg="#0B101B",
            highlightbackground="#00F5D4",
            highlightthickness=2,
            padx=10,
            pady=8
        )
        self.hud_frame.pack(fill=tk.X, padx=12, pady=(0, 6))

        # Barra superior del HUD
        top_bar = tk.Frame(self.hud_frame, bg="#0B101B")
        top_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_nombre = tk.Label(
            top_bar,
            text="JOLLY // AI-CORE v2.0",
            font=("Consolas", 8, "bold"),
            fg="#94A3B8",
            bg="#0B101B"
        )
        self.lbl_nombre.pack(side=tk.LEFT)

        self.lbl_estado = tk.Label(
            top_bar,
            text="● EN LÍNEA",
            font=("Consolas", 8, "bold"),
            fg="#00F5D4",
            bg="#0B101B"
        )
        self.lbl_estado.pack(side=tk.RIGHT)

        # Contenedor desplazable de respuesta (mantiene fijo el input abajo)
        texto_container = tk.Frame(self.hud_frame, bg="#0B101B")
        texto_container.pack(fill=tk.X, pady=(2, 8))

        self.scroll_texto = tk.Scrollbar(
            texto_container,
            orient=tk.VERTICAL,
            bg="#151E2E",
            troughcolor="#0B101B",
            activebackground="#00F5D4",
            width=8,
            relief=tk.FLAT
        )
        self.scroll_texto.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_respuesta = tk.Text(
            texto_container,
            height=4,
            font=("Segoe UI", 9),
            fg="#F1F5F9",
            bg="#0B101B",
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=2,
            pady=2,
            yscrollcommand=self.scroll_texto.set,
            state=tk.DISABLED,
            cursor="arrow"
        )
        self.txt_respuesta.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.scroll_texto.config(command=self.txt_respuesta.yview)

        # Caja de entrada + Botón micrófono + Botón enviar
        input_row = tk.Frame(self.hud_frame, bg="#151E2E", padx=4, pady=3)
        input_row.pack(fill=tk.X)

        self.entry = tk.Entry(
            input_row,
            font=("Segoe UI", 9),
            bg="#151E2E",
            fg="#FFFFFF",
            insertbackground="#00F5D4",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))

        # Atajos de teclado
        self.entry.bind("<Return>", self.enviar_mensaje)
        # F2 gestionado por hotkey global
        # Esc gestionado por hotkey global
        if KEYBOARD_DISPONIBLE:
            try:
                keyboard.add_hotkey("f2", lambda: self.root.after(0, self.alternar_grabacion))
                keyboard.add_hotkey("f3", lambda: self.root.after(0, self.alternar_vision))
                keyboard.add_hotkey("esc", lambda: self.root.after(0, self.detener_audio))
            except Exception:
                pass
        self.root.bind("<Alt-F4>", lambda e: self.cerrar_aplicacion())

        self.btn_vision = tk.Button(
            input_row,
            text="👁️",
            font=("Segoe UI", 9),
            bg="#1E293B",
            fg="#94A3B8",
            activebackground="#00BBF9",
            activeforeground="#061018",
            relief=tk.FLAT,
            cursor="hand2",
            padx=5,
            command=self.alternar_vision
        )
        self.btn_vision.pack(side=tk.RIGHT, padx=(2, 2))

        self.btn_mic = tk.Button(
            input_row,
            text="🎤",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#00F5D4",
            activebackground="#F43F5E",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            cursor="hand2",
            padx=6,
            command=self.alternar_grabacion
        )
        self.btn_mic.pack(side=tk.RIGHT, padx=(2, 3))

        self.btn_enviar = tk.Button(
            input_row,
            text="➤",
            font=("Segoe UI", 9, "bold"),
            bg="#00F5D4",
            fg="#061018",
            activebackground="#00BBF9",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            command=self.enviar_mensaje
        )
        self.btn_enviar.pack(side=tk.RIGHT)

    def iniciar_arrastre(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def mover_ventana(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_x)
        y = self.root.winfo_y() + (event.y - self.drag_y)
        self.root.geometry(f"+{x}+{y}")

    def mostrar_menu(self, event):
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#0F172A",
            fg="#F8FAFC",
            activebackground="#00F5D4",
            activeforeground="#061018"
        )
        estado_voz = "Silenciar voz" if self.voz_activa else "Activar voz"
        menu.add_command(label=f"🔊 {estado_voz}", command=self.alternar_voz)
        menu.add_command(label="🔇 Callar ahora [Esc]", command=self.detener_audio)
        menu.add_separator()
        menu.add_command(label="✕ Cerrar a Jolly [Alt+F4]", command=self.cerrar_aplicacion)
        menu.tk_popup(event.x_root, event.y_root)

    def cerrar_aplicacion(self):
        if KEYBOARD_DISPONIBLE:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        self.voz_activa = False
        self.grabando = False
        self.detener_audio()
        if self.stream_audio:
            try:
                self.stream_audio.stop()
                self.stream_audio.close()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

    def detener_audio(self):
        self.cancelar_audio = True
        self.hablando = False
        if self.proc_voz is not None:
            try:
                self.proc_voz.kill()
            except Exception:
                pass
            self.proc_voz = None
        if AUDIO_DISPONIBLE:
            try:
                sd.stop()
            except Exception:
                pass
        self.root.after(0, lambda: self.aplicar_tema_hud(self.emocion))

    def alternar_vision(self):
        if not VISION_DISPONIBLE:
            self.mostrar_respuesta("Faltan librerías de visión (mss / pillow).", "sorprendido", hablar=False)
            return
        self.modo_vision = not self.modo_vision
        if self.modo_vision:
            self.btn_vision.configure(bg="#00BBF9", fg="#061018")
            self.aplicar_tema_hud("neutral", "👁️ VISIÓN LISTA")
            self.actualizar_texto_hud("👁️ Modo Visión activado: tu próxima pregunta incluirá una captura de pantalla.")
        else:
            self.btn_vision.configure(bg="#1E293B", fg="#94A3B8")
            self.aplicar_tema_hud(self.emocion)

    def capturar_pantalla_base64(self):
        if not VISION_DISPONIBLE:
            return None
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                # Redimensionar a máximo 1280px de ancho para transferencia ultrarrápida
                max_w = 1280
                if img.width > max_w:
                    ratio = max_w / float(img.width)
                    new_h = int(float(img.height) * ratio)
                    img = img.resize((max_w, new_h), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=82)
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception:
            return None

    def alternar_voz(self):
        self.voz_activa = not self.voz_activa
        if not self.voz_activa:
            self.detener_audio()

    # ==========================================
    # CAPTURA Y TRANSCRIPCIÓN DE VOZ (GPU STT)
    # ==========================================
    def alternar_grabacion(self):
        ahora = time.time()
        if ahora - self.ultimo_f2 < 0.45:
            return
        self.ultimo_f2 = ahora
        if not AUDIO_DISPONIBLE or not WHISPER_DISPONIBLE:
            self.mostrar_respuesta("Faltan librerías de audio (sounddevice / faster-whisper).", "sorprendido", hablar=False)
            return

        if not self.grabando:
            self.iniciar_grabacion()
        else:
            self.detener_y_transcribir()

    def iniciar_grabacion(self):
        self.detener_audio()
        if self.whisper_model is None:
            self.mostrar_respuesta("Cargando modelo Whisper en GPU, intenta en 2 segundos...", "pensando", hablar=False)
            return

        self.grabando = True
        self.audio_frames = []
        self.emocion = "escuchando"
        self.aplicar_tema_hud("escuchando")
        self.btn_mic.configure(bg="#F43F5E", fg="#FFFFFF", text="⏹")
        self.actualizar_texto_hud("Escuchando... habla ahora y pulsa ⏹ o [F2] al terminar.")

        def callback_audio(indata, frames, time_info, status):
            if self.grabando:
                self.audio_frames.append(indata.copy())

        try:
            self.stream_audio = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=4096,
                latency="high",
                callback=callback_audio
            )
            self.stream_audio.start()
        except Exception as e:
            self.grabando = False
            self.btn_mic.configure(bg="#1E293B", fg="#00F5D4", text="🎤")
            self.mostrar_respuesta(f"Error de micrófono: {str(e)[:50]}", "sorprendido", hablar=False)

    def detener_y_transcribir(self):
        self.grabando = False
        self.btn_mic.configure(bg="#1E293B", fg="#00F5D4", text="🎤")

        if self.stream_audio:
            try:
                self.stream_audio.stop()
                self.stream_audio.close()
            except Exception:
                pass
            self.stream_audio = None

        if not self.audio_frames:
            self.mostrar_respuesta("No detecté audio del micrófono.", "neutral", hablar=False)
            return

        self.emocion = "pensando"
        self.aplicar_tema_hud("pensando", "◌ TRANSCRIBIENDO...")
        self.actualizar_texto_hud("Transcribiendo voz en GPU...")

        frames_copia = list(self.audio_frames)
        threading.Thread(target=self.procesar_audio_whisper, args=(frames_copia,), daemon=True).start()

    def procesar_audio_whisper(self, frames):
        tmp_path = None
        try:
            audio_np = np.concatenate(frames, axis=0)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_np.tobytes())

            segments, _ = self.whisper_model.transcribe(
                tmp_path,
                language="es",
                beam_size=5,
                vad_filter=True
            )
            texto_transcrito = " ".join(seg.text.strip() for seg in segments).strip()

            if not texto_transcrito:
                self.root.after(0, lambda: self.mostrar_respuesta("No logré entender el audio, intenta de nuevo.", "neutral", hablar=False))
                return

            self.root.after(0, lambda: self.enviar_texto_transcrito(texto_transcrito))
        except Exception as e:
            self.root.after(0, lambda: self.mostrar_respuesta(f"Error STT: {str(e)[:55]}", "sorprendido", hablar=False))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def enviar_texto_transcrito(self, texto):
        img_b64 = None
        if self.modo_vision:
            img_b64 = self.capturar_pantalla_base64()
            self.modo_vision = False
            self.btn_vision.configure(bg="#1E293B", fg="#94A3B8")
            self.actualizar_texto_hud(f"Tú [👁️]: \"{texto}\"\nAnalizando pantalla en GPU...")
        else:
            self.actualizar_texto_hud(f"Tú: \"{texto}\"\nProcesando en núcleo local...")
        self.aplicar_tema_hud("pensando")
        threading.Thread(target=self.consultar_n8n, args=(texto, img_b64), daemon=True).start()

    # ==========================================
    # RENDERIZADO VISUAL DEL ROBOT
    # ==========================================
    def calcular_mirada(self, cx, cy):
        try:
            mx = self.root.winfo_pointerx() - self.root.winfo_rootx()
            my = self.root.winfo_pointery() - self.root.winfo_rooty()
            dx = max(-6.0, min(6.0, (mx - cx) * 0.03))
            dy = max(-4.0, min(4.0, (my - cy) * 0.03))
            return dx, dy
        except Exception:
            return 0.0, 0.0

    def dibujar_robot(self):
        self.canvas.delete("all")
        tema = TEMAS_EMOCION.get(self.emocion, TEMAS_EMOCION["neutral"])
        neon = tema["neon"]
        sec = tema["secundario"]
        visor_bg = tema["visor"]
        chasis = tema["chasis"]

        cx = self.win_w // 2
        flote_y = math.sin(self.tiempo * 2.4) * 6.5
        cy = 115 + flote_y

        sombra_escala = 1.0 - (flote_y / 40.0)
        sw = 52 * sombra_escala
        self.canvas.create_oval(
            cx - sw, 198, cx + sw, 208,
            fill="#0A121E", outline=neon, width=1
        )

        vel_pulso = 9.0 if self.grabando else 3.5
        pulso = math.sin(self.tiempo * vel_pulso) * (6 if self.grabando else 4)
        r_aura = 74 + pulso
        self.canvas.create_oval(
            cx - r_aura, cy - r_aura, cx + r_aura, cy + r_aura,
            outline=sec, width=1.5 if self.grabando else 1, dash=(4, 4)
        )

        llama_h = 10 + abs(math.sin(self.tiempo * 12)) * 7
        self.canvas.create_polygon(
            cx - 16, cy + 56,
            cx + 16, cy + 56,
            cx, cy + 56 + llama_h,
            fill=neon, outline=""
        )

        inclinacion = -6 if self.emocion in ("feliz", "escuchando") else (8 if self.emocion == "cansado" else 0)
        self.canvas.create_polygon(
            cx - 58, cy - 18,
            cx - 76, cy - 46 + inclinacion,
            cx - 42, cy - 42,
            fill=chasis, outline=neon, width=2
        )
        self.canvas.create_polygon(
            cx + 58, cy - 18,
            cx + 76, cy - 46 + inclinacion,
            cx + 42, cy - 42,
            fill=chasis, outline=neon, width=2
        )

        self.canvas.create_line(cx, cy - 58, cx, cy - 82, fill=neon, width=2.5)
        self.canvas.create_oval(cx - 6, cy - 90, cx + 6, cy - 78, fill=neon, outline="#FFFFFF", width=1)

        self.canvas.create_oval(
            cx - 64, cy - 58, cx + 64, cy + 58,
            fill=chasis, outline=neon, width=2.5
        )
        self.canvas.create_rectangle(cx - 70, cy - 14, cx - 60, cy + 16, fill=sec, outline=neon, width=1.5)
        self.canvas.create_rectangle(cx + 60, cy - 14, cx + 70, cy + 16, fill=sec, outline=neon, width=1.5)

        self.canvas.create_oval(
            cx - 50, cy - 36, cx + 50, cy + 36,
            fill=visor_bg, outline=sec, width=2
        )
        self.canvas.create_arc(
            cx - 42, cy - 28, cx + 10, cy + 10,
            start=110, extent=55, style=tk.ARC, outline="#FFFFFF", width=1.5
        )

        dx, dy = self.calcular_mirada(cx, cy)
        ojo_izq_x = cx - 20 + dx
        ojo_der_x = cx + 20 + dx
        ojo_y = cy - 4 + dy

        if self.parpadeo or self.emocion == "cansado":
            self.canvas.create_line(ojo_izq_x - 10, ojo_y, ojo_izq_x + 10, ojo_y, fill=neon, width=3, capstyle=tk.ROUND)
            self.canvas.create_line(ojo_der_x - 10, ojo_y, ojo_der_x + 10, ojo_y, fill=neon, width=3, capstyle=tk.ROUND)
        elif self.emocion == "feliz":
            self.canvas.create_arc(ojo_izq_x - 11, ojo_y - 8, ojo_izq_x + 11, ojo_y + 10, start=0, extent=180, style=tk.ARC, outline=neon, width=3.5)
            self.canvas.create_arc(ojo_der_x - 11, ojo_y - 8, ojo_der_x + 11, ojo_y + 10, start=0, extent=180, style=tk.ARC, outline=neon, width=3.5)
        elif self.emocion in ("sorprendido", "escuchando"):
            self.canvas.create_oval(ojo_izq_x - 11, ojo_y - 11, ojo_izq_x + 11, ojo_y + 11, outline=neon, width=3)
            self.canvas.create_oval(ojo_izq_x - 4, ojo_y - 4, ojo_izq_x + 4, ojo_y + 4, fill="#FFFFFF", outline="")
            self.canvas.create_oval(ojo_der_x - 11, ojo_y - 11, ojo_der_x + 11, ojo_y + 11, outline=neon, width=3)
            self.canvas.create_oval(ojo_der_x - 4, ojo_y - 4, ojo_der_x + 4, ojo_y + 4, fill="#FFFFFF", outline="")
        elif self.emocion == "pensando":
            self.canvas.create_oval(ojo_izq_x - 8, ojo_y - 8, ojo_izq_x + 8, ojo_y + 8, fill=neon, outline="")
            self.canvas.create_rectangle(ojo_der_x - 10, ojo_y - 3, ojo_der_x + 10, ojo_y + 3, fill=neon, outline="")
        else:
            self.canvas.create_oval(ojo_izq_x - 9, ojo_y - 11, ojo_izq_x + 9, ojo_y + 11, fill=neon, outline="")
            self.canvas.create_oval(ojo_izq_x - 3, ojo_y - 6, ojo_izq_x + 2, ojo_y - 1, fill="#FFFFFF", outline="")
            self.canvas.create_oval(ojo_der_x - 9, ojo_y - 11, ojo_der_x + 9, ojo_y + 11, fill=neon, outline="")
            self.canvas.create_oval(ojo_der_x - 3, ojo_y - 6, ojo_der_x + 2, ojo_y - 1, fill="#FFFFFF", outline="")

        if self.emocion == "feliz":
            self.canvas.create_oval(cx - 38, cy + 8, cx - 26, cy + 14, fill=sec, outline="")
            self.canvas.create_oval(cx + 26, cy + 8, cx + 38, cy + 14, fill=sec, outline="")

        boca_y = cy + 18 + dy * 0.5
        if self.hablando or self.grabando:
            for i, offset_x in enumerate([-12, -6, 0, 6, 12]):
                amp = abs(math.sin(self.tiempo * 18 + i * 1.3)) * 8 + 2
                self.canvas.create_line(
                    cx + offset_x, boca_y - amp,
                    cx + offset_x, boca_y + amp,
                    fill=neon, width=2.5, capstyle=tk.ROUND
                )
        elif self.emocion == "feliz":
            self.canvas.create_arc(cx - 12, boca_y - 6, cx + 12, boca_y + 8, start=190, extent=160, style=tk.ARC, outline=neon, width=2.5)
        elif self.emocion == "sorprendido":
            self.canvas.create_oval(cx - 6, boca_y - 5, cx + 6, boca_y + 7, outline=neon, width=2.5)
        else:
            self.canvas.create_line(cx - 10, boca_y, cx + 10, boca_y, fill=neon, width=2.5, capstyle=tk.ROUND)

        if self.emocion == "pensando":
            for i in range(3):
                ang = self.tiempo * 4 + (i * 2.09)
                px = cx + math.cos(ang) * 84
                py = cy + math.sin(ang) * 28
                self.canvas.create_oval(px - 4, py - 4, px + 4, py + 4, fill=neon, outline="#FFFFFF", width=1)

    def animar(self):
        self.tiempo += 0.05
        ahora = time.time()

        if not self.parpadeo and ahora >= self.proximo_parpadeo:
            self.parpadeo = True
            self.fin_parpadeo = ahora + 0.14
        elif self.parpadeo and ahora >= self.fin_parpadeo:
            self.parpadeo = False
            self.proximo_parpadeo = ahora + random.uniform(2.5, 5.5)

        self.dibujar_robot()
        self.root.after(33, self.animar)

    def actualizar_texto_hud(self, texto):
        self.txt_respuesta.configure(state=tk.NORMAL)
        self.txt_respuesta.delete("1.0", tk.END)
        self.txt_respuesta.insert(tk.END, texto)
        lineas = max(3, min(7, (len(texto) // 42) + texto.count("\n") + 1))
        self.txt_respuesta.configure(height=lineas, state=tk.DISABLED)
        self.txt_respuesta.see(tk.END)
        self.root.update_idletasks()
        req_h = self.canvas.winfo_reqheight() + self.hud_frame.winfo_reqheight() + 14
        self.root.geometry(f"{self.win_w}x{req_h}")

    def aplicar_tema_hud(self, emocion, estado_custom=None):
        tema = TEMAS_EMOCION.get(emocion, TEMAS_EMOCION["neutral"])
        self.hud_frame.configure(highlightbackground=tema["neon"])
        self.lbl_estado.configure(
            text=estado_custom or tema["estado"],
            fg=tema["neon"]
        )
        self.btn_enviar.configure(bg=tema["neon"])

    def enviar_mensaje(self, event=None):
        mensaje = self.entry.get().strip()
        if not mensaje:
            return

        self.detener_audio()
        self.entry.delete(0, tk.END)
        img_b64 = None
        if self.modo_vision:
            img_b64 = self.capturar_pantalla_base64()
            self.modo_vision = False
            self.btn_vision.configure(bg="#1E293B", fg="#94A3B8")
            self.actualizar_texto_hud("Capturando pantalla y analizando en GPU...")
        else:
            self.actualizar_texto_hud("Procesando solicitud en el núcleo local...")

        self.emocion = "pensando"
        self.aplicar_tema_hud("pensando")

        hilo = threading.Thread(target=self.consultar_n8n, args=(mensaje, img_b64), daemon=True)
        hilo.start()

    def consultar_n8n(self, mensaje, imagen_base64=None):
        try:
            payload = {"mensaje": mensaje, "session_id": SESSION_ID}
            if imagen_base64:
                payload["imagen_base64"] = imagen_base64
            resp = requests.post(WEBHOOK_URL, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            texto = data.get("texto", "Listo.")
            emocion = data.get("emocion", "feliz").lower()
            if emocion not in TEMAS_EMOCION:
                emocion = "feliz"

            self.root.after(0, lambda: self.mostrar_respuesta(texto, emocion, hablar=True))
        except Exception as e:
            err_msg = f"Error de enlace con n8n: {str(e)[:60]}"
            self.root.after(0, lambda: self.mostrar_respuesta(err_msg, "sorprendido", hablar=False))

    def mostrar_respuesta(self, texto, emocion, hablar=True):
        self.emocion = emocion
        self.actualizar_texto_hud(texto)
        self.aplicar_tema_hud(emocion)

        if hablar and self.voz_activa:
            threading.Thread(target=self.hablar_texto, args=(texto,), daemon=True).start()

    # ==========================================
    # SÍNTESIS DE VOZ NEURONAL LOCAL (PIPER TTS)
    # ==========================================
    def hablar_texto(self, texto):
        self.cancelar_audio = False
        self.hablando = True
        self.root.after(0, lambda: self.aplicar_tema_hud(self.emocion, "🔊 HABLANDO"))
        try:
            if self.piper_voice and AUDIO_DISPONIBLE:
                audio_chunks = []
                for chunk in self.piper_voice.synthesize(texto):
                    if self.cancelar_audio:
                        return
                    audio_chunks.append(chunk.audio_int16_array)
                if audio_chunks and not self.cancelar_audio:
                    audio_completo = np.concatenate(audio_chunks)
                    silencio = np.zeros(int(self.piper_voice.config.sample_rate * 0.25), dtype=audio_completo.dtype)
                    audio_completo = np.concatenate([silencio, audio_completo, silencio])
                    time.sleep(0.15)
                    if self.cancelar_audio:
                        return
                    sd.play(audio_completo, samplerate=self.piper_voice.config.sample_rate)
                    while sd.get_stream().active:
                        if self.cancelar_audio:
                            sd.stop()
                            return
                        time.sleep(0.05)
                    return

            if self.cancelar_audio:
                return
            texto_limpio = texto.replace('"', "'").replace("\n", " ")
            cmd = (
                f'Add-Type -AssemblyName System.Speech; '
                f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$s.Rate = 1; '
                f'$s.Speak("{texto_limpio}")'
            )
            self.proc_voz = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", cmd],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.proc_voz.wait()
            self.proc_voz = None
        except Exception:
            pass
        finally:
            self.hablando = False
            self.root.after(0, lambda: self.aplicar_tema_hud(self.emocion))


if __name__ == "__main__":
    root = tk.Tk()
    app = JollyCyberPet(root)
    root.mainloop()