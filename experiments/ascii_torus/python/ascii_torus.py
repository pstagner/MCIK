import argparse
import sys
import time
import math
import csv
from typing import List

from mcik.experiments.ascii_torus import Params, estimate_ascii_quality, suggest_step

RAMP = " .:-=+*#%@"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["interactive", "batch", "synergy"], default="interactive")
    p.add_argument("--target-fps", type=int, default=30)
    p.add_argument("--frames", type=int, default=300)
    p.add_argument("--resolution-scale", type=float, default=1.0)
    p.add_argument("--samples-per-pixel", type=int, default=1)
    p.add_argument("--gamma", type=float, default=1.0)
    p.add_argument("--normal-smooth", type=float, default=0.0)
    p.add_argument("--ramp-size", type=int, default=10)
    p.add_argument("--controller", choices=["off", "K", "KH"], default="off")
    p.add_argument("--ctrl-interval", type=int, default=10)
    p.add_argument("--w-fps", type=float, default=0.5)
    p.add_argument("--w-quality", type=float, default=0.5)
    p.add_argument("--log-csv", type=str, default="")
    return p.parse_args()


def clear():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def build_ramp(size: int) -> str:
    if size <= 1:
        return RAMP[0]
    if size == len(RAMP):
        return RAMP
    out = []
    for i in range(size):
        t = i / (size - 1)
        idx = t * (len(RAMP) - 1)
        i0 = int(idx)
        i1 = min(len(RAMP) - 1, i0 + 1)
        c = RAMP[i0] if (idx - i0) < 0.5 else RAMP[i1]
        out.append(c)
    return "".join(out)


def render_frame(w: int, h: int, A: float, B: float, gamma: float, ramp: str) -> List[str]:
    buf = [" "] * (w * h)
    zbuf = [0.0] * (w * h)
    R = 1.0
    r = 0.5
    cosA, sinA = math.cos(A), math.sin(A)
    cosB, sinB = math.cos(B), math.sin(B)
    lx, ly, lz = 0.0, 1.0, -1.0
    K1, K2 = 20.0, 5.0

    th = 0.0
    while th < 2 * math.pi:
        costh, sinth = math.cos(th), math.sin(th)
        ph = 0.0
        while ph < 2 * math.pi:
            cosph, sinph = math.cos(ph), math.sin(ph)
            cx = (R + r * costh) * cosph
            cy = (R + r * costh) * sinph
            cz = r * sinth
            x = cx * cosB - cy * sinB
            y = cx * sinB + cy * cosB
            z = cz
            y2 = y * cosA - z * sinA
            z2 = y * sinA + z * cosA
            ooz = 1.0 / (z2 + K2)
            xp = int(w / 2 + K1 * ooz * x)
            yp = int(h / 2 + K1 * ooz * y2 * 0.5)
            nx, ny, nz = costh * cosph, costh * sinph, sinth
            nx_rz = nx * cosB - ny * sinB
            ny_rz = nx * sinB + ny * cosB
            nz_rz = nz
            nny = ny_rz * cosA - nz_rz * sinA
            nnz = ny_rz * sinA + nz_rz * cosA
            nnx = nx_rz
            L = max(0.0, nnx * lx + nny * ly + nnz * lz)
            shade = L ** (1.0 / gamma if gamma > 0 else 1.0)
            idx = min(len(ramp) - 1, max(0, int(shade * (len(ramp) - 1))))
            if 0 <= xp < w and 0 <= yp < h:
                off = yp * w + xp
                if ooz > zbuf[off]:
                    zbuf[off] = ooz
                    buf[off] = ramp[idx]
            ph += 0.02
        th += 0.07
    return buf


def draw(buf, w, h):
    for y in range(h):
        sys.stdout.write("".join(buf[y * w:(y + 1) * w]) + "\n")
    sys.stdout.flush()


def evaluate_score(p: Params, A: float, B: float, base_w: int, base_h: int, target_fps: int, w_fps: float, w_quality: float) -> float:
    w = max(10, int(base_w * p.resolution_scale))
    h = max(10, int(base_h * p.resolution_scale))
    ramp = build_ramp(p.ramp_size)
    t0 = time.time()
    buf = render_frame(w, h, A, B, p.gamma, ramp)
    elapsed_ms = (time.time() - t0) * 1000.0
    fps = 1000.0 / elapsed_ms if elapsed_ms > 0 else 0.0
    q = estimate_ascii_quality(buf, w, h)
    fps_norm = min(fps / max(1, target_fps), 1.0)
    return w_fps * fps_norm + w_quality * q


def synergy_demo(args):
    base_w, base_h = 80, 24
    A, B = 0.6, 0.4
    p = Params(args.resolution_scale, args.samples_per_pixel, args.gamma, args.normal_smooth, args.ramp_size)
    def ev(pp: Params) -> float:
        return evaluate_score(pp, A, B, base_w, base_h, args.target_fps, args.w_fps, args.w_quality)
    s0 = ev(p)
    pk, _ = suggest_step(p, ev, False)
    pkh, _ = suggest_step(p, ev, True)
    sk = ev(pk)
    skh = ev(pkh)
    print("Synergy demo (fixed scene)")
    print(f"Base score:{s0:.3f}")
    print(f"K-only  score:{sk:.3f}  d:{sk - s0:.3f}  params:[scale={pk.resolution_scale}, spp={pk.samples_per_pixel}, gamma={pk.gamma}, ramp={pk.ramp_size}]")
    print(f"K+H    score:{skh:.3f}  d:{skh - s0:.3f}  params:[scale={pkh.resolution_scale}, spp={pkh.samples_per_pixel}, gamma={pkh.gamma}, ramp={pkh.ramp_size}]")


def main():
    args = parse_args()
    if args.mode == "synergy":
        synergy_demo(args)
        return

    base_w, base_h = 80, 24
    w = max(10, int(base_w * args.resolution_scale))
    h = max(10, int(base_h * args.resolution_scale))
    ramp = build_ramp(args.ramp_size)

    frames = args.frames if args.mode == "batch" else 10**9
    A = 0.0
    B = 0.0
    dA, dB = 0.05, 0.03

    # controller params
    pv = Params(args.resolution_scale, args.samples_per_pixel, args.gamma, args.normal_smooth, args.ramp_size)

    # CSV logging
    writer = None
    fobj = None
    if args.mode == "batch":
        path = args.log_csv or f"test_data/ascii_torus/log-{int(time.time()*1000)}.csv"
        fobj = open(path, "w", newline="")
        writer = csv.writer(fobj)
        writer.writerow(["frame","ms","fps","quality","scale","spp","gamma","ramp","controller"])

    for i in range(frames):
        t0 = time.time()
        clear()
        buf = render_frame(w, h, A, B, args.gamma, ramp)
        elapsed_ms = (time.time() - t0) * 1000.0
        fps = 1000.0 / elapsed_ms if elapsed_ms > 0 else 0.0
        q = estimate_ascii_quality(buf, w, h)
        sys.stdout.write(f"FPS:{int(round(fps))}  target:{args.target_fps}  quality:{q:.2f}  params:[scale={args.resolution_scale}, spp={args.samples_per_pixel}, gamma={args.gamma}, ramp={args.ramp_size}]  controller:{args.controller}\n")
        draw(buf, w, h)

        # Controller step
        if args.controller != "off" and (i % max(1, args.ctrl_interval) == 0):
            def ev(pp: Params) -> float:
                return evaluate_score(pp, A, B, base_w, base_h, args.target_fps, args.w_fps, args.w_quality)
            use_h = (args.controller == "KH")
            nxt, _ = suggest_step(pv, ev, use_h)
            pv = nxt
            # apply
            args.resolution_scale = pv.resolution_scale
            args.samples_per_pixel = pv.samples_per_pixel
            args.gamma = pv.gamma
            args.normal_smooth = pv.normal_smooth
            args.ramp_size = pv.ramp_size
            ramp = build_ramp(args.ramp_size)
            w = max(10, int(base_w * args.resolution_scale))
            h = max(10, int(base_h * args.resolution_scale))

        # Batch CSV
        if writer is not None:
            writer.writerow([i, elapsed_ms, fps, q, args.resolution_scale, args.samples_per_pixel, args.gamma, args.ramp_size, args.controller])

        A += dA
        B += dB
        if args.mode == "interactive":
            target_ms = 1000.0 / max(1, args.target_fps)
            if elapsed_ms < target_ms:
                time.sleep((target_ms - elapsed_ms) / 1000.0)

    if fobj is not None:
        fobj.close()


if __name__ == "__main__":
    main()
