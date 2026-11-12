"""Paleta medieval compartilhada pelos assets."""

from __future__ import annotations

Color = tuple[int, int, int, int]

TRANSPARENTE: Color = (0, 0, 0, 0)
CONTORNO: Color = (38, 28, 24, 255)
CONTORNO_SUAVE: Color = (62, 46, 36, 255)

PEDRA: Color = (142, 136, 124, 255)
PEDRA_ESCURA: Color = (100, 96, 88, 255)
PEDRA_CLARA: Color = (178, 172, 158, 255)

MADEIRA: Color = (112, 74, 46, 255)
MADEIRA_ESCURA: Color = (74, 48, 32, 255)
MADEIRA_CLARA: Color = (148, 102, 64, 255)

REBOCO: Color = (222, 206, 174, 255)
REBOCO_ESCURO: Color = (190, 172, 138, 255)

TELHA: Color = (122, 60, 44, 255)
TELHA_ESCURA: Color = (84, 40, 32, 255)
TELHA_CLARA: Color = (154, 82, 58, 255)

FERRO: Color = (70, 72, 78, 255)
FERRO_CLARO: Color = (112, 116, 124, 255)
OURO: Color = (232, 190, 82, 255)
OURO_ESCURO: Color = (174, 128, 48, 255)

VIDRO: Color = (150, 204, 216, 255)
VIDRO_ESCURO: Color = (92, 150, 168, 255)
TECIDO: Color = (92, 118, 164, 255)
TECIDO_CLARO: Color = (130, 160, 206, 255)
VERMELHO: Color = (164, 62, 54, 255)
VERMELHO_ESCURO: Color = (112, 42, 38, 255)
VERDE: Color = (82, 132, 74, 255)
VERDE_ESCURO: Color = (52, 94, 58, 255)
VERDE_CLARO: Color = (118, 166, 92, 255)
PALHA: Color = (198, 166, 96, 255)
PELE: Color = (214, 166, 124, 255)
PELE_ESCURA: Color = (166, 116, 82, 255)
CABELO: Color = (86, 58, 38, 255)
CABELO_CLARO: Color = (134, 94, 54, 255)

GRAMA: Color = (76, 112, 70, 255)
GRAMA_ESCURA: Color = (58, 90, 58, 255)
GRAMA_CLARA: Color = (98, 136, 78, 255)
TERRA: Color = (132, 110, 80, 255)
TERRA_ESCURA: Color = (102, 82, 60, 255)
AGUA: Color = (54, 96, 144, 255)
AGUA_ESCURA: Color = (42, 74, 116, 255)
AGUA_CLARA: Color = (92, 148, 194, 255)

SOMBRA: Color = (18, 22, 26, 110)
FUMACA: Color = (150, 150, 148, 180)
FOGO: Color = (230, 132, 54, 255)
FOGO_CLARO: Color = (250, 206, 96, 255)
SANGUE: Color = (164, 52, 46, 255)
MAGIA: Color = (150, 120, 220, 255)
MAGIA_CLARA: Color = (202, 178, 250, 255)
SOMBRA_MAGICA: Color = (96, 62, 138, 255)

CORES_RECURSO = {
    "madeira": MADEIRA,
    "troncos": MADEIRA_ESCURA,
    "pedra": PEDRA,
    "ferro": FERRO_CLARO,
    "ouro": OURO,
    "dinheiro": (92, 200, 128, 255),
    "alimento": (218, 152, 78, 255),
    "minerio_arcano": (152, 100, 206, 255),
    "ambar": (224, 158, 62, 255),
    "cristal_runico": (104, 176, 220, 255),
    "essencia_sombria": (102, 70, 140, 255),
}


def com_alpha(cor: Color, alpha: int) -> Color:
    return (cor[0], cor[1], cor[2], max(0, min(255, alpha)))


def clarear(cor: Color, valor: int = 24) -> Color:
    return (
        min(255, cor[0] + valor),
        min(255, cor[1] + valor),
        min(255, cor[2] + valor),
        cor[3],
    )


def escurecer(cor: Color, valor: int = 24) -> Color:
    return (
        max(0, cor[0] - valor),
        max(0, cor[1] - valor),
        max(0, cor[2] - valor),
        cor[3],
    )
