import json
import boto3
import os
import uuid
import base64
import datetime
from decimal import Decimal

# Inicializar cliente de DynamoDB
# En LocalStack, el entorno suele autoconfigurarse, pero si estamos dentro del contenedor de Lambda
# creado por LocalStack, debería poder acceder a los servicios de LocalStack directamente.
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME')
table = dynamodb.Table(table_name) if table_name else None

def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))

    try:
        # 1. Obtener el cuerpo de la solicitud (la imagen)
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        # Simular decodificación si es necesario (para verificar que es una imagen válida, aunque aquí solo haremos mock)
        image_data = None
        if is_base64 and body:
            try:
                image_data = base64.b64decode(body)
                print(f"Imagen decodificada exitosamente. Tamaño: {len(image_data)} bytes")
            except Exception as e:
                print(f"Error decodificando base64: {str(e)}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid base64 encoding"})
                }
        elif body:
            # Asumimos que si no es base64, es texto plano o raw bytes (dependiendo del content-type)
            # Para este mock, solo registramos que recibimos datos.
            print(f"Body recibido (no base64). Longitud: {len(body)}")
        
        # 2. Mock del análisis de Gemini
        # En el futuro aquí llamaremos a la API de Gemini
        # Nota: Usamos Decimal para confidence porque DynamoDB no soporta float nativo con boto3 Table resource
        analysis_result = {
            "summary": "Análisis simulado: Se detecta un paisaje con montañas y un lago.",
            "tags": ["montaña", "lago", "naturaleza", "cielo azul"],
            "confidence": Decimal('0.98')
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
        else:
            print("ADVERTENCIA: TABLE_NAME no definido, no se guardó en DynamoDB")

        # 4. Retornar respuesta
        # Convertimos Decimal a float/str para JSON response
        response_analysis = analysis_result.copy()
        response_analysis['confidence'] = float(response_analysis['confidence'])

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Imagen recibida y analizada exitosamente (MOCK)",
                "imageId": item_id,
                "analysis": response_analysis
            })
        }

    except Exception as e:
        print(f"Error procesando la solicitud: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
