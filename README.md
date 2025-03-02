# 📊 Analizador de Chat de WhatsApp

Una aplicación web desarrollada con Streamlit que permite analizar chats de WhatsApp y generar visualizaciones estadísticas interactivas.

## 🌟 Características

- 📱 Análisis de chats exportados de WhatsApp
- 📊 Visualizaciones estadísticas:
  - Mensajes por persona
  - Actividad diaria
  - Distribución de tipos de mensajes
  - Actividad por hora
  - Actividad semanal
- 🔤 Nube de palabras personalizada por miembro
- 📈 Estadísticas detalladas por participante

## 🚀 Instalación Local

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/whatsapp-chat-analyzer.git
cd whatsapp-chat-analyzer
```

2. Crea un entorno virtual e instálalo:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## 📋 Requisitos

```txt
streamlit==1.31.1
pandas==2.2.0
matplotlib==3.8.2
seaborn==0.13.2
wordcloud==1.9.3
```

## 🎯 Uso

### Ejecutar Localmente

1. Inicia la aplicación:
```bash
streamlit run streamlit_app.py
```

2. Abre tu navegador (se abrirá automáticamente) en `http://localhost:8501`

3. Exporta un chat de WhatsApp:
   - Abre WhatsApp
   - Ve al chat que quieres analizar
   - Menú > Más > Exportar chat
   - Selecciona "Sin medios"

4. Sube el archivo .txt en la aplicación

### Compartir la Aplicación

Hay dos formas de compartir la aplicación:

#### 1. Compartir mediante Streamlit Cloud (Recomendado)

1. Crea una cuenta en [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu repositorio de GitHub
3. Despliega la aplicación con un clic
4. Comparte la URL pública con otros usuarios

#### 2. Compartir para Uso Local

1. Comparte el repositorio de GitHub
2. El usuario debe:
   - Clonar el repositorio
   - Instalar Python 3.8 o superior
   - Ejecutar los comandos de instalación
   - Iniciar la aplicación localmente

## 📊 Visualizaciones

- **Mensajes por Persona**: Gráfico de barras mostrando el número de mensajes por participante
- **Actividad Diaria**: Línea temporal de la actividad del chat
- **Tipos de Mensajes**: Gráfico circular mostrando la distribución de mensajes de texto vs multimedia
- **Actividad por Hora**: Distribución de mensajes por hora del día
- **Actividad Semanal**: Distribución de mensajes por día de la semana
- **Nube de Palabras**: Visualización de las palabras más usadas por cada participante

## 🛠️ Tecnologías Utilizadas

- **Framework**: Streamlit
- **Visualización**: Matplotlib, Seaborn, WordCloud
- **Procesamiento de Datos**: Pandas
- **Control de Versiones**: Git

## 📝 Notas

- La aplicación procesa solo archivos de texto (.txt) exportados de WhatsApp
- Las imágenes y otros archivos multimedia no se incluyen en el análisis
- Se filtran palabras comunes y stopwords en español para la nube de palabras
- Los datos se procesan localmente y no se almacenan en ningún servidor

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles. 