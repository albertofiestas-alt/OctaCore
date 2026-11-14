from app import tema


def test_contraste_paleta_minimo_4_5():
    for nombre, color in tema.COLOR.items():
        if nombre != "fondo":
            assert tema.contraste(color, tema.COLOR["fondo"]) >= 4.5, nombre
