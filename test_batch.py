"""Recorre todas las imágenes en test_images/ y muestra la predicción de cada una.

Uso: python test_batch.py [carpeta]   (por defecto test_images/)
"""
import sys
from pathlib import Path

from src.inference import predict

VALID_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "test_images")
    if not folder.exists():
        print(f"Carpeta no existe: {folder}", file=sys.stderr)
        sys.exit(1)

    images = sorted(p for p in folder.iterdir() if p.suffix.lower() in VALID_EXT)
    if not images:
        print(f"No hay imágenes en {folder}", file=sys.stderr)
        sys.exit(1)

    print(f"{'Archivo':<40} {'Clase predicha':<35} {'Confianza':<10}")
    print("-" * 90)
    for img in images:
        try:
            r = predict(img)
            print(f"{img.name:<40} {r['label_es']:<35} {r['confidence'] * 100:>6.1f}%")
        except Exception as e:
            print(f"{img.name:<40} ERROR: {e}")


if __name__ == "__main__":
    main()
