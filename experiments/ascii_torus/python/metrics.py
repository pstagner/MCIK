def char_density(c: str) -> float:
    ramp = " .:-=+*#%@"
    if c in ramp:
        return ramp.index(c) / (len(ramp) - 1)
    o = ord(c)
    o = max(32, min(126, o))
    return (o - 32) / (126 - 32)


def estimate_ascii_quality(buf, w: int, h: int) -> float:
    if w < 3 or h < 3:
        return 0.0
    acc = 0.0
    cnt = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            off = y * w + x
            c = char_density(buf[off])
            cx1 = char_density(buf[off - 1])
            cx2 = char_density(buf[off + 1])
            cy1 = char_density(buf[off - w])
            cy2 = char_density(buf[off + w])
            gx = 0.5 * (cx2 - cx1)
            gy = 0.5 * (cy2 - cy1)
            acc += (gx * gx + gy * gy) ** 0.5
            cnt += 1
    if cnt == 0:
        return 0.0
    avg = acc / cnt
    return max(0.0, min(1.0, avg))
