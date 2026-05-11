# Licencias del Dataset Úppa Moho Verde v1

Cada imagen del dataset registra su licencia individual en
`data/manifest.csv` (columna `license`) y el autor en la columna `author`.
Toda redistribución debe respetar la licencia de cada imagen.

## Distribución agregada (manifiesto procesado)

| Licencia | Imágenes | % |
|---|---|---|
| CC-BY-NC-4.0 | 1346 | 51.6% |
| CC0-1.0 | 503 | 19.3% |
| CC-BY-SA-4.0 | 347 | 13.3% |
| CC-BY-4.0 | 291 | 11.1% |
| CC-BY-NC-ND-4.0 | 103 | 3.9% |
| CC-BY-NC-SA-4.0 | 21 | 0.8% |
| **TOTAL** | **2611** | 100% |

## Implicaciones para Úppa

Como ~56% de las imágenes son **NC (Non-Commercial)**, el dataset agregado
sólo se puede usar para:

- Entrenamiento del modelo en uso académico, demostraciones, MVPs sin fines de
  lucro directo.
- Investigación interna del proyecto.

**Para uso comercial del modelo entrenado** (Úppa SaaS de pago):

1. Filtrar el manifiesto para entrenar **únicamente con licencias comerciales**:
   `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0` → ~1,141 imágenes (~44% del dataset).
2. O re-licenciar las imágenes NC contactando a sus autores (lista en
   `manifest.csv`).
3. O reemplazar las imágenes NC con captura de campo propia (estrategia
   recomendada para v1.1).

Comando para filtrar a licencias comerciales:
```bash
.venv/bin/python -c "
import csv, pandas as pd
df = pd.read_csv('data/manifest_processed.csv')
ok = df[df['license'].isin(['CC0-1.0','CC-BY-4.0','CC-BY-SA-4.0'])]
ok.to_csv('data/manifest_commercial.csv', index=False)
print(f'commercial-safe images: {len(ok)}')
"
```

## Atribuciones

Las atribuciones individuales por imagen están en
`data/manifest.csv` (columna `author`). Cualquier publicación o
producto derivado debe incluir las atribuciones correspondientes según los
términos de cada licencia. Para licencias `*-SA` (Share-Alike) las obras
derivadas deben distribuirse bajo la misma licencia.

## Fuentes y términos

- **iNaturalist** — usuarios eligen su licencia por foto. Solo se incluyeron
  fotos con `cc0`, `cc-by`, `cc-by-nc`. Política completa:
  https://www.inaturalist.org/pages/help#cc
- **GBIF** — multi-licencia heterogénea. Se filtró a CC0/CC-BY/CC-BY-NC/SA.
  Citas obligatorias en uso académico:
  https://www.gbif.org/citation-guidelines
- **Mushroom Observer** — licencias Creative Commons por foto. Términos:
  https://mushroomobserver.org/info/intro
- **Wikimedia Commons** — multi-licencia con preferencia CC. Términos:
  https://commons.wikimedia.org/wiki/Commons:Licensing

## Cumplimiento legal mexicano

Conforme a la Memoria Técnica de Úppa:

- **Ley Federal del Derecho de Autor**: cada imagen tiene autor y licencia
  registrados (manifest.csv).
- **Ley Federal de Protección de Datos Personales**: las imágenes en
  `data/processed/` tienen EXIF eliminado (sin geolocalización ni metadatos
  del fotógrafo). Los nombres en `author` provienen de la atribución pública
  obligatoria por las licencias CC y no constituyen datos personales no
  consentidos.
