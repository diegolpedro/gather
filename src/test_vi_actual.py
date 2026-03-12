"""Calculo de volatilidad implicita (VI) para CALLs de Galicia (GGAL) leyendo datos desde SQL."""

from datetime import date, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from common.tools import get_azure_secret_client
from test_VIs import call_iv


CALLS_QUERY = """
SELECT strike, expiration, last
FROM cotizacion_actual
WHERE symbol LIKE '%GFGC%'
  AND last IS NOT NULL
ORDER BY strike;
""".strip()

SPOT_QUERY = """
SELECT last
FROM public.cotizacion_actual
WHERE symbol = 'GGAL'
  AND settlement = 'spot';
""".strip()


def build_engine():
    """Crea engine de SQLAlchemy usando el mismo esquema de conexion que uphb.py."""
    azs_client = get_azure_secret_client()

    db = 'market_db'
    db_user = azs_client.get_secret('db-user').value
    db_pass = azs_client.get_secret('db-pass').value

    db_url = "postgresql://%s:%s@postgres:5432/%s" % (db_user, db_pass, db)
    return create_engine(db_url, poolclass=NullPool)


def fetch_spot_price(engine) -> float:
    """Obtiene el spot de GGAL desde SQL."""
    with engine.connect() as conn:
        row = conn.execute(text(SPOT_QUERY)).first()

    if row is None or row[0] is None:
        raise ValueError("No se pudo obtener spot_price para GGAL desde cotizacion_actual")

    return float(row[0])


def fetch_calls_galicia(engine) -> list[dict]:
    """Obtiene strikes/expiracion/last para CALLs de Galicia desde SQL."""
    with engine.connect() as conn:
        rows = conn.execute(text(CALLS_QUERY)).all()

    calls = []
    for strike, expiration, call_last in rows:
        if call_last is None:
            continue
        calls.append(
            {
                "strike": float(strike),
                "expiration": expiration,
                "call_last": float(call_last),
            }
        )

    return calls


def calcular_vis_calls_galicia(spot_price: float, r_pct: float, today: date, calls: list[dict]) -> list[dict]:
    """Calcula la VI para cada CALL de Galicia."""
    resultados = []

    for row in calls:
        strike_price = float(row["strike"])
        expiry = row["expiration"]
        call_last = float(row["call_last"])

        t_days = (expiry - today).days
        if t_days <= 0:
            continue

        ivc = call_iv(spot_price, strike_price, r_pct, t_days, call_last)

        resultados.append(
            {
                "strike": strike_price,
                "expiration": expiry,
                "t_days": t_days,
                "call_last": call_last,
                "call_iv": ivc,
                "call_iv_pct": ivc * 100.0,
            }
        )

    return resultados


if __name__ == "__main__":
    r_pct = 30.0
    today = datetime.now().date()

    engine = build_engine()
    try:
        spot_price = fetch_spot_price(engine)
        calls_galicia = fetch_calls_galicia(engine)
    finally:
        engine.dispose()

    resultados = calcular_vis_calls_galicia(spot_price, r_pct, today, calls_galicia)

    print(f"SPOT GGAL = {spot_price:.2f}")
    for r in resultados:
        print(
            f"CALL strike={r['strike']:.0f} exp={r['expiration']} "
            f"last={r['call_last']:.2f} -> IV={r['call_iv']:.6f} ({r['call_iv_pct']:.3f}%)"
        )
