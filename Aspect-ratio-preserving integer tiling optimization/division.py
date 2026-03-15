"""
Uso:
    python division.py <imagen> <WxH> [--unidad px|cm] [--epsilon F] [--verbose true|false]

Ejemplos:
    python division.py pintura.jpg 594x832
    python division.py pintura.jpg 22x15.7 --unidad cm
    python division.py pintura.jpg 22x15.7 --unidad cm --epsilon 0.03    
"""

import argparse
import sys, os

from PIL import Image
from scipy.optimize import differential_evolution

CM_PER_INCH = 2.54

def cm_a_px(w_cm, h_cm, dpi_x, dpi_y):
    w_px = round(w_cm / CM_PER_INCH * dpi_x)
    h_px = round(h_cm / CM_PER_INCH * dpi_y)
    return w_px, h_px

def parse_dim(text,un,dpi_x,dpi_y):
    parts = text.lower().replace(' ','').split('x')
    if len(parts) != 2:
        raise ValueError("Oe, no seas huevón p. \n'WxH'.")

    w, h = float(parts[0]), float(parts[1])
    if un == 'cm':
        w, h = cm_a_px(w, h, dpi_x, dpi_y)
    else:
        w, h = int(round(w)), int(round(h))
    return w, h

def dims(delta, w_base, h_base):
    #δ=0 → 0°, δ=1 → 90°
    if delta == 0:
        return w_base, h_base
    return h_base, w_base

def optimizar(rho_star, w_libro, h_libro, epsilon, max_cr=40):
    """
    Variables: C ∈ ℤ⁺, R ∈ ℤ⁺, δ ∈ {0,1}
    Objetivo:  minimizar N = C·R
    Restricción: |ρ(C,R,δ) − ρ*| / ρ* ≤ ε
    """
    BIG_M = 1e7
 
    def objetivo(x):
        C     = int(round(x[0]))
        R     = int(round(x[1]))
        delta = int(round(x[2]))

        w, h  = dims(delta, w_libro, h_libro)
        rho   = (C * w) / (R * h)
        err   = abs(rho - rho_star) / rho_star

        penal = BIG_M * max(0, err - epsilon) ** 2
        return C * R + penal
 
    result = differential_evolution(
        objetivo,
        bounds        = [(1, max_cr), (1, max_cr), (0, 1)],
        integrality   = [1, 1, 1],
        maxiter       = 10000,
        popsize       = 30,
        tol           = 1e-14,
        mutation      = (0.5, 1.5),
        recombination = 0.9,
    )
 
    C     = int(round(result.x[0]))
    R     = int(round(result.x[1]))
    delta = int(round(result.x[2]))
    w, h  = dims(delta, w_libro, h_libro)
    rho   = (C * w) / (R * h)
    err   = abs(rho - rho_star) / rho_star
 
    success = result.success
    message = result.message

    return {
        'success': success,
        'message': message,
        'C':       C,
        'R':       R,
        'delta':   delta,
        'ori':     'rotado' if delta else 'original',
        'N':       C * R,
        'w':       w,
        'h':       h,
        'rho':     rho,
        'err':     err,
        'grilla_w': C * w,
        'grilla_h': R * h,
    }

def exportar(img_path, sol, salida_dir):
    os.makedirs(salida_dir, exist_ok=True)

    img = Image.open(img_path).convert('RGB')
    img = img.resize((sol['grilla_w'], sol['grilla_h']), Image.LANCZOS)

    tile_w, tile_h = sol['w'], sol['h']

    for r in range(sol['R']):
        for c in range(sol['C']):
            x0, y0 = c * tile_w, r * tile_h
            tile = img.crop((x0, y0, x0 + tile_w, y0 + tile_h))
            tile.save(
                os.path.join(salida_dir,f'tile_R{r+1:02d}_C{c+1:02d}.png')
            )
 
    print(f"{sol['N']} tiles exportados → {salida_dir}")
 


def main():
    parser = argparse.ArgumentParser(
        description='Stochastic optimization with Differential Evolution.'
    )
    parser.add_argument('imagen',    help='Path a la imagen')
    parser.add_argument('dimensiones', help='Dimensiones del cuaderno WxH, ej: 594x832')
    parser.add_argument('--unidad',  default='cm', choices=['px', 'cm'],
                        help='Unidad de las dimensiones (default: cm)')
    parser.add_argument('--epsilon', type=float, default=0.05,
                        help='Tolerancia de ratio admisible (default: 0.05)')
    parser.add_argument('--salida',  default='tiles',
                        help='Directorio de salida (default: ./tiles)')
    parser.add_argument('--verbose', default='true', choices=['true','false'],
                        help='Printear la información (default: true)')
    args = parser.parse_args()
    verbose = True if args.verbose=='true' else False

    # Leer imagen
    img_path = args.imagen
    assert os.path.exists(img_path)
 
    with Image.open(img_path) as img:
        pin_w, pin_h = img.size
        dpi_x, dpi_y = img.info.get('dpi')
 
    rho_s = pin_w / pin_h
 
    # Parsear dimensiones
    w_libro, h_libro = parse_dim(args.dimensiones, args.unidad, dpi_x,dpi_y)
 
    if verbose:
        print()
        print("─── Parameters ─────────────────────────────────────────────────")
        print(f"  Image:       ({pin_w} × {pin_h} px)")
        print(f"  ρ* objetivo: {rho_s:.6f}")
        print(f"  Tile:        ({w_libro} × {h_libro} px)", end='')
        if args.unidad == 'cm':
            print(f"  (convertido desde {args.dimensiones} cm a {dpi_x}x{dpi_y} dpi)", end='')
        print()
        print(f"  Tolerance:   ε = {args.epsilon*100:.1f}%")
        print("────────────────────────────────────────────────────────────────")
        print()
    
    # Optimizar
    sol = optimizar(rho_s, w_libro, h_libro, args.epsilon)
 
    if verbose:
        print("─── Results ────────────────────────────────────────────────────")
        print(f"  Rotation:     {sol['ori']}  (δ = {sol['delta']})")
        print(f"  Grid:         C = {sol['C']} columns,  R = {sol['R']} rows")
        print(f"  Best N:       {sol['N']} tiles")
        print(f"  Dimensions:   {sol['grilla_w']} × {sol['grilla_h']} px")
        print(f"  ρ grid:       {sol['rho']:.6f}")
        print(f"  Error ratio:  {sol['err']*100:.4f}%")
        print()
        print(f"  Converged:    {sol['success']}")
        print(f"  Mensaje:      {sol['message']}")
        print("────────────────────────────────────────────────────────────────")
        print()

    if not sol['success']:
        print("La optimización no encontró solución dentro de la tolerancia.")
        print("Intentá aumentar --epsilon o ampliar el rango de búsqueda.")
        sys.exit(1)
 
    # Exportar
    print("─── Exportando ─────────────────────────────────────────────────")
    exportar(img_path, sol, args.salida)
    print("────────────────────────────────────────────────────────────────")
    print()
 
 
if __name__ == '__main__':
    main()
 
