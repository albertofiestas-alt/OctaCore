"""Fachada del servicio con dobles de las capas (dueño: Anderson).

Prueba la orquestación, la escalera de respaldo, el registro, la salud y la
auditoría sin esperar a ingesta, reglas, modelo ni motor. El flujo con las capas
reales vive en tests/integracion/.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import servicio
from contratos import (
    ETIQUETAS_REFERENCIA,
    Decision,
    DecisionPago,
    PagoConFecha,
    Pronostico,
    Propuesta,
    ReporteCalidad,
)
from servicio import ErrorServicio
from servicio.registro import leer_jsonl, leer_registros

RAIZ = Path(__file__).resolve().parents[3]
FECHA = date(2025, 11, 20)  # P0002 tiene historia en octubre y una cuota el día 28


# --------------------------------------------------------------------------- #
# Dobles de las capas
# --------------------------------------------------------------------------- #

def _pron(base: float) -> Pronostico:
    return Pronostico(por_horizonte={h: {"p5": base * h * 0.5, "p20": base * h * 0.75,
                                         "p50": base * h, "p80": base * h * 1.5} for h in (3, 7, 14)})


class Espia:
    """Guarda lo que recibió cada capa."""

    def __init__(self) -> None:
        self.historias: list[pd.DataFrame] = []


def _ingesta() -> SimpleNamespace:
    def cargar(origen, cfg):
        df = pd.read_csv(origen, parse_dates=["fecha_hora"])
        filas = len(df)
        df = df[~df["es_duplicado"]].drop(columns=list(ETIQUETAS_REFERENCIA))
        pagos = [{"customer_id": "P0002", "comercio": "Financiera Ficticia", "categoria": "deuda",
                  "monto": 350.0, "dia_mes": 28, "ocurrencias": 3}]
        reporte = ReporteCalidad(filas_entrada=filas, filas_salida=len(df),
                                 duplicados_eliminados=filas - len(df), atipicos=0, pagos_inferidos=pagos)
        return df, reporte, pagos

    def proximos_pagos(pagos_inferidos, customer_id, fecha_corte, ventana=14):
        salida = []
        for p in pagos_inferidos:
            if p["customer_id"] != customer_id:
                continue
            fecha = fecha_corte.replace(day=p["dia_mes"])
            dias = (fecha - fecha_corte).days
            if 0 <= dias <= ventana:
                salida.append(PagoConFecha(pago_id=f"{customer_id}:{p['comercio']}:{fecha}", dia=dias,
                                           monto=p["monto"], categoria=p["categoria"]))
        return salida

    def semanas_historia(movimientos, customer_id, fecha_corte):
        m = movimientos[movimientos.customer_id == customer_id]
        return (fecha_corte - m.fecha_hora.min().date()).days // 7

    return SimpleNamespace(cargar=cargar, proximos_pagos=proximos_pagos, semanas_historia=semanas_historia)


def _reglas(espia: Espia, falla_regla2: bool = False) -> SimpleNamespace:
    def regla1(historia, fecha, cfg):
        espia.historias.append(historia)
        return _pron(10)

    def regla2(historia, fecha, cfg):
        espia.historias.append(historia)
        if falla_regla2:
            raise NotImplementedError("regla 2 a las 12:30")
        return _pron(20)

    return SimpleNamespace(regla1=regla1, regla2=regla2)


def _motor() -> SimpleNamespace:
    def decidir(estado, pronostico, cfg):
        p20 = pronostico.por_horizonte[14].p20
        pagos = sum(p.monto for p in estado.pagos)
        numero = math.floor(max(0.0, (estado.saldo + p20 - pagos - estado.colchon) / 14))
        propuestas = [
            Propuesta(propuesta_id=f"{estado.customer_id}-{estado.fecha_corte}-{p.pago_id}", texto="Aparta S/10",
                      monto=10, pago_id=p.pago_id, antes={"numero_hoy": numero},
                      despues={"numero_hoy": numero - 1}, confianza="media")
            for p in estado.pagos
        ]
        return Decision(
            numero_hoy=numero,
            por_pago=[DecisionPago(pago_id=p.pago_id, dia=p.dia, monto=p.monto, permitido=numero,
                                   semaforo="verde") for p in estado.pagos],
            confianza="media",
            limites=["No promete resultados."],
            supuestos=["Gastas cada día lo que indica el número de hoy."],
            evidencia={"semanas_historia": estado.semanas_historia,
                       "rango_14d": pronostico.por_horizonte[14].model_dump()},
            propuestas=propuestas,
        )

    return SimpleNamespace(decidir=decidir)


class ModeloFalso:
    def predecir(self, historia, fecha):
        return _pron(30)

    @classmethod
    def cargar(cls, ruta):
        return cls()


@pytest.fixture
def espia() -> Espia:
    return Espia()


@pytest.fixture
def capas(espia) -> dict[str, SimpleNamespace]:
    return {
        "ingesta": _ingesta(),
        "reglas": _reglas(espia),
        "motor": _motor(),
        "modelo": SimpleNamespace(Modelo=ModeloFalso),
    }


@pytest.fixture
def srv(cfg, tmp_path, monkeypatch, capas, ruta_movimientos_minimo):
    """servicio con dobles, datos de tests/fixtures y registros en una carpeta temporal."""
    servicio.reiniciar()
    servicio._ESTADO["cfg"] = cfg.con(
        rutas_datos=[str(ruta_movimientos_minimo)],
        ruta_modelo=str(tmp_path / "modelo.joblib"),
        ruta_adopcion=str(tmp_path / "adopcion.json"),
        ruta_registro=str(tmp_path / "recomendaciones.jsonl"),
        ruta_respuestas=str(tmp_path / "respuestas.jsonl"),
        ruta_salud=str(tmp_path / "salud.jsonl"),
    )
    monkeypatch.setattr(servicio, "_capa", lambda nombre: capas[nombre])
    yield servicio
    servicio.reiniciar()


# --------------------------------------------------------------------------- #
# consultar
# --------------------------------------------------------------------------- #

def test_consultar_con_regla2_devuelve_decision_registrada(srv):
    d = srv.consultar("P0002", FECHA, "regla2")
    assert isinstance(d, Decision)
    assert d.registro_id.startswith("R-") and d.respaldo is False
    assert [p.dia for p in d.por_pago] == [8]

    (registro,) = leer_registros(srv._cfg()["ruta_registro"])
    assert registro.registro_id == d.registro_id
    assert registro.entradas["metodo_pedido"] == registro.entradas["metodo_usado"] == "regla2"
    assert registro.entradas["fecha"] == "2025-11-20"
    assert registro.decision == d.model_dump(mode="json")


def test_historia_solo_tiene_movimientos_anteriores_a_la_fecha(srv, espia):
    srv.consultar("P0002", date(2025, 10, 15), "regla2")
    historia = espia.historias[-1]
    assert historia["fecha_hora"].max() < pd.Timestamp(2025, 10, 15)
    assert set(historia["customer_id"]) == {"P0002"}
    assert not set(ETIQUETAS_REFERENCIA) & set(historia.columns)


def test_saldo_es_el_ultimo_informado(srv, espia, monkeypatch):
    estados = []
    original = _motor().decidir

    def decidir(estado, pronostico, cfg):
        estados.append(estado)
        return original(estado, pronostico, cfg)

    capas_motor = SimpleNamespace(decidir=decidir)
    capas = {"ingesta": _ingesta(), "reglas": _reglas(espia), "motor": capas_motor}
    monkeypatch.setattr(srv, "_capa", lambda nombre: capas[nombre])
    srv.consultar("P0002", FECHA, "regla2")
    assert estados[0].saldo == pytest.approx(1850.20)
    assert estados[0].semanas_historia == 7
    assert estados[0].colchon == 0


def test_fecha_como_texto(srv):
    assert srv.consultar("P0002", "2025-11-20", "regla2").numero_hoy >= 0


@pytest.mark.parametrize("args,mensaje", [
    (("P9999", FECHA, "regla2"), "No hay movimientos"),
    (("P0002", date(2020, 1, 1), "regla2"), "no tiene movimientos antes"),
    (("P0002", "20/11/2025", "regla2"), "Fecha inválida"),
    (("P0002", FECHA, "magia"), "Método desconocido"),
])
def test_errores_con_mensaje_para_la_persona(srv, args, mensaje):
    with pytest.raises(ErrorServicio, match=mensaje):
        srv.consultar(*args)
    assert srv.salud()["tasa_error"] == 1.0


def test_sin_datos_dice_como_generarlos(srv, tmp_path):
    srv._ESTADO["cfg"] = srv._cfg().con(rutas_datos=[str(tmp_path / "no-existe.csv")])
    with pytest.raises(ErrorServicio, match="tareas.py datos"):
        srv.consultar("P0002", FECHA, "regla2")


# --------------------------------------------------------------------------- #
# Escalera de respaldo
# --------------------------------------------------------------------------- #

def test_modelo_sin_entrenar_usa_regla2_con_respaldo(srv):
    d = srv.consultar("P0002", FECHA)  # metodo por defecto: modelo
    assert d.respaldo is True
    (registro,) = leer_registros(srv._cfg()["ruta_registro"])
    assert registro.entradas["metodo_usado"] == "regla2"
    assert "FileNotFoundError" in registro.entradas["motivos_respaldo"][0]
    assert srv.salud()["tasa_respaldo"] == 1.0


def test_modelo_entrenado_y_sin_veredicto_se_usa(srv):
    Path(srv._cfg()["ruta_modelo"]).write_bytes(b"x")
    d = srv.consultar("P0002", FECHA, "modelo")
    assert d.respaldo is False
    assert d.evidencia["rango_14d"]["p50"] == 30 * 14


def test_modelo_no_adoptado_usa_regla2(srv):
    Path(srv._cfg()["ruta_modelo"]).write_bytes(b"x")
    Path(srv._cfg()["ruta_adopcion"]).write_text(json.dumps({"adopta": False, "razon": "no supera"}))
    d = srv.consultar("P0002", FECHA, "modelo")
    assert d.respaldo is True
    (registro,) = leer_registros(srv._cfg()["ruta_registro"])
    assert "no adoptado" in registro.entradas["motivos_respaldo"][0]


def test_regla2_no_lista_baja_a_regla1(srv, capas, espia):
    capas["reglas"] = _reglas(espia, falla_regla2=True)
    d = srv.consultar("P0002", FECHA, "regla2")
    assert d.respaldo is True
    assert d.evidencia["rango_14d"]["p50"] == 10 * 14


def test_si_nada_funciona_error_claro(srv, capas):
    capas["reglas"] = SimpleNamespace()  # ni regla1 ni regla2
    with pytest.raises(ErrorServicio, match="pronóstico"):
        srv.consultar("P0002", FECHA, "regla2")


def test_acepta_contratos_de_otra_copia_del_modulo(srv, capas):
    """Si una capa devuelve un dict u otro objeto con la misma forma, se valida contra el contrato."""
    original = capas["motor"].decidir
    capas["motor"] = SimpleNamespace(decidir=lambda e, p, c: original(e, p, c).model_dump())
    assert isinstance(srv.consultar("P0002", FECHA, "regla2"), Decision)


# --------------------------------------------------------------------------- #
# cargar_archivo, responder, salud
# --------------------------------------------------------------------------- #

def test_cargar_archivo_activa_los_datos(srv, ruta_movimientos_minimo):
    reporte = srv.cargar_archivo(ruta_movimientos_minimo)
    assert isinstance(reporte, ReporteCalidad)
    assert reporte.duplicados_eliminados == 1
    assert srv._ESTADO["movimientos"] is not None
    assert srv.consultar("P0002", FECHA, "regla2").registro_id


def test_responder_anota_y_no_ejecuta(srv):
    d = srv.consultar("P0002", FECHA, "regla2")
    pid = d.propuestas[0].propuesta_id
    r = srv.responder(pid, "aprobar")
    assert r["ok"] is True and r["registro_id"] == d.registro_id
    assert "no se movió ningún dinero" in r["mensaje"]
    assert leer_jsonl(srv._cfg()["ruta_respuestas"])[0]["accion"] == "aprobar"

    otra = srv.responder(pid, "rechazar")
    assert otra["ok"] is False and otra["accion"] == "aprobar"


def test_responder_valida_entrada(srv):
    srv.consultar("P0002", FECHA, "regla2")
    with pytest.raises(ErrorServicio, match="Acción"):
        srv.responder("cualquiera", "ejecutar")
    with pytest.raises(ErrorServicio, match="No existe la propuesta"):
        srv.responder("P-no-existe", "aprobar")


def test_salud_resume_las_consultas(srv):
    for _ in range(3):
        srv.consultar("P0002", FECHA, "regla2")
    with pytest.raises(ErrorServicio):
        srv.consultar("P9999", FECHA, "regla2")
    s = srv.salud()
    assert s["consultas"] == 4
    assert s["tasa_error"] == 0.25
    assert s["p50"] is not None and s["p95"] >= s["p50"]


# --------------------------------------------------------------------------- #
# Auditoría
# --------------------------------------------------------------------------- #

def test_auditar_reproduce_la_recomendacion(srv):
    d = srv.consultar("P0002", FECHA, "regla2")
    a = srv.auditar(d.registro_id)
    assert a["encontrado"] and a["se_reproduce"], a
    assert a["misma_config"] and a["mismos_datos"] and a["diferencias"] == []
    assert a["decision"]["numero_hoy"] == d.numero_hoy


def test_auditar_desde_otro_proceso_relee_el_archivo(srv):
    d = srv.consultar("P0002", FECHA, "regla2")
    srv._ESTADO.update(movimientos=None, pagos=None, origen=None)  # como si fuera otro proceso
    assert srv.auditar(d.registro_id)["se_reproduce"] is True


def test_auditar_detecta_cambio_de_resultado(srv, capas, espia):
    d = srv.consultar("P0002", FECHA, "regla2")
    capas["reglas"] = SimpleNamespace(regla2=lambda h, f, c: _pron(99), regla1=lambda h, f, c: _pron(99))
    a = srv.auditar(d.registro_id)
    assert a["se_reproduce"] is False
    assert "numero_hoy" in a["diferencias"]


def test_auditar_id_inexistente(srv):
    a = srv.auditar("R-no-existe")
    assert a["encontrado"] is False and a["se_reproduce"] is False


def test_script_de_auditoria(srv, capsys):
    d = srv.consultar("P0002", FECHA, "regla2")
    spec = importlib.util.spec_from_file_location("auditar_recomendacion",
                                                  RAIZ / "scripts" / "auditar_recomendacion.py")
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    assert script.main([d.registro_id]) == 0
    assert json.loads(capsys.readouterr().out)["registro_id"] == d.registro_id
    assert script.main(["R-no-existe"]) == 2


# --------------------------------------------------------------------------- #
# Importar con el prefijo src. (plan de la app) da el mismo módulo
# --------------------------------------------------------------------------- #

def test_from_src_import_servicio_es_el_mismo_modulo(monkeypatch):
    monkeypatch.syspath_prepend(str(RAIZ))
    import src

    assert src.servicio is servicio
    assert sys.modules["src.servicio"] is servicio
    from src.contratos import Decision as DecisionSrc

    assert DecisionSrc is Decision
