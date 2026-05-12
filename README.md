# Úppa — Detector de enfermedades en setas

Plataforma de visión por computadora que analiza fotos de setas (Pleurotus / oyster mushroom) y entrega:

- **Especie**: detecta si la imagen es una seta, otro tipo de hongo, o un objeto no relacionado.
- **Estado**: clasifica si la seta está sana o presenta alguna de tres enfermedades comunes en producción.
- **Tratamiento**: lista recomendaciones específicas en español para fungicultores.

## Clases que detecta el modelo

| # | Clase | Significado |
|---|---|---|
| 0 | Healthy Oyster Mushroom | Seta sana |
| 1 | Invalid Identification | La imagen no contiene un hongo |
| 2 | Brown Blotch | Enfermedad bacteriana (Pseudomonas tolaasii) |
| 3 | Green Mold | Contaminación por Trichoderma spp. (moho verde) |
| 4 | Soft Rot | Pudrición blanda (Pectobacterium carotovorum) |
| 5 | Not an Oyster Mushroom | Hongo de otra especie |

## Replicación rápida en otra laptop

Requisitos: Python 3.9, 3.10 u 3.11 (no recomendado 3.12 todavía con tensorflow 2.15).

```bash
# 1. Clonar este repo
git clone <url-del-repo>
cd uppa-model

# 2. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate            # Windows PowerShell

# 3. Instalar dependencias (la versión completa con TensorFlow)
pip install -r requirements.txt

# 4a. Probar inferencia desde terminal
python predict.py ruta/a/foto.jpg

# 4b. Lanzar demo web en http://localhost:7860
python app.py
```

### Alternativa ligera (sin TensorFlow completo)

Si TensorFlow falla al instalar (típico en Mac M1/M2 o máquinas con poca RAM):

```bash
pip install -r requirements-lite.txt
```

Esto usa `tflite-runtime` que solo trae el intérprete (~5 MB en lugar de ~500 MB).

### Troubleshooting

| Problema | Solución |
|---|---|
| `tensorflow` no instala en Mac M1/M2 | `pip install tensorflow-macos tensorflow-metal` en lugar de `tensorflow` |
| `OSError: ... model_unquant.tflite` | Verifica que el archivo existe en `models/` (debe pesar ~2 MB) |
| Gradio no abre puerto 7860 | Cambia a `demo.launch(server_port=8080)` en `app.py` |
| Imports fallan al ejecutar | Asegúrate de correr los comandos desde la raíz del repo (`uppa-model/`), no desde `src/` |

## Estructura del repo

```
uppa-model/
├── README.md                  # este archivo
├── requirements.txt           # dependencias TensorFlow completo
├── requirements-lite.txt      # alternativa con tflite-runtime
├── predict.py                 # CLI: python predict.py foto.jpg
├── app.py                     # demo web con Gradio
├── models/
│   └── model_unquant.tflite   # modelo TFLite pre-entrenado
└── src/
    ├── inference.py           # función predict()
    ├── labels.py              # las 6 clases del modelo
    └── treatments.py          # recomendaciones por enfermedad
```

## Detalles técnicos del modelo

- **Backbone**: MobileNet fine-tuned vía Google Teachable Machine
- **Input**: 224×224×3 RGB, normalizado a [0, 1]
- **Output**: 6 probabilidades softmax
- **Tamaño**: ~2 MB

El modelo proviene del proyecto open-source **Mushease** ([naksusen/mushroom-disease-detector](https://github.com/naksusen/mushroom-disease-detector)) que originalmente lo distribuye dentro de una aplicación Android. Úppa lo reutiliza en un pipeline Python para uso desktop / web.

## Limitaciones conocidas

- El modelo fue entrenado principalmente sobre fotos de Pleurotus ostreatus en condiciones de cultivo controlado. Su precisión en fotos de smartphone en producción rural mexicana puede variar.
- No distingue subespecies dentro del género Pleurotus.
- La clase "Not an Oyster Mushroom" puede confundir champiñones (Agaricus) con setas si la foto está mal encuadrada.

## Próximos pasos sugeridos

- Recolectar 50–100 fotos de fungicultores mexicanos para fine-tuning específico.
- Añadir un modelo independiente de clasificación multi-especie de hongos comestibles.
- Empaquetar como API REST (FastAPI) para integrar con el frontend web de Úppa.

## Licencia

El modelo `model_unquant.tflite` es atribuible al proyecto Mushease. Este repo de integración es para propósitos del concurso académico de Úppa.
