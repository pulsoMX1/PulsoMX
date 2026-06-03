import os
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import urllib.parse
import base64
import re

# ⚙️ CONFIGURACIÓN
JSON_PATH = "data/noticias.json"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RSS_URL = "https://news.google.com/rss/search?q=when:1d+geo:Mexico&hl=es-419&gl=MX&ceid=MX:es-419"

# 🔥 CABECERAS NINJA: Esto hace que parezcas un Chrome real desde Windows
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-MX,es;q=0.9',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site'
}

FALLBACK_IMAGE_URL = "https://images.unsplash.com/photo-1504711434269-d0385429813a?q=80&w=800&auto=format&fit=crop"

def obtener_url_real_definitiva(google_url):
    """Extrae el link real usando un método más agresivo."""
    try:
        # A veces el link ya es directo, si no, intentamos obtenerlo
        res = requests.get(google_url, headers=HEADERS, timeout=10)
        
        # Intentar extraer el link de redirección que Google pone en su HTML
        match = re.search(r'window\.location\.replace\("([^"]+)"\)', res.text)
        if match:
            return match.group(1)
            
        # Fallback a buscar en el cuerpo de la página
        links = BeautifulSoup(res.text, 'html.parser').find_all('a')
        for link in links:
            url = link.get('href', '')
            if url.startswith('http') and 'news.google.com' not in url and 'google.com' not in url:
                return url
    except:
        pass
    return google_url

def obtener_imagen_periodico(url_real):
    """Entra a la web y busca la imagen de portada o la primera grande."""
    try:
        res = requests.get(url_real, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # 1. Intentar con meta tags estándar
        meta_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if meta_img and meta_img.get("content"):
            return meta_img["content"]
            
        # 2. Si falló, buscar la imagen más grande dentro del artículo
        imgs = soup.find_all("img")
        for img in imgs:
            src = img.get("src", "")
            # Filtramos iconos o logos pequeños
            if src.startswith("http") and len(src) > 50:
                return src
                
    except:
        pass
    return FALLBACK_IMAGE_URL

def reescribir_con_ia(titulo_orig):
    if not GROQ_API_KEY:
        return titulo_orig, "Noticia reciente.", "Detalles en el enlace original."

    prompt = f"""Eres un periodista profesional mexicano. A partir del siguiente titular, genera un artículo periodístico en español.
    TITULAR: {titulo_orig}
    Responde ÚNICAMENTE con un objeto JSON válido con 3 claves exactas:
    - "titulo": Un título llamativo.
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
        
        # 1. Atravesar Google News usando Cookies inyectadas
        url_real = obtener_url_real_definitiva(google_url)
        print(f"🔗 URL Destino: {url_real[:60]}...")
        
        # 2. Descargar la imagen del periódico final
        img_url = obtener_imagen_periodico(url_real)
        if img_url == FALLBACK_IMAGE_URL:
            print("⚠️ Usando imagen por defecto (El periódico bloqueó el acceso).")
        else:
            print(f"✅ ¡Imagen real extraída con éxito!: {img_url[:30]}...")

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
