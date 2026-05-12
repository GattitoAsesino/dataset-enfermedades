from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image

try:
    import tensorflow as tf
    _Interpreter = tf.lite.Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter as _Interpreter

from src.labels import LABELS, LABELS_ES, DISEASE_NAMES
from src.treatments import TREATMENTS, INVALID_MESSAGE, NOT_OYSTER_MESSAGE

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "model_unquant.tflite"
INPUT_SIZE = 224

_interpreter = None
_input_index = None
_output_index = None


def _load():
    global _interpreter, _input_index, _output_index
    if _interpreter is None:
        _interpreter = _Interpreter(model_path=str(MODEL_PATH))
        _interpreter.allocate_tensors()
        _input_index = _interpreter.get_input_details()[0]["index"]
        _output_index = _interpreter.get_output_details()[0]["index"]
    return _interpreter


def _preprocess(image: Image.Image) -> np.ndarray:
    image = image.convert("RGB").resize((INPUT_SIZE, INPUT_SIZE), Image.BILINEAR)
    arr = np.asarray(image, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def predict(source: Union[str, Path, Image.Image]) -> dict:
    if isinstance(source, (str, Path)):
        image = Image.open(source)
    else:
        image = source

    arr = _preprocess(image)
    interp = _load()
    interp.set_tensor(_input_index, arr)
    interp.invoke()
    probs = interp.get_tensor(_output_index)[0]

    idx = int(np.argmax(probs))
    confidence = float(probs[idx])

    is_mushroom = idx != 1
    is_oyster = idx in (0, 2, 3, 4)
    is_healthy = idx == 0
    disease = DISEASE_NAMES.get(idx)

    if idx == 1:
        message = INVALID_MESSAGE
    elif idx == 5:
        message = NOT_OYSTER_MESSAGE
    elif is_healthy:
        message = "Tu seta está sana. Mantén las buenas prácticas de cultivo."
    else:
        message = f"Se detectó la enfermedad: {disease}. Revisa las recomendaciones."

    return {
        "class_index": idx,
        "label_en": LABELS[idx],
        "label_es": LABELS_ES[idx],
        "confidence": round(confidence, 4),
        "probabilities": {LABELS[i]: round(float(p), 4) for i, p in enumerate(probs)},
        "is_mushroom": is_mushroom,
        "is_oyster": is_oyster,
        "is_healthy": is_healthy,
        "disease": disease,
        "message": message,
        "treatments": TREATMENTS.get(idx, []),
    }


OYSTER_INDICES = (0, 2, 3, 4)
ESTADO_POR_INDICE = {
    0: "Sano",
    2: "Mancha marrón (Brown Blotch)",
    3: "Moho verde (Green Mold)",
    4: "Pudrición blanda (Soft Rot)",
}


def _build_especie(base: dict) -> dict:
    idx = base["class_index"]
    probs = base["probabilities"]

    if idx == 1:
        return {
            "detectado": False,
            "especie": None,
            "confianza": base["confidence"],
            "mensaje": (
                "La imagen no parece contener un hongo. Sube una foto clara de "
                "tu seta tomada de frente o de costado, con buena iluminación."
            ),
        }

    if idx == 5:
        return {
            "detectado": True,
            "especie": "Otra especie de hongo (no Pleurotus)",
            "confianza": probs["Not an Oyster Mushroom"],
            "mensaje": (
                "Se detectó un hongo pero no es una seta (Pleurotus). "
                "Úppa actualmente solo analiza setas."
            ),
        }

    confianza_oyster = round(
        sum(probs[LABELS[i]] for i in OYSTER_INDICES), 4
    )
    return {
        "detectado": True,
        "especie": "Pleurotus ostreatus (seta)",
        "confianza": confianza_oyster,
        "mensaje": "La imagen se identificó como una seta del género Pleurotus.",
    }


def _build_salud(base: dict) -> dict:
    idx = base["class_index"]

    if idx == 1 or idx == 5:
        return {
            "sano": None,
            "estado": None,
            "confianza_salud": None,
            "mensaje_salud": (
                "No se evaluó la salud porque la imagen no corresponde a una seta."
            ),
        }

    if idx == 0:
        return {
            "sano": True,
            "estado": "Sano",
            "confianza_salud": base["confidence"],
            "mensaje_salud": (
                "La seta está sana. Recomendaciones: "
                + " | ".join(TREATMENTS.get(0, []))
            ),
        }

    return {
        "sano": False,
        "estado": ESTADO_POR_INDICE[idx],
        "confianza_salud": base["confidence"],
        "mensaje_salud": (
            f"Enfermedad detectada: {ESTADO_POR_INDICE[idx]}. Recomendaciones: "
            + " | ".join(TREATMENTS.get(idx, []))
        ),
    }


def predict_json(source: Union[str, Path, Image.Image]) -> dict:
    """Versión orientada a API: devuelve JSON plano con bloques de especie y salud."""
    base = predict(source)
    especie = _build_especie(base)
    salud = _build_salud(base)
    return {
        "detectado": especie["detectado"],
        "especie": especie.get("especie"),
        "confianza": especie.get("confianza"),
        "sano": salud["sano"],
        "estado": salud.get("estado"),
        "confianza_salud": salud.get("confianza_salud"),
        "mensaje_especie": especie.get("mensaje"),
        "mensaje_salud": salud.get("mensaje_salud"),
    }
