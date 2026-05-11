# Model Card — Úppa Moho Verde Detector v1

**Modelo**: YOLO11n (Ultralytics) fine-tuneado sobre dataset Úppa v1
**Tarea**: Clasificación binaria por imagen (sano vs. moho_verde)
**Formato**: YOLO detection con bbox que cubre toda la imagen

## Métricas en TEST (391 imágenes nunca vistas)

| Clase | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|
| moho_verde | 0.909 | 0.942 | **0.977** | 0.975 |
| sano | 0.913 | 0.967 | **0.982** | 0.982 |
| **promedio** | **0.911** | **0.954** | **0.979** | **0.978** |

mAP@50 en val (368 img): 0.981 → consistencia val/test ≈ no hay overfit visible.

## Datos de entrenamiento

- **Total**: 2,611 imágenes (1,414 sano + 1,197 moho_verde)
- **Splits**: 71% train / 14% val / 15% test, anti-fuga por observación
- **Fuentes**: iNaturalist (47%), GBIF (32%), Mushroom Observer (11%), Wikimedia (10%)
- **Especies**: *Agaricus bisporus* (sano) vs. *Trichoderma* spp. principalmente *T. aggressivum / harzianum / viride* (moho_verde)
- Ver `DATASHEET.md` para detalle completo

## Configuración de entrenamiento

| Parámetro | Valor |
|---|---|
| Modelo base | yolo11n.pt (pre-entrenado en COCO) |
| Optimizer | AdamW (auto-tuned) |
| Learning rate | 0.001667 |
| Batch | 16 |
| Image size | 640 |
| Epochs | 50 |
| AMP | enabled |
| GPU | NVIDIA RTX 4050 (6 GB) |
| Tiempo total | 16 minutos |

## Inferencia

```python
from ultralytics import YOLO
model = YOLO("runs/detect/runs/uppa/v1_yolo11n/weights/best.pt")
results = model.predict("imagen.jpg", conf=0.25)
for r in results:
    print(r.names[int(r.boxes.cls.argmax())], r.boxes.conf.max().item())
```

O usa el script incluido:
```bash
.venv/bin/python predict.py imagen.jpg
```

**Velocidad** (RTX 4050): 1.9 ms/imagen → throughput ≈ 500 img/s
**Tamaño del modelo**: 5.5 MB (`best.pt`)

## Caveats importantes

1. **No localiza dónde está el moho** — la bounding box cubre la imagen completa por diseño (ver `scripts/make_yolo.py`). Es un clasificador con pipeline de detector. Para localización real hace falta etiquetar bboxes manuales y reentrenar.

2. **Datos de origen son público, no de cultivo controlado mexicano** — el modelo puede degradarse en contexto real de fungicultura mexicana (iluminación de nave, sustrato típico, ángulos de cel del productor). Para producción real de Úppa hace falta complementar con captura de campo.

3. **Etiqueta moho_verde agrega varias especies** — no distingue *T. aggressivum* (el realmente patógeno en *A. bisporus*) de *T. harzianum/viride*. Suficiente para alerta temprana, no para identificación taxonómica fina.

4. **56% de imágenes son CC-BY-NC** — el modelo entrenado puede usarse libremente para investigación y demos sin fines de lucro. Para uso comercial revisa `LICENSES.md` y considera reentrenar con el subset comercial (~1,141 img).

5. **Una imagen del set de train resultó corrupta** y fue excluida automáticamente por Ultralytics: `gbif_5243447_6231332713_0.jpg`. No afecta resultados.

## Limitaciones conocidas

- Imágenes muy oscuras o con flash directo no fueron representadas en training.
- No hay imágenes de moho verde en sustrato (composta) sin cuerpo fructífero — el modelo se entrenó casi exclusivamente con cuerpo fructífero visible.
- Imágenes de microscopio fueron filtradas, así que el modelo no funciona ahí.

## Próximos pasos (roadmap)

- **v1.1**: captura de campo en granjas mexicanas — el cambio que más mejorará el modelo.
- **v2.0**: etiquetado por etapas (sano / incipiente / establecido / avanzado) — el valor diferencial real de Úppa frente al ojo humano empírico.
- **v2.1**: bounding boxes manuales para localización real, no solo clasificación.
- **v3.0**: multi-patógeno (mosquita, mancha bacteriana, cobweb) y multi-especie (Pleurotus, shiitake).
