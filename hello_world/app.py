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
                # Definir el esquema deseado para el análisis de tickets
                prompt = """
                Analyze this receipt image and extract the following information in JSON format:
                {
                    "store_name": "Name of the store",
                    "store_address": "Address or location of the store",
                    "date": "Date of purchase in YYYY-MM-DD format",
                    "time": "Time of purchase in HH:MM format",
                    "total_amount": "Total amount paid (number)",
                    "currency": "Currency code (e.g., MXN, USD)",
                    "items": [
                        {
                            "description": "Product description",
                            "quantity": "Quantity (number)",
                            "unit_price": "Unit price (number)",
                            "total_price": "Total price for this item (number)",
                            "category": "Inferred category (e.g., Grocery, Clothing, Electronics)"
                        }
                    ],
                    "payment_method": "Payment method (e.g., Cash, Credit Card)",
                    "summary": "Brief summary of the purchase"
                }
                If any field is missing or unclear, use null.
                """

                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type='image/jpeg',
                        ),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json'
                    )
                )
                
                print(f"Respuesta Raw de Gemini: {response.text}")
                parsed_response = json.loads(response.text)
                
                # Convertir floats a Decimal para DynamoDB
                def float_to_decimal(obj):
                    if isinstance(obj, float):
                        return Decimal(str(obj))
                    if isinstance(obj, dict):
                        return {k: float_to_decimal(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [float_to_decimal(v) for v in obj]
                    return obj

                analysis_result = float_to_decimal(parsed_response)

            except Exception as e:
                print(f"Error llamando a Gemini: {str(e)}")
                analysis_result = {
                    "error": str(e),
                    "summary": "Error analizando imagen",
                }
        else:
             analysis_result = {
                "summary": "Modo Simulado (No API Key found)",
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
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [decimal_to_float(v) for v in obj]
            return obj

        response_analysis = decimal_to_float(analysis_result)

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
