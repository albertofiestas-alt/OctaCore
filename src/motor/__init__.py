"""Capa 2: motor de decisión (número de hoy por fecha de pago, semáforo, confianza, propuestas).

Dueño: Sebastián. La firma de decidir es fija (contratos/firmas.py): se reemplaza el cuerpo, nunca la firma.
Función pura: no lee archivos ni la hora. El servicio pone respaldo y registro_id
(con_registro_id copia el id que generó el servicio a la Decision y a su desglose).

Archivos:
    decidir.py      fórmula por fecha de pago, semáforo, confianza, propuesta, desglose y evidencia
    plantillas.py   supuestos, límites, explicación y textos de propuesta (toda cifra sale del desglose)
    verificador.py  comprueba que cada cifra de los textos tenga origen en el estado, desglose o evidencia
"""

from __future__ import annotations

from motor.decidir import con_registro_id, decidir

__all__ = ["con_registro_id", "decidir"]
