# from common.tools import Logger

# app_logger = Logger(__name__).get_logger()

# app_logger.info("Esto está funcionando!!")
# app_logger.error("Ocurrió un error grave")


# import math
# from datetime import date

# def N(x: float) -> float:
#     return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

# def ndist(x: float) -> float:
#     return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

# def black_scholes_call(S: float, X: float, r: float, v: float, t: float) -> float:
#     sqt = math.sqrt(t)
#     d1 = (math.log(S / X) + r * t) / (v * sqt) + 0.5 * (v * sqt)
#     d2 = d1 - (v * sqt)
#     return S * N(d1) - X * math.exp(-r * t) * N(d2)

# def implied_vol_call_newton(S: float, X: float, r_pct: float, t_days: int, opt_price: float) -> float:
#     # igual que tu call_iv: r/100 y t/365
#     r = r_pct / 100.0
#     t = t_days / 365.0

#     sqt = math.sqrt(t)
#     sigma = (opt_price / S) / (0.398 * sqt)  # misma inicialización

#     MAX_ITER = 100
#     ACC = 0.0001

#     for _ in range(MAX_ITER):
#         price = black_scholes_call(S, X, r, sigma, t)
#         diff = opt_price - price
#         if abs(diff) < ACC:
#             return sigma
#         d1 = (math.log(S / X) + r * t) / (sigma * sqt) + 0.5 * sigma * sqt
#         vega = S * sqt * ndist(d1)
#         sigma = sigma + diff / vega

#     return 0.0

# # --- Tus datos ---
# S = 8290
# K = 8530
# opt_last = 213
# r_tna = 30.0

# today = date(2026, 1, 29)
# expiry = date(2026, 2, 19)
# t_days = (expiry - today).days  # 21

# iv = implied_vol_call_newton(S, K, r_tna, t_days, opt_last)
# print(f"IV = {iv:.6f}  ({iv*100:.3f}%)")

import math
from datetime import date

def N(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def ndist(x: float) -> float:
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

def black_scholes(S: float, X: float, r: float, v: float, t: float, call: bool) -> float:
    """
    Replica la función black_scholes(call,S,X,r,v,t) de tu GSheet.
    r: tasa anual en decimal (ej 0.30)
    t: tiempo en años (ej 21/365)
    """
    if t <= 0:
        return max(S - X, 0.0) if call else max(X - S, 0.0)

    sqt = math.sqrt(t)
    d1 = (math.log(S / X) + r * t) / (v * sqt) + 0.5 * (v * sqt)
    d2 = d1 - (v * sqt)

    ert = math.exp(-r * t)

    if call:
        delta = N(d1)
        Nd2 = N(d2)
    else:
        delta = -N(-d1)
        Nd2 = -N(-d2)

    # mismo return que tu JS: ( S*delta - X*ert*Nd2 )
    return S * delta - X * ert * Nd2

def option_implied_volatility(call: bool, S: float, X: float, r: float, t: float, o: float) -> float:
    """
    Replica option_implied_volatility(call,S,X,r,t,o) de tu GSheet (Newton-Raphson).
    """
    sqt = math.sqrt(t)
    MAX_ITER = 100
    ACC = 0.0001

    sigma = (o / S) / (0.398 * sqt)  # misma semilla

    for _ in range(MAX_ITER):
        price = black_scholes(S, X, r, sigma, t, call)
        diff = o - price
        if abs(diff) < ACC:
            return sigma

        d1 = (math.log(S / X) + r * t) / (sigma * sqt) + 0.5 * sigma * sqt
        vega = S * sqt * ndist(d1)
        sigma = sigma + diff / vega

    return 0.0

def call_iv(S: float, X: float, r_pct: float, t_days: int, o: float) -> float:
    return option_implied_volatility(True, S, X, r_pct/100.0, t_days/365.0, o)

def put_iv(S: float, X: float, r_pct: float, t_days: int, o: float) -> float:
    return option_implied_volatility(False, S, X, r_pct/100.0, t_days/365.0, o)

# ---------- Ejemplo ----------
if __name__ == "__main__":
    # Ejemplo: GGAL put cualquiera
    S = 8310
    X = 8530
    r_pct = 30.0

    today = date(2026, 1, 29)
    expiry = date(2026, 2, 19)
    t_days = (expiry - today).days  # 21

    put_last = 320.0  # <-- poné el último de tu put

    ivp = put_iv(S, X, r_pct, t_days, put_last)
    print(f"PUT IV = {ivp:.6f}  ({ivp*100:.3f}%)")

