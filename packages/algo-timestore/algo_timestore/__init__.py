"""ASP timestore: 24h circle, year horizon, SciPy ≥16-param fit (#20)."""

from .ciphers import FAIRFAX_CIRCLE_SIM_ID, REGISTERED_EXPERIMENT_IDS, experiment_tag
from .fit import N_PARAMS, fit_circle_series, model_circle
from .quantum import TIME_QUANTUM_S, circle_fraction_utc, quantize_posix, within_year_horizon
from .stamp import stamp
from .weather import FAIRFAX_COUNTY_CENTROID, fairfax_weather_prior

__all__ = [
    "TIME_QUANTUM_S",
    "N_PARAMS",
    "FAIRFAX_COUNTY_CENTROID",
    "FAIRFAX_CIRCLE_SIM_ID",
    "REGISTERED_EXPERIMENT_IDS",
    "quantize_posix",
    "circle_fraction_utc",
    "within_year_horizon",
    "model_circle",
    "fit_circle_series",
    "experiment_tag",
    "fairfax_weather_prior",
    "stamp",
]
