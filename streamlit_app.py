import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re
from io import BytesIO
import base64
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
plt.style.use('seaborn')

# Configuración de la página
st.set_page_config(
    page_title="📊 Analizador de Chat de WhatsApp",
    page_icon="📱",
    layout="wide"
)

# Título y descripción
st.title("📊 Analizador de Chat de WhatsApp")
st.markdown("""
Esta aplicación analiza chats de WhatsApp y genera visualizaciones estadísticas.
""")

def process_chat_file(content):
    """Procesa el contenido del archivo de chat"""
    patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2})\s-\s([^:]+):\s(.+)',
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APMapm]{2})\s-\s([^:]+):\s(.+)',
        r'\[(\d{1,2}/\d{1,2}/\d{2,4}\s\d{1,2}:\d{2}:\d{2})\]\s([^:]+):\s(.+)'
    ]
    
    matches = []
    used_pattern = None
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            used_pattern = pattern
            st.success(f"✅ Se encontraron {len(matches)} mensajes")
            break
    
    if not matches:
        st.error("No se encontró un patrón válido en el archivo")
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
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        
        members_info.append({
            'name': member,
            'messages': member_count,
            'percentage': round(member_count / total_messages * 100, 1),
            'top_words': top_words
        })
    
    return df, members_info, None

def generate_plots(df):
    """Genera todas las visualizaciones"""
    col1, col2 = st.columns(2)
    
    with col1:
        # 1. Mensajes por persona
        st.subheader("📊 Mensajes por Persona")
        fig, ax = plt.subplots(figsize=(10, 6))
        messages_per_person = df['sender'].value_counts().head(20)
        messages_per_person.plot(kind='bar', color='skyblue', ax=ax)
        plt.title('Top 20: Mensajes por persona')
        plt.xlabel('Miembro')
        plt.ylabel('Número de mensajes')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)
        plt.close()
        
        # 2. Distribución de tipos de mensajes
        st.subheader("📱 Tipos de Mensajes")
        fig, ax = plt.subplots(figsize=(8, 8))
        type_counts = df['type'].value_counts()
        type_counts.plot(kind='pie', autopct='%1.1f%%', colors=['lightcoral', 'lightblue'], ax=ax)
        plt.title('Distribución de tipos de mensajes')
        st.pyplot(fig)
        plt.close()
    
    with col2:
        # 3. Actividad diaria
        st.subheader("📈 Actividad Diaria")
        fig, ax = plt.subplots(figsize=(10, 6))
        daily_activity = df.resample('D', on='datetime').size()
        daily_activity.plot(kind='line', color='green', ax=ax)
        plt.title('Actividad diaria del chat')
        plt.xlabel('Fecha')
        plt.ylabel('Número de mensajes')
        st.pyplot(fig)
        plt.close()
        
        # 4. Actividad por hora
        st.subheader("🕒 Actividad por Hora")
        fig, ax = plt.subplots(figsize=(10, 6))
        df['hour'].value_counts().sort_index().plot(kind='bar', ax=ax)
        plt.title('Actividad por hora del día')
        plt.xlabel('Hora')
        plt.ylabel('Número de mensajes')
        st.pyplot(fig)
        plt.close()
    
    # 5. Actividad por día de la semana
    st.subheader("📅 Actividad Semanal")
    fig, ax = plt.subplots(figsize=(10, 6))
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_names_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    activity = df['day_of_week'].value_counts().reindex(day_order)
    activity.index = day_names_es
    activity.plot(kind='bar', ax=ax)
    plt.title('Actividad por día de la semana')
    plt.xlabel('Día')
    plt.ylabel('Número de mensajes')
    st.pyplot(fig)
    plt.close()

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
        
        # Crear y mostrar la figura
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        plt.close()
        
    except Exception as e:
        st.error(f"Error generando nube de palabras: {str(e)}")

# Sidebar
st.sidebar.header("📤 Subir Chat")
uploaded_file = st.sidebar.file_uploader("Selecciona un archivo de chat", type=['txt'])

if uploaded_file:
    # Leer y procesar el archivo
    content = uploaded_file.getvalue().decode('utf-8')
    df, members_info, error = process_chat_file(content)
    
    if error:
        st.error(error)
    else:
        # Mostrar estadísticas generales
        st.header("📊 Estadísticas Generales")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Mensajes", len(df))
        with col2:
            st.metric("Participantes", len(members_info))
        with col3:
            st.metric("Período", f"{df['datetime'].min().strftime('%d/%m/%y')} - {df['datetime'].max().strftime('%d/%m/%y')}")
        
        # Generar visualizaciones
        generate_plots(df)
        
        # Selector de miembro
        st.header("👤 Análisis por Miembro")
        selected_member = st.selectbox(
            "Selecciona un miembro para ver sus estadísticas:",
            options=[m['name'] for m in members_info]
        )
        
        if selected_member:
            # Mostrar información del miembro
            member_info = next(m for m in members_info if m['name'] == selected_member)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"Estadísticas de {selected_member}")
                st.write(f"📝 Mensajes: {member_info['messages']}")
                st.write(f"📊 Porcentaje del chat: {member_info['percentage']}%")
                st.write("🔤 Palabras más usadas:")
                for word, count in member_info['top_words']:
                    st.write(f"- {word}: {count} veces")
            
            with col2:
                st.subheader("🔤 Nube de Palabras")
                generate_member_wordcloud(df, selected_member)
else:
    # Instrucciones cuando no hay archivo
    st.info("👋 ¡Bienvenido al Analizador de Chat de WhatsApp!")
    st.markdown("""
    Para comenzar:
    1. Exporta un chat de WhatsApp (sin medios)
    2. Sube el archivo .txt usando el botón en el panel izquierdo
    3. Explora las estadísticas y visualizaciones
    
    ℹ️ Los datos se procesan localmente y no se almacenan en ningún servidor.
    """)

# Footer
st.markdown("---")
st.markdown("Desarrollado con ❤️ usando Streamlit") 