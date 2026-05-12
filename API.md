# Úppa — Documentación de la API

Servicio HTTP que recibe una foto de seta (Pleurotus) y devuelve un diagnóstico JSON.

---

## 1. Levantar el servidor

```bash
cd uppa-model
source .venv/bin/activate     # (o crea el venv si es la primera vez — ver README.md)
python app.py
```

Cuando arranca verás algo como:

```
Running on local URL:  http://0.0.0.0:7860
```

El servidor queda escuchando en el puerto **7860**.

### Variables para configurar

Editar el final de `app.py`:

```python
demo.launch(
    server_name="0.0.0.0",   # "127.0.0.1" si solo quieres acceso local
    server_port=7860,         # cambia si el puerto está ocupado
    share=False,              # True para tunelar a una URL pública (.gradio.live)
)
```

### Docs auto-generadas de Gradio

Una vez arriba, abre en el navegador:

```
http://localhost:7860/?view=api
```

Te muestra los endpoints disponibles, sus parámetros y respuestas, además de snippets de código (Python, JavaScript, curl).

---

## 2. Schema de la respuesta

Toda llamada exitosa devuelve un objeto JSON con exactamente estas 8 claves:

```json
{
  "detectado":        true,
  "especie":          "Pleurotus ostreatus (seta)",
  "confianza":        0.9876,
  "sano":             false,
  "estado":           "Moho verde (Green Mold)",
  "confianza_salud":  0.9543,
  "mensaje_especie":  "La imagen se identificó como una seta del género Pleurotus.",
  "mensaje_salud":    "Enfermedad detectada: Moho verde (Green Mold). Recomendaciones: Aísla inmediatamente las bolsas afectadas... | Aumenta la ventilación..."
}
```

### Tabla de campos

| Campo | Tipo | Descripción |
|---|---|---|
| `detectado` | `bool` | `true` si la imagen contiene un hongo (cualquier especie). `false` solo cuando la imagen NO es un hongo. |
| `especie` | `string \| null` | `"Pleurotus ostreatus (seta)"`, `"Otra especie de hongo (no Pleurotus)"`, o `null` si no es hongo. |
| `confianza` | `float \| null` | Confianza [0–1] de la detección de especie. Para Pleurotus se agrega la probabilidad de las 4 clases de seta. |
| `sano` | `bool \| null` | `true` si es seta sana, `false` si es seta enferma, `null` si no es seta. |
| `estado` | `string \| null` | `"Sano"`, `"Mancha marrón (Brown Blotch)"`, `"Moho verde (Green Mold)"`, `"Pudrición blanda (Soft Rot)"`, o `null` si no es seta. |
| `confianza_salud` | `float \| null` | Confianza [0–1] del diagnóstico de salud. `null` si no aplica. |
| `mensaje_especie` | `string` | Texto explicativo sobre la especie detectada. |
| `mensaje_salud` | `string` | Texto con el diagnóstico + recomendaciones de tratamiento concatenadas con ` \| `. |

### Combinaciones posibles

| `class_index` interno | `detectado` | `especie` | `sano` | `estado` |
|---|---|---|---|---|
| 0 — Sano | `true` | Pleurotus | `true` | "Sano" |
| 1 — No es hongo | `false` | `null` | `null` | `null` |
| 2 — Brown Blotch | `true` | Pleurotus | `false` | "Mancha marrón..." |
| 3 — Green Mold | `true` | Pleurotus | `false` | "Moho verde..." |
| 4 — Soft Rot | `true` | Pleurotus | `false` | "Pudrición blanda..." |
| 5 — Otra especie | `true` | "Otra especie..." | `null` | `null` |

---

## 3. Cómo llamar la API

El endpoint registrado se llama **`/predict`** (configurado con `api_name="predict"` en `app.py`).

### 3.1 Python con `gradio_client` (recomendado)

Instala el cliente en el proyecto que va a consumir la API:

```bash
pip install gradio-client
```

Llamada básica:

```python
from gradio_client import Client, handle_file

client = Client("http://localhost:7860")

resultado = client.predict(
    image=handle_file("ruta/a/foto.jpg"),
    api_name="/predict",
)

print(resultado)
# {
#   "detectado": True,
#   "especie": "Pleurotus ostreatus (seta)",
#   ...
# }
```

Con una URL de imagen remota:

```python
resultado = client.predict(
    image=handle_file("https://ejemplo.com/seta.jpg"),
    api_name="/predict",
)
```

Con bytes en memoria (útil si la foto viene de un upload web):

```python
import tempfile

with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
    tmp.write(image_bytes)
    tmp_path = tmp.name

resultado = client.predict(image=handle_file(tmp_path), api_name="/predict")
```

### 3.2 JavaScript / TypeScript con `@gradio/client`

```bash
npm install @gradio/client
```

```js
import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7860");

// Desde un input <input type="file">
const fileInput = document.querySelector("#foto");
const file = fileInput.files[0];

const result = await client.predict("/predict", { image: file });
console.log(result.data);
// [{ detectado: true, especie: "...", confianza: 0.98, ... }]
```

El cliente devuelve `result.data` como un array — la respuesta JSON es el primer elemento.

### 3.3 HTTP directo con `curl`

Gradio requiere dos pasos: (1) subir el archivo, (2) llamar al endpoint con el handle devuelto.

```bash
# Paso 1: subir el archivo
UPLOAD=$(curl -s -X POST -F "files=@foto.jpg" http://localhost:7860/gradio_api/upload)
echo "Path: $UPLOAD"
# UPLOAD ahora contiene una ruta tipo: ["/tmp/gradio/.../foto.jpg"]

# Paso 2: llamar al endpoint
FILE_PATH=$(echo $UPLOAD | python3 -c "import json,sys; print(json.load(sys.stdin)[0])")

curl -X POST http://localhost:7860/gradio_api/call/predict \
  -H "Content-Type: application/json" \
  -d "{
    \"data\": [
      {\"path\": \"$FILE_PATH\", \"meta\": {\"_type\": \"gradio.FileData\"}}
    ]
  }"
# Devuelve: {"event_id": "abc123..."}

# Paso 3: leer el resultado del stream
curl -N http://localhost:7860/gradio_api/call/predict/abc123...
```

Si esto te parece engorroso, **usa `gradio_client`** (Python o JS); fue diseñado justamente para esconder esos 3 pasos.

### 3.4 Si quieres una API REST tradicional (FastAPI)

Si necesitas un endpoint plano POST con `multipart/form-data` (más simple para integrar con un backend), no uses Gradio para servir y en su lugar empaqueta `predict_json()` con FastAPI. Ejemplo:

```python
# server_fastapi.py
from fastapi import FastAPI, UploadFile
from PIL import Image
import io

from src.inference import predict_json

app = FastAPI()

@app.post("/predict")
async def predict_endpoint(image: UploadFile):
    img = Image.open(io.BytesIO(await image.read()))
    return predict_json(img)
```

Arrancar:

```bash
pip install fastapi uvicorn python-multipart
uvicorn server_fastapi:app --host 0.0.0.0 --port 8000
```

Llamada:

```bash
curl -X POST -F "image=@foto.jpg" http://localhost:8000/predict
```

---

## 4. Ejemplos de respuesta

### 4.1 Seta sana

```json
{
  "detectado": true,
  "especie": "Pleurotus ostreatus (seta)",
  "confianza": 1.0,
  "sano": true,
  "estado": "Sano",
  "confianza_salud": 1.0,
  "mensaje_especie": "La imagen se identificó como una seta del género Pleurotus.",
  "mensaje_salud": "La seta está sana. Recomendaciones: Mantén temperatura controlada entre 18 y 22 °C..."
}
```

### 4.2 Seta con moho verde (Trichoderma)

```json
{
  "detectado": true,
  "especie": "Pleurotus ostreatus (seta)",
  "confianza": 0.9421,
  "sano": false,
  "estado": "Moho verde (Green Mold)",
  "confianza_salud": 0.8732,
  "mensaje_especie": "La imagen se identificó como una seta del género Pleurotus.",
  "mensaje_salud": "Enfermedad detectada: Moho verde (Green Mold). Recomendaciones: Aísla inmediatamente las bolsas afectadas... | Aumenta la ventilación..."
}
```

### 4.3 Imagen no es un hongo

```json
{
  "detectado": false,
  "especie": null,
  "confianza": 0.9987,
  "sano": null,
  "estado": null,
  "confianza_salud": null,
  "mensaje_especie": "La imagen no parece contener un hongo. Sube una foto clara de tu seta tomada de frente o de costado, con buena iluminación.",
  "mensaje_salud": "No se evaluó la salud porque la imagen no corresponde a una seta."
}
```

### 4.4 Hongo pero no es seta (ej. champiñón)

```json
{
  "detectado": true,
  "especie": "Otra especie de hongo (no Pleurotus)",
  "confianza": 0.8775,
  "sano": null,
  "estado": null,
  "confianza_salud": null,
  "mensaje_especie": "Se detectó un hongo pero no es una seta (Pleurotus). Úppa actualmente solo analiza setas.",
  "mensaje_salud": "No se evaluó la salud porque la imagen no corresponde a una seta."
}
```

---

## 5. Códigos de error

Gradio devuelve códigos HTTP estándar. Los más comunes en este servicio:

| Código | Significado | Causa típica |
|---|---|---|
| `200` | OK | La predicción se ejecutó correctamente. |
| `400` | Bad Request | El archivo subido no es una imagen válida (PIL no la puede abrir). |
| `404` | Not Found | El `api_name` no coincide. Verifica que sea `/predict`. |
| `500` | Internal Server Error | Falló la inferencia. Revisa los logs del servidor (`python app.py`). |

---

## 6. Desempeño esperado

- **Latencia por imagen**: ~80–150 ms en CPU (Intel i5 promedio), modelo TFLite ~2 MB.
- **Throughput**: ~10–15 imágenes/segundo en una sola CPU (el modelo es secuencial).
- **Memoria**: ~400 MB con TensorFlow completo, ~50 MB con `tflite-runtime`.
- **Cold start**: la primera llamada tarda ~1 s adicional para cargar el modelo en memoria. Llamadas subsecuentes reutilizan la sesión.

---

## 7. Producción (futuro)

El servidor de Gradio **no está pensado para producción a escala** (un solo worker, sin autenticación). Para producción real:

1. Reemplazar Gradio por FastAPI (sección 3.4) detrás de un reverse proxy (nginx).
2. Empaquetar en Docker con `gunicorn` + `uvicorn` workers.
3. Agregar autenticación con API keys (header `X-API-Key`).
4. Cachear resultados por hash de imagen.
5. Métricas con Prometheus + Grafana.

Para el concurso de demostración, Gradio es perfecto.

---

## 8. Troubleshooting

| Síntoma | Causa | Solución |
|---|---|---|
| `Connection refused` al llamar | Servidor no está corriendo o puerto incorrecto | `python app.py` y verificar el puerto en los logs |
| `Address already in use` al arrancar | Otro proceso ocupa el 7860 | Cambia `server_port` en `app.py` o mata el proceso: `lsof -ti:7860 \| xargs kill` |
| Respuesta es siempre clase 1 ("no es hongo") | Imagen muy pequeña o muy oscura | Sube fotos con resolución ≥ 300×300 px y buena iluminación |
| `confianza` muy bajo (<50%) | Foto con mucho fondo / ángulo malo | Recortar para que la seta llene >70% del frame |
| `gradio_client` arroja `AttributeError: handle_file` | Versión vieja del cliente | `pip install --upgrade gradio-client` |
