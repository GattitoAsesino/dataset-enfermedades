# Úppa — Dataset de Moho Verde (v1)

Dataset de imágenes para entrenar un clasificador binario que distingue
**champiñón sano** vs. **champiñón con moho verde** (*Trichoderma* spp.),
construido para alimentar la primera versión funcional de **Úppa** —
plataforma web descrita en `Memoria Tecnica.pdf`.

## Estructura

```
configs/sources.yaml          # taxonKeys, queries, límites por fuente
scripts/                      # fetchers + dedup + normalize + splits
data/manifest.csv             # ⭐ verdad única — toda imagen registra fuente, licencia, autor, md5
data/manifest_deduped.csv     # tras dedup md5 + perceptual
data/manifest_processed.csv   # tras normalización (sRGB, ≤1024px, sin EXIF)
data/raw/<fuente>/<clase>/    # archivos originales
data/processed/<clase>/       # archivos normalizados
data/splits/{train,val,test}.csv
reports/                      # logs de fetch, source_yields.md, review_*.html
DATASHEET.md                  # ficha del dataset (Gebru et al., 2021)
LICENSES.md                   # licencias agregadas y referencias
```

## Reproducir

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1. Descargar (idempotente; reanuda con base en source_id)
.venv/bin/python scripts/fetch_inaturalist.py
.venv/bin/python scripts/fetch_gbif.py
.venv/bin/python scripts/fetch_mushroom_observer.py
.venv/bin/python scripts/fetch_wikimedia.py
# (opcional) requiere ~/.kaggle/kaggle.json
.venv/bin/python scripts/fetch_kaggle.py

# 2. Reporte de yields por fuente
.venv/bin/python scripts/source_yields_report.py

# 3. Curado visual — abrir reports/review_<clase>.html en navegador
.venv/bin/python scripts/build_review_grid.py data/manifest.csv

# 4. Dedup (md5 + phash)
.venv/bin/python scripts/dedupe.py

# 5. Normalizar (sRGB, ≤1024px, strip EXIF)
.venv/bin/python scripts/normalize.py

# 6. Splits estratificados anti-fuga
.venv/bin/python scripts/make_splits.py

# 7. Verificación
.venv/bin/python scripts/check_leakage.py
.venv/bin/python scripts/sample_grid.py --n 30 --class moho_verde
.venv/bin/python scripts/sample_grid.py --n 30 --class sano
```

## Clases

- `sano` — *Agaricus bisporus* sin signos visibles de mohos competidores.
- `moho_verde` — colonias verdes de *Trichoderma* spp. (principalmente
  *T. aggressivum*, el patógeno dominante en cultivo de champiñón;
  *T. harzianum* y *T. viride* incluidos por compartir la firma visual).

## Caveats honestos

- *T. aggressivum* es subrepresentado en datos públicos (0 imágenes en
  GBIF al momento de armar este dataset). La clase `moho_verde` se apoya
  en *Trichoderma* genérico que comparte la firma visual del esporulado verde.
- La mayoría de fotos son de cuerpos fructíferos silvestres o de laboratorio,
  no de cultivo controlado mexicano. Para que el modelo generalice al caso
  de uso real de Úppa, **es indispensable** complementar con captura de campo
  en granjas mexicanas (planificado como v1.1).
- Las licencias agregan CC0 / CC-BY / CC-BY-NC / CC-BY-SA. Para uso comercial
  del modelo entrenado revisar restricciones por imagen en `manifest.csv`.

## Cumplimiento legal

- **Ley Federal del Derecho de Autor**: cada imagen registra licencia y autor.
- **Ley Federal de Protección de Datos Personales**: `normalize.py` elimina
  todo el EXIF antes de exportar a `data/processed/`.
- **NOM-081-FITO-2001**: las imágenes etiquetadas `moho_verde` documentan
  focos de infección con trazabilidad temporal vía `date_fetched`.

Ver `Memoria Tecnica.pdf` (p. 6) para contexto completo del proyecto Úppa.
