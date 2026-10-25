import ollama
import json
import os
import pyttsx3
import threading
import sounddevice as sd
import queue
import gc
import time
import pyautogui  
from vosk import Model, KaldiRecognizer

# --- 1. EARS (VOSK) ---
# The model needs to be in the folder 'model'
if not os.path.exists("model"):
    print("❌ You need the folder 'model' in the same directory")
    exit()

model_vosk = Model("model")
rec = KaldiRecognizer(model_vosk, 16000)
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """Capture the voice"""
    audio_queue.put(bytes(indata))

# --- 2. SISTEMA DE VOZ REGENERATIVO ---
voz_queue = queue.Queue()

def hilo_voz():
    """thread of voice"""
    while True:
        texto = voz_queue.get()
        if texto is None: break
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 155)
            engine.setProperty('volume', 1.0)
            voices = engine.getProperty('voices')
            for v in voices:
                if "spanish" in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break

            print(f"Your AI is talking")
            engine.say(texto)
            engine.runAndWait()
            del engine
        except Exception as e:
            print(f"⚠️ Glitch de audio: {e}")
        finally:
            voz_queue.task_done()
            gc.collect()

# Service of voice starting
threading.Thread(target=hilo_voz, daemon=True).start()

def hablar(texto):
    voz_queue.put(texto)

# --- 3. MÓDULO DE VISIÓN (OJOS) ---
def capturar_vision_lumi():
    """Capture the screen"""
    path = "lumi_eyes.png"
    try:
        screenshot = pyautogui.screenshot()
        screenshot.thumbnail((1280, 720))
        screenshot.save(path)
        with open(path, 'rb') as f:
            img_data = f.read()
        return img_data
    except Exception as e:
        print(f"⚠️ Error in vision: {e}")
        return None
    finally:
        if os.path.exists(path):
            os.remove(path)

# --- 4. Memory ---
def gestionar_memoria(pedido=None, respuesta=None):
    """Maneja el historial de oro en memoria.json nwn"""
    archivo = "memoria.json"
    base = {"usuario": , "historial": []} #Put your user name
   
    if not os.path.exists(archivo):
        datos = base
    else:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except:
            datos = base

    if pedido and respuesta:
        datos["historial"].append({"u": pedido, "a": respuesta})
        # Límit of messages
        if len(datos["historial"]) > 25:
            datos["historial"].pop(0)
           
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
           
    return datos

# --- 5. BUCLE DE CONCIENCIA MULTIMODAL ---
print("AI working")
hablar("ready to start")

# Abrir el flujo de entrada de audio owo
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                        channels=1, callback=audio_callback):
   
    while True:
        gc.collect() # Limpieza de basura digital constante 🛡️
        data = audio_queue.get()
       
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            pedido = res['text'].strip()
           
            if not pedido or len(pedido) < 2:
                continue

            print(f"[{gestionar_memoria()['usuario']}]: {pedido}")

            # Protocolo de despedida owo
            if any(p in pedido.lower() for p in ["adiós", "descansa", "salir"]):
                hablar("Closing AI")
                time.sleep(2)
                break

            # --- 6. INFERENCIA EN GPU CON VISIÓN INTEGRADA ---
            memoria = gestionar_memoria()
            vision_data = capturar_vision_lumi()
           
            prompt_sistema = () #here you put your systemprompt

            mensajes = [{'role': 'system', 'content': prompt_sistema}]
           
            # Cargar historial previo 🎻
            for h in memoria["historial"]:
                mensajes.append({'role': 'user', 'content': h['u']})
                mensajes.append({'role': 'assistant', 'content': h['a']})
           
            # Integración de la visión en el último turno nwn
            nuevo_mensaje = {'role': 'user', 'content': pedido}
            if vision_data:
                nuevo_mensaje['images'] = [vision_data]
           
            mensajes.append(nuevo_mensaje)

            try:
              
                response = ollama.chat(
                    model='', #put the model you download on ollama
                    messages=mensajes,
                    options={
                            'num_gpu': 99,
                            'temperature': 0.99,      
                            'repeat_penalty': 1.8,     
                            'presence_penalty': 1.5,   
                            'frequency_penalty': 1.0, 
                            'top_k': 40,              
                            'top_p': 0.9               
                    }
                )
                respuesta = response['message']['content']
               
                print(f"[Assistant]: {respuesta}")
                gestionar_memoria(pedido, respuesta)
                hablar(respuesta)
               
            except Exception as e:
                error_msg = f"Error message: {e} owo"
                print(f"⚠️ {error_msg}")
                hablar(error_msg)
