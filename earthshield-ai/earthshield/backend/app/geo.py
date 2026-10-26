"""Geometry utilities (pure Python). Planar-projected area on a local equirectangular frame.
Accurate to well under 1% for polygons < ~1 degree across; NOT a substitute for PyProj/GeoPandas in production."""
import math
from itertools import combinations
R = 6371008.8  # mean Earth radius, metres

def _open(ring):
    return ring[:-1] if len(ring) > 1 and tuple(ring[0]) == tuple(ring[-1]) else list(ring)

def validate_ring(ring):
    """Return list of error strings for a [lon, lat] ring (empty list = valid)."""
    errs = []
    if len(ring) < 4 or tuple(ring[0]) != tuple(ring[-1]):
        return ["ring must be closed with >= 4 points"]
    for lon, lat in ring:
        if not (math.isfinite(lon) and math.isfinite(lat)) or not (-180 <= lon <= 180 and -90 <= lat <= 90):
            return [f"invalid coordinate ({lon}, {lat})"]
    pts = _open(ring); n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if _seg_cross(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                errs.append("self-intersecting ring"); return errs
    lat0 = sum(p[1] for p in pts) / n; lon0 = sum(p[0] for p in pts) / n
    if abs(shoelace(project(pts, lat0, lon0))) < 1e-6:
        errs.append("zero area")
    return errs

def _cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
def _seg_cross(p1, p2, p3, p4):
    d1, d2, d3, d4 = _cross(p3, p4, p1), _cross(p3, p4, p2), _cross(p1, p2, p3), _cross(p1, p2, p4)
    return d1*d2 < 0 and d3*d4 < 0

def project(pts, lat0, lon0):
    k = R * math.cos(math.radians(lat0))
    return [(k * math.radians(x - lon0), R * math.radians(y - lat0)) for x, y in pts]

def shoelace(xy):
    return 0.5 * sum(xy[i][0]*xy[(i+1) % len(xy)][1] - xy[(i+1) % len(xy)][0]*xy[i][1] for i in range(len(xy)))

def area_m2(ring):
    pts = _open(ring)
    return abs(shoelace(project(pts, sum(p[1] for p in pts)/len(pts), sum(p[0] for p in pts)/len(pts))))

def is_convex(xy):
    s = [_cross(xy[i], xy[(i+1) % len(xy)], xy[(i+2) % len(xy)]) for i in range(len(xy))]
    return all(v >= -1e-9 for v in s) or all(v <= 1e-9 for v in s)

def clip_convex(subject, clip):
    """Sutherland-Hodgman: clip `subject` by a CONVEX polygon `clip` (planar coords)."""
    if shoelace(clip) < 0: clip = clip[::-1]
    out = subject
    for i in range(len(clip)):
        a, b = clip[i], clip[(i+1) % len(clip)]
        inp, out = out, []
        for j in range(len(inp)):
            p, q = inp[j], inp[(j+1) % len(inp)]
            ip, iq = _cross(a, b, p) >= 0, _cross(a, b, q) >= 0
            if ip != iq:
                dx, dy = q[0]-p[0], q[1]-p[1]; ex, ey = b[0]-a[0], b[1]-a[1]
                den = dx*ey - dy*ex
                t = ((a[0]-p[0])*ey - (a[1]-p[1])*ex) / den
                out.append((p[0]+t*dx, p[1]+t*dy))
            if iq: out.append(q)
        if not out: return []
    return out

def flood_overlap(region_ring, flood_rings):
    """Area (m2) of region covered by the UNION of flood polygons (overlaps counted once, via inclusion-exclusion).
    Flood polygons must be convex. Returns (affected_m2, region_m2)."""
    pts = _open(region_ring); lat0 = sum(p[1] for p in pts)/len(pts); lon0 = sum(p[0] for p in pts)/len(pts)
    reg = project(pts, lat0, lon0)
    pieces = []
    for fr in flood_rings:
        errs = validate_ring(fr)
        if errs: raise ValueError(f"invalid flood polygon: {errs[0]}")
        f = project(_open(fr), lat0, lon0)
        if not is_convex(f): raise ValueError("flood polygon must be convex in this implementation")
        p = clip_convex(reg, f)
        if len(p) >= 3: pieces.append(p)
    if len(pieces) > 8: raise ValueError("too many overlapping flood polygons (max 8)")
    total = 0.0
    for r in range(1, len(pieces)+1):
        for combo in combinations(pieces, r):
            cur = combo[0]
            for nxt in combo[1:]:
                cur = clip_convex(cur, nxt) if cur else []
                if len(cur) < 3: cur = []; break
            if cur: total += (-1)**(r+1) * abs(shoelace(cur))
    return total, abs(shoelace(reg))
