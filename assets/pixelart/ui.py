"""Ícones, botões, painéis, barras e elementos de interface."""

from __future__ import annotations

from .canvas import Canvas
from .paleta import (
    AGUA_CLARA,
    CONTORNO,
    CONTORNO_SUAVE,
    FERRO,
    FERRO_CLARO,
    FOGO,
    FOGO_CLARO,
    MADEIRA,
    MADEIRA_CLARA,
    MADEIRA_ESCURA,
    MAGIA,
    MAGIA_CLARA,
    OURO,
    OURO_ESCURO,
    PALHA,
    PEDRA,
    PEDRA_CLARA,
    PEDRA_ESCURA,
    PELE,
    REBOCO,
    SOMBRA_MAGICA,
    TECIDO,
    VERDE,
    VERDE_CLARO,
    VERMELHO,
    VERMELHO_ESCURO,
    VIDRO,
)


def _icone_base() -> Canvas:
    return Canvas(32, 32)


def icone_madeira() -> Canvas:
    canvas = _icone_base()
    for i in range(3):
        canvas.retangulo(4, 8 + i * 7, 24, 6, MADEIRA, CONTORNO)
        canvas.circulo(5, 11 + i * 7, 3, MADEIRA_CLARA, CONTORNO)
        canvas.circulo(27, 11 + i * 7, 3, MADEIRA_ESCURA, CONTORNO)
    return canvas


def icone_troncos() -> Canvas:
    canvas = _icone_base()
    canvas.retangulo(4, 11, 24, 10, MADEIRA, CONTORNO)
    canvas.circulo(5, 16, 5, MADEIRA_CLARA, CONTORNO)
    canvas.circulo(27, 16, 5, MADEIRA_ESCURA, CONTORNO)
    canvas.linha(8, 13, 24, 13, MADEIRA_CLARA)
    return canvas


def icone_pedra() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(6, 24), (10, 12), (20, 8), (27, 18), (23, 26), (11, 27)], PEDRA, CONTORNO)
    canvas.poligono([(12, 19), (16, 12), (22, 14), (20, 22)], PEDRA_CLARA)
    return canvas


def icone_ferro() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(6, 22), (10, 25), (26, 25), (22, 22)], FERRO, CONTORNO)
    canvas.poligono([(6, 18), (10, 21), (26, 21), (22, 18)], FERRO_CLARO, CONTORNO)
    canvas.poligono([(8, 14), (12, 17), (24, 17), (20, 14)], FERRO, CONTORNO)
    return canvas


def icone_ouro() -> Canvas:
    canvas = _icone_base()
    for x, y in ((10, 20), (16, 18), (22, 20)):
        canvas.circulo(x, y, 6, OURO, CONTORNO)
        canvas.circulo(x - 2, y - 2, 2, FOGO_CLARO)
    return canvas


def icone_dinheiro() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(8, 16), (11, 9), (21, 9), (24, 16), (21, 25), (11, 25)], PALHA, CONTORNO)
    canvas.linha(11, 11, 21, 11, MADEIRA_ESCURA)
    canvas.circulo(16, 18, 4, OURO, CONTORNO)
    canvas.linha(16, 15, 16, 21, OURO_ESCURO)
    return canvas


def icone_alimento() -> Canvas:
    canvas = _icone_base()
    canvas.retangulo(15, 8, 2, 20, VERDE, CONTORNO)
    for y in (12, 17, 22):
        canvas.linha(15, y, 9, y - 4, PALHA, 2)
        canvas.linha(17, y, 23, y - 4, PALHA, 2)
    canvas.circulo(16, 8, 4, PALHA, CONTORNO)
    return canvas


def icone_populacao() -> Canvas:
    canvas = _icone_base()
    canvas.circulo(16, 11, 6, PELE, CONTORNO)
    canvas.retangulo(14, 4, 4, 3, MADEIRA_ESCURA)
    canvas.poligono([(5, 27), (9, 17), (23, 17), (27, 27)], TECIDO, CONTORNO)
    return canvas


def icone_soldados() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(6, 24), (9, 11), (23, 8), (27, 16), (22, 24)], FERRO_CLARO, CONTORNO)
    canvas.retangulo(9, 16, 15, 3, FERRO)
    canvas.linha(12, 12, 12, 20, CONTORNO)
    canvas.linha(20, 10, 20, 22, CONTORNO)
    canvas.linha(24, 4, 10, 28, MADEIRA_ESCURA, 2)
    return canvas


def icone_minerio_arcano() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(9, 25), (13, 10), (18, 17), (22, 7), (26, 24)], MAGIA, CONTORNO)
    canvas.poligono([(13, 18), (15, 13), (18, 18), (16, 22)], MAGIA_CLARA)
    return canvas


def icone_ambar() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(10, 24), (8, 14), (16, 7), (24, 14), (22, 24)], (226, 150, 52, 255), CONTORNO)
    canvas.poligono([(13, 21), (12, 15), (17, 11), (20, 16)], (250, 198, 92, 255))
    return canvas


def icone_cristal_runico() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(16, 4), (25, 15), (20, 27), (11, 22), (7, 14)], (104, 176, 220, 255), CONTORNO)
    canvas.poligono([(16, 8), (20, 15), (16, 23), (12, 17)], (176, 226, 244, 255))
    return canvas


def icone_essencia_sombria() -> Canvas:
    canvas = _icone_base()
    canvas.circulo(16, 17, 9, SOMBRA_MAGICA, CONTORNO)
    canvas.circulo(14, 14, 4, MAGIA, None)
    canvas.circulo(16, 17, 3, (36, 24, 52, 255))
    canvas.circulo(22, 9, 2, MAGIA_CLARA)
    return canvas


ICONES_RECURSO = {
    "madeira": icone_madeira,
    "troncos": icone_troncos,
    "pedra": icone_pedra,
    "ferro": icone_ferro,
    "ouro": icone_ouro,
    "dinheiro": icone_dinheiro,
    "alimento": icone_alimento,
    "populacao": icone_populacao,
    "soldados": icone_soldados,
    "minerio_arcano": icone_minerio_arcano,
    "ambar": icone_ambar,
    "cristal_runico": icone_cristal_runico,
    "essencia_sombria": icone_essencia_sombria,
}


def folha_icones() -> Canvas:
    return Canvas.folha([fabrica() for fabrica in ICONES_RECURSO.values()])


def botao(estilo: str, estado: str) -> Canvas:
    canvas = Canvas(96, 30)
    base = (86, 132, 82, 255) if estilo == "primario" else (82, 72, 62, 255)
    borda = OURO_ESCURO if estilo == "primario" else PEDRA_CLARA
    if estado == "hover":
        base = (104, 156, 96, 255) if estilo == "primario" else (102, 90, 76, 255)
    elif estado == "pressionado":
        base = (62, 102, 62, 255) if estilo == "primario" else (64, 56, 50, 255)
    elif estado == "desabilitado":
        base = (56, 58, 60, 255)
        borda = PEDRA_ESCURA
    canvas.retangulo(0, 0, 96, 30, base, borda)
    canvas.retangulo(3, 3, 90, 24, None, CONTORNO)
    canvas.linha(5, 4, 90, 4, (base[0] + 30, base[1] + 30, base[2] + 30, 255))
    if estado == "pressionado":
        canvas.linha(5, 25, 90, 25, CONTORNO)
    return canvas


def painel_9slice() -> Canvas:
    canvas = Canvas(48, 48, (24, 27, 32, 245))
    canvas.retangulo(0, 0, 48, 48, None, PEDRA_ESCURA)
    canvas.retangulo(3, 3, 42, 42, None, MADEIRA_ESCURA)
    canvas.linha(6, 6, 41, 6, MADEIRA)
    canvas.linha(6, 41, 41, 41, CONTORNO)
    for x in (8, 24, 40):
        canvas.circulo(x, 8, 1, OURO)
        canvas.circulo(x, 40, 1, OURO)
    return canvas


def barra_preenchimento(largura: int, altura: int, cor) -> Canvas:
    canvas = Canvas(largura, altura)
    canvas.retangulo(0, 0, largura, altura, cor)
    canvas.linha(0, 0, largura - 1, 0, (min(255, cor[0] + 40), min(255, cor[1] + 40), min(255, cor[2] + 40), 255))
    canvas.linha(0, altura - 1, largura - 1, altura - 1, (max(0, cor[0] - 36), max(0, cor[1] - 36), max(0, cor[2] - 36), 255))
    return canvas


def barra_fundo(largura: int, altura: int) -> Canvas:
    canvas = Canvas(largura, altura)
    canvas.retangulo(0, 0, largura, altura, (30, 32, 38, 255), CONTORNO)
    return canvas


def alerta_ataque() -> Canvas:
    canvas = _icone_base()
    canvas.linha(6, 26, 26, 6, FERRO_CLARO, 3)
    canvas.linha(6, 6, 26, 26, FERRO_CLARO, 3)
    canvas.retangulo(4, 23, 5, 5, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(23, 23, 5, 5, MADEIRA_ESCURA, CONTORNO)
    return canvas


def alerta_fome() -> Canvas:
    canvas = _icone_base()
    canvas.retangulo(15, 8, 2, 20, VERDE, CONTORNO)
    for y in (12, 17, 22):
        canvas.linha(15, y, 9, y - 4, PALHA, 2)
        canvas.linha(17, y, 23, y - 4, PALHA, 2)
    return canvas


def alerta_aviso() -> Canvas:
    canvas = _icone_base()
    canvas.poligono([(16, 4), (29, 27), (3, 27)], OURO, CONTORNO)
    canvas.retangulo(15, 11, 3, 9, CONTORNO)
    canvas.retangulo(15, 23, 3, 3, CONTORNO)
    return canvas


def _digito(canvas: Canvas, numero: int, x: int, y: int, escala: int = 2) -> None:
    padroes = {
        1: ("010", "110", "010", "010", "111"),
        2: ("111", "001", "111", "100", "111"),
        4: ("101", "101", "111", "001", "001"),
    }
    padrao = padroes[numero]
    for py, linha in enumerate(padrao):
        for px, valor in enumerate(linha):
            if valor == "1":
                canvas.retangulo(x + px * escala, y + py * escala, escala, escala, REBOCO)


def _icone_x(canvas: Canvas, x: int, y: int, escala: int = 2) -> None:
    for i in range(5):
        canvas.retangulo(x + i * escala, y + i * escala, escala, escala, REBOCO)
        canvas.retangulo(x + (4 - i) * escala, y + i * escala, escala, escala, REBOCO)


def controle(velocidade: str) -> Canvas:
    canvas = _icone_base()
    canvas.circulo(16, 16, 14, (30, 34, 40, 240), OURO_ESCURO)
    if velocidade == "pausar":
        canvas.retangulo(10, 8, 4, 16, REBOCO)
        canvas.retangulo(18, 8, 4, 16, REBOCO)
    elif velocidade == "play":
        canvas.poligono([(11, 8), (25, 16), (11, 24)], VERDE_CLARO, CONTORNO)
    else:
        numero = int(velocidade.rstrip("x"))
        _digito(canvas, numero, 7, 10, 2)
        _icone_x(canvas, 17, 10, 2)
    return canvas


def logo() -> Canvas:
    canvas = Canvas(320, 96, (24, 20, 18, 255))
    canvas.retangulo(0, 0, 320, 96, None, OURO_ESCURO)
    canvas.retangulo(6, 6, 308, 84, None, MADEIRA_ESCURA)
    canvas.poligono([(160, 10), (206, 30), (198, 70), (160, 88), (122, 70), (114, 30)], PEDRA, CONTORNO)
    canvas.poligono([(160, 17), (198, 34), (191, 66), (160, 81), (129, 66), (122, 34)], TECIDO, CONTORNO)
    canvas.circulo(160, 46, 13, OURO, CONTORNO)
    canvas.circulo(160, 46, 7, OURO_ESCURO)
    canvas.linha(92, 74, 228, 22, FERRO_CLARO, 3)
    canvas.linha(92, 22, 228, 74, FERRO_CLARO, 3)
    canvas.retangulo(86, 70, 12, 8, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(222, 70, 12, 8, MADEIRA_ESCURA, CONTORNO)
    for x in (52, 252):
        canvas.retangulo(x, 20, 16, 36, VERMELHO, CONTORNO)
        canvas.poligono([(x - 3, 20), (x + 8, 10), (x + 19, 20)], OURO, CONTORNO)
        canvas.circulo(x + 8, 36, 4, OURO, CONTORNO)
    return canvas


def cursor() -> Canvas:
    canvas = Canvas(32, 32)
    canvas.poligono([(4, 4), (9, 24), (14, 17), (21, 27), (26, 23), (19, 14), (27, 10)], REBOCO, CONTORNO)
    canvas.circulo(6, 6, 2, OURO, CONTORNO)
    return canvas


def minimapa_moldura() -> Canvas:
    canvas = Canvas(220, 165, (16, 19, 24, 230))
    canvas.retangulo(0, 0, 220, 165, None, PEDRA_ESCURA)
    canvas.retangulo(4, 4, 212, 157, None, MADEIRA_ESCURA)
    for x in range(20, 200, 24):
        canvas.pixel(x, 8, OURO)
    return canvas


def minimapa_marcador() -> Canvas:
    canvas = Canvas(16, 16)
    canvas.circulo(8, 8, 6, VERMELHO, CONTORNO)
    for dx, dy in ((0, -7), (0, 7), (-7, 0), (7, 0)):
        canvas.circulo(8 + dx, 8 + dy, 2, VERMELHO_ESCURO)
    return canvas


def caixa_selecao() -> Canvas:
    canvas = Canvas(32, 32)
    canvas.retangulo(0, 0, 32, 32, (240, 204, 90, 40), OURO)
    for x in range(3, 29, 7):
        canvas.pixel(x, 1, OURO)
        canvas.pixel(x, 30, OURO)
    return canvas
