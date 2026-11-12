"""Fundo do reino, parallax e overlay noturno."""

from __future__ import annotations

import random

from .canvas import Canvas
from .mapa import tile_grama
from .paleta import (
    AGUA,
    AGUA_CLARA,
    CONTORNO,
    GRAMA_ESCURA,
    MADEIRA_ESCURA,
    PEDRA_ESCURA,
    VERDE,
    VERDE_CLARO,
    VERDE_ESCURO,
    com_alpha,
)

LARGURA = 2048
ALTURA = 1536


def _ceu(canvas: Canvas, altura: int = 900) -> None:
    for y in range(altura):
        fracao = y / max(1, altura - 1)
        r = int(84 + 116 * fracao)
        g = int(142 + 62 * fracao)
        b = int(188 - 18 * fracao)
        canvas.linha(0, y, LARGURA - 1, y, (r, g, b, 255))


def fundo_reino_dia() -> Canvas:
    canvas = Canvas(LARGURA, ALTURA)
    _ceu(canvas, 980)
    rng = random.Random(77)
    for _ in range(36):
        x = rng.randrange(0, LARGURA)
        y = rng.randrange(100, 420)
        largura = rng.randrange(60, 140)
        canvas.elipse(x, y, largura, 22, (236, 238, 230, 130))
    canvas.poligono(
        [(0, 800), (260, 540), (520, 760), (820, 480), (1120, 750), (1420, 520),
         (1740, 760), (2048, 610), (2048, 1536), (0, 1536)],
        (78, 104, 92, 255),
    )
    canvas.poligono(
        [(0, 980), (300, 760), (620, 960), (920, 720), (1240, 950), (1560, 740),
         (1840, 930), (2048, 820), (2048, 1536), (0, 1536)],
        (58, 86, 66, 255),
    )
    for _ in range(130):
        x = rng.randrange(0, LARGURA)
        y = rng.randrange(900, 1320)
        altura = rng.randrange(30, 80)
        canvas.retangulo(x, y, 8, altura, MADEIRA_ESCURA)
        canvas.circulo(x + 4, y - 4, rng.randrange(18, 34), VERDE_ESCURO, CONTORNO)
        canvas.circulo(x - 4, y + 2, 12, VERDE)
    for _ in range(180):
        x = rng.randrange(0, LARGURA)
        y = rng.randrange(1150, 1530)
        canvas.linha(x, y, x, y - rng.randrange(4, 16), VERDE_CLARO)
    castelo_x = LARGURA // 2
    canvas.retangulo(castelo_x - 120, 780, 240, 240, PEDRA_ESCURA, CONTORNO)
    for torre in (castelo_x - 170, castelo_x + 90):
        canvas.retangulo(torre, 720, 80, 300, PEDRA_ESCURA, CONTORNO)
        canvas.poligono([(torre - 10, 720), (torre + 40, 650), (torre + 90, 720)], (84, 54, 48, 255), CONTORNO)
    canvas.poligono(
        [(castelo_x - 150, 780), (castelo_x, 650), (castelo_x + 150, 780)],
        (94, 62, 52, 255),
        CONTORNO,
    )
    canvas.retangulo(castelo_x - 4, 610, 8, 90, MADEIRA_ESCURA)
    canvas.poligono([(castelo_x + 4, 614), (castelo_x + 78, 632), (castelo_x + 4, 660)], (168, 58, 52, 255), CONTORNO)
    return canvas


def ceu_parallax() -> Canvas:
    canvas = Canvas(LARGURA, 512)
    for y in range(512):
        fracao = y / 511
        canvas.linha(
            0,
            y,
            LARGURA - 1,
            y,
            (int(72 + 122 * fracao), int(134 + 72 * fracao), int(186 - 12 * fracao), 255),
        )
    return canvas


def montanhas_parallax() -> Canvas:
    canvas = Canvas(LARGURA, 512)
    rng = random.Random(91)
    pontos = [(0, 512)]
    x = 0
    while x < LARGURA:
        x += rng.randrange(90, 180)
        y = rng.randrange(180, 360)
        pontos.append((x, y))
    pontos.extend([(LARGURA, 512), (0, 512)])
    canvas.poligono(pontos, (78, 92, 100, 255), CONTORNO)
    neve = [(px, py) for px, py in pontos if 80 < px < LARGURA - 80]
    for px, py in neve:
        canvas.poligono([(px - 22, py + 22), (px, py), (px + 22, py + 22)], (214, 216, 212, 255))
    return canvas


def arvores_parallax() -> Canvas:
    canvas = Canvas(LARGURA, 512)
    rng = random.Random(93)
    for _ in range(90):
        x = rng.randrange(0, LARGURA)
        base = rng.randrange(400, 512)
        altura = rng.randrange(50, 120)
        canvas.retangulo(x, base - altura, 8, altura, (54, 40, 28, 255))
        for raio, dy, cor in ((34, -20, VERDE_ESCURO), (26, -38, VERDE), (18, -52, VERDE_CLARO)):
            canvas.circulo(x + 4, base - altura + dy, raio, cor, CONTORNO)
    return canvas


def overlay_noite() -> Canvas:
    canvas = Canvas(LARGURA, ALTURA)
    for y in range(ALTURA):
        fracao = y / ALTURA
        alpha = int(30 + 130 * fracao)
        canvas.linha(0, y, LARGURA - 1, y, (18, 26, 58, alpha))
    canvas.circulo(1740, 200, 54, (220, 220, 190, 200))
    canvas.circulo(1762, 184, 10, (196, 198, 174, 160))
    canvas.circulo(1720, 216, 7, (196, 198, 174, 140))
    return canvas


def tile_grama_fundo() -> Canvas:
    return tile_grama(0)
