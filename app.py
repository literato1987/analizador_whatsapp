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

# Configuración adicional de matplotlib
plt.ioff()  # Desactivar modo interactivo

app = Flask(__name__)

# Variable global para almacenar los datos del chat
chat_data = {
    'df': None,
    'members': None
}

def process_chat_file(file_content):
    """Procesa el contenido del archivo de chat"""
    patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2})\s-\s([^:]+):\s(.+)',
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APMapm]{2})\s-\s([^:]+):\s(.+)',
        r'\[(\d{1,2}/\d{1,2}/\d{2,4}\s\d{1,2}:\d{2}:\d{2})\]\s([^:]+):\s(.+)'
    ]
    
    matches = []
    used_pattern = None
    
    for pattern in patterns:
        matches = re.findall(pattern, file_content, re.MULTILINE)
        if matches:
            used_pattern = pattern
            print(f"✅ Patrón encontrado: {pattern}")
            print(f"Mensajes encontrados: {len(matches)}")
            break
    
    if not matches:
        return None, None, "No se encontró un patrón válido en el archivo"
    
    # Crear DataFrame
    df = pd.DataFrame(matches, columns=['datetime', 'sender', 'message'])
    
    # Convertir fechas a datetime
    df['datetime'] = pd.to_datetime(df['datetime'], format='%d/%m/%y, %H:%M')
    
    # Extraer hora y día de la semana
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.day_name()
    
    # Identificar tipo de mensaje
    df['type'] = df['message'].apply(lambda x: 'media' if '<Multimedia omitido>' in x else 'text')
    
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
        words = ' '.join(text_messages).lower().split()
        word_freq = Counter([w for w in words if len(w) > 3])
        top_words = word_freq.most_common(3)
        
        members_info.append({
            'name': member,
            'messages': member_count,
            'percentage': round(member_count / total_messages * 100, 1),
            'top_words': top_words
        })
    
    return df, members_info, None

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
        # Lista de stopwords en español
        stopwords = {
            'a', 'al', 'ante', 'bajo', 'cabe', 'con', 'contra', 'de', 'desde', 'durante',
            'en', 'entre', 'hacia', 'hasta', 'mediante', 'para', 'por', 'según', 'sin',
            'sobre', 'tras', 'y', 'e', 'ni', 'que', 'si', 'no', 'el', 'la', 'los', 'las',
            'un', 'una', 'unos', 'unas', 'lo', 'este', 'esta', 'estos', 'estas', 'ese',
            'esa', 'esos', 'esas', 'del', 'multimedia', 'omitido', '<multimedia', 'omitido>',
            'ha', 'he', 'has', 'han', 'hemos', 'habéis', 'había', 'hubo', 'ser', 'es',
            'soy', 'eres', 'somos', 'sois', 'estar', 'estoy', 'está', 'estamos', 'estáis',
            'te', 'mi', 'tu', 'su', 'nos', 'os', 'les', 'me', 'se', 'pero', 'más', 'ya',
            'esto', 'eso', 'aquello', 'quien', 'donde', 'cuando', 'cuanto', 'como',
            'imagen', 'video', 'audio', 'sticker', 'gif', 'documento', 'eliminado'
        }
        
        # Obtener solo mensajes de texto
        member_messages = df[(df['sender'] == member) & (df['type'] == 'text')]['message']
        
        # Procesar y filtrar palabras
        words = []
        for message in member_messages:
            # Convertir a minúsculas y dividir en palabras
            message_words = message.lower().split()
            # Filtrar palabras no deseadas y palabras cortas
            filtered_words = [word for word in message_words 
                            if word not in stopwords 
                            and len(word) > 3 
                            and not word.startswith('http')
                            and not word.startswith('<')
                            and not word.endswith('>')]
            words.extend(filtered_words)
        
        # Unir palabras filtradas
        text = ' '.join(words)
        
        # Configurar y generar la nube de palabras
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            max_words=100,
            collocations=False,
            stopwords=stopwords
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
    
    try:
        content = file.read().decode('utf-8')
        df, members_info, error = process_chat_file(content)
        
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