import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse
import base64
import re

# ⚙️ CONFIGURACIÓN DEL BOT
MODO_TURBO = True
NOTICIAS_POR_CARRERA = 10 if MODO_TURBO else 1
RSS_URL = "https://news.google.com/rss/search?q=when:1d+geo:Mexico&hl=es-419&gl=MX&ceid=MX:es-419"
JSON_PATH = "data/noticias.json"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Headers potentes para hacernos pasar por un humano en Google Chrome
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

FALLBACK_IMAGE_URL = "https://images.unsplash.com/photo-1504711434269-d0385429813a?q=80&w=800&auto=format&fit=crop"

def cargar_noticias():
    if not os.path.exists(JSON_PATH): return []
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def guardar_noticias(noticias):
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

def obtener_url_real_definitiva(google_url):
    """
    Atraviesa la pantalla de carga de Google News. Usa 2 métodos:
    1. Decodificación Base64 matemática.
    2. Scraping del código JavaScript de la página de redirección.
    """
    # Método 1: Decodificación matemática
    try:
        if "articles/" in google_url:
            base64_str = google_url.split("articles/")[1].split("?")[0]
            base64_str += "=" * ((4 - len(base64_str) % 4) % 4)
            decoded_bytes = base64.urlsafe_b64decode(base64_str)
            
            # Buscar la URL escondida en el código binario
            match = re.search(b'(https?://[a-zA-Z0-9./_\-\?\&\=\%]+)', decoded_bytes)
            if match:
                url_limpia = match.group(1).decode('utf-8')
                if "google.com" not in url_limpia:
                    return url_limpia
    except Exception:
        pass

    # Método 2: Leer la página de espera de Google y robar el enlace
    try:
        res = requests.get(google_url, headers=HEADERS, timeout=10)
        # 1. Buscamos en etiquetas A ocultas
        match = re.search(r'<a[^>]+href="(https?://[^"]+)"', res.text)
        if match and "google.com" not in match.group(1):
            return match.group(1)
            
        # 2. Buscamos en el redireccionador de JavaScript
        match = re.search(r'window\.location\.replace\("([^"]+)"\)', res.text)
        if match:
            return match.group(1)
    except Exception:
        pass

    return google_url

def obtener_imagen_periodico(url_real):
    if "news.google.com" in url_real:
        return FALLBACK_IMAGE_URL
        
    try:
        # Entramos a la página real del periódico
        res = requests.get(url_real, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # Buscamos la foto de portada (og:image o twitter:image)
            img_tag = soup.find("meta", property="og:image") or \
                      soup.find("meta", attrs={"name": "twitter:image"}) or \
                      soup.find("meta", itemprop="image")
                      
            if img_tag and img_tag.get("content"):
                imagen = img_tag["content"]
                # Ajustamos el enlace si el periódico lo hizo relativo
                if imagen.startswith("/"):
                    imagen = urllib.parse.urljoin(url_real, imagen)
                return imagen
                
    except Exception as e:
        print(f"⚠️ Error buscando imagen en el periódico: {e}")
        
    return FALLBACK_IMAGE_URL

def reescribir_con_ia(titulo_orig):
    if not GROQ_API_KEY:
        return titulo_orig, "Noticia importante de México.", "Revisa el enlace original para más detalles."

    prompt = f"""Eres un periodista profesional mexicano. A partir del siguiente titular de noticia, genera un artículo periodístico completo en español.
    TITULAR: {titulo_orig}
    Responde ÚNICAMENTE con un objeto JSON válido con estas 3 claves exactas:
    - "titulo": Un título llamativo para la noticia.
    - "resumen": Un texto breve de dos líneas.
    - "contenido": El cuerpo de la noticia con al menos 300 palabras, estructurado en párrafos.
    No agregues introducciones ni markdown fuera de las llaves."""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                          headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                          json=payload, timeout=45)
        res = r.json()
        
        if 'choices' in res:
            data = json.loads(res['choices'][0]['message']['content'])
            return data.get("titulo", titulo_orig), data.get("resumen", "Noticia importante."), data.get("contenido", "Detalles en el enlace.")
        else:
            return titulo_orig, "Noticia disponible en el enlace.", "Revisa el enlace original."

    except Exception:
        return titulo_orig, "Noticia disponible en el enlace.", "Revisa el enlace original."

def ejecutar():
    try:
        res = requests.get(RSS_URL, timeout=10)
        root = ET.fromstring(res.content)
    except Exception as e:
        print(f"❌ Error RSS: {e}")
        return

    noticias_guardadas = cargar_noticias()
    nuevos = 0

    for item in root.findall(".//item")[:NOTICIAS_POR_CARRERA]:
        t_orig = item.find("title").text
        google_url = item.find("link").text if item.find("link") is not None else "#"

        if any(n.get('titulo_original') == t_orig for n in noticias_guardadas):
            continue

        print(f"🔄 Procesando: {t_orig[:60]}...")
        
        t_ia, r_ia, c_ia = reescribir_con_ia(t_orig)
        
        # 1. Obtenemos URL cruzando el bloqueo de Google
        url_real = obtener_url_real_definitiva(google_url)
        print(f"🔗 URL Destino: {url_real[:60]}...")
        
        # 2. Le robamos la foto oficial al periódico
        img_url = obtener_imagen_periodico(url_real)
        if img_url == FALLBACK_IMAGE_URL:
            print("⚠️ No se encontró imagen. Usando imagen por defecto.")
        else:
            print(f"✅ Imagen capturada exitosamente.")

        nuevo_id = max([n.get("id", 0) for n in noticias_guardadas], default=0) + 1
        noticias_guardadas.append({
            "id": nuevo_id,
            "titulo_original": t_orig,
            "titulo": t_ia,
            "resumen": r_ia,
            "contenido": c_ia,
            "imagen": img_url,
            "fecha": datetime.today().strftime('%Y-%m-%d'),
            "url_origen": url_real
        })
        nuevos += 1

    if nuevos > 0:
        guardar_noticias(noticias_guardadas[-100:])
        print(f"💾 Guardadas {nuevos} noticias nuevas.")
    else:
        print("ℹ️ No hay noticias nuevas.")

if __name__ == "__main__":
    ejecutar()
