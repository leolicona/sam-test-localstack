#!/bin/bash

# Detener el script si hay errores
set -e

echo "🔨 Construyendo la aplicación..."
sam build

echo "🚀 Desplegando en LocalStack..."
# Nota: Ya no pasamos GeminiApiKey porque la Lambda la leerá de Secrets Manager
samlocal deploy \
  --stack-name sam-app \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM

echo "✅ Despliegue completado."