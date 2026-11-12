"""Geração procedural de personagens, tropas, inimigos e caravana."""

from __future__ import annotations

from PIL import Image

from .canvas import Canvas
from .paleta import (
    CABELO,
    CABELO_CLARO,
    CONTORNO,
    CONTORNO_SUAVE,
    FERRO,
    FERRO_CLARO,
    MAGIA,
    MAGIA_CLARA,
    MADEIRA,
    MADEIRA_CLARA,
    MADEIRA_ESCURA,
    OURO,
    OURO_ESCURO,
    PALHA,
    PEDRA,
    PELE,
    PELE_ESCURA,
    REBOCO,
    SOMBRA_MAGICA,
    TECIDO,
    TELHA_ESCURA,
    TECIDO_CLARO,
    VERDE,
    VERDE_CLARO,
    VERDE_ESCURO,
    VERMELHO,
    VERMELHO_ESCURO,
    VIDRO,
)

PROFISSOES = {
    "ocioso": {"cor": (200, 205, 215, 255), "acao": "trabalhar", "chapeu": "none"},
    "madeireiro": {"cor": (168, 118, 66, 255), "acao": "cortar", "chapeu": "capuz"},
    "serrador": {"cor": (214, 150, 70, 255), "acao": "trabalhar", "chapeu": "avental"},
    "fazendeiro": {"cor": (110, 190, 96, 255), "acao": "trabalhar", "chapeu": "palha"},
    "minerador": {"cor": (150, 160, 176, 255), "acao": "trabalhar", "chapeu": "elmo"},
    "comerciante": {"cor": (230, 196, 92, 255), "acao": "trabalhar", "chapeu": "gorro"},
    "pedreiro": {"cor": (150, 145, 138, 255), "acao": "minerar", "chapeu": "avental"},
    "pescador": {"cor": (96, 170, 200, 255), "acao": "pescar", "chapeu": "palha"},
    "colonizador": {"cor": (120, 200, 210, 255), "acao": "trabalhar", "chapeu": "capuz"},
}

ACOES_CIDADAO = {
    "ocioso": ("idle", "andar"),
    "madeireiro": ("idle", "andar", "cortar", "carregar"),
    "serrador": ("idle", "andar", "trabalhar"),
    "fazendeiro": ("idle", "andar", "trabalhar"),
    "minerador": ("idle", "andar", "trabalhar"),
    "comerciante": ("idle", "andar", "trabalhar"),
    "pedreiro": ("idle", "andar", "minerar", "carregar"),
    "pescador": ("idle", "andar", "pescar"),
    "colonizador": ("idle", "andar", "trabalhar"),
    "rei": ("idle", "andar"),
}

CLASSES = {
    "soldado": {"base": "soldado", "cor": (90, 150, 220, 255), "acao": "atacar", "arma": "espada"},
    "defensor": {"base": "soldado", "cor": (120, 170, 240, 255), "acao": "atacar", "arma": "escudo"},
    "destruidor": {"base": "soldado", "cor": (220, 130, 100, 255), "acao": "atacar", "arma": "machado"},
    "arqueiro": {"base": "arqueiro", "cor": (110, 180, 120, 255), "acao": "atacar", "arma": "arco"},
    "patrulheiro": {"base": "arqueiro", "cor": (140, 210, 130, 255), "acao": "atacar", "arma": "arco"},
    "guardiao": {"base": "arqueiro", "cor": (90, 190, 170, 255), "acao": "atacar", "arma": "arco_longo"},
    "mago": {"base": "mago", "cor": (150, 120, 210, 255), "acao": "conjurar", "arma": "cajado"},
    "mago_eletrico": {"base": "mago", "cor": (200, 180, 90, 255), "acao": "conjurar", "arma": "cajado_raio"},
    "mago_gelo": {"base": "mago", "cor": (130, 200, 240, 255), "acao": "conjurar", "arma": "cajado_gelo"},
    "curandeiro": {"base": "curandeiro", "cor": (240, 220, 160, 255), "acao": "curar", "arma": "cajado_cura"},
    "bardo": {"base": "curandeiro", "cor": (240, 200, 120, 255), "acao": "curar", "arma": "alaude"},
    "protetor": {"base": "curandeiro", "cor": (180, 210, 240, 255), "acao": "curar", "arma": "escudo_cura"},
}

ACOES_COMBATE = {
    "soldado": ("idle", "andar", "atacar", "morrer"),
    "arqueiro": ("idle", "andar", "atacar", "morrer"),
    "mago": ("idle", "andar", "conjurar", "morrer"),
    "curandeiro": ("idle", "andar", "curar", "morrer"),
}

INIMIGOS = {
    "horda": {"cor": (206, 72, 72, 255), "base": "soldado", "arma": "espada"},
    "errante": {"cor": (150, 80, 170, 255), "base": "soldado", "arma": "machado"},
    "bandido": {"cor": (176, 116, 64, 255), "base": "soldado", "arma": "adaga"},
    "barbaro": {"cor": (156, 82, 52, 255), "base": "soldado", "arma": "machado"},
    "cavaleiro": {"cor": (112, 122, 142, 255), "base": "soldado", "arma": "espada"},
    "chefe": {"cor": (136, 54, 72, 255), "base": "soldado", "arma": "machado"},
}


def _quadro_idle(i: int) -> int:
    return [0, 1, 1, 0][i % 4]


def _quadro_andar(i: int) -> int:
    return [0, 1, 2, 1, 0, -1][i % 6]


def _desenhar_cabeca(
    canvas: Canvas,
    x: int,
    y: int,
    tamanho: int,
    chapeu: str,
    cor_cabelo=CABELO,
) -> None:
    canvas.retangulo(x, y, tamanho, tamanho, PELE, CONTORNO)
    canvas.retangulo(x, y, tamanho, max(1, tamanho // 3), cor_cabelo)
    if chapeu == "palha":
        canvas.retangulo(x - 2, y - 1, tamanho + 4, 2, PALHA, CONTORNO)
        canvas.retangulo(x + 1, y - 3, tamanho - 2, 2, PALHA, CONTORNO)
    elif chapeu == "capuz":
        canvas.poligono(
            [(x - 1, y + 1), (x + tamanho // 2, y - 3), (x + tamanho + 1, y + 1)],
            cor_cabelo,
            CONTORNO,
        )
    elif chapeu == "elmo":
        canvas.retangulo(x - 1, y - 1, tamanho + 2, 3, FERRO_CLARO, CONTORNO)
        canvas.retangulo(x, y, tamanho, 1, FERRO)
    elif chapeu == "gorro":
        canvas.retangulo(x, y - 2, tamanho, 3, VERMELHO, CONTORNO)
    elif chapeu == "avental":
        canvas.retangulo(x + 1, y + tamanho - 1, tamanho - 2, 2, MADEIRA_ESCURA)


def _ferramenta_cidadao(
    canvas: Canvas,
    profissao: str,
    acao: str,
    i: int,
    tamanho: int,
    lado: int,
) -> None:
    if profissao in ("ocioso", "rei"):
        if profissao == "rei":
            canvas.linha(25, 17, 25, 8, OURO, 2)
            canvas.circulo(25, 7, 2, OURO, CONTORNO)
        return
    if acao == "carregar":
        y = 21 if profissao != "pedreiro" else 22
        if profissao == "pedreiro":
            canvas.circulo(16, y, 4, PEDRA, CONTORNO)
        else:
            canvas.retangulo(9, y, 14, 4, MADEIRA, CONTORNO)
        return
    if acao not in ("trabalhar", "cortar", "minerar", "pescar"):
        return
    fase = [0, 1, 2, 1][i % 4]
    x_mao = 23 + lado
    y_mao = 18 - fase
    if profissao in ("madeireiro", "serrador"):
        canvas.linha(x_mao, y_mao, x_mao + 6, y_mao - 8, MADEIRA_ESCURA, 2)
        canvas.poligono(
            [(x_mao + 4, y_mao - 9), (x_mao + 11, y_mao - 11), (x_mao + 9, y_mao - 5)],
            FERRO_CLARO,
            CONTORNO,
        )
    elif profissao == "minerador":
        canvas.linha(x_mao, y_mao, x_mao + 5, y_mao - 9, MADEIRA_ESCURA, 2)
        canvas.linha(x_mao + 1, y_mao - 10, x_mao + 11, y_mao - 7, FERRO_CLARO, 2)
    elif profissao == "fazendeiro":
        canvas.linha(x_mao, y_mao, x_mao + 4, y_mao - 9, MADEIRA_ESCURA, 2)
        canvas.retangulo(x_mao + 2, y_mao - 10, 5, 2, FERRO, CONTORNO)
    elif profissao == "pedreiro":
        canvas.linha(x_mao, y_mao, x_mao + 4, y_mao - 6, MADEIRA_ESCURA, 2)
        canvas.retangulo(x_mao + 2, y_mao - 8, 5, 4, FERRO, CONTORNO)
    elif profissao == "pescador":
        canvas.linha(x_mao, y_mao - 2, x_mao + 12, y_mao - 22, MADEIRA_ESCURA)
        canvas.linha(x_mao + 12, y_mao - 22, x_mao + 12, y_mao - 8, TECIDO_CLARO)
        canvas.circulo(x_mao + 12, y_mao - 7, 1, FERRO_CLARO)
    elif profissao == "comerciante":
        canvas.circulo(x_mao + 3, y_mao, 4, PALHA, CONTORNO)
        canvas.circulo(x_mao + 4, y_mao - 1, 1, OURO)
    elif profissao == "colonizador":
        canvas.retangulo(x_mao + 2, y_mao - 1, 3, 9, MADEIRA, CONTORNO)
        canvas.poligono(
            [(x_mao + 5, y_mao), (x_mao + 13, y_mao + 2), (x_mao + 5, y_mao + 5)],
            VERDE,
            CONTORNO,
        )


def _cidadao_frame(profissao: str, acao: str, i: int) -> Canvas:
    canvas = Canvas(32, 32)
    dados = PROFISSOES.get(profissao, PROFISSOES["ocioso"])
    cor = dados["cor"]
    if profissao == "rei":
        cor = OURO
    yoff = _quadro_idle(i) if acao == "idle" else 0
    passo = _quadro_andar(i) if acao == "andar" else 0
    if acao in ("trabalhar", "cortar", "minerar", "pescar"):
        yoff = 0
    _sombra = Canvas(1, 1)
    canvas.elipse(8, 27, 16, 4, (18, 22, 26, 90))

    perna_esq = 2 + max(0, passo)
    perna_dir = 2 + max(0, -passo)
    canvas.retangulo(12, 23, 3, perna_esq, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(17, 23, 3, perna_dir, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(11, 14 + yoff, 10, 10, cor, CONTORNO)
    canvas.retangulo(11, 14 + yoff, 10, 2, TECIDO if profissao != "rei" else OURO_ESCURO)
    braço_esq = 18 + (passo if acao == "andar" else 0)
    braço_dir = 18 - (passo if acao == "andar" else 0)
    canvas.retangulo(8, braço_esq, 3, 7, PELE, CONTORNO)
    canvas.retangulo(21, braço_dir, 3, 7, PELE, CONTORNO)
    _desenhar_cabeca(canvas, 12, 5 + yoff, 8, dados["chapeu"])
    if profissao == "rei":
        canvas.poligono(
            [(12, 5), (13, 1), (15, 3), (16, 0), (17, 3), (19, 1), (20, 5)],
            OURO,
            CONTORNO,
        )
    if profissao in ("serrador", "pedreiro"):
        canvas.retangulo(11, 21 + yoff, 10, 3, REBOCO, CONTORNO)
    if profissao == "colonizador":
        canvas.retangulo(9, 16 + yoff, 3, 8, MADEIRA, CONTORNO)
    _ferramenta_cidadao(canvas, profissao, acao, i, 32, 0)
    return canvas


def gerar_cidadao(profissao: str, acao: str) -> Canvas:
    acoes = ACOES_CIDADAO.get(profissao, ("idle", "andar"))
    if acao not in acoes:
        acao = acoes[0]
    quantidade = 6 if acao in ("andar", "cortar", "minerar", "pescar") else 4
    if acao == "carregar":
        quantidade = 4
    return Canvas.folha(
        [_cidadao_frame(profissao, acao, i) for i in range(quantidade)]
    )


def _sombra_personagem(canvas: Canvas, largura: int, altura: int) -> None:
    canvas.elipse(largura // 2 - 14, altura - 6, 28, 6, (18, 22, 26, 110))


def _desenhar_arma(
    canvas: Canvas,
    arma: str,
    cor: tuple[int, int, int, int],
    fase: int,
    acao: str,
) -> None:
    if acao == "morrer" or acao == "idle":
        if acao == "morrer":
            return
    x = 34
    y = 24 - fase
    if arma in ("espada", "adaga"):
        canvas.linha(x, y, x + 8, y - 14, FERRO_CLARO, 2)
        canvas.linha(x + 1, y, x + 9, y - 14, FERRO)
        canvas.retangulo(x - 2, y - 1, 7, 2, OURO_ESCURO, CONTORNO)
    elif arma in ("machado", "machado_dois"):
        canvas.linha(x, y + 2, x + 7, y - 15, MADEIRA_ESCURA, 2)
        canvas.poligono(
            [(x + 5, y - 16), (x + 15, y - 18), (x + 12, y - 9), (x + 5, y - 11)],
            FERRO_CLARO,
            CONTORNO,
        )
    elif arma in ("escudo", "escudo_cura"):
        canvas.poligono(
            [(28, 16), (40, 18), (38, 31), (28, 30)],
            cor,
            CONTORNO,
        )
        canvas.linha(32, 20, 32, 27, OURO if arma == "escudo_cura" else FERRO_CLARO)
    elif arma in ("arco", "arco_longo"):
        canvas.linha(35, 10, 30, 22, MADEIRA, 2)
        canvas.linha(30, 22, 35, 34, MADEIRA, 2)
        canvas.linha(35, 10, 35, 34, TECIDO_CLARO)
        if acao == "atacar":
            canvas.linha(28, 22, 42, 22, MADEIRA_ESCURA)
            canvas.poligono([(42, 22), (38, 20), (38, 24)], FERRO_CLARO)
    elif arma in ("cajado", "cajado_raio", "cajado_gelo", "cajado_cura"):
        canvas.linha(36, 34, 36, 10, MADEIRA_ESCURA, 2)
        cor_magia = MAGIA_CLARA
        if arma == "cajado_raio":
            cor_magia = OURO
        elif arma == "cajado_gelo":
            cor_magia = VIDRO
        canvas.circulo(36, 8, 4, cor_magia, CONTORNO)
        if acao == "conjurar":
            canvas.circulo(36, 8, 6 + fase, (255, 255, 255, 40), cor_magia)
    elif arma == "alaude":
        canvas.elipse(29, 20, 13, 12, MADEIRA_CLARA, CONTORNO)
        canvas.retangulo(34, 12, 2, 12, MADEIRA_ESCURA)
        canvas.linha(31, 19, 38, 19, OURO)
    elif arma == "escudo_cura":
        canvas.circulo(35, 22, 6, cor, CONTORNO)
        canvas.circulo(35, 22, 3, MAGIA_CLARA)


def _combate_frame(classe: str, acao: str, i: int, inimigo: bool = False) -> Canvas:
    dados = CLASSES.get(classe, CLASSES["soldado"])
    cor = dados["cor"] if not inimigo else INIMIGOS.get(classe, INIMIGOS["horda"])["cor"]
    base = dados["base"]
    arma = dados["arma"] if not inimigo else INIMIGOS.get(classe, INIMIGOS["horda"])["arma"]
    canvas = Canvas(48, 48)
    _sombra_personagem(canvas, 48, 48)
    if acao == "morrer":
        return canvas
    passo = _quadro_andar(i) if acao == "andar" else 0
    yoff = _quadro_idle(i) if acao == "idle" else 0
    fase = [0, 1, 2, 1, 0, 1][i % 6] if acao in ("atacar", "conjurar", "curar") else 0
    perna_esq = 3 + max(0, passo)
    perna_dir = 3 + max(0, -passo)
    canvas.retangulo(18, 34, 4, perna_esq, MADEIRA_ESCURA, CONTORNO)
    canvas.retangulo(26, 34, 4, perna_dir, MADEIRA_ESCURA, CONTORNO)
    if base in ("mago", "curandeiro"):
        canvas.poligono([(15, 28 + yoff), (33, 28 + yoff), (36, 38), (12, 38)], cor, CONTORNO)
    else:
        canvas.retangulo(16, 19 + yoff, 16, 16, cor, CONTORNO)
        canvas.retangulo(16, 19 + yoff, 16, 3, TECIDO_CLARO)
    cor_pele = PELE if not inimigo else PELE_ESCURA
    canvas.retangulo(19, 8 + yoff, 10, 11, cor_pele, CONTORNO)
    canvas.retangulo(19, 8 + yoff, 10, 3, CABELO if not inimigo else VERMELHO_ESCURO)
    canvas.retangulo(14, 20 + yoff, 4, 10, cor_pele, CONTORNO)
    canvas.retangulo(30, 20 + yoff, 4, 10, cor_pele, CONTORNO)
    if base == "soldado":
        canvas.retangulo(18, 6 + yoff, 12, 4, FERRO_CLARO, CONTORNO)
        canvas.retangulo(21, 10 + yoff, 6, 2, FERRO)
    elif base == "arqueiro":
        canvas.poligono([(17, 7 + yoff), (28, 5 + yoff), (30, 10 + yoff), (20, 12 + yoff)], VERDE_ESCURO, CONTORNO)
    elif base == "mago":
        canvas.poligono([(16, 5 + yoff), (32, 5 + yoff), (36, 13 + yoff), (12, 13 + yoff)], cor, CONTORNO)
    else:
        canvas.retangulo(18, 6 + yoff, 12, 4, PALHA, CONTORNO)
    if classe == "defensor":
        _desenhar_arma(canvas, "escudo", cor, fase, acao)
    elif classe == "protetor":
        _desenhar_arma(canvas, "escudo_cura", cor, fase, acao)
    else:
        _desenhar_arma(canvas, arma, cor, fase, acao)
    return canvas


def _morrer_folha(frames: list[Canvas], centro: tuple[int, int]) -> list[Canvas]:
    base = frames[0]
    angulos = [0, 20, 40, 60, 78, 90]
    resultado = []
    for angulo in angulos:
        novo = Canvas(base.largura, base.altura)
        rotacionado = base.imagem.rotate(
            angulo,
            resample=Image.Resampling.NEAREST,
            center=centro,
        )
        novo.imagem.alpha_composite(rotacionado, (0, 0))
        resultado.append(novo)
    return resultado


def gerar_combatente(classe: str, acao: str) -> Canvas:
    dados = CLASSES.get(classe, CLASSES["soldado"])
    acoes = ACOES_COMBATE[dados["base"]]
    if acao not in acoes:
        acao = acoes[0]
    if acao == "morrer":
        frames = [
            _combate_frame(classe, "idle", 0),
            _combate_frame(classe, "andar", 0),
        ]
        return Canvas.folha(_morrer_folha(frames, (24, 40)))
    quantidade = 6 if acao != "idle" else 4
    return Canvas.folha(
        [_combate_frame(classe, acao, i) for i in range(quantidade)]
    )


def gerar_inimigo(nome: str, acao: str) -> Canvas:
    if nome == "catapulta":
        return gerar_catapulta(acao)
    frames = []
    quantidade = 6 if acao != "idle" else 2
    if acao == "morrer":
        base = _combate_frame(nome, "idle", 0, inimigo=True)
        return Canvas.folha(_morrer_folha([base], (24, 40)))
    for i in range(quantidade):
        frames.append(_combate_frame(nome, acao, i, inimigo=True))
    return Canvas.folha(frames)


def gerar_catapulta(acao: str) -> Canvas:
    quantidade = 2 if acao == "idle" else 6
    frames = []
    for i in range(quantidade):
        canvas = Canvas(64, 48)
        canvas.elipse(4, 40, 56, 7, (18, 22, 26, 110))
        canvas.retangulo(8, 28, 46, 14, MADEIRA, CONTORNO)
        canvas.circulo(18, 42, 5, FERRO, CONTORNO)
        canvas.circulo(46, 42, 5, FERRO, CONTORNO)
        angulo = -i * 6 if acao == "atacar" else 0
        canvas.polilinha([(16, 30), (40, 14 + angulo), (52, 28)], MADEIRA_ESCURA, 3)
        canvas.circulo(34, 24, 3, FERRO_CLARO, CONTORNO)
        frames.append(canvas)
    return Canvas.folha(frames)


def gerar_caravana(acao: str) -> Canvas:
    quantidade = 6 if acao == "andar" else 4
    frames = []
    for i in range(quantidade):
        canvas = Canvas(64, 48)
        canvas.elipse(6, 38, 52, 8, (18, 22, 26, 110))
        canvas.retangulo(14, 20, 34, 18, MADEIRA, CONTORNO)
        canvas.retangulo(16, 22, 30, 14, MADEIRA_CLARA)
        canvas.poligono([(12, 20), (32, 10), (52, 20)], TELHA_ESCURA, CONTORNO)
        canvas.retangulo(20, 26, 10, 8, OURO_ESCURO, CONTORNO)
        canvas.retangulo(34, 26, 8, 8, PALHA, CONTORNO)
        for x, fase in ((22, i), (44, i + 3)):
            canvas.circulo(x, 40, 6, FERRO, CONTORNO)
            canvas.linha(x - 4, 40 - 4 + fase % 2, x + 4, 40 + 4 - fase % 2, FERRO_CLARO)
        if acao == "andar":
            canvas.retangulo(50, 26, 8, 3, MADEIRA_ESCURA)
            canvas.poligono([(58, 26), (63, 28), (58, 30)], VERMELHO, CONTORNO)
        frames.append(canvas)
    return Canvas.folha(frames)
