import gradio as gr

from src.inference import predict_json


def analyze(image):
    if image is None:
        return {}
    return predict_json(image)


with gr.Blocks(title="Úppa — Detector de enfermedades en setas") as demo:
    gr.Markdown(
        "# 🍄 Úppa\n"
        "**Plataforma de detección de enfermedades en setas (Pleurotus) "
        "para fungicultores mexicanos.**\n\n"
        "Sube una foto de tu seta para recibir un diagnóstico en formato JSON."
    )

    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(type="pil", label="Foto de la seta")
            analyze_btn = gr.Button("Analizar", variant="primary")

        with gr.Column(scale=2):
            result_json = gr.JSON(label="Resultado")

    analyze_btn.click(
        analyze, inputs=image_input, outputs=result_json, api_name="predict"
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
