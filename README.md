# WhatsApp Chat Analyzer

Este proyecto analiza chats de WhatsApp y genera visualizaciones y estadísticas. Incluye dos versiones:
- Una aplicación web (app.py)
- Un notebook interactivo (whatsapp_style_analyzer.ipynb)

## 🚀 Funcionalidades

- Detección automática del formato de chat (iPhone/Android)
- Análisis de patrones de mensajes
- Visualizaciones:
  - Mensajes por persona
  - Actividad diaria
  - Distribución de tipos de mensajes
  - Actividad por hora
  - Actividad por día de la semana
  - Nube de palabras general y por miembro
- Análisis de estilo de escritura por miembro
- Generación de mensajes imitando el estilo de cada miembro (usando OpenAI)

## 📋 Requisitos

```
python 3.8+
pandas
matplotlib
seaborn
wordcloud
nltk
openai
python-dotenv
flask (para la versión web)
```

## 🛠️ Instalación

1. Clona el repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```
3. Para usar la generación de mensajes, crea un archivo `.env` con tu API key de OpenAI:
```
OPENAI_API_KEY=tu_api_key_aquí
```

## 💻 Uso

### Versión Web (app.py)
1. Ejecuta la aplicación:
```bash
python app.py
```
2. Abre tu navegador en `http://localhost:5000`
3. Selecciona el tipo de dispositivo (iPhone/Android)
4. Sube tu archivo de chat
5. Explora las visualizaciones y estadísticas

### Versión Notebook (whatsapp_style_analyzer.ipynb)
1. Coloca tu archivo de chat exportado en la misma carpeta
2. Abre el notebook en Jupyter/VSCode
3. Ejecuta las celdas en orden
4. Explora las visualizaciones y análisis

## 📱 Formatos de Chat Soportados

- iPhone: `[dd/mm/yy, HH:MM:SS] Nombre: Mensaje`
- Android: `dd/mm/yy, HH:MM - Nombre: Mensaje`

## 🤖 Generación de Mensajes

El proyecto puede generar mensajes imitando el estilo de escritura de cada miembro usando GPT-3.5. Para usar esta función:
1. Asegúrate de tener configurada tu API key de OpenAI
2. Ejecuta la sección de generación de mensajes en el notebook
3. El sistema analizará el estilo de cada miembro y generará mensajes similares

## 📊 Visualizaciones Disponibles

- Distribución de mensajes por miembro
- Actividad temporal (diaria/semanal)
- Tipos de mensajes (texto/multimedia)
- Patrones de actividad por hora
- Nubes de palabras (general y por miembro)

## 🔒 Privacidad

- Los chats se procesan localmente
- No se almacena ninguna información en servidores externos
- La única conexión externa es con OpenAI para la generación de mensajes (opcional) 