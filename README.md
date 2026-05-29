# NotiRápido 🚀📰

> Portal de noticias automatizado con IA — México y el Mundo

[![GitHub Actions](https://github.com/TU-USUARIO/notirapido/actions/workflows/automate.yml/badge.svg)](https://github.com/TU-USUARIO/notirapido/actions)

## 🌐 Demo
**[Ver sitio →](https://TU-USUARIO.github.io/notirapido)**

---

## 🏗️ Cómo Funciona

```
RSS Feeds → Python Script → Claude AI → Pollinations.ai → GitHub Pages + Facebook
```

Cada 2 horas, GitHub Actions:
1. Descarga noticias de 9+ fuentes RSS (México y mundo)
2. Claude reescribe cada noticia de forma original
3. Pollinations.ai genera una imagen sin costo
4. Se crea un post Jekyll en `_posts/`
5. Se publica en Facebook automáticamente
6. GitHub Pages hace deploy del sitio

---

## ⚙️ Setup Inicial (15 minutos)

### Paso 1 — Fork del repositorio
1. Haz clic en **Fork** en la parte superior derecha
2. Nómbralo `notirapido`

### Paso 2 — Configurar GitHub Pages
1. Ve a **Settings → Pages**
2. Source: **GitHub Actions**
3. Guarda

### Paso 3 — Agregar Secrets
Ve a **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Cómo obtenerlo |
|--------|---------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `FB_PAGE_ACCESS_TOKEN` | Ver instrucciones abajo |
| `FB_PAGE_ID` | ID numérico de tu página de Facebook |
| `SITE_URL` | `https://TU-USUARIO.github.io/notirapido` |

### Paso 4 — Obtener Token de Facebook

1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Crea una App → Tipo: **Negocios**
3. Agrega el producto **Pages API**
4. En **Graph API Explorer**: selecciona tu página y solicita permisos:
   - `pages_manage_posts`
   - `pages_read_engagement`  
   - `publish_to_groups`
5. Genera el **Page Access Token** (larga duración)
6. Usa [Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/) para convertirlo a token de larga duración

### Paso 5 — Actualizar _config.yml
```yaml
url: "https://TU-USUARIO.github.io"
baseurl: "/notirapido"
```

### Paso 6 — Actualizar links de Facebook
Busca `TU-PAGINA-AQUI` en los archivos y reemplaza con el URL de tu página.

### Paso 7 — Primer run manual
1. Ve a **Actions → NotiRápido Automatización**
2. Clic en **Run workflow**
3. Observa los logs en tiempo real 🎉

---

## 🎯 AdSense — Solicitud de Aprobación

Antes de aplicar, asegúrate de:

- [ ] El sitio tiene **mínimo 20 artículos** publicados
- [ ] El dominio lleva activo **al menos 2-4 semanas**
- [ ] Las páginas legales están completas (Privacidad, Términos, Sobre nosotros, Contacto)
- [ ] El sitio carga rápido y es mobile-friendly
- [ ] No hay contenido duplicado exacto

Una vez aprobado, agrega en `_config.yml`:
```yaml
adsense_publisher: "ca-pub-XXXXXXXXXXXXXXXXX"
adsense_slot_header: "XXXXXXXXXX"
adsense_slot_article: "XXXXXXXXXX"
adsense_slot_sidebar: "XXXXXXXXXX"
```

---

## 📁 Estructura del Proyecto

```
notirapido/
├── _posts/              # Artículos generados automáticamente
├── _layouts/            # Plantillas HTML
├── _includes/           # Componentes reutilizables
├── _data/               # published.json (hashes anti-duplicados)
├── assets/
│   ├── css/main.css     # Estilos completos
│   └── images/noticias/ # Imágenes generadas por IA
├── scripts/
│   └── automation.py    # Script principal de automatización
├── .github/workflows/
│   └── automate.yml     # GitHub Actions (corre cada 2 horas)
├── _config.yml          # Configuración de Jekyll
├── index.html           # Página principal
├── Gemfile              # Dependencias Ruby/Jekyll
└── páginas legales...
```

---

## 🔧 Personalización

### Cambiar frecuencia de publicación
En `.github/workflows/automate.yml`, modifica el cron:
```yaml
- cron: '0 */2 * * *'   # Cada 2 horas (actual)
- cron: '0 */1 * * *'   # Cada hora
- cron: '0 6,12,18 * * *' # 3 veces al día
```

### Agregar más fuentes RSS
En `scripts/automation.py`, agrega URLs en `RSS_FEEDS`.

### Cambiar balance México/Mundo
En `main()`, ajusta `mx_limit` y `other_limit`.

---

## 💰 Stack de Costos

| Servicio | Costo |
|----------|-------|
| GitHub Actions | **Gratis** (2,000 min/mes) |
| GitHub Pages | **Gratis** |
| Claude API (Haiku) | ~$0.25 por 100 artículos |
| Pollinations.ai | **Gratis** |
| Facebook API | **Gratis** |

---

## 📄 Licencia

MIT — Úsalo libremente para tu propio portal de noticias.

---

*Creado con ❤️ en México 🇲🇽*
