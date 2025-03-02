from flask import Flask, render_template, request, jsonify
import os
import re
import pandas as pd
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

# Variable global para almacenar los datos del chat
chat_data = {
    'df': None,
    'members': None,
    'generator': None
}

def init_model():
    """Inicializa el modelo de generación de texto"""
    try:
        # Usar un modelo en español más ligero
        model_name = "PlanTL-GOB-ES/gpt2-base-bne"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        return generator
    except Exception as e:
        print(f"Error al cargar el modelo principal: {str(e)}")
        try:
            # Intentar con un modelo alternativo
            model_name = "bertin-project/bertin-gpt-j-6B-text"
            generator = pipeline(
                "text-generation",
                model=model_name,
                device="cuda" if torch.cuda.is_available() else "cpu"
            )
            return generator
        except Exception as e:
            print(f"Error al cargar el modelo alternativo: {str(e)}")
            return None

def process_chat_file(file_content):
    """Procesa el contenido del archivo de chat"""
    patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2})\s-\s([^:]+):\s(.+)',
        r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APMapm]{2})\s-\s([^:]+):\s(.+)',
        r'\[(\d{1,2}/\d{1,2}/\d{2,4}\s\d{1,2}:\d{2}:\d{2})\]\s([^:]+):\s(.+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, file_content, re.MULTILINE)
        if matches:
            df = pd.DataFrame(matches, columns=['datetime', 'sender', 'message'])
            
            # Contar mensajes por miembro y obtener top 15
            message_counts = df['sender'].value_counts()
            top_members = message_counts.head(15).index.tolist()
            
            # Filtrar DataFrame para incluir solo los top 15
            df = df[df['sender'].isin(top_members)]
            
            # Crear lista de miembros con su conteo de mensajes y estadísticas
            total_messages = len(matches)
            members_info = [
                {
                    'name': member,
                    'messages': int(message_counts[member]),
                    'percentage': round(message_counts[member] / total_messages * 100, 1),
                    'rank': idx + 1
                }
                for idx, member in enumerate(top_members)
            ]
            
            return df, members_info
    
    return None, None

@app.route('/')
def home():
    """Página principal"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Procesa el archivo de chat subido"""
    if 'file' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not file.filename.endswith('.txt'):
        return jsonify({'error': 'El archivo debe ser .txt'}), 400
    
    try:
        # Leer y procesar el archivo
        content = file.read().decode('utf-8')
        df, members_info = process_chat_file(content)
        
        if df is None or members_info is None:
            return jsonify({'error': 'Formato de chat no válido'}), 400
        
        # Guardar los datos procesados
        chat_data['df'] = df
        chat_data['members'] = [m['name'] for m in members_info]
        
        # Inicializar el modelo si no está cargado
        if chat_data['generator'] is None:
            chat_data['generator'] = init_model()
            if chat_data['generator'] is None:
                return jsonify({'error': 'No se pudo cargar el modelo'}), 500
        
        return jsonify({
            'success': True,
            'members': members_info
        })
    
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500

@app.route('/generate', methods=['POST'])
def generate_message():
    """Genera un mensaje para un miembro específico"""
    try:
        data = request.json
        member = data.get('member')
        prompt = data.get('prompt')
        
        if not member or not prompt:
            return jsonify({'error': 'Falta el miembro o el prompt'}), 400
        
        if chat_data['df'] is None or chat_data['generator'] is None:
            return jsonify({'error': 'No hay datos de chat cargados'}), 400
        
        # Obtener mensajes del miembro
        member_messages = chat_data['df'][chat_data['df']['sender'] == member]['message'].tolist()
        sample_messages = member_messages[-10:] if len(member_messages) > 10 else member_messages
        
        # Crear el contexto
        context = f"""Analizando mensajes de {member}. Ejemplos:
{chr(10).join(f'- {msg}' for msg in sample_messages)}

Basándote en estos ejemplos, genera una respuesta típica de {member} a: {prompt}
La respuesta debe mantener el mismo estilo, vocabulario y forma de escribir."""
        
        # Generar respuesta
        response = chat_data['generator'](
            context,
            max_length=100,
            num_return_sequences=1,
            temperature=0.8,
            do_sample=True,
            pad_token_id=50256
        )
        
        # Extraer y limpiar la respuesta
        generated_text = response[0]['generated_text']
        final_response = generated_text.split(prompt)[-1].strip()
        if not final_response:
            final_response = generated_text.split("respuesta")[-1].strip()
        
        return jsonify({
            'success': True,
            'response': final_response
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al generar mensaje: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True) 