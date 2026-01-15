import json
import boto3
import os
import uuid
import base64
import datetime
from decimal import Decimal
from google import genai
from google.genai import types

# Inicializar cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME')
table = dynamodb.Table(table_name) if table_name else None

# Inicializar cliente de Gemini
gemini_api_key = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None

def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))

    try:
        # 1. Obtener el cuerpo de la solicitud
        raw_body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        image_data = None
        
        # Intentar detectar si es JSON con campo 'image' o 'body'
        try:
            # Si viene como base64 desde APIGW (ej: binary media types), decodificar primero
            if is_base64:
                decoded_body = base64.b64decode(raw_body).decode('utf-8')
                payload = json.loads(decoded_body)
            else:
                payload = json.loads(raw_body) if raw_body else {}
                
            # Extraer imagen del payload JSON
            if 'image' in payload:
                image_b64 = payload['image']
                image_data = base64.b64decode(image_b64)
            elif 'body' in payload: # Compatibilidad con el script anterior
                image_b64 = payload['body']
                image_data = base64.b64decode(image_b64)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Si falla JSON, intentar tratar el raw body como la imagen directa en base64
            # (Caso fallback o binary directo)
            if is_base64:
                 image_data = base64.b64decode(raw_body)
            pass

        if not image_data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No valid image data found. Send JSON with 'image' field containing base64 string."})
            }
        
        print(f"Imagen decodificada exitosamente. Tamaño: {len(image_data)} bytes")
        
        # 2. Análisis con Gemini (Real)
        analysis_result = {}
        if client and image_data:
            try:
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type='image/jpeg',
                        ),
                        'Describe this image in detail. Return a JSON with "summary" (string), "tags" (list of strings), and "confidence" (number between 0 and 1).'
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json'
                    )
                )
                
                print(f"Respuesta Raw de Gemini: {response.text}")
                parsed_response = json.loads(response.text)
                
                analysis_result = {
                    "summary": parsed_response.get('summary', 'No summary available'),
                    "tags": parsed_response.get('tags', []),
                    "confidence": Decimal(str(parsed_response.get('confidence', 0.99)))
                }

            except Exception as e:
                print(f"Error llamando a Gemini: {str(e)}")
                analysis_result = {
                    "error": str(e),
                    "summary": "Error analizando imagen",
                    "confidence": Decimal('0')
                }
        else:
             analysis_result = {
                "summary": "Modo Simulado (No API Key found)",
                "confidence": Decimal('0.0')
            }

        # 3. Guardar en DynamoDB
        item_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        item = {
            'imageId': item_id,
            'timestamp': timestamp,
            'analysis': analysis_result,
            'status': 'PROCESSED'
        }
        
        if table:
            table.put_item(Item=item)
            print(f"Item guardado en DynamoDB: {item_id}")

        # 4. Retornar respuesta
        response_analysis = analysis_result.copy()
        if 'confidence' in response_analysis:
            response_analysis['confidence'] = float(response_analysis['confidence'])

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Imagen procesada exitosamente",
                "imageId": item_id,
                "analysis": response_analysis
            })
        }

    except Exception as e:
        print(f"Error procesando la solicitud: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
