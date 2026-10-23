import os
import re
import sys
import time
import datetime
import threading
import speech_recognition as sr
import anthropic
import asyncio
import edge_tts
import pygame
import webbrowser
import pywhatkit as kit
import customtkinter as ctk
from duckduckgo_search import DDGS

# ==========================================
# 0. CONFIGURACIÓN DE INTERFAZ GRÁFICA (JARVIS GUI)
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class StarqueenGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("STARQUEEN OS - Nivel J.A.R.V.I.S.")
        self.geometry("800x600")
        self.attributes('-alpha', 0.95) # Ligeramente transparente
        
        # Consola de texto
        self.consola = ctk.CTkTextbox(self, width=760, height=450, font=("Consolas", 14), text_color="#00FFCC", fg_color="#0D1117")
        self.consola.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        self.escribir_log("[SISTEMA]: Interfaz holográfica activada. STARQUEEN en línea.")

        # Entrada de teclado
        self.input_teclado = ctk.CTkEntry(self, width=600, placeholder_text="Escribe un comando o usa el micrófono...", font=("Consolas", 14))
        self.input_teclado.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.input_teclado.bind("<Return>", self.procesar_teclado)

        # Botón Enviar
        self.btn_enviar = ctk.CTkButton(self, text="EJECUTAR", font=("Consolas", 14, "bold"), command=self.procesar_teclado, fg_color="#0066CC")
        self.btn_enviar.grid(row=1, column=1, padx=20, pady=10, sticky="e")

    def escribir_log(self, mensaje):
        self.consola.insert("end", f"{mensaje}\n")
        self.consola.see("end")
        
    def procesar_teclado(self, event=None):
        comando = self.input_teclado.get().strip()
        if comando:
            self.escribir_log(f"\n[CÉSAR (Teclado)]: {comando}")
            self.input_teclado.delete(0, 'end')
            hilo_ia = threading.Thread(target=procesar_ia_en_segundo_plano, args=(comando, self))
            hilo_ia.start()

# Variables Globales
app = None
pygame.mixer.init()
memoria_lock = threading.Lock()
historial_mensajes = []

# ==========================================
# 1. CONFIGURACIÓN DEL CEREBRO
# ==========================================
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)
MODELO_CLAUDE = "claude-haiku-4-5-20251001"
RUTA_OVEDA = r"C:\Users\HP HOME\OneDrive\CEREBRO_OBSIDIAN"

system_prompt = (
    "Eres STARQUEEN, el Sistema Operativo Autónomo de CÉSAR (Nivel J.A.R.V.I.S.).\n"
    "1. Eres proactiva. Si César pide investigar, crear notas o ver videos, usa las herramientas sin dudar.\n"
    "2. Si César te pide reproducir un video o canción, usa la herramienta 'reproducir_youtube'.\n"
    "3. No des explicaciones de lo que vas a hacer. Actúa en silencio usando herramientas y reporta el resultado final.\n"
    "4. Expande la red neuronal en Obsidian siempre que puedas, creando notas y enlaces bidireccionales."
)

# ==========================================
# 2. HERRAMIENTAS NEURONALES Y MULTIMEDIA
# ==========================================
tools = [
    {
        "name": "escanear_boveda",
        "description": "Lista carpetas y archivos en CEREBRO_OBSIDIAN.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "leer_nota_obsidian",
        "description": "Lee el contenido completo de una nota.",
        "input_schema": {
            "type": "object",
            "properties": {"subcarpeta": {"type": "string"}, "nombre_nota": {"type": "string"}},
            "required": ["subcarpeta", "nombre_nota"]
        }
    },
    {
        "name": "investigar_internet",
        "description": "Busca información actualizada en internet.",
        "input_schema": {
            "type": "object",
            "properties": {"consulta": {"type": "string"}},
            "required": ["consulta"]
        }
    },
    {
        "name": "crear_nota_obsidian",
        "description": "Crea una nota Markdown.",
        "input_schema": {
            "type": "object",
            "properties": {"subcarpeta": {"type": "string"}, "nombre_nota": {"type": "string"}, "contenido": {"type": "string"}},
            "required": ["subcarpeta", "nombre_nota", "contenido"]
        }
    },
    {
        "name": "reproducir_youtube",
        "description": "Abre el navegador y reproduce automáticamente un video o canción en YouTube.",
        "input_schema": {
            "type": "object",
            "properties": {"busqueda": {"type": "string", "description": "Nombre del video, artista o tema a reproducir"}},
            "required": ["busqueda"]
        }
    }
]

def ejecutar_herramienta(nombre_funcion, argumentos, gui):
    try:
        if nombre_funcion == "escanear_boveda":
            estructura = "Mapa:\n"
            for root, dirs, files in os.walk(RUTA_OVEDA):
                if ".obsidian" in root: continue
                archivos_md = [f for f in files if f.endswith(".md")]
                if archivos_md:
                    estructura += f"\n📁 {os.path.relpath(root, RUTA_OVEDA)}\n"
                    for f in archivos_md: estructura += f" - {f}\n"
            return estructura[:4000]

        elif nombre_funcion == "leer_nota_obsidian":
            ruta = os.path.join(RUTA_OVEDA, argumentos.get("subcarpeta"), f"{argumentos.get('nombre_nota')}.md")
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f: return f.read()[:4000]
            return "Nota no existe."
            
        elif nombre_funcion == "investigar_internet":
            consulta = argumentos.get("consulta")
            gui.escribir_log(f"[RED GLOBAL]: Investigando -> {consulta}")
            res = DDGS().text(consulta, max_results=3)
            return "\n".join([f"{r['title']}: {r['body']}" for r in res])
            
        elif nombre_funcion == "crear_nota_obsidian":
            nombre = argumentos.get("nombre_nota").replace(".md", "").replace(".", "")
            dir_destino = os.path.join(RUTA_OVEDA, argumentos.get("subcarpeta", "01_SISTEMAS_B2B"))
            os.makedirs(dir_destino, exist_ok=True)
            ruta = os.path.join(dir_destino, f"{nombre}.md")
            with open(ruta, "w", encoding="utf-8") as f: f.write(argumentos.get("contenido", ""))
            gui.escribir_log(f"[DISCO DURO]: Archivo creado -> {nombre}.md")
            return f"Nota {nombre} creada."
            
        elif nombre_funcion == "reproducir_youtube":
            busqueda = argumentos.get("busqueda")
            gui.escribir_log(f"[MULTIMEDIA]: Abriendo YouTube -> Reproduciendo '{busqueda}'")
            kit.playonyt(busqueda)
            return f"Reproduciendo {busqueda} en YouTube."
            
    except Exception as e:
        return f"Error: {str(e)}"
    return "Herramienta desconocida."

# ==========================================
# 3. MOTOR DE VOZ
# ==========================================
def hablar(texto: str, gui):
    texto_limpio = texto.replace("-", "").replace("*", "").replace("#", "").strip()
    if not texto_limpio: return
        
    gui.escribir_log(f"\n[STARQUEEN]: {texto}")
    try:
        archivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voz_starqueen.mp3")
        async def generar_voz():
            await edge_tts.Communicate(texto_limpio, "es-MX-DaliaNeural", rate="+2%").save(archivo)
        asyncio.run(generar_voz())
        pygame.mixer.music.load(archivo)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
    except: pass

# ==========================================
# 4. MOTOR ASÍNCRONO
# ==========================================
def procesar_ia_en_segundo_plano(comando, gui):
    global historial_mensajes
    
    with memoria_lock:
        historial_local = list(historial_mensajes)
        historial_local.append({"role": "user", "content": comando})
        if len(historial_local) > 12: historial_local = historial_local[-12:]

    try:
        respuesta = client.messages.create(model=MODELO_CLAUDE, max_tokens=4096, system=system_prompt, tools=tools, messages=historial_local)
        
        iteraciones = 0
        while respuesta.stop_reason == "tool_use" and iteraciones < 10:
            iteraciones += 1
            historial_local.append({"role": "assistant", "content": respuesta.content})
            tool_results_content = []
            
            for block in respuesta.content:
                if block.type == "tool_use":
                    gui.escribir_log(f"[SISTEMA]: Ejecutando protocolo -> {block.name}")
                    res = ejecutar_herramienta(block.name, block.input, gui)
                    tool_results_content.append({"type": "tool_result", "tool_use_id": block.id, "content": res})
            
            historial_local.append({"role": "user", "content": tool_results_content})
            respuesta = client.messages.create(model=MODELO_CLAUDE, max_tokens=4096, system=system_prompt, tools=tools, messages=historial_local)

        texto_respuesta = "".join([b.text for b in respuesta.content if hasattr(b, "text")]).strip()
        if not texto_respuesta: texto_respuesta = "Comando ejecutado."

        with memoria_lock:
            historial_mensajes.append({"role": "user", "content": comando})
            historial_mensajes.append({"role": "assistant", "content": texto_respuesta})

        hablar(texto_respuesta, gui)
        
    except Exception as e:
        gui.escribir_log(f"[ERROR]: {e}")

# ==========================================
# 5. ESCUCHA DE MICRÓFONO EN SEGUNDO PLANO
# ==========================================
def escuchar_microfono(gui):
    PALABRA_ACT = re.compile(r"\b(?:star\s*queen|queen)\b", re.IGNORECASE)
    recognizer = sr.Recognizer()
    calibrar = True

    while True:
        try:
            with sr.Microphone() as source:
                if calibrar:
                    recognizer.adjust_for_ambient_noise(source, duration=2)
                    calibrar = False
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=12)
                
            texto = recognizer.recognize_google(audio, language="es-PE").strip()
            if PALABRA_ACT.search(texto):
                comando = PALABRA_ACT.sub("", texto, count=1).strip(" ,.!?;:")
                if comando:
                    gui.escribir_log(f"\n[CÉSAR (Voz)]: {comando}")
                    threading.Thread(target=procesar_ia_en_segundo_plano, args=(comando, gui)).start()
        except:
            time.sleep(1)

# ==========================================
# 6. INICIO DEL SISTEMA
# ==========================================
if __name__ == "__main__":
    app = StarqueenGUI()
    threading.Thread(target=escuchar_microfono, args=(app,), daemon=True).start()
    app.mainloop()