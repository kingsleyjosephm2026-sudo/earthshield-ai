import numpy as np
def ndvi(nir, red, nodata=None, scale=1.0, eps=1e-6):
    """NDVI=(NIR-Red)/(NIR+Red). `scale` divides raw values (Sentinel-2 L2A DN -> reflectance: scale=10000).
    Returns float array; nodata pixels, NaNs and |NIR+Red|<eps become NaN (never 0)."""
    nir = np.asarray(nir, float); red = np.asarray(red, float)
    bad = ~np.isfinite(nir) | ~np.isfinite(red)
    if nodata is not None: bad |= (nir == nodata) | (red == nodata)
    n, r = nir/scale, red/scale
    den = n + r
    bad |= np.abs(den) < eps
    out = np.full(n.shape, np.nan)
    np.divide(n - r, den, out=out, where=~bad)
    return np.clip(out, -1.0, 1.0)
