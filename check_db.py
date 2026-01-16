import boto3
import json
from decimal import Decimal

# Helper para convertir Decimals a float/int para imprimir JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def scan_table():
    # Conectarse a DynamoDB en LocalStack
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4566')
    table_name = 'ImageAnalysisResults'
    table = dynamodb.Table(table_name)

    try:
        print(f"🔍 Escaneando tabla: {table_name}...")
        response = table.scan()
        items = response.get('Items', [])
        
        print(f"📊 Total de items encontrados: {len(items)}")
        
        # Ordenar por timestamp descendente
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        if items:
            print("\n--- Últimos 3 Resultados ---")
            for item in items[:3]:
                print(json.dumps(item, cls=DecimalEncoder, indent=2))
                print("-" * 30)
        else:
            print("La tabla está vacía.")

    except Exception as e:
        print(f"❌ Error consultando DynamoDB: {e}")

if __name__ == "__main__":
    scan_table()
