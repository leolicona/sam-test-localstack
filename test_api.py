import requests
import base64
import sys
import os
import json

# Configuración
# Nota: La URL puede cambiar si recreamos el stack. Asegúrate de actualizarla.
API_URL = "https://d3lxglaakj.execute-api.localhost.localstack.cloud:4566/Prod/analyze" 
IMAGE_PATH = "test_image.jpg"

def test_analyze_image():
    # 1. Verificar imagen
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Error: No se encuentra la imagen '{IMAGE_PATH}'")
        create_dummy_image()
    
    print(f"📸 Leyendo imagen: {IMAGE_PATH}...")
    
    # 2. Codificar imagen a Base64
    with open(IMAGE_PATH, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # 3. Preparar payload JSON estándar
    # En un API REST moderno, enviamos un objeto JSON.
    payload = {
        "image": encoded_string
    }

    print(f"🚀 Enviando solicitud a {API_URL}...")
    
    try:
        # requests.post con json=... envía Content-Type: application/json automáticamente
        response = requests.post(API_URL, json=payload)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\n✅ ¡Éxito! Respuesta del servidor:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\n❌ Error del servidor:")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")

def create_dummy_image():
    print("⚠️  Creando imagen dummy de prueba (un cuadrado rojo)...")
    dummy_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
    with open(IMAGE_PATH, "wb") as f:
        f.write(base64.b64decode(dummy_b64))

if __name__ == "__main__":
    test_analyze_image()
