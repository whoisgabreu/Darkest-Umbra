"""Spritesheets de efeitos visuais."""

from __future__ import annotations

import math

from .canvas import Canvas
from .paleta import (
    CONTORNO,
    FERRO_CLARO,
    FOGO,
    FOGO_CLARO,
    FUMACA,
    MADEIRA_ESCURA,
    OURO,
    PEDRA,
    PEDRA_CLARA,
    SANGUE,
    VERMELHO,
    com_alpha,
)


def _alfa(cor, alpha: int):
    return com_alpha(cor, alpha)


def corte_espada() -> Canvas:
    frames = []
    for i in range(6):
        canvas = Canvas(64, 64)
        inicio = -60 + i * 22
        fim = inicio + 95
        for passo in range(0, 46, 3):
            angulo = math.radians(inicio + passo * 2)
            raio = 14 + passo * 0.55
            x = 32 + math.cos(angulo) * raio
            y = 32 + math.sin(angulo) * raio
            canvas.circulo(int(x), int(y), max(1, 4 - i // 2), _alfa(FERRO_CLARO, 230 - i * 28))
        frames.append(canvas)
    return Canvas.folha(frames)


def flecha() -> Canvas:
    frames = []
    for i in range(4):
        canvas = Canvas(32, 32)
        x = 4 + i * 7
        y = 24 - i * 4
        canvas.linha(x, y, x + 12, y - 4, MADEIRA_ESCURA, 2)
        canvas.poligono([(x + 12, y - 4), (x + 8, y - 6), (x + 8, y)], FERRO_CLARO, CONTORNO)
        canvas.linha(x - 2, y + 1, x + 2, y - 1, VERMELHO)
        frames.append(canvas)
    return Canvas.folha(frames)


def pedra_catapulta() -> Canvas:
    frames = []
    for i in range(4):
        canvas = Canvas(32, 32)
        x = 4 + i * 7
        y = 24 - i * 5
        canvas.circulo(x, y, 4, PEDRA, CONTORNO)
        canvas.circulo(x - 1, y - 1, 2, PEDRA_CLARA)
        canvas.circulo(x - 4, y + 3, 1, FUMACA)
        frames.append(canvas)
    return Canvas.folha(frames)


def fumaca() -> Canvas:
    frames = []
    for i in range(6):
        canvas = Canvas(64, 64)
        for j in range(6):
            x = 20 + (j * 13 + i * 3) % 30
            y = 46 - i * 5 - (j % 3) * 5
            raio = 6 + i * 2 + j % 3
            canvas.circulo(x, y, raio, _alfa(FUMACA, 150 - i * 20))
        frames.append(canvas)
    return Canvas.folha(frames)


def fogo() -> Canvas:
    frames = []
    for i in range(6):
        canvas = Canvas(64, 64)
        for j in range(7):
            x = 18 + j * 5
            y = 52 - ((j + i) % 4) * 3
            altura = 12 + (j * 3 + i * 2) % 15
            cor = FOGO_CLARO if j % 2 else FOGO
            canvas.poligono(
                [(x - 5, y), (x, y - altura), (x + 5, y)],
                _alfa(cor, 210 - i * 12),
            )
        frames.append(canvas)
    return Canvas.folha(frames)


def poeira_construcao() -> Canvas:
    frames = []
    for i in range(6):
        canvas = Canvas(64, 64)
        for j in range(8):
            x = 14 + (j * 11 + i * 2) % 38
            y = 52 - (j % 2) * 8 - i * 2
            canvas.circulo(x, y, 3 + i // 2, _alfa((162, 132, 96, 255), 150 - i * 18))
        frames.append(canvas)
    return Canvas.folha(frames)


def faisca_upgrade() -> Canvas:
    frames = []
    for i in range(6):
        canvas = Canvas(64, 64)
        for j in range(8):
            angulo = j * math.tau / 8 + i * 0.2
            raio = 8 + i * 5
            x = 32 + math.cos(angulo) * raio
            y = 32 + math.sin(angulo) * raio
            canvas.circulo(int(x), int(y), 2, _alfa(OURO, 240 - i * 30))
            canvas.circulo(32, 32, 3 + i, _alfa(OURO, 90 - i * 10))
        frames.append(canvas)
    return Canvas.folha(frames)


def moedas() -> Canvas:
    frames = []
    for i in range(4):
        canvas = Canvas(32, 32)
        x = 8 + i * 5
        y = 24 - (i % 2) * 6
        canvas.circulo(x, y, 4, OURO, CONTORNO)
        canvas.linha(x - 1, y - 2, x + 1, y + 2, OURO)
        canvas.circulo(x + 10, y + 4, 3, OURO, CONTORNO)
        frames.append(canvas)
    return Canvas.folha(frames)


def explosao() -> Canvas:
    frames = []
    for i in range(8):
        canvas = Canvas(64, 64)
        raio = 4 + i * 3
        canvas.circulo(32, 32, raio, _alfa(FOGO, 220 - i * 20))
        canvas.circulo(32, 32, max(2, raio // 2), _alfa(FOGO_CLARO, 255 - i * 24))
        for j in range(6):
            angulo = j * math.tau / 6
            x = 32 + math.cos(angulo) * (raio + 3)
            y = 32 + math.sin(angulo) * (raio + 3)
            canvas.circulo(int(x), int(y), max(1, 4 - i // 2), _alfa(FUMACA, 180 - i * 18))
        frames.append(canvas)
    return Canvas.folha(frames)


def tiro_posto() -> Canvas:
    frames = []
    for i in range(4):
        canvas = Canvas(64, 64)
        fim_x = 18 + i * 12
        canvas.linha(4, 52, fim_x, 20, _alfa((246, 220, 120, 255), 240 - i * 30), 2)
        canvas.circulo(fim_x, 20, 2 + i % 2, (250, 236, 170, 255))
        frames.append(canvas)
    return Canvas.folha(frames)


EFEITOS = {
    "corte_espada": corte_espada,
    "flecha": flecha,
    "pedra_catapulta": pedra_catapulta,
    "fumaca": fumaca,
    "fogo": fogo,
    "poeira_construcao": poeira_construcao,
    "faisca_upgrade": faisca_upgrade,
    "moedas": moedas,
    "explosao": explosao,
    "tiro_posto": tiro_posto,
}


def gerar_efeito(nome: str) -> Canvas:
    if nome not in EFEITOS:
        raise ValueError(f"Efeito desconhecido: {nome}")
    return EFEITOS[nome]()
