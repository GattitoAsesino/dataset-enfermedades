"""Inferir moho verde en una imagen con el modelo Úppa v1.

Uso:
    .venv/bin/python predict.py imagen.jpg
    .venv/bin/python predict.py carpeta_con_imagenes/

El modelo retorna detecciones tipo "esta imagen es sano|moho_verde con
confianza X". La bounding box cubre la imagen completa (ver MODEL_CARD.md
sección "Caveats" para por qué).
"""
from __future__ import annotations

import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
WEIGHTS = ROOT / "runs" / "detect" / "runs" / "uppa" / "v1_yolo11n" / "weights" / "best.pt"


def main() -> None:
    if len(sys.argv) < 2:
        print(f"uso: python {sys.argv[0]} <imagen-o-carpeta>")
        sys.exit(1)
    source = sys.argv[1]
    if not WEIGHTS.exists():
        print(f"ERROR: faltan pesos en {WEIGHTS}")
        print("Asegúrate de incluir runs/detect/runs/uppa/v1_yolo11n/weights/best.pt")
        sys.exit(1)

    model = YOLO(str(WEIGHTS))
    results = model.predict(source=source, conf=0.25, save=True, verbose=False)

    for r in results:
        path = Path(r.path).name
        if r.boxes is None or len(r.boxes) == 0:
            print(f"{path}: sin detección (confianza < 0.25)")
            continue
        # Mejor detección por confianza
        best = r.boxes[r.boxes.conf.argmax()]
        cid = int(best.cls.item())
        conf = float(best.conf.item())
        cls_name = r.names[cid]
        print(f"{path}: {cls_name}  (confianza={conf:.2%})")

    if results:
        out = Path(results[0].save_dir)
        print(f"\nImágenes con anotaciones guardadas en: {out}")


if __name__ == "__main__":
    main()
