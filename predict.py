import json
import sys
from pathlib import Path

from src.inference import predict_json


def main():
    if len(sys.argv) != 2:
        print("Uso: python predict.py <ruta_a_imagen.jpg>", file=sys.stderr)
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Error: archivo no encontrado: {image_path}", file=sys.stderr)
        sys.exit(2)

    result = predict_json(image_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
