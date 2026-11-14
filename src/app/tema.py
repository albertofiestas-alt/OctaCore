"""Tema y accesibilidad (respaldo; dueño: Alberto). Contraste >= 4.5 sobre el fondo."""

import streamlit as st

COLOR = {
    "fondo": "#FFFFFF",
    "texto": "#1A1A1A",
    "verde": "#1B7F3B",
    "ambar": "#8A5A00",
    "rojo": "#B3261E",
    "acento": "#0B2A6F",
}
TAMANO_TEXTO_PX = 16
SIMBOLO = {"verde": "✔", "ambar": "▲", "rojo": "✖"}
ETIQUETA = {"verde": "Cubierto", "ambar": "Con riesgo", "rojo": "No cubierto"}


def contraste(hex1: str, hex2: str) -> float:
    def lum(h: str) -> float:
        r, g, b = [int(h[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    a, b = sorted([lum(hex1), lum(hex2)], reverse=True)
    return (a + 0.05) / (b + 0.05)


def aplicar() -> None:
    """Inyecta el CSS mínimo: texto de 16 px, número grande, tarjetas de estado."""
    c = COLOR
    st.markdown(
        f"""<style>
        html, body, [class*="st-"] {{ font-size: {TAMANO_TEXTO_PX}px; }}
        .numero-hoy {{ font-size: clamp(2.4rem, 9vw, 4.5rem); font-weight: 800;
            color: {c['acento']}; line-height: 1.1; margin: .2rem 0 .6rem; }}
        .numero-hoy small {{ display:block; font-size: 1rem; font-weight: 500; color: {c['texto']}; }}
        .estado {{ border-left: 8px solid; padding: .5rem .8rem; margin: .4rem 0;
            background: #F5F6F8; border-radius: 4px; }}
        .estado.verde {{ border-color: {c['verde']}; }} .estado.verde b {{ color: {c['verde']}; }}
        .estado.ambar {{ border-color: {c['ambar']}; }} .estado.ambar b {{ color: {c['ambar']}; }}
        .estado.rojo {{ border-color: {c['rojo']}; }} .estado.rojo b {{ color: {c['rojo']}; }}
        </style>""",
        unsafe_allow_html=True,
    )
