"""Geração procedural das estruturas medievais."""

from __future__ import annotations

from .canvas import Canvas
from .paleta import (
    AGUA,
    CONTORNO,
    CONTORNO_SUAVE,
    FOGO,
    FOGO_CLARO,
    FUMACA,
    FERRO,
    FERRO_CLARO,
    GRAMA,
    GRAMA_CLARA,
    GRAMA_ESCURA,
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
    REBOCO_ESCURO,
    SOMBRA,
    TECIDO,
    TECIDO_CLARO,
    TELHA,
    TELHA_CLARA,
    TELHA_ESCURA,
    TERRA,
    TERRA_ESCURA,
    VERDE,
    VERDE_CLARO,
    VERDE_ESCURO,
    VERMELHO,
    VERMELHO_ESCURO,
    VIDRO,
)

TAMANHOS = {
    "castelo": (256, 288),
    "casas": (64, 64),
    "madeireira": (128, 64),
    "mina": (128, 64),
    "fazenda": (192, 128),
    "mercado": (128, 64),
    "ferraria": (64, 64),
    "quartel": (128, 128),
    "celeiro": (128, 64),
    "muralha": (64, 64),
    "barricada": (64, 64),
    "posto": (128, 96),
    "arquearia": (128, 64),
    "torre_magia": (64, 96),
    "santuario": (128, 64),
}

NOMES = {
    "castelo": "Castelo",
    "casas": "Casas",
    "madeireira": "Madeireira",
    "mina": "Mina",
    "fazenda": "Fazenda",
    "mercado": "Mercado",
    "ferraria": "Ferraria",
    "quartel": "Quartel",
    "celeiro": "Celeiro",
    "muralha": "Muralha",
    "barricada": "Barricada",
    "posto": "Posto Avançado",
    "arquearia": "Arquearia",
    "torre_magia": "Torre de Magia",
    "santuario": "Santuário",
}


def _sombra(canvas: Canvas, x: int, y: int, largura: int, altura: int) -> None:
    canvas.elipse(x, y, largura, altura, SOMBRA)


def _telhado(
    canvas: Canvas,
    x: int,
    y: int,
    largura: int,
    altura: int,
    cor_telha=TELHA,
    cor_escura=TELHA_ESCURA,
    cor_clara=TELHA_CLARA,
    linhas: int = 4,
) -> None:
    topo_inset = max(2, largura // 5)
    pontos = [
        (x + topo_inset, y),
        (x + largura - topo_inset, y),
        (x + largura, y + altura),
        (x, y + altura),
    ]
    canvas.poligono(pontos, cor_telha, CONTORNO)
    for indice in range(1, linhas + 1):
        fracao = indice / (linhas + 1)
        yy = int(y + altura * fracao)
        left = int(x + (largura * (1 - fracao)) * 0.5)
        right = int(x + largura - (largura * (1 - fracao)) * 0.5)
        canvas.linha(left + 1, yy, right - 1, yy, cor_escura)
        if indice % 2 == 0:
            canvas.linha(left + 2, yy - 1, right - 2, yy - 1, cor_clara)
    canvas.polilinha(
        [(x, y + altura), (x + topo_inset, y), (x + largura - topo_inset, y), (x + largura, y + altura)],
        CONTORNO,
    )
    canvas.linha(x + topo_inset, y, x + largura - topo_inset, y, cor_escura)


def _janela(canvas: Canvas, x: int, y: int, largura: int, altura: int) -> None:
    canvas.retangulo(x, y, largura, altura, VIDRO, MADEIRA_ESCURA)
    if largura >= 4:
        canvas.linha(x + largura // 2, y, x + largura // 2, y + altura - 1, MADEIRA_ESCURA)
    if altura >= 4:
        canvas.linha(x, y + altura // 2, x + largura - 1, y + altura // 2, MADEIRA_ESCURA)


def _porta(canvas: Canvas, x: int, y: int, largura: int, altura: int) -> None:
    canvas.retangulo(x, y, largura, altura, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(x + 1, y + 1, largura - 2, 1, MADEIRA)
    if largura >= 5:
        canvas.pixel(x + largura - 2, y + altura // 2, OURO)


def _parede_enxaimel(
    canvas: Canvas,
    x: int,
    y: int,
    largura: int,
    altura: int,
    janelas: int = 2,
    porta: bool = True,
    cor_parede=REBOCO,
) -> None:
    if largura <= 4 or altura <= 4:
        return
    canvas.retangulo(x, y, largura, altura, cor_parede, CONTORNO)
    base = max(2, altura // 5)
    canvas.retangulo(x, y + altura - base, largura, base, PEDRA, CONTORNO_SUAVE)
    for bx in range(x + 1, x + largura - 1, max(4, largura // 6)):
        canvas.linha(bx, y + altura - base + 1, bx, y + altura - 2, PEDRA_ESCURA)
    canvas.linha(x + 1, y + altura - base, x + largura - 2, y + altura - base, PEDRA_ESCURA)

    viga = max(1, altura // 12)
    canvas.retangulo(x, y, largura, viga, MADEIRA)
    canvas.retangulo(x, y + altura - base - viga, largura, viga, MADEIRA)
    for bx in (x, x + largura // 3, x + (largura * 2) // 3, x + largura - 1):
        canvas.retangulo(bx, y, viga, altura - base, MADEIRA)
    if largura > 40:
        canvas.linha(x + viga, y + altura - base - viga - 1, x + largura // 3, y + viga + 1, MADEIRA)
        canvas.linha(x + largura - viga - 1, y + altura - base - viga - 1, x + (largura * 2) // 3, y + viga + 1, MADEIRA)

    topo_janela = y + max(3, altura // 4)
    tam_janela = max(3, min(6, altura // 5))
    if janelas >= 1:
        _janela(canvas, x + max(2, largura // 10), topo_janela, tam_janela, tam_janela)
    if janelas >= 2:
        _janela(canvas, x + largura - tam_janela - max(2, largura // 10), topo_janela, tam_janela, tam_janela)
    if porta:
        largura_porta = max(4, min(10, largura // 4))
        altura_porta = max(5, altura // 2)
        _porta(
            canvas,
            x + (largura - largura_porta) // 2,
            y + altura - altura_porta - 1,
            largura_porta,
            altura_porta,
        )


def _casa_base(
    largura: int,
    altura: int,
    nivel: int,
    cor_telha=TELHA,
    cor_parede=REBOCO,
    janelas: int = 2,
    porta: bool = True,
) -> Canvas:
    canvas = Canvas(largura, altura)
    margem = max(2, largura // 20)
    chao = altura - max(2, altura // 32)
    _sombra(canvas, margem, chao - max(2, altura // 20), largura - margem * 2, max(3, altura // 12))
    esquerda = max(3, largura // 10)
    direita = largura - esquerda
    parede_topo = int(altura * (0.47 - 0.01 * (nivel - 1)))
    parede_altura = chao - parede_topo
    topo_telhado = int(altura * (0.18 - 0.02 * (nivel - 1)))
    _telhado(
        canvas,
        max(1, esquerda - max(2, largura // 18)),
        topo_telhado,
        min(largura - 2, (direita - esquerda) + max(2, largura // 9)),
        parede_topo - topo_telhado,
        cor_telha=cor_telha,
        linhas=max(2, altura // 16),
    )
    _parede_enxaimel(
        canvas,
        esquerda,
        parede_topo,
        direita - esquerda,
        parede_altura,
        janelas=janelas,
        porta=porta,
        cor_parede=cor_parede,
    )
    if nivel >= 2 and largura >= 48:
        chaminé_x = min(largura - 12, int(largura * 0.72))
        canvas.retangulo(chaminé_x, topo_telhado - 2, max(3, largura // 18), max(5, altura // 8), PEDRA, CONTORNO)
        canvas.retangulo(chaminé_x - 1, topo_telhado - 3, max(5, largura // 12), 2, PEDRA_ESCURA, CONTORNO)
    return canvas


def _casas(nivel: int) -> Canvas:
    return _casa_base(64, 64, nivel, cor_telha=TELHA, janelas=2)


def _madeireira(nivel: int) -> Canvas:
    canvas = _casa_base(128, 64, nivel, cor_telha=TELHA_CLARA, janelas=1, porta=True)
    _sombra(canvas, 62, 52, 58, 9)
    for indice in range(3 + nivel):
        y = 48 - indice * 4
        canvas.elipse(74, y, 18, 6, MADEIRA_CLARA, MADEIRA_ESCURA)
        canvas.circulo(92, y + 3, 3, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(104, 22, 4, 30, MADEIRA)
    canvas.poligono([(104, 24), (120, 30), (120, 34), (104, 28)], FERRO_CLARO, CONTORNO)
    return canvas


def _mina(nivel: int) -> Canvas:
    canvas = Canvas(128, 64)
    _sombra(canvas, 8, 52, 112, 10)
    canvas.poligono([(10, 55), (22, 22), (58, 12), (98, 20), (118, 55)], PEDRA_ESCURA, CONTORNO)
    canvas.poligono([(24, 55), (34, 30), (56, 24), (76, 30), (88, 55)], PEDRA, CONTORNO)
    canvas.retangulo(44, 34, 32, 21, (26, 22, 20, 255), CONTORNO)
    for x in (41, 73):
        canvas.retangulo(x, 28, 5, 27, MADEIRA, CONTORNO)
    canvas.retangulo(41, 28, 37, 4, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(84, 47, 22, 6, MADEIRA_ESCURA, CONTORNO)
    canvas.circulo(88, 56, 4, FERRO, CONTORNO)
    canvas.circulo(102, 56, 4, FERRO, CONTORNO)
    if nivel >= 2:
        canvas.circulo(60, 48, 3, MAGIA, MAGIA_CLARA)
    return canvas


def _fazenda(nivel: int) -> Canvas:
    canvas = Canvas(192, 128)
    canvas.retangulo(0, 78, 192, 46, TERRA, TERRA_ESCURA)
    for linha in range(4):
        y = 84 + linha * 10
        canvas.linha(4, y, 140, y, TERRA_ESCURA)
        for x in range(8 + linha % 2 * 4, 136, 12):
            canvas.linha(x, y - 2, x, y + 3, VERDE_ESCURO)
            canvas.circulo(x, y - 3, 2, PALHA if nivel >= 2 else VERDE_CLARO)
    casa = _casa_base(74, 68, nivel, cor_telha=TELHA_CLARA, janelas=1)
    canvas.colar(casa, 112, 12)
    for x in range(4, 188, 18):
        canvas.retangulo(x, 64, 2, 12, MADEIRA, CONTORNO)
    canvas.linha(4, 68, 188, 68, MADEIRA)
    if nivel >= 3:
        canvas.retangulo(152, 10, 3, 22, MADEIRA_ESCURA)
        canvas.poligono([(155, 12), (172, 18), (155, 24)], VERMELHO, CONTORNO)
    return canvas


def _mercado(nivel: int) -> Canvas:
    canvas = Canvas(128, 64)
    _sombra(canvas, 2, 54, 124, 8)
    for indice, x in enumerate((8, 48, 88)):
        cor = (TECIDO, VERMELHO, VERDE)[indice % 3]
        canvas.retangulo(x, 32, 32, 24, MADEIRA, CONTORNO)
        canvas.poligono([(x - 2, 32), (x + 16, 20), (x + 34, 32)], cor, CONTORNO)
        canvas.retangulo(x + 2, 38, 28, 10, REBOCO_ESCURO, CONTORNO)
        for px in range(x + 4, x + 28, 6):
            canvas.circulo(px, 36, 2, OURO if indice == 1 else VERDE_CLARO)
        canvas.retangulo(x + 2, 48, 3, 12, MADEIRA_ESCURA)
        canvas.retangulo(x + 27, 48, 3, 12, MADEIRA_ESCURA)
    return canvas


def _ferraria(nivel: int) -> Canvas:
    canvas = Canvas(64, 64)
    _sombra(canvas, 6, 52, 52, 8)
    canvas.retangulo(10, 24, 44, 30, PEDRA, CONTORNO)
    canvas.retangulo(14, 28, 36, 22, PEDRA_CLARA, CONTORNO)
    canvas.poligono([(6, 25), (32, 10), (58, 25)], TELHA, CONTORNO)
    canvas.retangulo(28, 34, 10, 18, (24, 20, 18, 255), CONTORNO)
    canvas.retangulo(30, 40, 6, 4, FOGO, FOGO_CLARO)
    canvas.retangulo(44, 8, 8, 18, PEDRA_ESCURA, CONTORNO)
    if nivel >= 2:
        canvas.retangulo(8, 44, 14, 8, FERRO, CONTORNO)
        canvas.linha(10, 46, 20, 50, FERRO_CLARO)
    if nivel >= 3:
        canvas.circulo(18, 49, 3, FOGO_CLARO)
    return canvas


def _quartel(nivel: int) -> Canvas:
    canvas = Canvas(128, 128)
    _sombra(canvas, 8, 112, 112, 12)
    canvas.retangulo(18, 54, 92, 56, PEDRA, CONTORNO)
    canvas.retangulo(24, 60, 80, 44, REBOCO, CONTORNO)
    canvas.poligono([(10, 56), (64, 18), (118, 56)], TELHA, CONTORNO)
    _porta(canvas, 54, 78, 20, 32)
    _janela(canvas, 34, 70, 10, 10)
    _janela(canvas, 84, 70, 10, 10)
    for x in (18, 100):
        canvas.retangulo(x, 34, 4, 58, MADEIRA_ESCURA)
        canvas.poligono([(x + 4, 36), (x + 18, 42), (x + 4, 50)], VERMELHO, CONTORNO)
    if nivel >= 2:
        canvas.retangulo(24, 112, 80, 4, PEDRA_ESCURA)
        canvas.circulo(26, 116, 5, PALHA, CONTORNO)
        canvas.linha(26, 116, 26, 106, MADEIRA_ESCURA)
    if nivel >= 3:
        canvas.retangulo(56, 8, 2, 18, MADEIRA_ESCURA)
        canvas.poligono([(58, 10), (76, 16), (58, 22)], OURO, CONTORNO)
    return canvas


def _celeiro(nivel: int) -> Canvas:
    canvas = Canvas(128, 64)
    _sombra(canvas, 6, 52, 116, 9)
    canvas.retangulo(14, 26, 100, 28, MADEIRA, CONTORNO)
    for x in range(18, 112, 10):
        canvas.retangulo(x, 28, 3, 25, MADEIRA_ESCURA)
    canvas.poligono([(8, 28), (64, 6), (120, 28)], TELHA_ESCURA, CONTORNO)
    canvas.retangulo(40, 34, 48, 20, MADEIRA_ESCURA, CONTORNO)
    canvas.linha(64, 34, 64, 53, MADEIRA_CLARA)
    for x in (24, 96):
        canvas.circulo(x, 52, 4, PALHA, CONTORNO)
    if nivel >= 2:
        canvas.circulo(64, 32, 5, PALHA, CONTORNO)
    if nivel >= 3:
        canvas.retangulo(66, 2, 2, 12, MADEIRA_ESCURA)
        canvas.poligono([(68, 4), (78, 8), (68, 12)], VERDE, CONTORNO)
    return canvas


def _muralha(nivel: int) -> Canvas:
    canvas = Canvas(64, 64)
    _sombra(canvas, 2, 54, 60, 8)
    canvas.retangulo(4, 22, 56, 34, PEDRA, CONTORNO)
    for x in range(6, 58, 10):
        canvas.retangulo(x, 16, 7, 10, PEDRA_CLARA, CONTORNO)
    for y in range(28, 50, 8):
        for x in range(8, 56, 12):
            canvas.linha(x, y, min(58, x + 8), y, PEDRA_ESCURA)
    if nivel >= 2:
        canvas.retangulo(26, 30, 12, 18, (30, 26, 24, 255), CONTORNO)
    if nivel >= 3:
        canvas.circulo(48, 26, 4, VERMELHO, CONTORNO)
        canvas.poligono([(52, 26), (62, 22), (62, 30)], VERMELHO_ESCURO, CONTORNO)
    return canvas


def _barricada(nivel: int) -> Canvas:
    canvas = Canvas(64, 64)
    _sombra(canvas, 4, 54, 56, 7)
    for x in (8, 22, 36, 50):
        canvas.retangulo(x, 20, 5, 34, MADEIRA)
        canvas.poligono([(x, 22), (x + 2, 8), (x + 5, 22)], MADEIRA_CLARA, CONTORNO)
        canvas.retangulo(x, 20, 5, 34, CONTORNO, contorno=None, largura_contorno=1)
        canvas.retangulo(x + 1, 22, 3, 30, None, None)
    canvas.retangulo(4, 38, 56, 5, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(4, 48, 56, 4, MADEIRA_ESCURA, CONTORNO)
    if nivel >= 2:
        canvas.linha(4, 38, 60, 52, MADEIRA_CLARA)
    if nivel >= 3:
        canvas.circulo(32, 18, 5, FERRO, CONTORNO)
    return canvas


def _posto(nivel: int) -> Canvas:
    canvas = Canvas(128, 96)
    _sombra(canvas, 20, 82, 88, 10)
    canvas.retangulo(30, 46, 68, 34, PEDRA, CONTORNO)
    canvas.retangulo(36, 52, 56, 26, MADEIRA, CONTORNO)
    for x in (42, 64, 86):
        canvas.retangulo(x, 34, 5, 46, MADEIRA_ESCURA, CONTORNO)
    canvas.poligono([(24, 36), (64, 12), (104, 36)], TELHA_ESCURA, CONTORNO)
    canvas.retangulo(58, 58, 12, 22, (28, 24, 22, 255), CONTORNO)
    canvas.retangulo(64, 6, 2, 22, MADEIRA_ESCURA)
    canvas.poligono([(66, 8), (94, 14), (66, 22)], VERMELHO, CONTORNO)
    canvas.retangulo(100, 42, 4, 40, MADEIRA_ESCURA)
    if nivel >= 2:
        _janela(canvas, 42, 58, 8, 8)
    if nivel >= 3:
        canvas.circulo(64, 30, 5, OURO, CONTORNO)
    return canvas


def _arquearia(nivel: int) -> Canvas:
    canvas = Canvas(128, 64)
    _sombra(canvas, 4, 54, 120, 8)
    canvas.retangulo(8, 44, 112, 10, TERRA, TERRA_ESCURA)
    for x in (26, 64, 102):
        canvas.circulo(x, 30, 12, REBOCO, CONTORNO)
        canvas.circulo(x, 30, 8, VERMELHO, CONTORNO_SUAVE)
        canvas.circulo(x, 30, 3, OURO, CONTORNO_SUAVE)
        canvas.retangulo(x - 2, 42, 4, 10, MADEIRA_ESCURA)
    for x in (10, 118):
        canvas.retangulo(x, 18, 4, 32, MADEIRA_ESCURA)
    canvas.linha(12, 32, 118, 32, MADEIRA)
    if nivel >= 2:
        canvas.poligono([(14, 12), (44, 18), (14, 24)], VERDE, CONTORNO)
    if nivel >= 3:
        canvas.poligono([(84, 12), (114, 18), (84, 24)], VERDE, CONTORNO)
    return canvas


def _torre_magia(nivel: int) -> Canvas:
    canvas = Canvas(64, 96)
    _sombra(canvas, 8, 84, 48, 9)
    canvas.retangulo(18, 40, 28, 44, PEDRA, CONTORNO)
    canvas.retangulo(22, 44, 20, 36, PEDRA_CLARA, CONTORNO)
    for y in (54, 66, 78):
        canvas.linha(22, y, 41, y, PEDRA_ESCURA)
    canvas.poligono([(12, 42), (32, 12), (52, 42)], TELHA_ESCURA, CONTORNO)
    canvas.circulo(32, 10, 8, MAGIA, CONTORNO)
    canvas.circulo(32, 10, 4, MAGIA_CLARA)
    _porta(canvas, 28, 68, 8, 16)
    if nivel >= 2:
        canvas.circulo(32, 52, 3, MAGIA_CLARA)
        canvas.circulo(32, 64, 3, MAGIA_CLARA)
    if nivel >= 3:
        canvas.linha(32, 2, 32, 6, MAGIA_CLARA)
        canvas.circulo(32, 1, 2, MAGIA_CLARA)
    return canvas


def _santuario(nivel: int) -> Canvas:
    canvas = Canvas(128, 64)
    _sombra(canvas, 4, 54, 120, 8)
    canvas.retangulo(18, 20, 92, 34, REBOCO, CONTORNO)
    for x in (28, 52, 76, 100):
        canvas.retangulo(x, 16, 6, 38, PEDRA_CLARA, CONTORNO)
    canvas.poligono([(10, 20), (64, 4), (118, 20)], TELHA, CONTORNO)
    _porta(canvas, 56, 32, 16, 22)
    _janela(canvas, 34, 30, 8, 8)
    _janela(canvas, 86, 30, 8, 8)
    canvas.retangulo(56, 12, 16, 2, OURO)
    if nivel >= 2:
        canvas.circulo(64, 13, 4, MAGIA_CLARA, CONTORNO)
    if nivel >= 3:
        canvas.linha(14, 10, 14, 22, MADEIRA_ESCURA)
        canvas.poligono([(14, 10), (26, 14), (14, 18)], MAGIA, CONTORNO)
        canvas.linha(114, 10, 114, 22, MADEIRA_ESCURA)
        canvas.poligono([(114, 10), (102, 14), (114, 18)], MAGIA, CONTORNO)
    return canvas


def _castelo(nivel: int) -> Canvas:
    canvas = Canvas(256, 288)
    _sombra(canvas, 20, 262, 216, 22)
    if nivel == 1:
        casa = _casa_base(180, 190, 1, cor_telha=PALHA, cor_parede=MADEIRA_CLARA, janelas=2)
        canvas.colar(casa, 38, 78)
        for x in range(20, 236, 20):
            canvas.retangulo(x, 244, 6, 20, MADEIRA_ESCURA, CONTORNO)
        return canvas
    largura = 160 + nivel * 12
    esquerda = (256 - largura) // 2
    altura_muro = 80 + nivel * 10
    topo_muro = 250 - altura_muro
    canvas.retangulo(esquerda, topo_muro, largura, altura_muro, PEDRA, CONTORNO)
    for x in range(esquerda + 6, esquerda + largura, 18):
        canvas.retangulo(x, topo_muro - 12, 10, 14, PEDRA_CLARA, CONTORNO)
    torre_l = esquerda - 10
    torre_r = esquerda + largura - 28
    for torre_x in (torre_l, torre_r):
        canvas.retangulo(torre_x, topo_muro - 36, 38, altura_muro + 36, PEDRA_ESCURA, CONTORNO)
        canvas.poligono(
            [(torre_x - 4, topo_muro - 36), (torre_x + 19, topo_muro - 60), (torre_x + 42, topo_muro - 36)],
            TELHA_ESCURA,
            CONTORNO,
        )
    keep_largura = largura - 48
    keep_esquerda = (256 - keep_largura) // 2
    keep_altura = 100 + nivel * 12
    keep_topo = topo_muro - 46
    canvas.retangulo(keep_esquerda, keep_topo, keep_largura, keep_altura, PEDRA, CONTORNO)
    canvas.retangulo(keep_esquerda + 8, keep_topo + 8, keep_largura - 16, keep_altura - 16, REBOCO_ESCURO, CONTORNO)
    canvas.poligono(
        [(keep_esquerda - 6, keep_topo), (128, keep_topo - 52), (keep_esquerda + keep_largura + 6, keep_topo)],
        TELHA,
        CONTORNO,
    )
    _porta(canvas, 116, 244, 24, 38)
    for x in (keep_esquerda + 20, keep_esquerda + keep_largura - 38):
        _janela(canvas, x, keep_topo + 20, 10, 14)
    canvas.retangulo(124, keep_topo - 70, 4, 66, MADEIRA_ESCURA)
    canvas.poligono([(128, keep_topo - 68), (174, keep_topo - 58), (128, keep_topo - 44)], VERMELHO, CONTORNO)
    if nivel >= 3:
        for x in range(esquerda + 10, esquerda + largura - 10, 34):
            canvas.retangulo(x, topo_muro + 12, 8, 10, (34, 30, 28, 255), CONTORNO)
    if nivel >= 4:
        canvas.retangulo(28, 238, 12, 24, PEDRA_ESCURA, CONTORNO)
        canvas.retangulo(216, 238, 12, 24, PEDRA_ESCURA, CONTORNO)
    if nivel >= 5:
        canvas.circulo(128, keep_topo - 76, 10, OURO, CONTORNO)
        canvas.circulo(128, keep_topo - 76, 5, OURO_ESCURO)
    return canvas


def gerar_estrutura(tipo: str, nivel: int) -> Canvas:
    if tipo == "castelo":
        return _castelo(nivel)
    if tipo == "casas":
        return _casas(nivel)
    if tipo == "madeireira":
        return _madeireira(nivel)
    if tipo == "mina":
        return _mina(nivel)
    if tipo == "fazenda":
        return _fazenda(nivel)
    if tipo == "mercado":
        return _mercado(nivel)
    if tipo == "ferraria":
        return _ferraria(nivel)
    if tipo == "quartel":
        return _quartel(nivel)
    if tipo == "celeiro":
        return _celeiro(nivel)
    if tipo == "muralha":
        return _muralha(nivel)
    if tipo == "barricada":
        return _barricada(nivel)
    if tipo == "posto":
        return _posto(nivel)
    if tipo == "arquearia":
        return _arquearia(nivel)
    if tipo == "torre_magia":
        return _torre_magia(nivel)
    if tipo == "santuario":
        return _santuario(nivel)
    raise ValueError(f"Estrutura desconhecida: {tipo}")


def gerar_icone(tipo: str, nivel: int = 1) -> Canvas:
    return gerar_estrutura(tipo, nivel).ajustar_em(48, 48)


def gerar_construcao(frame: int) -> Canvas:
    canvas = Canvas(64, 64)
    progresso = [0.2, 0.45, 0.7, 1.0][frame % 4]
    altura = int(42 * progresso)
    _sombra(canvas, 6, 54, 52, 7)
    canvas.retangulo(8, 56 - altura, 48, altura, MADEIRA, CONTORNO)
    for x in range(12, 54, 8):
        canvas.linha(x, 56, x, 56 - altura, MADEIRA_ESCURA)
    canvas.linha(8, 56 - altura, 56, 56 - altura, MADEIRA_ESCURA)
    if progresso >= 0.45:
        canvas.poligono([(4, 56 - altura), (32, 30 - altura // 2), (60, 56 - altura)], TELHA, CONTORNO)
    if progresso >= 0.7:
        canvas.retangulo(26, 46, 12, 10, REBOCO, CONTORNO)
    if frame < 3:
        for i in range(3):
            canvas.circulo(14 + i * 18, 48 - (i % 2) * 4, 3, FUMACA)
    return canvas


def gerar_dano_estrutura() -> Canvas:
    canvas = Canvas(128, 128)
    for _ in range(18):
        x = 10 + (_ * 37) % 108
        y = 20 + (_ * 53) % 96
        canvas.linha(x, y, x + 11, y + 9, CONTORNO)
        canvas.linha(x + 4, y + 3, x + 7, y + 14, CONTORNO_SUAVE)
    for i in range(7):
        canvas.circulo(18 + i * 16, 112, 4 + i % 2, FUMACA)
    return canvas


def gerar_bandeira(frame: int) -> Canvas:
    canvas = Canvas(32, 32)
    canvas.retangulo(4, 2, 2, 28, MADEIRA_ESCURA)
    deslocamento = [0, 1, 2, 1][frame % 4]
    canvas.poligono(
        [
            (6, 4),
            (28 - deslocamento, 7 + deslocamento),
            (24 - deslocamento, 14),
            (28 - deslocamento, 21 - deslocamento),
            (6, 20),
        ],
        VERMELHO,
        CONTORNO,
    )
    canvas.circulo(17, 12, 3, OURO, CONTORNO)
    return canvas
