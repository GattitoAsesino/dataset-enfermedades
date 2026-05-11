# Datasheet — Úppa Moho Verde Dataset v1

Sigue el esquema de Gebru et al. (2021), *Datasheets for Datasets*.
Los conteos finales por clase y por fuente viven en `reports/source_yields.md`
(autogenerado por `scripts/source_yields_report.py`).

## 1. Motivation

**¿Para qué se creó?**
Para entrenar el modelo CNN de Úppa, una plataforma web que ayuda a
fungicultores mexicanos a identificar moho verde (*Trichoderma* spp.) en
champiñón blanco (*Agaricus bisporus*). El moho verde causa pérdidas de
30–100% en producción según ECOSUR (2007).

**¿Quién lo creó?**
Equipo de Úppa, con asistencia automatizada (Claude). Imágenes provienen
de fuentes públicas con licencias compatibles.

**¿Quién lo financió?**
Recursos propios del proyecto Úppa. Las imágenes son CC0 / CC-BY / CC-BY-NC
/ CC-BY-SA — sin costo de licencia.

## 2. Composition

**¿Qué representa cada instancia?**
Una imagen JPG (RGB sRGB, lado mayor ≤1024 px) de un cuerpo fructífero o
colonia fúngica.

**¿Cuántas instancias hay?**
Ver `reports/source_yields.md` para conteos finales tras dedup y normalización.
Objetivo v1: ≥500 imágenes por clase.

**¿Qué etiquetas tiene?**
- `sano` — *Agaricus bisporus* sano
- `moho_verde` — *Trichoderma* spp.

**¿Hay ruido o errores?**
Sí. La etiqueta `moho_verde` agrega especies que comparten firma visual
(verde sporulado) pero no son todas *T. aggressivum*. La clase `sano`
puede contener ejemplares silvestres o post-cosecha que no representan el
contexto exacto de cultivo de Úppa.

**¿Hay datos personales?**
Los nombres de autores aparecen en `manifest.csv` (atribución obligatoria
por licencias CC-BY). EXIF de las imágenes se eliminó en el paso de
normalización (sin geolocalización ni metadatos del fotógrafo).

## 3. Collection process

**¿Cómo se obtuvieron los datos?**
APIs públicas:
- iNaturalist `api.inaturalist.org/v1/observations` (research-grade, CC license filter)
- GBIF `api.gbif.org/v1/occurrence/search` (mediaType=StillImage, license normalization)
- Mushroom Observer `mushroomobserver.org/api2/images`
- Wikimedia Commons MediaWiki API
- (opcional) Kaggle datasets

**¿En qué periodo?**
Ver `date_fetched` por imagen en `manifest.csv`.

**¿Hubo proceso de revisión humana?**
Spot-check vía `reports/review_<clase>.html`. Las etiquetas heredan de la
identificación taxonómica de la fuente original (research-grade en iNat,
identificación experta en Mushroom Observer y GBIF).

## 4. Preprocessing / cleaning / labeling

- **Dedup MD5**: descarta duplicados exactos cruzando fuentes.
- **Dedup perceptual (phash)**: hamming ≤5 dentro de cada clase.
- **Normalización**: sRGB JPG q92, lado mayor ≤1024 px.
- **Strip EXIF**: privacidad (Ley Federal de Protección de Datos Personales).

Manifiestos por etapa (raw → deduped → processed) están en `data/`.

## 5. Uses

**Usos previstos:**
- Entrenar la CNN inicial de Úppa para detección binaria de moho verde.
- Benchmark de baseline para estimar el techo alcanzable con datos públicos.

**Usos NO recomendados:**
- Producción comercial sin captura de campo complementaria — los datos
  públicos no representan el contexto de cultivo controlado mexicano.
- Identificación taxonómica fina (esa no es la tarea entrenada).
- Re-distribución de imágenes con licencia ND o sin atribución.

## 6. Distribution

**¿Se distribuirá fuera del equipo?**
Por definir. Si sí, la redistribución debe respetar la licencia de cada
imagen (ver `manifest.csv` columna `license` y `LICENSES.md`).

## 7. Maintenance

**¿Quién mantiene?**
Equipo de Úppa.

**¿Cómo reportar errores?**
Issues en el repo del proyecto. Para correcciones de etiqueta, abrir issue
con el `id` de la imagen del manifiesto.

**Roadmap:**
- v1.1 — añadir captura de campo en granjas mexicanas
- v2.0 — etiquetado por etapas (sano/incipiente/establecido/avanzado)
- v3.0 — multi-patógeno y multi-especie

## Referencias

- ECOSUR (2007). Reporte sobre pérdidas en producción de hongos.
- Williams et al. (2003). *Aggressive green mould of Agaricus bisporus
  caused by Trichoderma aggressivum*. Mycol Res.
- Fletcher et al. (1995). *Variations in isolates of Mycogone perniciosa
  and in disease symptoms in Agaricus bisporus*. Plant Pathology 44.
- Gebru et al. (2021). *Datasheets for Datasets*. CACM.
