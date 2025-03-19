from enum import Enum


class CoordinateSystem(Enum):
    """Available coordinate systems for a group element."""

    AFFINE = 0
    """Affine coordinate system (x, y)."""

    P2 = 1
    """Projective coordinate system (X:Y:Z) satisfying x=X/Z, y=Y/Z."""

    P3 = 2
    """Extended projective coordinate system (X:Y:Z:T) satisfying x=X/Z, y=Y/Z, XY=ZT."""

    P1xP1 = 3
    """Completed coordinate system ((X:Z), (Y:T)) satisfying x=X/Z, y=Y/T."""

    PRECOMPUTED = 4
    """Precomputed coordinate system (y+x, y-x, 2dxy)."""

    CACHED = 5
    """Cached coordinate system (Y+X, Y-X, Z, 2dT)."""
