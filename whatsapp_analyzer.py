# %% [markdown]
# # 🤖 WhatsApp Chat Style Mimicker
# 
# Este script analiza un chat de WhatsApp y puede imitar cómo habla cada persona.
# 
# ## 📝 Antes de empezar:
# 1. Exporta un chat de WhatsApp (sin medios)
# 2. Pon el archivo .txt en esta carpeta
# 3. Instala las dependencias necesarias

# %% [markdown]
# ## 📚 Importar lo necesario

# %%
import os
import re
import pandas as pd
from datetime import datetime
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

print("🔧 Configurando el modelo...")

# Usar un modelo más ligero y gratuito
model_name = "facebook/blenderbot-400M-distill"
try:
    # Inicializar el generador de texto
    generator = pipeline(
        "text-generation",
        model=model_name,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    print("✅ Modelo cargado correctamente")
except Exception as e:
    print(f"❌ Error al cargar el modelo: {str(e)}")
    print("Intentando descargar el modelo primero...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        print("✅ Modelo descargado y cargado correctamente")
    except Exception as e:
        raise Exception(f"❌ No se pudo cargar el modelo: {str(e)}")

# %% [markdown]
# ## 📂 Buscar archivos de chat

# %%
# Ver qué archivos de chat hay disponibles
chat_files = [f for f in os.listdir() if f.endswith('.txt')]

print("📁 Archivos encontrados:")
for i, file in enumerate(chat_files, 1):
    print(f"{i}. {file}")

if not chat_files:
    print("❌ No se encontraron archivos .txt")
    raise Exception("Necesitas exportar un chat de WhatsApp primero")

# Elegir un archivo
file_number = int(input("\nElige el número del archivo a analizar: "))
selected_file = chat_files[file_number - 1]
print(f"Archivo seleccionado: {selected_file}")

# %% [markdown]
# ## 📖 Leer y procesar el chat

# %%
# Leer el archivo y mostrar las primeras líneas para debug
with open(selected_file, 'r', encoding='utf-8') as file:
    content = file.read()
    
print("Primeras 5 líneas del archivo:")
print("\n".join(content.split('\n')[:5]))
print("\nTotal de líneas:", len(content.split('\n')))

# Intentar diferentes patrones de regex para WhatsApp
patterns = [
    # Patrón 1: Formato típico de WhatsApp
    r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2})\s-\s([^:]+):\s(.+)',
    
    # Patrón 2: Con AM/PM
    r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APMapm]{2})\s-\s([^:]+):\s(.+)',
    
    # Patrón 3: Formato alternativo
    r'\[(\d{1,2}/\d{1,2}/\d{2,4}\s\d{1,2}:\d{2}:\d{2})\]\s([^:]+):\s(.+)'
]

matches = []
used_pattern = None

for pattern in patterns:
    matches = re.findall(pattern, content, re.MULTILINE)
    if matches:
        used_pattern = pattern
        print(f"\n✅ Patrón encontrado: {pattern}")
        print(f"Mensajes encontrados: {len(matches)}")
        break

if not matches:
    print("\n❌ No se pudo encontrar un patrón válido en el archivo")
    print("Por favor, verifica que el archivo es una exportación de WhatsApp")
    raise Exception("Formato de archivo no reconocido")

# Crear DataFrame
df = pd.DataFrame(matches, columns=['datetime', 'sender', 'message'])
print("\nEstructura del DataFrame:")
print(df.head())

# Ver miembros del chat
members = df['sender'].unique().tolist()
print(f"\n👥 Miembros encontrados ({len(members)}):")
for i, member in enumerate(members, 1):
    print(f"{i}. {member}")

if not members:
    print("❌ No se encontraron miembros en el chat")
    raise Exception("No se pudieron extraer los miembros del chat")

# %% [markdown]
# ## 🎯 Seleccionar miembro y analizar su estilo

# %%
# Elegir miembro
member_number = int(input("\nElige el número del miembro a imitar: "))
selected_member = members[member_number - 1]

# Obtener mensajes del miembro
member_messages = df[df['sender'] == selected_member]['message'].tolist()
sample_messages = member_messages[-20:] if len(member_messages) > 20 else member_messages

print(f"\nAnalizando los últimos {len(sample_messages)} mensajes de {selected_member}")
print("\nEjemplos de mensajes:")
for i, msg in enumerate(sample_messages[:3], 1):
    print(f"{i}. {msg}")

# %% [markdown]
# ## 💬 Generar mensaje en su estilo

# %%
# Preparar el prompt
prompt = input("\nEscribe el mensaje que quieres generar: ")

# Crear el contexto con los mensajes de ejemplo
context = "\n".join([
    "Ejemplos de cómo habla esta persona:",
    *[f"- {msg}" for msg in sample_messages[-5:]],  # Usar los últimos 5 mensajes como ejemplo
    "\nAhora, responde en el mismo estilo a este mensaje:",
    prompt
])

try:
    # Generar respuesta
    response = generator(
        context,
        max_length=150,
        num_return_sequences=1,
        temperature=0.7,
        do_sample=True
    )

    # Extraer la respuesta generada
    generated_text = response[0]['generated_text']
    # Limpiar la respuesta (quedarnos solo con la última parte después del prompt)
    final_response = generated_text.split(prompt)[-1].strip()

    print(f"\n💬 Mensaje generado en el estilo de {selected_member}:")
    print(final_response)
except Exception as e:
    print(f"❌ Error al generar el mensaje: {str(e)}")
    print("Intenta con un prompt más corto o diferente")

# %% [markdown]
# ## 🎭 Generar mensaje típico de cada miembro

# %%
print("🔄 Verificando el modelo...")

# Asegurarnos de que el modelo está cargado y que tenemos datos
if 'generator' not in locals():
    print("⚙️ Cargando el modelo...")
    try:
        # Usar un modelo más ligero y en español
        model_name = "PlanTL-GOB-ES/gpt2-base-bne"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        print("✅ Modelo cargado correctamente")
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {str(e)}")
        print("Intentando un modelo alternativo...")
        try:
            # Intentar con un modelo más pequeño
            model_name = "bertin-project/bertin-gpt-j-6B-text"
            generator = pipeline(
                "text-generation",
                model=model_name,
                device="cuda" if torch.cuda.is_available() else "cpu"
            )
            print("✅ Modelo alternativo cargado correctamente")
        except Exception as e:
            print(f"❌ Error al cargar el modelo alternativo: {str(e)}")
            raise Exception("No se pudo cargar ningún modelo de generación de texto")

# Verificar que tengamos datos de chat y miembros
if not members or df is None:
    print("❌ Error: No hay datos de chat o miembros cargados. Por favor, analiza un archivo de chat primero.")
    raise Exception("No hay datos de chat cargados")

print("\n💬 Generando mensajes típicos de cada miembro...")

# Prompts variados para obtener diferentes tipos de mensajes
prompts = [
    # Relacionados con beber/fiesta
    "¿Alguien se apunta a unas cervezas?",
    "¿Quedamos en el bar de siempre?",
    "¿Quién viene de cubatas?",
    "¿Hacemos una previa antes de salir?",
    "¿Alguien tiene resaca hoy? 🤢",
    "¿Dónde nos tomamos la última?",
    
    # Relacionados con música/tocar
    "¿Ensayamos esta tarde?",
    "¿Quién trae las partituras?",
    "¿Alguien tiene las baquetas de repuesto?",
    "¿A qué hora es el bolo del sábado?",
    "¿Quién puede sustituirme en el ensayo?",
    "¿Habéis visto el nuevo local de ensayo?",
    
    # Mezcla de ambos
    "¿Cerveza después del ensayo?",
    "¿Quedamos antes de tocar para tomar algo?",
    "¿Alguien se acuerda qué tocamos ayer? 😅",
    "¿Quién viene al concierto? Primera ronda va por mi cuenta 🍺",
    "¿Os acordáis de la última vez que tocamos borrachos?",
    "¿Hacemos una jam session en el bar?",
    
    # Situaciones específicas
    "¿Quién se encarga de las bebidas para el local?",
    "¿Alguien grabó el ensayo de ayer? No me acuerdo de nada 🤣",
    "¿Dónde dejé mi instrumento anoche?",
    "¿Quién conduce hoy? Yo quiero beber",
    "¿Repetimos lo del otro día en el bar?",
    "¿Os acordáis de la última vez que tocamos en ese garito?"
]

# Para cada miembro, generar respuestas a todos los prompts
for member in members:
    print(f"\n👤 Generando mensajes típicos de: {member}")
    print("=" * 50)
    
    try:
        # Obtener mensajes del miembro
        member_messages = df[df['sender'] == member]['message'].tolist()
        if not member_messages:
            print("⚠️ No se encontraron mensajes para este miembro")
            continue
            
        # Usar los últimos 10 mensajes o todos si hay menos
        sample_messages = member_messages[-10:] if len(member_messages) > 10 else member_messages
        
        # Generar respuesta para cada prompt
        for prompt in prompts:
            print(f"\n🗨️ Prompt: {prompt}")
            
            # Crear el contexto con los mensajes de ejemplo
            context = f"""Analizando mensajes de {member}. Ejemplos:
{chr(10).join(f'- {msg}' for msg in sample_messages)}

Basándote en estos ejemplos, genera una respuesta típica de {member} a: {prompt}
La respuesta debe mantener el mismo estilo, vocabulario y forma de escribir."""

            try:
                # Generar respuesta
                response = generator(
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
                
                print(f"💭 Respuesta: {final_response}")
                
            except Exception as e:
                print(f"❌ Error al generar respuesta: {str(e)}")
            
            print("-" * 30)
    
    except Exception as e:
        print(f"❌ Error general al procesar miembro: {str(e)}")
    finally:
        print("=" * 50)

print("\n✅ Generación de mensajes típicos completada!")

# %% [markdown]
# ## 🔄 ¿Generar otro mensaje?

# %%
# Puedes ejecutar la celda anterior de nuevo con un prompt diferente
# O volver a la celda de selección de miembro para elegir otra persona 