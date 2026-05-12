TREATMENTS = {
    0: [
        "Mantén temperatura controlada entre 18 y 22 °C y humedad relativa de 85 a 90%.",
        "Asegura ventilación constante para evitar acumulación de CO₂.",
        "Cosecha antes de que las laminillas se abran completamente.",
        "Usa herramientas limpias y desinfectadas para cada cosecha.",
        "Inspecciona diariamente las bolsas o bandejas en busca de signos tempranos de contaminación.",
    ],
    2: [
        "Reduce la humedad superficial — evita gotas de agua sobre los sombreros.",
        "Mejora la ventilación para secar la superficie tras cada riego.",
        "Desinfecta bandejas y superficies con hipoclorito de sodio al 1% entre lotes.",
        "Retira inmediatamente las bolsas afectadas para evitar diseminación bacteriana.",
        "Aplica cloro al agua de riego (50 a 150 ppm de Cl libre) como medida preventiva.",
        "Evita manipular las setas con las manos húmedas — Pseudomonas tolaasii se propaga por contacto.",
    ],
    3: [
        "Aísla inmediatamente las bolsas afectadas para evitar contaminación cruzada.",
        "Aumenta la ventilación y reduce la humedad relativa por debajo del 85%.",
        "Desinfecta herramientas y superficies con hipoclorito al 1% o peróxido de hidrógeno.",
        "Revisa la pasteurización del sustrato: temperaturas menores a 60 °C por 8 horas favorecen el Trichoderma.",
        "Elimina las bolsas con micelio verdoso visible — no son recuperables; quema o entierra lejos del cultivo.",
        "Mejora la higiene del personal: cambio de ropa y lavado de manos al entrar al área de cultivo.",
        "Mantén el pH del sustrato entre 7.0 y 7.5 — el Trichoderma prospera en pH ácido.",
        "No reutilices bolsas ni sustrato que haya estado en contacto con material contaminado.",
    ],
    4: [
        "Aumenta la ventilación y reduce drásticamente la humedad ambiental.",
        "Elimina bolsas y residuos infectados — no los compostes en el sitio de cultivo.",
        "Desinfecta el área con yodopovidona o amonio cuaternario.",
        "Evita el exceso de agua en el sustrato durante la fructificación.",
        "Inspecciona y descarta bolsas con lesiones acuosas antes de que se propaguen.",
        "Cosecha tempranamente para minimizar el tiempo de exposición a Pectobacterium.",
    ],
}

INVALID_MESSAGE = (
    "La imagen subida no parece ser un hongo. Por favor sube una foto clara de tu seta "
    "(Pleurotus) tomada de frente o de costado, con buena iluminación."
)

NOT_OYSTER_MESSAGE = (
    "Úppa actualmente solo analiza setas (Pleurotus / oyster mushroom). "
    "La imagen muestra otra especie de hongo. Próximamente soportaremos más especies."
)
