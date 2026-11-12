"""Tiles, natureza e marcadores do mapa."""

from __future__ import annotations

import random

from .canvas import Canvas
from .paleta import (
    AGUA,
    AGUA_CLARA,
    AGUA_ESCURA,
    CONTORNO,
    CONTORNO_SUAVE,
    FERRO,
    GRAMA,
    GRAMA_CLARA,
    GRAMA_ESCURA,
    MADEIRA,
    MADEIRA_ESCURA,
    OURO,
    PEDRA,
    PEDRA_CLARA,
    PEDRA_ESCURA,
    SOMBRA,
    TERRA,
    TERRA_ESCURA,
    VERDE,
    VERDE_CLARO,
    VERDE_ESCURO,
    VERMELHO,
    VERMELHO_ESCURO,
)

TILE = 64


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def tile_grama(variacao: int = 0) -> Canvas:
    canvas = Canvas(TILE, TILE, GRAMA)
    rng = _rng(100 + variacao)
    for _ in range(42):
        x = rng.randrange(2, TILE - 2)
        y = rng.randrange(2, TILE - 2)
        cor = GRAMA_CLARA if rng.random() < 0.55 else GRAMA_ESCURA
        canvas.retangulo(x, y, 2, 1, cor)
    for x, y in ((9, 18), (42, 10), (24, 48), (54, 40)):
        canvas.linha(x, y, x + 1, y - 4, GRAMA_ESCURA)
        canvas.linha(x + 1, y - 4, x + 3, y - 2, GRAMA_CLARA)
    return canvas


def tile_terra(variacao: int = 0) -> Canvas:
    canvas = Canvas(TILE, TILE, TERRA)
    rng = _rng(200 + variacao)
    for _ in range(36):
        x = rng.randrange(2, TILE - 3)
        y = rng.randrange(2, TILE - 3)
        canvas.retangulo(x, y, rng.choice((1, 2, 3)), 1, TERRA_ESCURA)
    for x, y in ((12, 12), (34, 24), (48, 46), (20, 50)):
        canvas.circulo(x, y, 2, PEDRA, CONTORNO_SUAVE)
        canvas.circulo(x - 1, y - 1, 1, PEDRA_CLARA)
    return canvas


def tile_floresta(variacao: int = 0) -> Canvas:
    canvas = Canvas(TILE, TILE, GRAMA_ESCURA)
    rng = _rng(300 + variacao)
    for _ in range(40):
        x = rng.randrange(4, TILE - 4)
        y = rng.randrange(4, TILE - 4)
        canvas.retangulo(x, y, 2, 2, GRAMA_CLARA if rng.random() < 0.4 else GRAMA)
    for x, y in ((14, 42), (38, 20), (52, 48)):
        canvas.circulo(x, y, 8, VERDE_ESCURO, CONTORNO_SUAVE)
        canvas.circulo(x - 2, y - 2, 4, VERDE)
        canvas.circulo(x + 2, y - 3, 3, VERDE_CLARO)
    return canvas


def tile_agua(frame: int = 0) -> Canvas:
    canvas = Canvas(TILE, TILE, AGUA)
    canvas.retangulo(0, 0, TILE, 6, AGUA_ESCURA)
    for linha in range(4):
        y = 10 + linha * 14
        offset = (frame * 8 + linha * 6) % 20
        for x in range(-20 + offset, TILE, 24):
            canvas.linha(x, y, x + 11, y, AGUA_CLARA)
            canvas.linha(x + 4, y + 3, x + 15, y + 3, AGUA_ESCURA)
    return canvas


def tile_rocha(variacao: int = 0) -> Canvas:
    canvas = Canvas(TILE, TILE, PEDRA_ESCURA)
    rng = _rng(400 + variacao)
    for _ in range(24):
        x = rng.randrange(0, TILE - 4)
        y = rng.randrange(0, TILE - 4)
        canvas.retangulo(x, y, rng.choice((3, 4, 6)), 2, PEDRA if rng.random() < 0.6 else PEDRA_CLARA)
    for _ in range(5):
        x = rng.randrange(8, TILE - 8)
        y = rng.randrange(8, TILE - 8)
        canvas.linha(x, y, x + 6, y + 4, PEDRA_ESCURA)
    return canvas


def autotile_grama() -> Canvas:
    frames = []
    for mascara in range(16):
        canvas = tile_grama(mascara % 3)
        borda = PEDRA_ESCURA
        if mascara & 1:
            canvas.retangulo(0, 0, TILE, 6, borda)
        if mascara & 2:
            canvas.retangulo(TILE - 6, 0, 6, TILE, borda)
        if mascara & 4:
            canvas.retangulo(0, TILE - 6, TILE, 6, borda)
        if mascara & 8:
            canvas.retangulo(0, 0, 6, TILE, borda)
        frames.append(canvas)
    return Canvas.folha(frames)


def _arvore(variacao: int) -> Canvas:
    canvas = Canvas(TILE, TILE)
    canvas.elipse(16, 53, 32, 8, SOMBRA)
    canvas.retangulo(29, 30, 7, 25, MADEIRA_ESCURA, CONTORNO)
    for dx, dy, raio, cor in (
        (-8, -3, 11, VERDE_ESCURO),
        (8, -4, 11, VERDE),
        (0, -12, 13, VERDE_CLARO),
        (-3, 3, 10, VERDE),
    ):
        canvas.circulo(32 + dx, 25 + dy, raio, cor, CONTORNO_SUAVE)
    if variacao == 1:
        canvas.circulo(20, 22, 5, VERDE_CLARO)
    elif variacao == 2:
        canvas.circulo(44, 28, 5, VERDE_ESCURO)
    return canvas


def arvore_adulta(variacao: int = 0) -> Canvas:
    return _arvore(variacao % 3)


def arvore_toco() -> Canvas:
    canvas = Canvas(TILE, TILE)
    canvas.elipse(17, 54, 30, 7, SOMBRA)
    canvas.elipse(23, 46, 18, 12, MADEIRA, CONTORNO)
    canvas.elipse(27, 46, 10, 6, MADEIRA_ESCURA)
    return canvas


def _rocha(variacao: int) -> Canvas:
    canvas = Canvas(TILE, TILE)
    canvas.elipse(11, 51, 42, 9, SOMBRA)
    canvas.elipse(14, 30, 36, 26, PEDRA, CONTORNO)
    canvas.elipse(18, 26, 20, 16, PEDRA_CLARA)
    canvas.poligono([(12, 42), (20, 26), (35, 22), (50, 37), (43, 49), (22, 50)], PEDRA, CONTORNO)
    if variacao:
        canvas.poligono([(38, 30), (52, 28), (46, 44)], PEDRA_CLARA, CONTORNO_SUAVE)
    return canvas


def rocha_adulta(variacao: int = 0) -> Canvas:
    return _rocha(variacao % 2)


def rocha_esgotada() -> Canvas:
    canvas = Canvas(TILE, TILE)
    canvas.elipse(18, 54, 28, 7, SOMBRA)
    canvas.poligono([(18, 48), (24, 40), (35, 42), (41, 49), (31, 53), (20, 52)], PEDRA_ESCURA, CONTORNO)
    canvas.circulo(28, 48, 2, PEDRA_CLARA)
    return canvas


def acampamento_inimigo() -> Canvas:
    canvas = Canvas(128, 128)
    canvas.elipse(12, 116, 104, 18, SOMBRA)
    canvas.poligono([(18, 106), (48, 54), (78, 106)], VERMELHO_ESCURO, CONTORNO)
    canvas.poligono([(58, 106), (84, 64), (110, 106)], (94, 58, 48, 255), CONTORNO)
    canvas.retangulo(72, 78, 24, 10, (28, 24, 22, 255), CONTORNO)
    canvas.circulo(64, 110, 7, MADEIRA, CONTORNO)
    canvas.circulo(64, 110, 3, OURO)
    for x in (20, 102):
        canvas.retangulo(x, 82, 3, 30, MADEIRA_ESCURA)
        canvas.poligono([(x + 3, 84), (x + 17, 88), (x + 3, 92)], VERMELHO, CONTORNO)
    return canvas


def barra_recurso(preenchimento: bool) -> Canvas:
    canvas = Canvas(32, 4)
    if preenchimento:
        canvas.retangulo(0, 0, 32, 4, VERDE_CLARO)
        canvas.retangulo(0, 0, 32, 1, (188, 230, 150, 255))
    else:
        canvas.retangulo(0, 0, 32, 4, (30, 32, 38, 255), CONTORNO)
    return canvas


def tronco_carregado() -> Canvas:
    canvas = Canvas(16, 16)
    canvas.retangulo(1, 6, 14, 5, MADEIRA, CONTORNO)
    canvas.circulo(2, 8, 2, MADEIRA_ESCURA, CONTORNO)
    canvas.circulo(13, 8, 2, MADEIRA_ESCURA, CONTORNO)
    return canvas


def anel_selecao(tamanho: int, raio: int) -> Canvas:
    canvas = Canvas(tamanho, tamanho)
    canvas.circulo(tamanho // 2, tamanho // 2, raio, contorno=OURO, largura_contorno=2)
    return canvas


def caixa_selecao() -> Canvas:
    canvas = Canvas(32, 32)
    canvas.retangulo(0, 0, 32, 32, (240, 204, 90, 40), OURO)
    for x in range(4, 28, 6):
        canvas.pixel(x, 0, (255, 236, 160, 255))
        canvas.pixel(x, 31, (255, 236, 160, 255))
    return canvas


def marcador_ordem() -> Canvas:
    canvas = Canvas(32, 32)
    canvas.circulo(16, 16, 11, contorno=OURO, largura_contorno=2)
    canvas.linha(3, 16, 29, 16, OURO)
    canvas.linha(16, 3, 16, 29, OURO)
    return canvas


def texto_recurso() -> Canvas:
    canvas = Canvas(32, 16)
    canvas.retangulo(1, 7, 10, 2, OURO)
    canvas.retangulo(5, 3, 2, 10, OURO)
    canvas.circulo(23, 8, 5, OURO, CONTORNO)
    return canvas


def grupo_inimigo(cor) -> Canvas:
    canvas = Canvas(64, 64)
    for indice, x in enumerate((16, 32, 48)):
        canvas.elipse(x - 7, 50, 14, 4, SOMBRA)
        canvas.circulo(x, 42, 7, cor, CONTORNO)
        canvas.poligono([(x - 8, 41), (x, 24 - indice * 2), (x + 8, 41)], cor, CONTORNO)
        canvas.circulo(x, 27 - indice * 2, 4, (214, 166, 124, 255), CONTORNO)
    return canvas


def fantasma_posicionamento(valido: bool) -> Canvas:
    canvas = Canvas(64, 64)
    if valido:
        canvas.retangulo(0, 0, 64, 64, (70, 200, 110, 80), (100, 230, 140, 255))
    else:
        canvas.retangulo(0, 0, 64, 64, (220, 80, 80, 90), (240, 110, 110, 255))
    return canvas


def raio_construcao(tamanho: int = 512) -> Canvas:
    canvas = Canvas(tamanho, tamanho)
    canvas.circulo(
        tamanho // 2,
        tamanho // 2,
        tamanho // 2 - 2,
        contorno=(230, 220, 150, 90),
        largura_contorno=2,
    )
    return canvas


def barra_hp_estrutura(preenchimento: bool) -> Canvas:
    canvas = Canvas(32, 4)
    if preenchimento:
        canvas.retangulo(0, 0, 32, 4, (150, 190, 230, 255))
        canvas.retangulo(0, 0, 32, 1, (206, 226, 246, 255))
    else:
        canvas.retangulo(0, 0, 32, 4, (30, 32, 38, 255), CONTORNO)
    return canvas
