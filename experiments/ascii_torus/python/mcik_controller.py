from dataclasses import dataclass
from typing import Callable, Tuple


@dataclass
class Params:
    resolution_scale: float  # 0.25..1.0
    samples_per_pixel: int   # 1..4
    gamma: float             # 0.5..3.0
    normal_smooth: float     # 0..1
    ramp_size: int           # 8..16


def _clamp(p: Params) -> Params:
    return Params(
        resolution_scale=max(0.25, min(1.0, p.resolution_scale)),
        samples_per_pixel=max(1, min(4, p.samples_per_pixel)),
        gamma=max(0.5, min(3.0, p.gamma)),
        normal_smooth=max(0.0, min(1.0, p.normal_smooth)),
        ramp_size=max(8, min(16, p.ramp_size)),
    )


def suggest_step_K(current: Params, evaluate: Callable[[Params], float]) -> Tuple[Params, str]:
    base = evaluate(current)
    best_p = current
    best_s = base

    def try_update(p: Params):
        nonlocal best_p, best_s
        p = _clamp(p)
        s = evaluate(p)
        if s > best_s:
            best_s = s
            best_p = p

    # deltas
    d_scale = 0.05
    d_spp = 1
    d_gamma = 0.1
    d_ns = 0.1
    d_ramp = 2

    p = Params(**{**current.__dict__, "resolution_scale": current.resolution_scale + d_scale}); try_update(p)
    p = Params(**{**current.__dict__, "resolution_scale": current.resolution_scale - d_scale}); try_update(p)
    p = Params(**{**current.__dict__, "samples_per_pixel": current.samples_per_pixel + d_spp}); try_update(p)
    p = Params(**{**current.__dict__, "samples_per_pixel": current.samples_per_pixel - d_spp}); try_update(p)
    p = Params(**{**current.__dict__, "gamma": current.gamma + d_gamma}); try_update(p)
    p = Params(**{**current.__dict__, "gamma": current.gamma - d_gamma}); try_update(p)
    p = Params(**{**current.__dict__, "normal_smooth": current.normal_smooth + d_ns}); try_update(p)
    p = Params(**{**current.__dict__, "normal_smooth": current.normal_smooth - d_ns}); try_update(p)
    p = Params(**{**current.__dict__, "ramp_size": current.ramp_size + d_ramp}); try_update(p)
    p = Params(**{**current.__dict__, "ramp_size": current.ramp_size - d_ramp}); try_update(p)

    return best_p, "K"


def suggest_step_KH(current: Params, evaluate: Callable[[Params], float]) -> Tuple[Params, str]:
    best_p, _ = suggest_step_K(current, evaluate)
    best_s = evaluate(best_p)

    def try_pair(apply_a, apply_b):
        nonlocal best_p, best_s
        pa = _clamp(apply_a(current))
        pb = _clamp(apply_b(current))
        pab = _clamp(apply_b(pa))
        s0 = evaluate(current)
        sa = evaluate(pa)
        sb = evaluate(pb)
        sab = evaluate(pab)
        synergy = (sab - s0) - ((sa - s0) + (sb - s0))
        if synergy > 0.0 and sab > best_s:
            best_s = sab
            best_p = pab

    d_scale = 0.05
    d_spp = 1
    d_gamma = 0.1
    d_ns = 0.1

    # Pair 1: scale × spp
    try_pair(
        lambda p: Params(**{**p.__dict__, "resolution_scale": p.resolution_scale + d_scale}),
        lambda p: Params(**{**p.__dict__, "samples_per_pixel": p.samples_per_pixel + d_spp}),
    )

    # Pair 2: gamma × normal_smooth
    try_pair(
        lambda p: Params(**{**p.__dict__, "gamma": p.gamma + d_gamma}),
        lambda p: Params(**{**p.__dict__, "normal_smooth": p.normal_smooth + d_ns}),
    )

    # Pair 3: scale × gamma
    try_pair(
        lambda p: Params(**{**p.__dict__, "resolution_scale": p.resolution_scale - d_scale}),
        lambda p: Params(**{**p.__dict__, "gamma": p.gamma + d_gamma}),
    )

    return best_p, "K+H"


def suggest_step(current: Params, evaluate: Callable[[Params], float], use_h: bool):
    return suggest_step_KH(current, evaluate) if use_h else suggest_step_K(current, evaluate)
