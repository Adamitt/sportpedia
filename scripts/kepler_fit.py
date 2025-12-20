"""
Kepler Orbit Parameter Estimation (pure Python, no NumPy)

Given Kepler's polar form: r = p / (1 - e cos(theta)),
we can linearize by taking reciprocals:

    1/r = (1/p) - (e/p) cos(theta) = x1 + x2 * cos(theta)

So we fit a linear model y = A x with
- y_i = 1 / r_i
- A_i = [1, cos(theta_i)]
- unknown x = [x1, x2]^T with x1 = 1/p and x2 = -(e/p)

From the least squares normal equations: (A^T A) x = A^T y,
we solve for x (2x1) using LU decomposition (no external libraries).
Then recover:
- p = 1 / x1
- e = -x2 / x1

Finally, classify the orbit:
- e < 1  -> ellipse
- e = 1  -> parabola (within tolerance)
- e > 1  -> hyperbola

This script uses the dataset from the prompt:
(theta, r) = (pi/4, 45), (pi/3, 22), (2pi/3, 6.5), (3pi/4, 7)

Run:
    python scripts/kepler_fit.py
"""

from math import cos, pi, isclose
from typing import List, Tuple


def transpose(M: List[List[float]]) -> List[List[float]]:
    return [list(row) for row in zip(*M)]


def matmul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    n, m, p = len(A), len(A[0]), len(B[0])
    # A: n x m, B: m x p
    out = [[0.0 for _ in range(p)] for _ in range(n)]
    for i in range(n):
        for k in range(m):
            aik = A[i][k]
            for j in range(p):
                out[i][j] += aik * B[k][j]
    return out


def matvec(A: List[List[float]], v: List[float]) -> List[float]:
    n, m = len(A), len(A[0])
    out = [0.0 for _ in range(n)]
    for i in range(n):
        s = 0.0
        for j in range(m):
            s += A[i][j] * v[j]
        out[i] = s
    return out


def lu_decompose(A: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """Doolittle LU decomposition without pivoting.
    A must be square and non-singular. Returns (L, U) with diag(L)=1.
    """
    n = len(A)
    # Deep copy
    U = [row[:] for row in A]
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        L[i][i] = 1.0
    for k in range(n - 1):
        pivot = U[k][k]
        if abs(pivot) < 1e-12:
            raise ZeroDivisionError("Zero pivot encountered; pivoting required")
        for i in range(k + 1, n):
            factor = U[i][k] / pivot
            L[i][k] = factor
            # Row operation on U
            for j in range(k, n):
                U[i][j] -= factor * U[k][j]
    return L, U


def forward_substitution(L: List[List[float]], b: List[float]) -> List[float]:
    n = len(L)
    y = [0.0] * n
    for i in range(n):
        s = b[i]
        for j in range(i):
            s -= L[i][j] * y[j]
        # L[i][i] assumed 1.0
        y[i] = s
    return y


def back_substitution(U: List[List[float]], y: List[float]) -> List[float]:
    n = len(U)
    x = [0.0] * n
    for i in reversed(range(n)):
        s = y[i]
        for j in range(i + 1, n):
            s -= U[i][j] * x[j]
        pivot = U[i][i]
        if abs(pivot) < 1e-12:
            raise ZeroDivisionError("Zero pivot in back substitution")
        x[i] = s / pivot
    return x


def solve_lu(A: List[List[float]], b: List[float]) -> List[float]:
    L, U = lu_decompose(A)
    y = forward_substitution(L, b)
    x = back_substitution(U, y)
    return x


def kepler_fit(data: List[Tuple[float, float]]) -> Tuple[float, float, float]:
    """Return (p, e, residual_L2) from (theta, r) data via least squares."""
    # Build A (n x 2) and b (n)
    A = []
    b = []
    for theta, r in data:
        A.append([1.0, cos(theta)])
        b.append(1.0 / r)

    AT = transpose(A)
    ATA = matmul(AT, A)  # 2x2
    ATb = matvec(AT, b)  # 2

    # Solve (ATA) x = ATb
    x1, x2 = solve_lu(ATA, ATb)

    # Recover p and e
    p = 1.0 / x1
    e = -x2 / x1

    # Compute residual ||Ax - b||_2
    # Ax
    Ax = matvec(A, [x1, x2])
    res2 = 0.0
    for yi, bi in zip(Ax, b):
        diff = yi - bi
        res2 += diff * diff

    return p, e, res2 ** 0.5


def classify_orbit(e: float, tol: float = 1e-3) -> str:
    if isclose(e, 1.0, rel_tol=0.0, abs_tol=tol):
        return "parabola"
    if e < 1.0:
        return "ellipse"
    return "hyperbola"


def main() -> None:
    # Dataset from the prompt
    data = [
        (pi/4, 45.0),
        (pi/3, 22.0),
        (2*pi/3, 6.5),
        (3*pi/4, 7.0),
    ]

    # Build and print A and b explicitly
    A = [[1.0, cos(t)] for t, _ in data]
    b = [1.0 / r for _, r in data]

    print("A (rows = [1, cos(theta)]):")
    for row in A:
        print([round(v, 6) for v in row])
    print("b (entries = 1/r):")
    print([round(v, 6) for v in b])

    p, e, res = kepler_fit(data)

    print("\nEstimated parameters:")
    print(f"x1 = 1/p = {1.0/p:.6f}")
    print(f"x2 = -(e/p) = {-e/p:.6f}")
    print(f"p = {p:.6f}")
    print(f"e = {e:.6f}")
    print(f"Residual L2 norm = {res:.6e}")
    print(f"Orbit type = {classify_orbit(e)}")


if __name__ == "__main__":
    main()
