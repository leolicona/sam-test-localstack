# SAM Test LocalStack

Este proyecto es una aplicación serverless de ejemplo configurada para ejecutarse localmente utilizando **LocalStack** y **Docker Compose**, lo que permite simular un entorno de AWS completo en tu máquina sin costos ni conexión a internet.

## Estructura del Proyecto

- `hello_world/`: Código de la función Lambda (Python 3.12).
- `events/`: Eventos JSON para pruebas locales.
- `tests/`: Tests unitarios y de integración.
- `template.yaml`: Plantilla SAM que define la infraestructura (Lambda, API Gateway).
- `docker-compose.yaml`: Configuración para levantar LocalStack en Docker.
- `.env`: Variables de entorno para la configuración de Docker.

## Prerrequisitos

Asegúrate de tener instaladas las siguientes herramientas:

### Instalación en macOS (Homebrew)

Si estás configurando tu entorno desde cero, utiliza Homebrew para instalar las herramientas base y pip para los wrappers:

```bash
# 1. Instalar Docker y herramientas AWS
brew install --cask docker
brew install awscli aws-sam-cli

# 2. Instalar LocalStack CLI (Opcional, útil para debug)
brew install localstack/tap/localstack-cli

# 3. Instalar Wrappers de Python (Esenciales para facilitar comandos)
pip3 install aws-local aws-sam-cli-local
```

Al finalizar, deberías tener disponibles los comandos `docker`, `sam`, `awslocal` y `samlocal`.

## Configuración Inicial

1.  **Variables de Entorno**:
    Asegúrate de tener un archivo `.env` en la raíz del proyecto (ya incluido en `.gitignore`).
    
    ```bash
    # .env
    LOCALSTACK_DOCKER_NAME=localstack_main
    LOCALSTACK_VOLUME_DIR=./volume
    ```

2.  **Levantar el Entorno (LocalStack)**:
    Inicia el contenedor de LocalStack en segundo plano.

    ```bash
    docker-compose up -d
    ```

    Verifica que esté corriendo:
    ```bash
    docker ps
    ```
    Deberías ver un contenedor llamado `localstack_main` (o el nombre que hayas definido) escuchando en el puerto `4566`.

## Build y Deploy

El ciclo de desarrollo es el siguiente:

1.  **Construir la aplicación**:
    Compila el código y prepara las dependencias.

    ```bash
    sam build
    ```

2.  **Desplegar en LocalStack**:
    Utiliza `samlocal` para desplegar la infraestructura en tu contenedor local.

    ```bash
    samlocal deploy
    ```
    *Nota: `samlocal` es un wrapper que redirige automáticamente los comandos a `http://localhost:4566`.*

## Probar la Aplicación

Una vez desplegado, obtendrás una URL de salida (Output) similar a:
`https://<api_id>.execute-api.localhost.localstack.cloud:4566/Prod/hello/`

Puedes probarla con `curl`:

```bash
curl https://<api_id>.execute-api.localhost.localstack.cloud:4566/Prod/hello/
```

Respuesta esperada:
```json
{"message": "hello world"}
```

## Comandos Útiles

- **Ver logs de LocalStack**:
  ```bash
  docker logs -f localstack_main
  ```

- **Listar Lambdas creadas**:
  ```bash
  awslocal lambda list-functions
  ```

- **Detener el entorno**:
  ```bash
  docker-compose down
  ```

## Tests

Para ejecutar los tests unitarios:

```bash
pip install -r tests/requirements.txt
python -m pytest tests/unit -v
```
