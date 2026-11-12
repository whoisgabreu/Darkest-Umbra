"""Catálogo, lotes, manifesto e previews do pacote de assets."""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import efeitos, eventos, fundo, mapa, personagens, ui
from .canvas import Canvas
from .estruturas import NOMES as NOMES_ESTRUTURAS
from .estruturas import TAMANHOS, gerar_bandeira, gerar_construcao, gerar_dano_estrutura, gerar_estrutura, gerar_icone
from .paleta import CONTORNO, VERDE, VERMELHO

PASTA_ASSETS = Path(__file__).resolve().parents[1]
CAMINHO_MANIFESTO = PASTA_ASSETS / "manifest.json"
PASTA_PREVIEWS = PASTA_ASSETS / "_previews"

LOTES = (
    "estruturas",
    "personagens",
    "mapa",
    "efeitos",
    "ui",
    "eventos",
    "fundo",
)

ACOES_CIDADAO = personagens.ACOES_CIDADAO
ACOES_COMBATE = personagens.ACOES_COMBATE
PROFISSOES = personagens.PROFISSOES
CLASSES = personagens.CLASSES
INIMIGOS = personagens.INIMIGOS

FRAMES_EFEITO = {
    "corte_espada": 6,
    "flecha": 4,
    "pedra_catapulta": 4,
    "fumaca": 6,
    "fogo": 6,
    "poeira_construcao": 6,
    "faisca_upgrade": 6,
    "moedas": 4,
    "explosao": 8,
    "tiro_posto": 4,
}


def _carregar_manifesto() -> dict:
    if CAMINHO_MANIFESTO.exists():
        try:
            dados = json.loads(CAMINHO_MANIFESTO.read_text(encoding="utf-8"))
            if isinstance(dados, dict) and isinstance(dados.get("assets"), list):
                return dados
        except (OSError, json.JSONDecodeError):
            pass
    return {"versao": 1, "paleta": "medieval", "assets": []}


def _salvar_manifesto(dados: dict) -> None:
    dados["atualizado_em"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    CAMINHO_MANIFESTO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _atualizar_manifesto(lote: str, entradas: list[dict]) -> None:
    dados = _carregar_manifesto()
    dados["assets"] = [
        entrada
        for entrada in dados["assets"]
        if entrada.get("categoria") != lote
    ]
    dados["assets"].extend(entradas)
    dados["assets"].sort(key=lambda item: (item.get("categoria", ""), item.get("id", "")))
    _salvar_manifesto(dados)


def _salvar(
    entradas: list[dict],
    categoria: str,
    identificador: str,
    canvas: Canvas,
    caminho: str,
    frames: int = 1,
    largura_frame: int | None = None,
    ancora: str = "centro-base",
    descricao: str = "",
    forcar: bool = False,
) -> Canvas:
    destino = PASTA_ASSETS / caminho
    if not destino.exists() or forcar:
        canvas.salvar(destino)
    entradas.append(
        {
            "id": identificador,
            "categoria": categoria,
            "arquivo": caminho,
            "largura": canvas.largura,
            "altura": canvas.altura,
            "frames": frames,
            "largura_frame": largura_frame or (canvas.largura // frames),
            "ancora": ancora,
            "descricao": descricao,
        }
    )
    return canvas


def _preview(itens: list[tuple[Canvas, str]], nome: str, colunas: int = 6) -> Path:
    if not itens:
        caminho = PASTA_PREVIEWS / f"{nome}.png"
        Canvas(1, 1).salvar(caminho)
        return caminho
    celula_l = 168
    celula_a = 108
    linhas = (len(itens) + colunas - 1) // colunas
    folha = Canvas(colunas * celula_l, linhas * celula_a, (22, 26, 33, 255))
    for indice, (canvas, _rotulo) in enumerate(itens):
        col = indice % colunas
        row = indice // colunas
        thumb = canvas.ajustar_em(celula_l - 12, celula_a - 12)
        x = col * celula_l + 6
        y = row * celula_a + 6
        folha.imagem.alpha_composite(thumb.imagem, (x, y))
        folha.retangulo(
            col * celula_l,
            row * celula_a,
            celula_l - 1,
            celula_a - 1,
            None,
            (58, 64, 74, 255),
        )
    caminho = PASTA_PREVIEWS / f"{nome}.png"
    folha.salvar(caminho)
    return caminho


def _lote_estruturas(entradas: list[dict], forcar: bool) -> list[tuple[Canvas, str]]:
    preview = []
    for tipo in NOMES_ESTRUTURAS:
        if tipo == "castelo":
            continue
        for nivel in (1, 2, 3):
            canvas = gerar_estrutura(tipo, nivel)
            _salvar(
                entradas,
                "estruturas",
                f"predio_{tipo}_nivel_{nivel}",
                canvas,
                f"predios/{tipo}/nivel_{nivel}.png",
                descricao=f"{NOMES_ESTRUTURAS[tipo]} nível {nivel}",
                forcar=forcar,
            )
            if nivel == 3:
                preview.append((canvas, tipo))
        icone = gerar_icone(tipo, 3)
        _salvar(
            entradas,
            "estruturas",
            f"predio_{tipo}_icone",
            icone,
            f"predios/{tipo}/icone.png",
            ancora="centro",
            descricao=f"Ícone de {NOMES_ESTRUTURAS[tipo]}",
            forcar=forcar,
        )
    for nivel in range(1, 6):
        canvas = gerar_estrutura("castelo", nivel)
        _salvar(
            entradas,
            "estruturas",
            f"castelo_nivel_{nivel}",
            canvas,
            f"castelo/castelo_nivel_{nivel}.png",
            descricao=f"Castelo nível {nivel}",
            forcar=forcar,
        )
        if nivel in (1, 3, 5):
            preview.append((canvas, f"castelo_{nivel}"))
    for nivel in (1, 2, 3):
        canvas = gerar_estrutura("muralha", nivel)
        _salvar(
            entradas,
            "estruturas",
            f"castelo_muralha_nivel_{nivel}",
            canvas,
            f"castelo/muralha_nivel_{nivel}.png",
            descricao=f"Muralha do castelo nível {nivel}",
            forcar=forcar,
        )
    dano_base = gerar_estrutura("castelo", 4)
    for nome, intensidade in (("leve", 8), ("medio", 16), ("critico", 28), ("ruinas", 44)):
        canvas = Canvas(dano_base.largura, dano_base.altura)
        canvas.colar(dano_base, 0, 0)
        for indice in range(intensidade):
            x = 20 + (indice * 47) % (canvas.largura - 40)
            y = 30 + (indice * 61) % (canvas.altura - 60)
            canvas.linha(x, y, x + 14, y + 9, CONTORNO, 2)
            canvas.linha(x + 5, y + 2, x + 9, y + 16, CONTORNO)
        if nome == "ruinas":
            canvas.retangulo(24, 150, 46, 60, (0, 0, 0, 0))
            canvas.retangulo(184, 130, 48, 80, (0, 0, 0, 0))
        _salvar(
            entradas,
            "estruturas",
            f"castelo_dano_{nome}",
            canvas,
            f"castelo/dano_{nome}.png",
            descricao=f"Castelo com dano {nome}",
            forcar=forcar,
        )
    bandeira = Canvas.folha([gerar_bandeira(i) for i in range(4)])
    _salvar(
        entradas,
        "estruturas",
        "castelo_bandeira",
        bandeira,
        "castelo/bandeira.png",
        frames=4,
        largura_frame=32,
        ancora="centro",
        descricao="Bandeira do castelo animada",
        forcar=forcar,
    )
    construcao = Canvas.folha([gerar_construcao(i) for i in range(4)])
    _salvar(
        entradas,
        "estruturas",
        "predio_construcao",
        construcao,
        "predios/_compartilhado/construcao.png",
        frames=4,
        largura_frame=64,
        descricao="Animação compartilhada de construção",
        forcar=forcar,
    )
    dano = gerar_dano_estrutura()
    _salvar(
        entradas,
        "estruturas",
        "predio_dano",
        dano,
        "predios/_compartilhado/dano.png",
        descricao="Overlay compartilhado de dano",
        forcar=forcar,
    )
    return preview


def _lote_personagens(entradas: list[dict], forcar: bool) -> list[tuple[Canvas, str]]:
    preview = []
    for profissao, acoes in ACOES_CIDADAO.items():
        for acao in acoes:
            canvas = personagens.gerar_cidadao(profissao, acao)
            frames = canvas.largura // 32
            _salvar(
                entradas,
                "personagens",
                f"cidadao_{profissao}_{acao}",
                canvas,
                f"unidades/cidadaos/{profissao}_{acao}.png",
                frames=frames,
                largura_frame=32,
                descricao=f"Cidadão {profissao} — {acao}",
                forcar=forcar,
            )
            if acao in ("idle", "trabalhar", "cortar", "pescar"):
                preview.append((canvas, f"{profissao}_{acao}"))
    for classe, dados in CLASSES.items():
        for acao in ACOES_COMBATE[dados["base"]]:
            canvas = personagens.gerar_combatente(classe, acao)
            frames = canvas.largura // 48
            _salvar(
                entradas,
                "personagens",
                f"tropa_{classe}_{acao}",
                canvas,
                f"unidades/soldado/{classe}_{acao}.png",
                frames=frames,
                largura_frame=48,
                descricao=f"{classe} — {acao}",
                forcar=forcar,
            )
            if acao in ("idle", "atacar", "conjurar", "curar"):
                preview.append((canvas, f"{classe}_{acao}"))
    for nome in INIMIGOS:
        acoes = ("idle", "andar", "atacar", "morrer")
        for acao in acoes:
            canvas = personagens.gerar_inimigo(nome, acao)
            frames = canvas.largura // 48
            _salvar(
                entradas,
                "personagens",
                f"inimigo_{nome}_{acao}",
                canvas,
                f"unidades/inimigos/{nome}_{acao}.png",
                frames=frames,
                largura_frame=48,
                descricao=f"Inimigo {nome} — {acao}",
                forcar=forcar,
            )
            if acao in ("idle", "atacar"):
                preview.append((canvas, f"{nome}_{acao}"))
    if "catapulta" not in INIMIGOS:
        for acao in ("idle", "atacar"):
            canvas = personagens.gerar_catapulta(acao)
            frames = canvas.largura // 64
            _salvar(
                entradas,
                "personagens",
                f"inimigo_catapulta_{acao}",
                canvas,
                f"unidades/inimigos/catapulta_{acao}.png",
                frames=frames,
                largura_frame=64,
                descricao=f"Catapulta — {acao}",
                forcar=forcar,
            )
            preview.append((canvas, f"catapulta_{acao}"))
    for acao in ("idle", "andar"):
        canvas = personagens.gerar_caravana(acao)
        frames = canvas.largura // 64
        _salvar(
            entradas,
            "personagens",
            f"caravana_{acao}",
            canvas,
            f"unidades/caravana/caravana_{acao}.png",
            frames=frames,
            largura_frame=64,
            descricao=f"Caravana — {acao}",
            forcar=forcar,
        )
        preview.append((canvas, f"caravana_{acao}"))
    return preview


def _lote_mapa(entradas: list[dict], forcar: bool) -> list[tuple[Canvas, str]]:
    preview = []
    for variacao in range(3):
        canvas = mapa.tile_grama(variacao)
        _salvar(entradas, "mapa", f"tile_grama_{variacao + 1}", canvas, f"mapa/tiles/grama_{variacao + 1}.png", ancora="centro", descricao="Tile de grama", forcar=forcar)
    for variacao in range(2):
        canvas = mapa.tile_terra(variacao)
        _salvar(entradas, "mapa", f"tile_terra_{variacao + 1}", canvas, f"mapa/tiles/terra_{variacao + 1}.png", ancora="centro", descricao="Tile de terra/caminho", forcar=forcar)
    for variacao in range(3):
        canvas = mapa.tile_floresta(variacao)
        _salvar(entradas, "mapa", f"tile_floresta_{variacao + 1}", canvas, f"mapa/tiles/floresta_{variacao + 1}.png", ancora="centro", descricao="Tile de floresta", forcar=forcar)
    for frame in range(4):
        canvas = mapa.tile_agua(frame)
        _salvar(entradas, "mapa", f"tile_agua_{frame + 1}", canvas, f"mapa/tiles/agua_{frame + 1}.png", ancora="centro", descricao="Tile de água", forcar=forcar)
        preview.append((canvas, f"agua_{frame + 1}"))
    for variacao in range(2):
        canvas = mapa.tile_rocha(variacao)
        _salvar(entradas, "mapa", f"tile_rocha_{variacao + 1}", canvas, f"mapa/tiles/rocha_{variacao + 1}.png", ancora="centro", descricao="Tile de rocha", forcar=forcar)
    canvas = mapa.autotile_grama()
    _salvar(entradas, "mapa", "autotile_grama", canvas, "mapa/autotile_grama.png", frames=16, largura_frame=64, ancora="centro", descricao="Autotile de grama", forcar=forcar)
    for variacao in range(3):
        canvas = mapa.arvore_adulta(variacao)
        _salvar(entradas, "mapa", f"arvore_{variacao + 1}", canvas, f"mapa/natureza/arvore_{variacao + 1}.png", descricao="Árvore adulta", forcar=forcar)
        preview.append((canvas, f"arvore_{variacao + 1}"))
    canvas = mapa.arvore_toco()
    _salvar(entradas, "mapa", "arvore_toco", canvas, "mapa/natureza/arvore_toco.png", descricao="Toco de árvore", forcar=forcar)
    for variacao in range(2):
        canvas = mapa.rocha_adulta(variacao)
        _salvar(entradas, "mapa", f"rocha_{variacao + 1}", canvas, f"mapa/natureza/rocha_{variacao + 1}.png", descricao="Rocha adulta", forcar=forcar)
    canvas = mapa.rocha_esgotada()
    _salvar(entradas, "mapa", "rocha_esgotada", canvas, "mapa/natureza/rocha_esgotada.png", descricao="Rocha esgotada", forcar=forcar)
    canvas = mapa.acampamento_inimigo()
    _salvar(entradas, "mapa", "acampamento_inimigo", canvas, "mapa/natureza/acampamento_inimigo.png", descricao="Acampamento inimigo", forcar=forcar)
    preview.append((canvas, "acampamento"))
    for nome, preenchimento, caminho in (
        ("recurso_fundo", False, "mapa/barras/recurso_fundo.png"),
        ("recurso_preenchimento", True, "mapa/barras/recurso_preenchimento.png"),
    ):
        canvas = mapa.barra_recurso(preenchimento)
        _salvar(entradas, "mapa", nome, canvas, caminho, ancora="centro", descricao="Barra de recurso", forcar=forcar)
    canvas = mapa.tronco_carregado()
    _salvar(entradas, "mapa", "tronco_carregado", canvas, "mapa/tronco_carregado.png", ancora="centro", descricao="Tronco carregado", forcar=forcar)
    canvas = mapa.anel_selecao(64, 15)
    _salvar(entradas, "mapa", "anel_selecao_unidade", canvas, "mapa/anel_selecao_unidade.png", ancora="centro", descricao="Anel de seleção de unidade", forcar=forcar)
    canvas = mapa.anel_selecao(128, 30)
    _salvar(entradas, "mapa", "anel_selecao_predio", canvas, "mapa/anel_selecao_predio.png", ancora="centro", descricao="Anel de seleção de prédio", forcar=forcar)
    canvas = mapa.fantasma_posicionamento(True)
    _salvar(entradas, "mapa", "fantasma_valido", canvas, "mapa/fantasma_valido.png", ancora="centro", descricao="Fantasma de posicionamento válido", forcar=forcar)
    canvas = mapa.fantasma_posicionamento(False)
    _salvar(entradas, "mapa", "fantasma_invalido", canvas, "mapa/fantasma_invalido.png", ancora="centro", descricao="Fantasma de posicionamento inválido", forcar=forcar)
    canvas = mapa.raio_construcao(512)
    _salvar(entradas, "mapa", "raio_construcao", canvas, "mapa/raio_construcao.png", ancora="centro", descricao="Círculo do raio de construção", forcar=forcar)
    for nome, preenchimento in (("barra_hp_estrutura_fundo", False), ("barra_hp_estrutura_preenchimento", True)):
        canvas = mapa.barra_hp_estrutura(preenchimento)
        _salvar(entradas, "mapa", nome, canvas, f"mapa/barras/{nome}.png", ancora="centro", descricao="Barra de HP de estrutura", forcar=forcar)
    for nome, fabrica, descricao in (
        ("caixa_selecao", mapa.caixa_selecao, "Caixa de seleção"),
        ("marcador_ordem", mapa.marcador_ordem, "Marcador de ordem"),
        ("texto_recurso", mapa.texto_recurso, "Texto flutuante de recurso"),
    ):
        canvas = fabrica()
        _salvar(entradas, "mapa", nome, canvas, f"mapa/{nome}.png", ancora="centro", descricao=descricao, forcar=forcar)
    for nome, cor in (("bandido", (176, 116, 64, 255)), ("barbaro", (156, 82, 52, 255)), ("cavaleiro", (112, 122, 142, 255))):
        canvas = mapa.grupo_inimigo(cor)
        _salvar(entradas, "mapa", f"grupo_{nome}", canvas, f"mapa/grupo_{nome}.png", descricao=f"Grupo de {nome}", forcar=forcar)
    return preview


def _lote_efeitos(entradas: list[dict], forcar: bool) -> list[tuple[Canvas, str]]:
    preview = []
    for nome in FRAMES_EFEITO:
        canvas = efeitos.gerar_efeito(nome)
        _salvar(
            entradas,
            "efeitos",
            f"efeito_{nome}",
            canvas,
            f"efeitos/{nome}.png",
            frames=FRAMES_EFEITO[nome],
            largura_frame=canvas.largura // FRAMES_EFEITO[nome],
            ancora="centro",
            descricao=f"Efeito {nome}",
            forcar=forcar,
        )
        preview.append((canvas, nome))
    return preview


def _lote_ui(entradas: list[dict], forcar: bool) -> list[tuple[Canvas, str]]:
    preview = []
    for nome, fabrica in ui.ICONES_RECURSO.items():
        canvas = fabrica()
        _salvar(entradas, "ui", f"icone_{nome}", canvas, f"ui/icones/recursos/{nome}.png", ancora="centro", descricao=f"Ícone de {nome}", forcar=forcar)
        if nome in ("madeira", "pedra", "ouro", "dinheiro", "alimento", "populacao", "soldados"):
            preview.append((canvas, nome))
    canvas = ui.folha_icones()
    _salvar(entradas, "ui", "icones_recursos", canvas, "ui/icones/recursos.png", frames=len(ui.ICONES_RECURSO), largura_frame=32, ancora="centro", descricao="Folha de ícones de recursos", forcar=forcar)
    for estilo in ("primario", "secundario"):
        for estado in ("normal", "hover", "pressionado", "desabilitado"):
            canvas = ui.botao(estilo, estado)
            _salvar(entradas, "ui", f"botao_{estilo}_{estado}", canvas, f"ui/botoes/{estilo}_{estado}.png", ancora="centro", descricao=f"Botão {estilo} {estado}", forcar=forcar)
    canvas = ui.painel_9slice()
    _salvar(entradas, "ui", "painel_9slice", canvas, "ui/paineis/painel_9slice.png", ancora="centro", descricao="Painel 9-slice", forcar=forcar)
    for nome, largura, altura, cor in (
        ("progresso_fundo", 64, 8, None),
        ("progresso_preenchimento", 64, 8, VERDE),
        ("hp_castelo_fundo", 128, 10, None),
        ("hp_castelo_preenchimento", 128, 10, VERMELHO),
        ("hp_unidade_fundo", 32, 4, None),
        ("hp_unidade_preenchimento", 32, 4, VERMELHO),
    ):
        canvas = ui.barra_fundo(largura, altura) if nome.endswith("fundo") else ui.barra_preenchimento(largura, altura, cor)
        _salvar(entradas, "ui", nome, canvas, f"ui/barras/{nome}.png", ancora="centro", descricao="Barra de UI", forcar=forcar)
    for nome, fabrica, descricao in (
        ("ataque", ui.alerta_ataque, "Alerta de ataque"),
        ("fome", ui.alerta_fome, "Alerta de fome"),
        ("aviso", ui.alerta_aviso, "Alerta de aviso"),
    ):
        canvas = fabrica()
        _salvar(entradas, "ui", f"alerta_{nome}", canvas, f"ui/alertas/{nome}.png", ancora="centro", descricao=descricao, forcar=forcar)
        preview.append((canvas, nome))
    for velocidade in ("pausar", "play", "1x", "2x", "4x"):
        canvas = ui.controle(velocidade)
        _salvar(entradas, "ui", f"controle_{velocidade}", canvas, f"ui/controles/{velocidade}.png", ancora="centro", descricao=f"Controle {velocidade}", forcar=forcar)
        preview.append((canvas, velocidade))
    for nome, fabrica, caminho, descricao in (
        ("logo", ui.logo, "ui/logo.png", "Logo do reino"),
        ("cursor", ui.cursor, "ui/cursor.png", "Cursor medieval"),
        ("minimapa_moldura", ui.minimapa_moldura, "ui/minimapa_moldura.png", "Moldura do minimapa"),
        ("minimapa_marcador_ataque", ui.minimapa_marcador, "ui/minimapa_marcador_ataque.png", "Marcador de ataque no minimapa"),
        ("caixa_selecao", ui.caixa_selecao, "ui/caixa_selecao.png", "Caixa de seleção"),
    ):
        canvas = fabrica()
        _salvar(entradas, "ui", nome, canvas, caminho, ancora="centro", descricao=descricao, forcar=forcar)
    preview.append((ui.logo(), "logo"))
    return preview


def _lote_eventos(entradas: list[dict], forcar: bool) -> list[tuple[Canvas, str]]:
    preview = []
    for nome in eventos.BANNERS:
        canvas = eventos.gerar_banner(nome)
        _salvar(entradas, "eventos", f"banner_{nome}", canvas, f"eventos/{nome}.png", ancora="centro", descricao=f"Banner de {nome}", forcar=forcar)
        preview.append((canvas, nome))
    return preview


def _lote_fundo(entradas: list[dict], forcar: bool) -> list[tuple[Canvas, str]]:
    preview = []
    for nome, fabrica, caminho, descricao in (
        ("fundo_reino_dia", fundo.fundo_reino_dia, "fundo/fundo_reino_dia.png", "Fundo do reino — dia"),
        ("ceu", fundo.ceu_parallax, "fundo/ceu.png", "Camada de céu"),
        ("montanhas", fundo.montanhas_parallax, "fundo/montanhas.png", "Camada de montanhas"),
        ("arvores", fundo.arvores_parallax, "fundo/arvores.png", "Camada de árvores"),
        ("overlay_noite", fundo.overlay_noite, "fundo/overlay_noite.png", "Overlay noturno"),
        ("tile_grama", fundo.tile_grama_fundo, "fundo/tile_grama.png", "Tile de grama de referência"),
    ):
        canvas = fabrica()
        _salvar(entradas, "fundo", nome, canvas, caminho, ancora="centro", descricao=descricao, forcar=forcar)
        preview.append((canvas, nome))
    return preview


GERADORES = {
    "estruturas": _lote_estruturas,
    "personagens": _lote_personagens,
    "mapa": _lote_mapa,
    "efeitos": _lote_efeitos,
    "ui": _lote_ui,
    "eventos": _lote_eventos,
    "fundo": _lote_fundo,
}


def executar_lote(lote: str, forcar: bool = False) -> int:
    if lote == "todos":
        total = 0
        for nome in LOTES:
            total += executar_lote(nome, forcar=forcar)
        return total
    if lote not in GERADORES:
        raise ValueError(f"Lote desconhecido: {lote}")
    entradas: list[dict] = []
    preview = GERADORES[lote](entradas, forcar)
    _atualizar_manifesto(lote, entradas)
    _preview(preview, lote)
    return len(entradas)
