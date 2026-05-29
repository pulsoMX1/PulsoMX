import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_URL = "https://news.google.com/rss/search?q=when:1d+geo:Mexico&hl=es-419&gl=MX&ceid=MX:es-419"
JSON_PATH = "data/noticias.json"
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

def cargar_noticias():
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def guardar_noticias(noticias):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

def reescribir_con_ia(titulo_orig, resumen_orig):
    if not GROQ_API_KEY:
        return titulo_orig, resumen_orig
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    prompt = f"Actúa como un periodista digital mexicano. Crea un título clickbait pero ético y un resumen corto (máximo 3 líneas) de esta noticia. Devuelve solo un objeto JSON con las llaves 'titulo' y 'resumen'. Noticia: {titulo_orig} - {resumen_orig}"
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        data = json.loads(res['choices'][0]['message']['content'])
        return data.get("titulo", titulo_orig), data.get("resumen", resumen_orig)
    except:
        return titulo_orig, resumen_orig

def ejecutar():
    print("Buscando noticias...")
    res = requests.get(RSS_URL, timeout=10)
    if res.status_code != 200: return
    
    root = ET.fromstring(res.content)
    noticias_guardadas = cargar_noticias()
    titulos_viejos = {n["titulo_original"] for n in noticias_guardadas if "titulo_original" in n}
    
    nuevos = 0
    for item in root.findall(".//item")[:3]: # Procesar 3 noticias por tanda
        t_orig = item.find("title").text
        link = item.find("link").text
        desc = item.find("description").text or t_orig
        
        if t_orig in titulos_viejos: continue
        
        t_ia, r_ia = reescribir_con_ia(t_orig, desc)
        
        # Generar imagen con IA de forma gratuita usando Pollinations
        prompt_img = requests.utils.quote(f"news photo, {t_ia[:50]}")
        img_url = f"https://image.pollinations.ai/prompt/{prompt_img}?width=800&height=500&nologo=true"
        
        nuevo_id = max([n["id"] for n in noticias_guardadas], default=0) + 1
        
        noticias_guardadas.append({
            "id": nuevo_id,
            "titulo_original": t_orig,
            "titulo": t_ia,
            "resumen": r_ia,
            "imagen": img_url,
            "fecha": datetime.today().strftime('%Y-%m-%d'),
            "url_origen": link
        })
        nuevos += 1
        print(f"✅ Noticia agregada: {t_ia[:40]}")
        
    if nuevos > 0:
        guardar_noticias(noticias_guardadas)

if __name__ == "__main__":
    ejecutar()
