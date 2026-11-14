"""Opción C: asistente conversacional del semáforo (LLM + RAG + ML). Diseño: Diseno_Opcion_C_asistente_del_semaforo.docx.

Dueños: flujo.py (Anderson); intenciones.py y prompts.py (Gino); plantillas.py y verificador.py (Sebastián);
rag.py, kb/ y data/chat (Rafael); guardia.py (Mathias). Funciona completo SIN LLM (modo 1); el LLM es el modo 2.
Nivel P2: puntos de corte 13:00, 16:00, 17:30 y 17:45; nunca desplaza una prueba P0.
La app no importa este paquete: solo llama a servicio.preguntar. Esqueleto V0: reemplaza el cuerpo, NO la firma.
"""