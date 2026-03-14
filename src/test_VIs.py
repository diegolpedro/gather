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

import math

import math

def ndist(x: float) -> float:
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

def N(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

# Se implementa en vez de ndist para evitar confusiones con la función de distribución acumulada N(x).
def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def black_scholes(S: float, X: float, r: float, sigma: float, t: float, call: bool) -> float:
    sqt = math.sqrt(t)

    d1 = (math.log(S / X) + r * t) / (sigma * sqt) + 0.5 * (sigma * sqt)
    d2 = d1 - (sigma * sqt)

    if call:
        delta = N(d1)
        Nd2 = N(d2)
    else:
        delta = -N(-d1)
        Nd2 = -N(-d2)

    ert = math.exp(-r * t)

    gamma = ndist(d1) / (S * sigma * sqt)
    vega = S * sqt * ndist(d1)
    theta = -(S * sigma * ndist(d1)) / (2 * sqt) - r * X * ert * Nd2
    rho = X * t * ert * Nd2

    return S * delta - X * ert * Nd2

def option_implied_volatility(call: bool, S: float, X: float, r: float, t: float, o: float) -> float:
    sqt = math.sqrt(t)
    MAX_ITER = 100
    ACC = 0.0001
    MIN_SIGMA = 1e-6
    MAX_SIGMA = 5.0

    sigma = (o / S) / (0.398 * sqt)
    sigma = max(MIN_SIGMA, min(sigma, 2.0))

    for i in range(MAX_ITER):
        price = black_scholes(S, X, r, sigma, t, call)
        diff = o - price

        if abs(diff) < ACC:
            return sigma

        d1 = (math.log(S / X) + r * t) / (sigma * sqt) + 0.5 * sigma * sqt
        vega = S * sqt * ndist(d1)

        print(
            f"Iter {i}: sigma={sigma:.8f}, price={price:.8f}, diff={diff:.8f}, "
            f"d1={d1:.8f}, vega={vega:.8f}"
        )

        if not math.isfinite(vega) or vega < 1e-12:
            return 0.0

        step = diff / vega

        # limitar saltos destructivos
        step = max(min(step, 1.0), -1.0)

        sigma = sigma + step

        if not math.isfinite(sigma):
            return 0.0

        sigma = max(MIN_SIGMA, min(sigma, MAX_SIGMA))

    return 0.0

# def call_iv(S: float, X: float, r_pct: float, t_days: int, o: float) -> float:
#     return option_implied_volatility(True, S, X, r_pct/100.0, t_days/365.0, o)

# def put_iv(S: float, X: float, r_pct: float, t_days: int, o: float) -> float:
#     return option_implied_volatility(False, S, X, r_pct/100.0, t_days/365.0, o)

def call_iv(S: float, X: float, r_pct: float, t_days: int, o: float) -> float:
    return get_implied_volatility(
                expected_cost=o,
                s=S,
                k=X,
                t=t_days/365.0,
                r=r_pct/100.0,
                call_put="call",
                estimate=0.1
                )

def put_iv(S: float, X: float, r_pct: float, t_days: int, o: float) -> float:
    return option_implied_volatility(False, S, X, r_pct/100.0, t_days/365.0, o)


# -----------------------------------------

def _double_factorial(n: int) -> int:
    val = 1
    for i in range(n, 1, -2):
        val *= i
    return val

def std_norm_cdf(x: float) -> float:
    probability = 0.0
    if x >= 8:
        return 1.0
    if x <= -8:
        return 0.0

    for i in range(100):
        probability += (x ** (2 * i + 1)) / _double_factorial(2 * i + 1)

    probability *= math.exp(-0.5 * x * x)
    probability /= math.sqrt(2 * math.pi)
    probability += 0.5
    return probability

def black_scholes_bisec(s: float, k: float, t: float, v: float, r: float, call_put: str) -> float:
    w = (r * t + (v ** 2) * t / 2 - math.log(k / s)) / (v * math.sqrt(t))

    if call_put == "call":
        return s * std_norm_cdf(w) - k * math.exp(-r * t) * std_norm_cdf(w - v * math.sqrt(t))
    else:
        return k * math.exp(-r * t) * std_norm_cdf(v * math.sqrt(t) - w) - s * std_norm_cdf(-w)

def get_implied_volatility(expected_cost: float, s: float, k: float, t: float, r: float,
                           call_put: str, estimate: float = 0.1) -> float:
    low = 0.0
    high = float("inf")

    for _ in range(100):
        actual_cost = black_scholes_bisec(s, k, t, estimate, r, call_put)

        if expected_cost * 100 == math.floor(actual_cost * 100):
            break
        elif actual_cost > expected_cost:
            high = estimate
            estimate = (estimate - low) / 2 + low
        else:
            low = estimate
            estimate = (high - estimate) / 2 + estimate
            if not math.isfinite(estimate):
                estimate = low * 2

    return estimate

# ---------- Ejemplo ----------
if __name__ == "__main__":
    # Ejemplo: GGAL put cualquiera
    spot_price = 8310   # Precio del subyacente (spot)
    strike_price = 8530 # Precio de strike
    r_pct = 30.0        # TNA Segura

    today = date(2026, 1, 29)
    expiry = date(2026, 2, 19)      
    t_days = (expiry - today).days  # Dias al vencimiento

    call_last = 213.0  # <-- poné el último de tu call
    put_last = 320.0  # <-- poné el último de tu put

    ivp = put_iv(spot_price, strike_price, r_pct, t_days, put_last)
    print(f"PUT IV = {ivp:.6f}  ({ivp*100:.3f}%)")

    ivc = call_iv(spot_price, strike_price, r_pct, t_days, call_last)
    print(f"CALL IV = {ivc:.6f}  ({ivc*100:.3f}%)")