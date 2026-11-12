"""Banners de eventos medievais."""

from __future__ import annotations

from .canvas import Canvas
from .paleta import (
    CONTORNO,
    FERRO_CLARO,
    FOGO,
    FOGO_CLARO,
    MADEIRA_ESCURA,
    MAGIA,
    MAGIA_CLARA,
    OURO,
    OURO_ESCURO,
    PALHA,
    PEDRA,
    PEDRA_CLARA,
    SOMBRA_MAGICA,
    VERDE,
    VERDE_CLARO,
    VERMELHO,
    VERMELHO_ESCURO,
)


def _base(cor_fundo, cor_borda) -> Canvas:
    canvas = Canvas(320, 96)
    canvas.retangulo(0, 0, 320, 88, cor_fundo, cor_borda)
    canvas.poligono(
        [(0, 88), (32, 96), (64, 88), (96, 96), (128, 88), (160, 96),
         (192, 88), (224, 96), (256, 88), (288, 96), (320, 88)],
        cor_fundo,
        cor_borda,
    )
    canvas.retangulo(4, 4, 312, 78, None, CONTORNO)
    for x in range(12, 314, 24):
        canvas.circulo(x, 12, 2, OURO)
    return canvas


def ataque() -> Canvas:
    canvas = _base((62, 28, 28, 255), VERMELHO_ESCURO)
    for x0, y0, x1, y1 in ((74, 72, 130, 20), (130, 72, 74, 20)):
        canvas.linha(x0, y0, x1, y1, FERRO_CLARO, 5)
        canvas.retangulo(x0 - 5, y0 - 3, 10, 7, MADEIRA_ESCURA, CONTORNO)
    canvas.circulo(102, 46, 16, (34, 20, 20, 255), CONTORNO)
    canvas.circulo(102, 46, 9, VERMELHO, CONTORNO)
    return canvas


def fome() -> Canvas:
    canvas = _base((62, 48, 28, 255), MADEIRA_ESCURA)
    canvas.retangulo(154, 16, 5, 58, VERDE, CONTORNO)
    for y in (25, 36, 47, 58):
        canvas.linha(156, y, 132, y - 13, PALHA, 4)
        canvas.linha(158, y, 182, y - 13, PALHA, 4)
    canvas.circulo(156, 14, 9, PALHA, CONTORNO)
    canvas.circulo(156, 14, 4, FOGO)
    return canvas


def mercador() -> Canvas:
    canvas = _base((34, 58, 40, 255), VERDE)
    canvas.poligono([(120, 62), (130, 30), (190, 30), (200, 62), (184, 78), (136, 78)], PALHA, CONTORNO)
    canvas.linha(134, 38, 186, 38, MADEIRA_ESCURA, 3)
    canvas.circulo(160, 56, 12, OURO, CONTORNO)
    canvas.circulo(160, 56, 6, OURO_ESCURO)
    canvas.circulo(214, 60, 8, OURO, CONTORNO)
    canvas.circulo(230, 52, 5, OURO, CONTORNO)
    return canvas


def praga() -> Canvas:
    canvas = _base((48, 38, 54, 255), SOMBRA_MAGICA)
    canvas.circulo(160, 38, 22, PEDRA_CLARA, CONTORNO)
    canvas.poligono([(138, 56), (146, 74), (174, 74), (182, 56)], PEDRA_CLARA, CONTORNO)
    canvas.circulo(152, 36, 5, (26, 22, 28, 255))
    canvas.circulo(168, 36, 5, (26, 22, 28, 255))
    canvas.poligono([(160, 42), (156, 48), (164, 48)], (26, 22, 28, 255))
    for x in (144, 152, 160, 168, 176):
        canvas.retangulo(x, 58, 3, 6, PEDRA)
    canvas.circulo(122, 28, 5, MAGIA, MAGIA_CLARA)
    canvas.circulo(198, 26, 4, MAGIA, MAGIA_CLARA)
    return canvas


BANNERS = {
    "ataque": ataque,
    "fome": fome,
    "mercador": mercador,
    "praga": praga,
}


def gerar_banner(nome: str) -> Canvas:
    if nome not in BANNERS:
        raise ValueError(f"Banner desconhecido: {nome}")
    return BANNERS[nome]()
