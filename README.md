# Analizador de WhatsApp

Este proyecto es un analizador de chats de WhatsApp que utiliza modelos de lenguaje para imitar el estilo de escritura de los participantes del chat.

## Características

- Análisis de chats de WhatsApp exportados en formato .txt
- Identificación de los 15 miembros más activos
- Estadísticas de participación (mensajes y porcentajes)
- Generación de respuestas imitando el estilo de cada miembro
- Interfaz web amigable

## Requisitos

- Python 3.8 o superior
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/literato1987/analizador_whatsapp.git
cd analizador_whatsapp
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecutar la aplicación:
```bash
python app.py
```

2. Abrir el navegador en `http://localhost:5000`
3. Subir un archivo de chat de WhatsApp exportado (formato .txt)
4. Seleccionar un miembro del top 15
5. Escribir un mensaje para generar una respuesta en su estilo

## Tecnologías

- Flask para el backend
- Hugging Face Transformers para el procesamiento de lenguaje
- Bootstrap para la interfaz de usuario
- Pandas para el procesamiento de datos

## Estructura del Proyecto

- `app.py`: Servidor Flask y lógica principal
- `templates/index.html`: Interfaz web
- `requirements.txt`: Dependencias del proyecto 