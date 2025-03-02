from flask import Flask, render_template, request, jsonify
import os
import re
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Configurar backend no interactivo antes de importar pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import base64
from io import BytesIO
from datetime import datetime
import nltk
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
from nltk.corpus import stopwords

# Configuración adicional de matplotlib
plt.ioff()  # Desactivar modo interactivo

# Definir conjunto global de palabras a excluir
EXCLUDED_WORDS = {
    'todo', 'porque', 'tiene', 'multimedia', 'omitido', 
    '<multimedia', 'omitido>', 'imagen', 'video', 'audio', 
    'sticker', 'gif', 'documento', 'eliminado', 'omitted',
    'image', 'para', 'pero', 'este', 'esta', 'esto', 'como',
    'cuando', 'donde', 'media', '<image', 'media', 'omitted',
    'ahora', 'algo', 'aquí', 'así', 'aunque', 'bien', 'cada',
    'casi', 'como', 'cual', 'debe', 'desde', 'después',
    'dice', 'dijo', 'donde', 'entonces', 'entre', 'está',
    'están', 'había', 'hace', 'hasta', 'hola', 'luego',
    'mejor', 'menos', 'mismo', 'mucho', 'nada', 'otro',
    'pues', 'quién', 'sabe', 'sido', 'sine', 'sino',
    'sobre', 'solo', 'también', 'tanto', 'tengo', 'todas',
    'todos', 'vamos', 'vaya', 'verdad', 'puede', 'pudo',
    'quiere', 'sería', 'hacer', 'hecho', 'siendo', 'tenía',
    'través', 'primera', 'según', 'ningún', 'manera', 'misma',
    'image>', 'omitted>', 'attached:', 'image', 'attached','porq','bueno','gente','creo','cosa','siempre','claro','año','cierto','cómo','gran','toda','años','decir','dicho','tiempo','parece'
}

def filter_words(messages):
    """
    Filtra las palabras de una lista de mensajes aplicando todos los criterios de exclusión.
    
    Args:
        messages: Lista de mensajes de texto
        
    Returns:
        Lista de palabras filtradas
    """
    # Obtener stopwords en español
    stop_words = set(stopwords.words('spanish'))
    stop_words.update(EXCLUDED_WORDS)
    
    # Procesar y filtrar palabras
    words = []
    for message in messages:
        message_words = message.lower().split()
        filtered_words = [word for word in message_words 
                        if word not in stop_words
                        and len(word) > 3 
                        and not word.startswith('http')
                        and not word.startswith('<')
                        and not word.endswith('>')
                        and not any(char.isdigit() for char in word)]
        words.extend(filtered_words)
    
    return words

app = Flask(__name__)

# Variable global para almacenar los datos del chat
chat_data = {
    'df': None,
    'members': None
}

def process_chat_file(file_content, device_type):
    """Procesa el contenido del archivo de chat"""
    print(f"Procesando archivo con tipo de dispositivo: {device_type}")
    
    # Patrones específicos para cada dispositivo
    patterns = {
        'android': [
            # Formato Android: "dd/mm/yy, HH:MM - Nombre: Mensaje"
            r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2})\s-\s([^:]+):\s(.+)',
            # Formato Android AM/PM: "dd/mm/yy, HH:MM AM/PM - Nombre: Mensaje"
            r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APMapm]{2})\s-\s([^:]+):\s(.+)'
        ],
        'iphone': [
            # Formato iPhone con segundos: "[dd/m/yy, HH:MM:SS] Nombre: Mensaje"
            r'\[(\d{1,2}/\d{1,2}/\d{2},\s\d{1,2}:\d{2}:\d{2})\]\s([^:]+):\s(.+)',
            # Formato iPhone sin segundos: "[dd/m/yy, HH:MM] Nombre: Mensaje"
            r'\[(\d{1,2}/\d{1,2}/\d{2},\s\d{1,2}:\d{2})\]\s([^:]+):\s(.+)'
        ]
    }
    
    matches = []
    used_pattern = None
    date_format = None
    
    # Seleccionar patrones según el dispositivo
    device_patterns = patterns.get(device_type, [])
    if not device_patterns:
        print(f"Error: Tipo de dispositivo no válido - {device_type}")
        return None, None, "Tipo de dispositivo no válido"
    
    # Imprimir las primeras líneas del archivo para depuración
    print("Primeras 3 líneas del archivo:")
    for line in file_content.split('\n')[:3]:
        print(f"LÍNEA: {line}")
    
    for pattern in device_patterns:
        print(f"Probando patrón: {pattern}")
        matches = re.findall(pattern, file_content, re.MULTILINE)
        if matches:
            used_pattern = pattern
            print(f"✅ Patrón encontrado: {pattern}")
            print(f"Mensajes encontrados: {len(matches)}")
            print(f"Ejemplo de coincidencia: {matches[0]}")
            
            # Determinar el formato de fecha basado en el patrón encontrado
            sample_date = matches[0][0]
            print(f"Fecha de ejemplo: {sample_date}")
            
            if device_type == 'iphone':
                if ':' in sample_date.split()[1] and len(sample_date.split()[1].split(':')) == 3:  # Si tiene segundos
                    date_format = '%d/%m/%y, %H:%M:%S'
                else:
                    date_format = '%d/%m/%y, %H:%M'
            else:  # Android
                if 'AM' in sample_date or 'PM' in sample_date:
                    date_format = '%d/%m/%y, %I:%M %p'
                else:
                    date_format = '%d/%m/%y, %H:%M'
            print(f"Formato de fecha detectado: {date_format}")
            break
    
    if not matches:
        print(f"No se encontraron coincidencias para ningún patrón de {device_type}")
        return None, None, f"No se encontró un patrón válido para el formato de {device_type}"
    
    # Crear DataFrame
    df = pd.DataFrame(matches, columns=['datetime', 'sender', 'message'])
    
    try:
        # Limpiar la fecha si es necesario
        if device_type == 'iphone':
            df['datetime'] = df['datetime'].str.replace('[', '').str.replace(']', '')
            # Intentar primero con el formato que incluye coma
            try:
                df['datetime'] = pd.to_datetime(df['datetime'], format=date_format)
            except ValueError:
                # Si falla, intentar sin la coma
                date_format = date_format.replace(', ', ' ')
                df['datetime'] = pd.to_datetime(df['datetime'], format=date_format)
        else:
            df['datetime'] = pd.to_datetime(df['datetime'], format=date_format)
        
        # Extraer hora y día de la semana
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.day_name()
        
        # Identificar tipo de mensaje según el dispositivo
        media_patterns = {
            'android': '<Multimedia omitido>',
            'iphone': 'Media omitted'
        }
        media_text = media_patterns.get(device_type, '<Multimedia omitido>')
        df['type'] = df['message'].apply(lambda x: 'media' if media_text in x else 'text')
        
        # Obtener miembros y estadísticas
        members = df['sender'].unique().tolist()
        message_counts = df['sender'].value_counts()
        
        # Crear información de miembros
        members_info = []
        total_messages = len(df)
        
        for member in members:
            member_messages = df[df['sender'] == member]
            member_count = len(member_messages)
            
            # Obtener palabras más frecuentes
            text_messages = member_messages[member_messages['type'] == 'text']['message'].tolist()
            
            # Filtrar palabras usando la función auxiliar
            words = filter_words(text_messages)
            
            # Obtener las palabras más frecuentes
            word_freq = Counter(words)
            top_words = word_freq.most_common(3)
            
            members_info.append({
                'name': member,
                'messages': member_count,
                'percentage': round(member_count / total_messages * 100, 1),
                'top_words': top_words
            })
        
        return df, members_info, None
        
    except Exception as e:
        print(f"Error procesando fechas: {str(e)}")
        return None, None, f"Error procesando el archivo: {str(e)}"

def generate_plots(df):
    """Genera todas las visualizaciones"""
    plots = {}
    
    try:
        # 1. Mensajes por persona
        fig, ax = plt.subplots(figsize=(12, 6))
        messages_per_person = df['sender'].value_counts().head(20)
        messages_per_person.plot(kind='bar', color='skyblue', ax=ax)
        plt.title('Top 20: Mensajes por persona')
        plt.xlabel('Miembro')
        plt.ylabel('Número de mensajes')
        plt.xticks(rotation=45)
        plots['messages_per_person'] = get_plot_url()
        plt.close(fig)
        
        # 2. Actividad a lo largo del tiempo
        fig, ax = plt.subplots(figsize=(12, 6))
        daily_activity = df.resample('D', on='datetime').size()
        daily_activity.plot(kind='line', color='green', ax=ax)
        plt.title('Actividad diaria del chat')
        plt.xlabel('Fecha')
        plt.ylabel('Número de mensajes')
        plots['daily_activity'] = get_plot_url()
        plt.close(fig)
        
        # 3. Distribución de tipos de mensajes
        fig, ax = plt.subplots(figsize=(8, 8))
        type_counts = df['type'].value_counts()
        type_counts.plot(kind='pie', autopct='%1.1f%%', colors=['lightcoral', 'lightblue'], ax=ax)
        plt.title('Distribución de tipos de mensajes')
        plots['message_types'] = get_plot_url()
        plt.close(fig)
        
        # 4. Actividad por hora
        fig, ax = plt.subplots(figsize=(12, 6))
        df['hour'].value_counts().sort_index().plot(kind='bar', ax=ax)
        plt.title('Actividad por hora del día')
        plt.xlabel('Hora')
        plt.ylabel('Número de mensajes')
        plots['hourly_activity'] = get_plot_url()
        plt.close(fig)
        
        # 5. Actividad por día de la semana
        fig, ax = plt.subplots(figsize=(12, 6))
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['day_of_week'].value_counts().reindex(day_order).plot(kind='bar', ax=ax)
        plt.title('Actividad por día de la semana')
        plt.xlabel('Día')
        plt.ylabel('Número de mensajes')
        plots['weekly_activity'] = get_plot_url()
        plt.close(fig)
        
        # 6. Nube de palabras general del grupo
        text_messages = df[df['type'] == 'text']['message']
        words = filter_words(text_messages)
        text = ' '.join(words)
        
        stop_words = set(stopwords.words('spanish'))
        stop_words.update(EXCLUDED_WORDS)
        
        wordcloud = WordCloud(
            width=1200, 
            height=600, 
            background_color='white',
            max_words=150,
            collocations=False,
            stopwords=stop_words
        ).generate(text)
        
        fig = plt.figure(figsize=(15, 7.5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Palabras más usadas en el grupo')
        plots['group_wordcloud'] = get_plot_url()
        plt.close(fig)
        
        return plots
    except Exception as e:
        print(f"Error generando gráficas: {str(e)}")
        return {}

def get_plot_url():
    """Convierte el plot actual en una URL de imagen"""
    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return f'data:image/png;base64,{plot_url}'

def generate_member_wordcloud(df, member):
    """Genera una nube de palabras para un miembro específico"""
    try:
        # Obtener solo mensajes de texto del miembro
        member_messages = df[(df['sender'] == member) & (df['type'] == 'text')]['message']
        
        # Filtrar palabras usando la función auxiliar
        words = filter_words(member_messages)
        
        # Unir palabras filtradas
        text = ' '.join(words)
        
        # Configurar y generar la nube de palabras
        stop_words = set(stopwords.words('spanish'))
        stop_words.update(EXCLUDED_WORDS)
        
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            max_words=100,
            collocations=False,
            stopwords=stop_words
        ).generate(text)
        
        # Crear una nueva figura con el backend Agg
        fig = plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        # Guardar la imagen en memoria
        img = BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)  # Cerrar la figura explícitamente
        
        # Preparar la imagen para enviar
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()
        
    except Exception as e:
        print(f"Error generando nube de palabras: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'})
    
    # Obtener el tipo de dispositivo del formulario
    device_type = request.form.get('device_type')
    if not device_type:
        return jsonify({'error': 'No se especificó el tipo de dispositivo'})
    
    try:
        content = file.read().decode('utf-8')
        df, members_info, error = process_chat_file(content, device_type)
        
        if error:
            return jsonify({'error': error})
        
        # Guardar DataFrame en la variable global
        chat_data['df'] = df
        chat_data['members'] = members_info
        
        plots = generate_plots(df)
        
        return jsonify({
            'success': True,
            'members': members_info,
            'plots': plots
        })
    except Exception as e:
        return jsonify({'error': f'Error procesando el archivo: {str(e)}'})

@app.route('/member_wordcloud', methods=['POST'])
def get_member_wordcloud():
    data = request.json
    member = data.get('member')
    
    if not member:
        return jsonify({'error': 'Falta el miembro'})
    
    if chat_data['df'] is None:
        return jsonify({'error': 'No hay datos de chat cargados'})
    
    try:
        wordcloud = generate_member_wordcloud(chat_data['df'], member)
        return jsonify({
            'success': True,
            'wordcloud': wordcloud
        })
    except Exception as e:
        return jsonify({'error': f'Error generando nube de palabras: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True) 