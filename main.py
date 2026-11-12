"""Reino Incremental — mapa top-down com cidadãos e combate.

Execute com: python main.py
"""

from __future__ import annotations

import math
import os

import arcade
from arcade.camera import Camera2D
from arcade.shape_list import (
    ShapeElementList,
    create_ellipse_filled,
    create_line,
    create_rectangle_filled,
)

from mapa import (
    AGUA,
    ALTURA_MUNDO,
    ESTRADA,
    CASTELO_ID,
    COLUNAS,
    FLORESTA,
    GRAMA,
    LARGURA_MUNDO,
    LINHAS,
    PEGADAS,
    RAIO_CONSTRUCAO,
    RAIO_POSTO,
    ROCHA,
    TAMANHO_CHUNK,
    TERRA,
    TILE,
    Mapa,
)
from mundo import Mundo
from persistencia import carregar_jogo, novo_jogo, salvar_jogo
from reino import (
    CONSTRUCOES,
    CONSUMO_POR_PESSOA,
    CUSTO_SOLDADO,
    DIA_SEGUNDOS,
    MAX_NIVEL,
    NOMES_CONSTRUCOES,
    NOMES_RECURSOS,
    RECURSOS,
    Reino,
)
from unidades import (
    CLASSES_TROPA,
    CORES_PROFISSAO,
    CUSTO_TROPA,
    RECURSOS_RAROS,
    NOMES_PROFISSAO,
    TRABALHO_POR_PREDIO,
    Cidadao,
    Inimigo,
    Soldado,
    distancia,
    nivel_por_xp,
    xp_para_proximo_nivel,
)

LARGURA = 1100
ALTURA = 700

TOPO_H = 44
TOPO_Y = ALTURA - TOPO_H

DET_X = 8
DET_Y = 64
DET_W = 320
DET_H = 584

OBRAS_X = 792
OBRAS_Y = 64
OBRAS_W = 300
OBRAS_H = 584

CTX_X = 340
CTX_Y = 8
CTX_W = 440
CTX_H = 220

MINI_W = 220
MINI_H = 165
MINI_X = LARGURA - MINI_W - 8
MINI_Y = 8

OBRAS_LINHAS_VISIVEIS = 10

ECON_X = 250
ECON_Y = 64
ECON_W = 560
ECON_H = 520

TROPAS_POR_PREDIO = {
    "quartel": ("soldado", "defensor", "destruidor"),
    "arquearia": ("arqueiro", "patrulheiro", "guardiao"),
    "torre_magia": ("mago", "mago_eletrico", "mago_gelo"),
    "santuario": ("curandeiro", "bardo", "protetor"),
}

DIRETORIO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_SAVE = os.path.join(DIRETORIO, "save.json")

COR_FUNDO = (16, 19, 24)
COR_PAINEL = (22, 26, 33, 232)
COR_PAINEL_CLARO = (33, 38, 48, 238)
COR_BORDA = (68, 76, 90)
COR_TEXTO = (230, 234, 240)
COR_TEXTO_SUAVE = (150, 158, 170)
COR_DOURADO = (230, 196, 92)
COR_VERDE = (98, 196, 124)
COR_VERMELHO = (214, 92, 92)
COR_AZUL = (72, 132, 200)
COR_CINZA_BOTAO = (66, 76, 92)
COR_DESABILITADO = (52, 56, 64)

CORES_RECURSOS = {
    "madeira": (156, 108, 62),
    "troncos": (118, 82, 48),
    "pedra": (145, 142, 136),
    "ferro": (150, 162, 176),
    "ouro": (238, 200, 74),
    "dinheiro": (92, 200, 128),
    "alimento": (226, 128, 88),
}

CORES_PREDIOS = {
    "madeireira": (140, 98, 58),
    "mina": (96, 100, 110),
    "fazenda": (112, 146, 72),
    "mercado": (156, 124, 62),
    "ferraria": (132, 82, 70),
    "quartel": (100, 84, 122),
    "casas": (150, 120, 92),
    "celeiro": (140, 112, 72),
    "muralha": (122, 124, 132),
    "barricada": (128, 92, 54),
    "posto": (92, 118, 150),
    "arquearia": (102, 142, 96),
    "torre_magia": (128, 108, 170),
    "santuario": (200, 180, 130),
}

SIGLAS = {
    "castelo": "Castelo",
    "madeireira": "Mad",
    "mina": "Mina",
    "fazenda": "Faz",
    "mercado": "Mer",
    "ferraria": "Fer",
    "quartel": "Qua",
    "casas": "Cas",
    "celeiro": "Cel",
    "muralha": "Mur",
    "barricada": "Bar",
    "posto": "Pos",
    "arquearia": "Arq",
    "torre_magia": "Tor",
    "santuario": "San",
}

ABREVIACOES = {
    "madeira": "Mad",
    "troncos": "Tro",
    "pedra": "Ped",
    "ferro": "Fer",
    "ouro": "Our",
    "dinheiro": "Din",
    "alimento": "Ali",
}

RECURSOS_TOPO = ("madeira", "troncos", "pedra", "alimento", "ferro", "ouro", "dinheiro")


def fmt(valor: float, casas: int = 0) -> str:
    if valor >= 1_000_000:
        texto = f"{valor / 1_000_000:.1f}M"
    elif valor >= 1000:
        texto = f"{valor / 1000:.1f}k"
    else:
        texto = f"{valor:.{casas}f}"
    return texto.replace(".", ",")


def limitar(valor: float, minimo: float, maximo: float) -> float:
    if minimo > maximo:
        return (minimo + maximo) / 2
    return max(minimo, min(maximo, valor))


class Botao:
    __slots__ = (
        "x",
        "y",
        "largura",
        "altura",
        "rotulo",
        "acao",
        "habilitado",
        "cor",
        "tamanho_fonte",
    )

    def __init__(
        self,
        x,
        y,
        largura,
        altura,
        rotulo,
        acao,
        habilitado=True,
        cor=COR_CINZA_BOTAO,
        tamanho_fonte=10.5,
    ):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.rotulo = rotulo
        self.acao = acao
        self.habilitado = habilitado
        self.cor = cor
        self.tamanho_fonte = tamanho_fonte

    def contem(self, px, py) -> bool:
        return (
            self.x <= px <= self.x + self.largura
            and self.y <= py <= self.y + self.altura
        )


class Jogo(arcade.Window):
    def __init__(self) -> None:
        super().__init__(
            LARGURA,
            ALTURA,
            "Reino Incremental — Cidadãos e Conquistas",
            update_rate=1 / 60,
        )
        arcade.set_background_color(COR_FUNDO)

        self.reino, self.mapa, self.mundo, camera_salva = self._carregar_ou_novo()
        self.camera = Camera2D()
        if camera_salva is not None:
            self.camera.position = camera_salva
        else:
            self.camera.position = self.mapa.centro_mundo(CASTELO_ID)
        self.zoom = 1.0
        self.camera.zoom = self.zoom
        self._limitar_camera()

        self._dia_salvo = self.reino.dia
        self.mouse = (0.0, 0.0)
        self._ultimo_mouse = (0.0, 0.0)
        self._arrastando_camera = False
        self._teclas: set[int] = set()
        self._tempo_anim = 0.0

        self.botoes: list[Botao] = []
        self.botao_pressionado: Botao | None = None
        self.textos: dict[str, arcade.Text] = {}

        self.detalhe_aberto = False
        self.obras_aberto = False
        self.economia_aberto = False
        self.minimapa_aberto = True
        self.obras_scroll = 0
        self._espaco_cache: dict[str, bool] = {}
        self._espaco_versao = -1

        self.cidadaos_sel: list[Cidadao] = []
        self.soldados_sel: list[Soldado] = []
        self.predio_sel: int | None = None
        self.arvore_sel: tuple[int, int] | None = None
        self.rocha_sel: tuple[int, int] | None = None
        self.caravana_sel = None

        self.modo_posicionamento: str | None = None
        self.modo_estrada = False
        self._mouse_esquerdo = False
        self._ultimo_tile_estrada = None
        self.id_movendo: int | None = None
        self._caixa_inicio: tuple[float, float] | None = None
        self._caixa_atual: tuple[float, float] | None = None
        self._marcador: tuple[float, float, float] | None = None

        self.toast_texto = ""
        self.toast_cor = COR_VERDE
        self.toast_timer = 0.0

        self._combate_visto = id(self.reino.ultimo_combate)
        self._aviso_visto = self.reino.aviso_ataque
        self._raid_visto = self.mundo.raid_ativo

        self._terreno_chunks: dict[tuple[int, int], ShapeElementList] = {}
        self._arvores_chunks: dict[tuple[int, int], ShapeElementList] = {}
        self._rochas_chunks: dict[tuple[int, int], ShapeElementList] = {}
        self._montar_botoes()
        if not self.reino.derrota:
            self._mostrar_toast(
                "Você é o Rei: selecione-o e use o botão direito para "
                "coletar recursos e construir.",
                COR_AZUL,
            )

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def _carregar_ou_novo(self):
        if os.path.exists(CAMINHO_SAVE):
            try:
                return carregar_jogo(CAMINHO_SAVE)
            except (OSError, ValueError, KeyError, TypeError):
                pass
        reino, mapa, mundo = novo_jogo()
        return reino, mapa, mundo, None

    def _salvar(self) -> None:
        try:
            posicao = self.camera.position
            salvar_jogo(
                self.reino,
                self.mapa,
                self.mundo,
                CAMINHO_SAVE,
                camera=(posicao.x, posicao.y),
            )
        except OSError:
            pass

    def _novo_jogo(self) -> None:
        self.reino, self.mapa, self.mundo = novo_jogo()
        self._dia_salvo = self.reino.dia
        self._limpar_selecao()
        self.modo_posicionamento = None
        self.modo_estrada = False
        self.id_movendo = None
        self._caixa_inicio = None
        self._caixa_atual = None
        self._marcador = None
        self.toast_timer = 0.0
        self.obras_aberto = False
        self.detalhe_aberto = False
        self._espaco_cache.clear()
        self._espaco_versao = -1
        self._combate_visto = id(None)
        self._aviso_visto = False
        self._raid_visto = False
        self._terreno_chunks.clear()
        self._arvores_chunks.clear()
        self._rochas_chunks.clear()
        self._centralizar()
        self._salvar()
        self._mostrar_toast(
            "Novo reinado: selecione o Rei, construa e prospere. "
            "O jogo acaba apenas se o Rei morrer.",
            COR_AZUL,
        )

    def _centralizar(self) -> None:
        self.camera.position = self.mapa.centro_mundo(CASTELO_ID)
        self._limitar_camera()

    def _sair(self) -> None:
        self._salvar()
        self.close()

    # ------------------------------------------------------------------
    # Câmera
    # ------------------------------------------------------------------
    def _limitar_camera(self) -> None:
        meia_w = LARGURA / (2 * self.zoom)
        meia_h = ALTURA / (2 * self.zoom)
        x, y = self.camera.position
        x = limitar(x, meia_w, LARGURA_MUNDO - meia_w)
        y = limitar(y, meia_h, ALTURA_MUNDO - meia_h)
        self.camera.position = (x, y)

    def _mover_camera(self, dt: float) -> None:
        dx = dy = 0.0
        if arcade.key.A in self._teclas or arcade.key.LEFT in self._teclas:
            dx -= 1
        if arcade.key.D in self._teclas or arcade.key.RIGHT in self._teclas:
            dx += 1
        if arcade.key.S in self._teclas or arcade.key.DOWN in self._teclas:
            dy -= 1
        if arcade.key.W in self._teclas or arcade.key.UP in self._teclas:
            dy += 1
        if dx or dy:
            comprimento = math.hypot(dx, dy)
            velocidade = 680.0 / self.zoom
            x, y = self.camera.position
            self.camera.position = (
                x + dx / comprimento * velocidade * dt,
                y + dy / comprimento * velocidade * dt,
            )
            self._limitar_camera()

    def _mundo_do_mouse(self) -> tuple[float, float]:
        ponto = self.camera.unproject(self.mouse)
        return (ponto.x, ponto.y)

    def _anchor_posicionamento(self) -> tuple[int, int] | None:
        if self.modo_posicionamento is None:
            return None
        largura, altura = PEGADAS[self.modo_posicionamento]
        mundo_x, mundo_y = self._mundo_do_mouse()
        col = int(mundo_x // TILE) - largura // 2
        row = int(mundo_y // TILE) - altura // 2
        return (col, row)

    # ------------------------------------------------------------------
    # Atualização
    # ------------------------------------------------------------------
    def on_update(self, delta_time: float) -> None:
        self._tempo_anim += delta_time
        self._mover_camera(delta_time)
        self.mundo.atualizar(delta_time)

        if self.mundo.chunks_arvores_dirty:
            for chunk in self.mundo.chunks_arvores_dirty:
                self._arvores_chunks.pop(chunk, None)
            self.mundo.chunks_arvores_dirty.clear()
        if self.mundo.chunks_rochas_dirty:
            for chunk in self.mundo.chunks_rochas_dirty:
                self._rochas_chunks.pop(chunk, None)
            self.mundo.chunks_rochas_dirty.clear()

        self._podar_selecao()

        if self.reino.dia != self._dia_salvo:
            self._dia_salvo = self.reino.dia
            self._salvar()

        self._atualizar_avisos()

        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - delta_time)
        if self._marcador is not None:
            mx, my, tempo = self._marcador
            tempo -= delta_time
            self._marcador = (mx, my, tempo) if tempo > 0 else None

        self._montar_botoes()

    def _podar_selecao(self) -> None:
        self.cidadaos_sel = [
            c for c in self.cidadaos_sel if any(c is vivo for vivo in self.mundo.cidadaos)
        ]
        self.soldados_sel = [
            s for s in self.soldados_sel if any(s is vivo for vivo in self.mundo.soldados)
        ]
        if self.predio_sel is not None and (
            self.predio_sel not in self.mapa.posicoes
            or self.predio_sel not in self.reino.construcoes
        ):
            self.predio_sel = None
        if self.arvore_sel is not None and self.arvore_sel not in self.mundo.arvores:
            self.arvore_sel = None
        if self.rocha_sel is not None and self.rocha_sel not in self.mundo.rochas:
            self.rocha_sel = None
        if self.caravana_sel is not None and self.caravana_sel not in self.mundo.caravanas:
            self.caravana_sel = None

    def _atualizar_avisos(self) -> None:
        combate = self.reino.ultimo_combate
        if combate is not None and id(combate) != self._combate_visto:
            self._combate_visto = id(combate)
            alvo = combate.get("alvo", "Castelo")
            if combate.get("vitoria", True):
                if alvo == "Castelo":
                    texto_combate = (
                        f"Ataque repelido! {combate.get('inimigos', 0)} "
                        f"inimigo(s). Perdas: {combate.get('perdas', 0)} "
                        f"soldado(s). +{combate.get('ouro', 0)} ouro."
                    )
                else:
                    texto_combate = (
                        f"{alvo} defendido! {combate.get('inimigos', 0)} "
                        f"inimigo(s). Perdas: {combate.get('perdas', 0)}."
                    )
                cor_combate = COR_VERDE
            else:
                texto_combate = f"{alvo} foi destruído durante o ataque!"
                cor_combate = COR_VERMELHO
            self._mostrar_toast(texto_combate, cor_combate)

        if self.reino.aviso_ataque and not self._aviso_visto:
            self._mostrar_toast(
                f"Inimigos a caminho! Ataque no dia "
                f"{self.reino.proximo_ataque_dia}.",
                COR_DOURADO,
            )
        self._aviso_visto = self.reino.aviso_ataque

        if self.mundo.raid_ativo and not self._raid_visto:
            if self.mundo.raid_posto_id is not None:
                self._mostrar_toast(
                    f"Horda ataca o Posto #{self.mundo.raid_posto_id}! "
                    "Envie soldados para defendê-lo.",
                    COR_VERMELHO,
                )
            else:
                self._mostrar_toast(
                    "Horda inimiga! Soldados, defendam o castelo!",
                    COR_VERMELHO,
                )
        self._raid_visto = self.mundo.raid_ativo

    def _mostrar_toast(self, texto: str, cor=COR_VERDE) -> None:
        self.toast_texto = texto
        self.toast_cor = cor
        self.toast_timer = 4.0

    # ------------------------------------------------------------------
    # Texto e formas
    # ------------------------------------------------------------------
    def texto(
        self,
        chave: str,
        conteudo: str,
        x: float,
        y: float,
        tamanho: float = 12,
        cor=COR_TEXTO,
        anchor_x: str = "left",
        anchor_y: str = "center",
        negrito: bool = False,
    ) -> None:
        rotulo = self.textos.get(chave)
        if rotulo is None:
            rotulo = arcade.Text(
                conteudo,
                x,
                y,
                color=cor,
                font_size=tamanho,
                bold=negrito,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
            )
            self.textos[chave] = rotulo
        else:
            if rotulo.text != conteudo:
                rotulo.text = conteudo
            rotulo.x = x
            rotulo.y = y
            if rotulo.color != cor:
                rotulo.color = cor
        rotulo.draw()

    def painel(self, x, y, largura, altura, cor=COR_PAINEL, borda=COR_BORDA) -> None:
        arcade.draw_lbwh_rectangle_filled(x, y, largura, altura, cor)
        arcade.draw_lbwh_rectangle_outline(x, y, largura, altura, borda, 1)

    # ------------------------------------------------------------------
    # Botões
    # ------------------------------------------------------------------
    def _add(
        self,
        x,
        y,
        largura,
        altura,
        rotulo,
        acao,
        habilitado=True,
        cor=COR_CINZA_BOTAO,
        tamanho_fonte=10.5,
    ) -> None:
        self.botoes.append(
            Botao(x, y, largura, altura, rotulo, acao, habilitado, cor, tamanho_fonte)
        )

    def _montar_botoes(self) -> None:
        self.botoes = []
        if self.reino.derrota:
            self._add(
                LARGURA / 2 - 150,
                260,
                140,
                42,
                "Novo Jogo",
                self._novo_jogo,
                cor=COR_AZUL,
                tamanho_fonte=13,
            )
            self._add(
                LARGURA / 2 + 10,
                260,
                140,
                42,
                "Sair",
                self._sair,
                cor=COR_CINZA_BOTAO,
                tamanho_fonte=13,
            )
            return

        pausado = self.reino.pausado
        self._add(
            700,
            663,
            64,
            30,
            "Continuar" if pausado else "Pausar",
            self._alternar_pausa,
            cor=COR_CINZA_BOTAO,
            tamanho_fonte=9.5,
        )
        for indice, velocidade in enumerate((1, 2, 4)):
            ativo = self.reino.velocidade == velocidade and not pausado
            self._add(
                768 + indice * 32,
                663,
                30,
                30,
                f"{velocidade}x",
                lambda v=velocidade: self._definir_velocidade(v),
                cor=COR_AZUL if ativo else COR_CINZA_BOTAO,
                tamanho_fonte=9.5,
            )
        self._add(
            864,
            663,
            80,
            30,
            "Obras [B]",
            self._alternar_obras,
            cor=COR_AZUL if self.obras_aberto else COR_CINZA_BOTAO,
            tamanho_fonte=9,
        )
        self._add(
            948,
            663,
            76,
            30,
            "Centro [C]",
            self._centralizar,
            cor=COR_CINZA_BOTAO,
            tamanho_fonte=9,
        )
        self._add(
            1028,
            663,
            72,
            30,
            "Ataq ON" if self.reino.ataques_ativos else "Ataq OFF",
            self._alternar_ataques,
            cor=COR_VERMELHO if self.reino.ataques_ativos else COR_CINZA_BOTAO,
            tamanho_fonte=8.5,
        )

        if self.obras_aberto:
            self._add(
                800,
                592,
                90,
                30,
                "Sold [T]",
                self._treinar_soldado,
                habilitado=self.mundo.pode_treinar_soldado(),
                cor=COR_VERDE,
                tamanho_fonte=8.5,
            )
            self._add(
                894,
                592,
                90,
                30,
                "Arq [Q]",
                self._treinar_arqueiro,
                habilitado=self.mundo.pode_treinar_arqueiro(),
                cor=COR_AZUL,
                tamanho_fonte=8.5,
            )
            self._add(
                988,
                592,
                94,
                30,
                "Reparar [R]",
                self.reparar_castelo,
                habilitado=self.reino.pode_reparar_castelo(),
                cor=COR_DOURADO,
                tamanho_fonte=8.5,
            )
            topo = 574
            tipos = list(CONSTRUCOES)[
                self.obras_scroll:self.obras_scroll + OBRAS_LINHAS_VISIVEIS
            ]
            for tipo in tipos:
                quantidade = self.reino.quantidade_instancias(tipo)
                sem_mapa = PEGADAS.get(tipo, (0, 0))[0] <= 0
                instancia_unica = (
                    self.reino.primeira_instancia(tipo) if sem_mapa else None
                )
                if instancia_unica is not None:
                    if instancia_unica.nivel >= MAX_NIVEL:
                        rotulo, habilitado, cor = "Máx", False, COR_CINZA_BOTAO
                        acao = lambda: None
                    else:
                        rotulo = "Melhorar"
                        habilitado = self.reino.pode_melhorar(instancia_unica.id)
                        cor = COR_AZUL
                        acao = lambda i=instancia_unica.id: self._melhorar(i)
                else:
                    rotulo = "Construir"
                    habilitado = self.reino.pode_construir_nova(tipo) and (
                        sem_mapa or self._tem_espaco(tipo)
                    )
                    cor = COR_VERDE
                    acao = lambda t=tipo: self._iniciar_construcao(t)
                self._add(
                    986,
                    topo - 32,
                    100,
                    24,
                    rotulo,
                    acao,
                    habilitado=habilitado,
                    cor=cor,
                    tamanho_fonte=8.5,
                )
                topo -= 42

        if self.economia_aberto and self.reino.mercador_dias > 0:
            vendas = [
                ("madeira", 50),
                ("pedra", 30),
                ("ferro", 20),
                ("ouro", 10),
            ]
            for indice, (recurso, quantidade) in enumerate(vendas):
                self._add(
                    ECON_X + 14 + indice * 134,
                    ECON_Y + 28,
                    126,
                    30,
                    f"Vender {quantidade} {ABREVIACOES[recurso]}",
                    lambda r=recurso, q=quantidade: self._vender(r, q),
                    habilitado=self.reino.recursos.get(recurso, 0.0)
                    >= quantidade,
                    cor=COR_DOURADO,
                    tamanho_fonte=8.5,
                )

        self._montar_botoes_contexto()

    def _montar_botoes_contexto(self) -> None:
        if self.reino.derrota:
            return
        if self.predio_sel is not None and self.predio_sel == CASTELO_ID:
            self._add(
                352,
                20,
                90,
                32,
                "Reparar",
                self.reparar_castelo,
                habilitado=self.reino.pode_reparar_castelo(),
                cor=COR_DOURADO,
                tamanho_fonte=9,
            )
            if self.reino.nivel_castelo >= 5:
                rotulo_castelo, habilita_castelo = "Fortaleza", False
            else:
                rotulo_castelo = "Melhorar Castelo"
                habilita_castelo = self.reino.pode_melhorar_castelo()
            self._add(
                448,
                20,
                130,
                32,
                rotulo_castelo,
                self._melhorar_castelo,
                habilitado=habilita_castelo,
                cor=COR_AZUL,
                tamanho_fonte=8.5,
            )
            self._add(
                584,
                20,
                120,
                32,
                "Liberar [U]" if self.reino.toque_de_recolher else "Recolher [U]",
                self._alternar_recolher,
                habilitado=self.reino.toque_disponivel,
                cor=COR_VERMELHO if self.reino.toque_de_recolher else COR_VERDE,
                tamanho_fonte=8.5,
            )
            if self.reino.hp_castelo <= 0:
                self._add(
                    352,
                    58,
                    140,
                    26,
                    "Êxodo",
                    self._exodo,
                    cor=COR_VERDE,
                    tamanho_fonte=9,
                )
            self._add(
                710,
                20,
                60,
                32,
                "Fechar",
                self._limpar_selecao,
                cor=COR_CINZA_BOTAO,
                tamanho_fonte=9,
            )
            return

        if self.predio_sel is not None:
            nome = self.predio_sel
            construcao = self.reino.construcoes.get(nome)
            pos_melhoria = 584
            pos_fechar = 690
            largura_fechar = 80
            if construcao is not None and construcao.nivel > 0:
                tipo = construcao.tipo
                if tipo in TRABALHO_POR_PREDIO:
                    self._add(
                        352,
                        20,
                        130,
                        32,
                        "Enviar ociosos",
                        lambda i=nome: self._enviar_ociosos_predio(i),
                        habilitado=any(
                            c.profissao == "ocioso" for c in self.mundo.cidadaos
                        ),
                        cor=COR_AZUL,
                        tamanho_fonte=8.5,
                    )
                    self._add(
                        488,
                        20,
                        90,
                        32,
                        "Liberar",
                        lambda i=nome: self._liberar_funcionarios(i),
                        habilitado=bool(
                            self.mundo.funcionarios_instancia(nome)
                        ),
                        cor=COR_CINZA_BOTAO,
                        tamanho_fonte=8.5,
                    )
                    if tipo == "posto":
                        self._add(
                            352,
                            58,
                            120,
                            26,
                            "Mover [M]",
                            lambda i=nome: self._iniciar_mover(i),
                            cor=COR_CINZA_BOTAO,
                            tamanho_fonte=8,
                        )
                        if construcao.hp_max > 0:
                            self._add(
                                488,
                                58,
                                90,
                                26,
                                "Reparar",
                                lambda i=nome: self._reparar_estrutura(i),
                                habilitado=self.reino.pode_reparar_instancia(nome),
                                cor=COR_DOURADO,
                                tamanho_fonte=8,
                            )
                elif tipo in TROPAS_POR_PREDIO:
                    classes = TROPAS_POR_PREDIO[tipo]
                    base_tropa = classes[0]
                    self._add(
                        352,
                        20,
                        130,
                        32,
                        f"Treinar {CLASSES_TROPA[base_tropa]['nome']}",
                        lambda c=base_tropa: self._treinar_tropa(c),
                        habilitado=self.mundo.pode_treinar_tropa(base_tropa),
                        cor=COR_VERDE,
                        tamanho_fonte=8.5,
                    )
                    self._add(
                        488,
                        20,
                        90,
                        32,
                        "Mover [M]",
                        lambda i=nome: self._iniciar_mover(i),
                        cor=COR_CINZA_BOTAO,
                        tamanho_fonte=8.5,
                    )
                    for indice, classe_especial in enumerate(classes[1:]):
                        self._add(
                            352 + indice * 130,
                            58,
                            120,
                            26,
                            CLASSES_TROPA[classe_especial]["nome"],
                            lambda c=classe_especial: self._treinar_tropa(c),
                            habilitado=self.mundo.pode_treinar_tropa(
                                classe_especial
                            ),
                            cor=COR_DOURADO,
                            tamanho_fonte=8,
                        )
                else:
                    self._add(
                        352,
                        20,
                        90,
                        32,
                        "Mover [M]",
                        lambda i=nome: self._iniciar_mover(i),
                        cor=COR_CINZA_BOTAO,
                        tamanho_fonte=8.5,
                    )
                    if construcao.hp_max > 0:
                        self._add(
                            448,
                            20,
                            100,
                            32,
                            "Reparar",
                            lambda i=nome: self._reparar_estrutura(i),
                            habilitado=self.reino.pode_reparar_instancia(nome),
                            cor=COR_DOURADO,
                            tamanho_fonte=9,
                        )
                if tipo in TRABALHO_POR_PREDIO or tipo in TROPAS_POR_PREDIO:
                    pos_melhoria = 584
                    pos_fechar = 690
                    largura_fechar = 80
                else:
                    pos_melhoria = 554
                    pos_fechar = 660
                    largura_fechar = 100
                if construcao.nivel >= MAX_NIVEL:
                    rotulo, habilitado = "Máximo", False
                else:
                    rotulo = f"Melhorar Nv {construcao.nivel + 1}"
                    habilitado = self.reino.pode_melhorar(nome)
                self._add(
                    pos_melhoria,
                    20,
                    100,
                    32,
                    rotulo,
                    lambda i=nome: self._melhorar(i),
                    habilitado=habilitado,
                    cor=COR_AZUL,
                    tamanho_fonte=8.5,
                )
            self._add(
                pos_fechar if construcao is not None else 690,
                20,
                largura_fechar if construcao is not None else 80,
                32,
                "Fechar",
                self._limpar_selecao,
                cor=COR_CINZA_BOTAO,
                tamanho_fonte=9.5,
            )
            return

        if self.caravana_sel is not None:
            self._add(
                352,
                20,
                140,
                32,
                "Fundar Posto [F]",
                self._fundar_posto_caravana,
                habilitado=self.mundo.pode_fundar_posto_caravana(
                    self.caravana_sel
                ),
                cor=COR_VERDE,
                tamanho_fonte=9,
            )
            self._add(
                500,
                20,
                110,
                32,
                "Dispensar",
                self._dispensar_caravana,
                cor=COR_DOURADO,
                tamanho_fonte=9.5,
            )
            self._add(
                352,
                58,
                130,
                26,
                "Coletar Posto [X]",
                self._coletar_posto_caravana,
                habilitado=self.mundo.pode_coletar_posto(self.caravana_sel),
                cor=COR_AZUL,
                tamanho_fonte=8.5,
            )
            self._add(
                488,
                58,
                130,
                26,
                "Entregar Reino [Y]",
                self._entregar_caravana,
                habilitado=self.mundo.pode_entregar_caravana(self.caravana_sel),
                cor=COR_VERDE,
                tamanho_fonte=8.5,
            )
            self._add(
                690,
                20,
                80,
                32,
                "Fechar",
                self._limpar_selecao,
                cor=COR_CINZA_BOTAO,
                tamanho_fonte=9.5,
            )
            return

        if self.cidadaos_sel or self.soldados_sel:
            self._add(
                352,
                20,
                100,
                32,
                "Parar",
                self._parar_selecao,
                cor=COR_CINZA_BOTAO,
                tamanho_fonte=9.5,
            )
            self._add(
                458,
                20,
                110,
                32,
                "Caravana [V]",
                self._criar_caravana,
                cor=COR_DOURADO,
                tamanho_fonte=9,
            )
            if self.soldados_sel:
                self._add(
                    574,
                    20,
                    110,
                    32,
                    "Defender castelo",
                    self._defender_castelo,
                    cor=COR_AZUL,
                    tamanho_fonte=8.5,
                )
            if len(self.cidadaos_sel) == 1 and not self.soldados_sel:
                cidadao = self.cidadaos_sel[0]
                pontos = self.mundo.pontos_disponiveis_cidadao(cidadao)
                for indice, (atributo, rotulo) in enumerate(
                    (("vida", "+Vida"), ("eficiencia", "+Efic"), ("velocidade", "+Vel"))
                ):
                    self._add(
                        352 + indice * 76,
                        58,
                        70,
                        26,
                        rotulo,
                        lambda c=cidadao, a=atributo: self._evoluir_cidadao(c, a),
                        habilitado=pontos > 0,
                        cor=COR_VERDE,
                        tamanho_fonte=8.5,
                    )
            if len(self.soldados_sel) == 1 and not self.cidadaos_sel:
                soldado = self.soldados_sel[0]
                pontos = self.mundo.pontos_disponiveis_soldado(soldado)
                for indice, (atributo, rotulo) in enumerate(
                    (("vida", "+Vida"), ("dano", "+Dano"), ("velocidade", "+Vel"))
                ):
                    self._add(
                        352 + indice * 76,
                        58,
                        70,
                        26,
                        rotulo,
                        lambda sold=soldado, a=atributo: self._evoluir_soldado(sold, a),
                        habilitado=pontos > 0,
                        cor=COR_VERDE,
                        tamanho_fonte=8.5,
                    )
            self._add(
                690,
                20,
                80,
                32,
                "Fechar",
                self._limpar_selecao,
                cor=COR_CINZA_BOTAO,
                tamanho_fonte=9.5,
            )
            return

        if self.arvore_sel is not None or self.rocha_sel is not None:
            acao = (
                self._enviar_ociosos_arvore
                if self.arvore_sel is not None
                else self._enviar_ociosos_rocha
            )
            self._add(
                352,
                20,
                150,
                32,
                "Enviar ociosos",
                acao,
                habilitado=any(
                    c.profissao == "ocioso" for c in self.mundo.cidadaos
                ),
                cor=COR_AZUL,
                tamanho_fonte=9,
            )
            self._add(
                664,
                20,
                96,
                32,
                "Fechar",
                self._limpar_selecao,
                cor=COR_CINZA_BOTAO,
                tamanho_fonte=10,
            )

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def _tem_espaco(self, tipo: str) -> bool:
        versao = self.mapa.versao_passabilidade
        if versao != self._espaco_versao:
            self._espaco_cache.clear()
            self._espaco_versao = versao
        if tipo not in self._espaco_cache:
            self._espaco_cache[tipo] = self.mapa.existe_espaco(tipo)
        return self._espaco_cache[tipo]

    def _alternar_pausa(self) -> None:
        if not self.reino.derrota:
            self.reino.pausado = not self.reino.pausado

    def _definir_velocidade(self, velocidade: int) -> None:
        if not self.reino.derrota:
            self.reino.velocidade = velocidade
            self.reino.pausado = False

    def _alternar_ataques(self) -> None:
        self.reino.ataques_ativos = not self.reino.ataques_ativos
        self._mostrar_toast(
            "Ataques ligados." if self.reino.ataques_ativos
            else "Ataques desligados (dificuldade continua escalando).",
            COR_DOURADO,
        )
        self._salvar()

    def _alternar_obras(self) -> None:
        self.obras_aberto = not self.obras_aberto
        if self.obras_aberto:
            self.detalhe_aberto = False
            self.economia_aberto = False
            self._cancelar_modo()
            self.modo_estrada = False
            self._limpar_selecao()

    def _alternar_detalhe(self) -> None:
        self.detalhe_aberto = not self.detalhe_aberto
        if self.detalhe_aberto:
            self.obras_aberto = False
            self.economia_aberto = False
            self._cancelar_modo()
            self.modo_estrada = False
            self._limpar_selecao()

    def _alternar_economia(self) -> None:
        self.economia_aberto = not self.economia_aberto
        if self.economia_aberto:
            self.detalhe_aberto = False
            self.obras_aberto = False
            self._cancelar_modo()
            self.modo_estrada = False
            self._limpar_selecao()

    def _alternar_minimapa(self) -> None:
        self.minimapa_aberto = not self.minimapa_aberto

    def _limpar_selecao(self) -> None:
        self.cidadaos_sel = []
        self.soldados_sel = []
        self.predio_sel = None
        self.arvore_sel = None
        self.rocha_sel = None
        self.caravana_sel = None

    def _selecionar_ociosos(self) -> None:
        self.cidadaos_sel = [
            c
            for c in self.mundo.cidadaos
            if c.profissao == "ocioso" and not c.rei
        ]
        self.soldados_sel = []
        self.predio_sel = None
        self.arvore_sel = None
        if not self.cidadaos_sel:
            self._mostrar_toast("Nenhum cidadão ocioso.", COR_TEXTO_SUAVE)

    def _selecionar_soldados(self) -> None:
        self.soldados_sel = list(self.mundo.soldados)
        self.cidadaos_sel = []
        self.predio_sel = None
        self.arvore_sel = None
        if not self.soldados_sel:
            self._mostrar_toast("Nenhum soldado disponível.", COR_TEXTO_SUAVE)

    def _enviar_ociosos_predio(self, id_predio: int) -> None:
        ociosos = [
            c
            for c in self.mundo.cidadaos
            if c.profissao == "ocioso" and not c.rei
        ]
        if not ociosos:
            self._mostrar_toast("Nenhum cidadão ocioso.", COR_TEXTO_SUAVE)
            return
        mensagem = self.mundo.ordenar_predio(ociosos, id_predio)
        if mensagem:
            self._mostrar_toast(mensagem, COR_DOURADO)

    def _liberar_funcionarios(self, id_predio: int) -> None:
        self.mundo.liberar_instancia(id_predio)
        self._mostrar_toast("Funcionários liberados.", COR_TEXTO_SUAVE)

    def _enviar_ociosos_rocha(self) -> None:
        if self.rocha_sel is None:
            return
        ociosos = [
            c
            for c in self.mundo.cidadaos
            if c.profissao == "ocioso" and not c.rei
        ]
        if not ociosos:
            self._mostrar_toast("Nenhum cidadão ocioso.", COR_TEXTO_SUAVE)
            return
        mensagem = self.mundo.ordenar_rocha(
            ociosos, self.rocha_sel[0], self.rocha_sel[1]
        )
        if mensagem:
            self._mostrar_toast(mensagem, COR_DOURADO)

    def _enviar_ociosos_arvore(self) -> None:
        if self.arvore_sel is None:
            return
        ociosos = [
            c
            for c in self.mundo.cidadaos
            if c.profissao == "ocioso" and not c.rei
        ]
        if not ociosos:
            self._mostrar_toast("Nenhum cidadão ocioso.", COR_TEXTO_SUAVE)
            return
        mensagem = self.mundo.ordenar_arvore(
            ociosos, self.arvore_sel[0], self.arvore_sel[1]
        )
        if mensagem:
            self._mostrar_toast(mensagem, COR_DOURADO)

    def _criar_caravana(self) -> None:
        ok, mensagem, caravana = self.mundo.criar_caravana(
            list(self.cidadaos_sel), list(self.soldados_sel)
        )
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
            return
        self._limpar_selecao()
        self.caravana_sel = caravana
        self._mostrar_toast(
            f"Caravana #{caravana.id} criada. Botão direito move; "
            "revela a névoa.",
            COR_VERDE,
        )
        self._salvar()

    def _fundar_posto_caravana(self) -> None:
        if self.caravana_sel is None:
            return
        ok, mensagem = self.mundo.fundar_posto_caravana(self.caravana_sel)
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._mostrar_toast("Posto avançado fundado.", COR_VERDE)
            self._salvar()

    def _coletar_posto_caravana(self) -> None:
        if self.caravana_sel is None:
            return
        ok, mensagem = self.mundo.coletar_posto_caravana(self.caravana_sel)
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._mostrar_toast("Recursos recolhidos do posto.", COR_AZUL)
            self._salvar()

    def _entregar_caravana(self) -> None:
        if self.caravana_sel is None:
            return
        ok, mensagem = self.mundo.entregar_caravana(self.caravana_sel)
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._mostrar_toast("Recursos entregues ao reino.", COR_VERDE)
            self._salvar()

    def _dispensar_caravana(self) -> None:
        if self.caravana_sel is None:
            return
        self.mundo.dispensar_caravana(self.caravana_sel)
        self.caravana_sel = None
        self._mostrar_toast("Caravana dispensada.", COR_TEXTO_SUAVE)
        self._salvar()

    def _melhorar_castelo(self) -> None:
        ok, mensagem = self.reino.melhorar_castelo()
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._mostrar_toast(
                f"Castelo agora é nível {self.reino.nivel_castelo}.",
                COR_VERDE,
            )
            self._salvar()

    def _alternar_recolher(self) -> None:
        if not self.reino.toque_disponivel:
            self._mostrar_toast(
                "Toque de recolher libera no castelo nível 3 (Solar).",
                COR_VERMELHO,
            )
            return
        self.reino.toque_de_recolher = not self.reino.toque_de_recolher
        self._mostrar_toast(
            "Toque de recolher ativado: civis se escondem."
            if self.reino.toque_de_recolher
            else "Toque de recolher encerrado: civis voltam ao trabalho.",
            COR_DOURADO,
        )
        self._salvar()

    def _exodo(self) -> None:
        reino_antigo = self.reino
        king = next(
            (c for c in self.mundo.cidadaos if c.rei), None
        )
        subjects = [c for c in self.mundo.cidadaos if not c.rei]
        for caravana in self.mundo.caravanas:
            for membro in caravana.membros:
                if isinstance(membro, Soldado):
                    self.mundo.soldados.append(membro)
                else:
                    subjects.append(membro)
        soldados = list(self.mundo.soldados)

        novo_reino = Reino()
        novo_reino.castelos_perdidos = reino_antigo.castelos_perdidos + 1
        novo_reino.melhor_periodo = max(
            reino_antigo.melhor_periodo, reino_antigo.dia
        )
        novo_reino.recorde_dias = max(
            reino_antigo.recorde_dias, reino_antigo.dia
        )
        novo_reino.ataques_ativos = reino_antigo.ataques_ativos
        novo_reino.populacao = 1 + len(subjects) + len(soldados)
        for recurso, valor in reino_antigo.recursos.items():
            if recurso == "troncos":
                novo_reino.recursos[recurso] = 0.0
            elif recurso == "alimento":
                novo_reino.recursos[recurso] = min(
                    novo_reino.capacidade_alimento, valor * 0.25
                )
            else:
                novo_reino.recursos[recurso] = valor * 0.25

        novo_mapa = Mapa()
        novo_mundo = Mundo(novo_reino, novo_mapa)
        novo_mundo.cidadaos = []
        novo_mundo.soldados = []
        novo_mundo.caravanas = []
        if king is None:
            king = Cidadao(id=1, x=0, y=0, rei=True)
        kx, ky = novo_mundo._ponto_livre(CASTELO_ID)
        king.x, king.y = kx, ky
        king.estado = "ocioso"
        king.profissao = "ocioso"
        king.caminho = []
        king.alvo_predio = None
        king.alvo_arvore = None
        king.alvo_rocha = None
        king.hp = king.hp_max
        novo_mundo.cidadaos.append(king)
        for membro in subjects:
            x, y = novo_mundo._ponto_livre(CASTELO_ID)
            membro.x, membro.y = x, y
            membro.estado = "ocioso"
            membro.profissao = "ocioso"
            membro.caminho = []
            membro.alvo_predio = None
            membro.alvo_arvore = None
            membro.alvo_rocha = None
            membro.hp = membro.hp_max
            novo_mundo.cidadaos.append(membro)
        for soldado in soldados:
            x, y = novo_mundo._ponto_livre(CASTELO_ID)
            soldado.x, soldado.y = x, y
            soldado.caminho = []
            soldado.alvo = None
            soldado.ordem_ataque = False
            soldado.hp = soldado.hp_max
            soldado.poste = (x, y)
            novo_mundo.soldados.append(soldado)
        novo_mundo._sincronizar()

        self.reino = novo_reino
        self.mapa = novo_mapa
        self.mundo = novo_mundo
        self._dia_salvo = self.reino.dia
        self._limpar_selecao()
        self._cancelar_modo()
        self.economia_aberto = False
        self.detalhe_aberto = False
        self.obras_aberto = False
        self._espaco_cache.clear()
        self._espaco_versao = -1
        self._terreno_chunks.clear()
        self._arvores_chunks.clear()
        self._rochas_chunks.clear()
        self._mini_versao = -1
        self._centralizar()
        self._mostrar_toast(
            "Êxodo! O Rei e seus súditos recomeçam em uma nova região.",
            COR_DOURADO,
        )
        self._salvar()

    def _evoluir_cidadao(self, cidadao, atributo: str) -> None:
        ok = self.mundo.evoluir_cidadao(cidadao, atributo)
        if not ok:
            self._mostrar_toast("Sem pontos de evolução.", COR_VERMELHO)
        else:
            self._salvar()

    def _evoluir_soldado(self, soldado, atributo: str) -> None:
        ok = self.mundo.evoluir_soldado(soldado, atributo)
        if not ok:
            self._mostrar_toast("Sem pontos de evolução.", COR_VERMELHO)
        else:
            self._salvar()

    def _parar_selecao(self) -> None:
        self.mundo.ordenar_parar(self.cidadaos_sel)
        for soldado in self.soldados_sel:
            soldado.caminho = []
            soldado.alvo = None
            soldado.ordem_ataque = False

    def _defender_castelo(self) -> None:
        x, y = self.mapa.centro_mundo(CASTELO_ID)
        self.mundo.ordenar_soldados_mover(self.soldados_sel, x, y)

    def _treinar_soldado(self) -> None:
        ok, mensagem = self.mundo.treinar_soldado()
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._salvar()

    def _treinar_tropa(self, classe: str) -> None:
        ok, mensagem = self.mundo.treinar_tropa(classe)
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._salvar()

    def _treinar_arqueiro(self) -> None:
        self._treinar_tropa("arqueiro")

    def reparar_castelo(self) -> None:
        ok, mensagem = self.reino.reparar_castelo()
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._salvar()

    def _iniciar_construcao(self, tipo: str) -> None:
        if PEGADAS.get(tipo, (0, 0))[0] <= 0:
            ok, mensagem, id_instancia = self.reino.adicionar_instancia(tipo)
            if not ok:
                self._mostrar_toast(mensagem, COR_VERMELHO)
            else:
                self._mostrar_toast(
                    f"{NOMES_CONSTRUCOES[tipo]} construída (#{id_instancia}).",
                    COR_VERDE,
                )
                self._salvar()
            return
        if not self.reino.pode_construir_nova(tipo):
            self._mostrar_toast("Recursos insuficientes.", COR_VERMELHO)
            return
        if not self._tem_espaco(tipo):
            self._mostrar_toast("Não há espaço construível no reino.", COR_VERMELHO)
            return
        self.modo_posicionamento = tipo
        self.id_movendo = None
        self.obras_aberto = False
        self._limpar_selecao()
        self._mostrar_toast(
            f"Posicione {NOMES_CONSTRUCOES[tipo]}: clique no mapa "
            "(botão direito cancela).",
            COR_AZUL,
        )

    def _melhorar(self, id_instancia: int) -> None:
        construcao = self.reino.construcoes.get(id_instancia)
        if construcao is None:
            return
        ok, mensagem = self.reino.melhorar_instancia(id_instancia)
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
            return
        self.predio_sel = (
            id_instancia
            if id_instancia in self.mapa.posicoes and not self.obras_aberto
            else None
        )
        self.cidadaos_sel = []
        self.soldados_sel = []
        self.arvore_sel = None
        self.rocha_sel = None
        self._mostrar_toast(
            f"{NOMES_CONSTRUCOES[construcao.tipo]} #{id_instancia} "
            f"agora está no nível {construcao.nivel}.",
            COR_VERDE,
        )
        self._salvar()

    def _iniciar_mover(self, id_instancia: int) -> None:
        construcao = self.reino.construcoes.get(id_instancia)
        if construcao is None or id_instancia not in self.mapa.posicoes:
            return
        self.modo_posicionamento = construcao.tipo
        self.id_movendo = id_instancia
        self.obras_aberto = False
        self.detalhe_aberto = False
        self._mostrar_toast(
            f"Mover {NOMES_CONSTRUCOES[construcao.tipo]} #{id_instancia}: "
            "clique no novo local.",
            COR_AZUL,
        )

    def _reparar_estrutura(self, id_instancia: int) -> None:
        ok, mensagem = self.reino.reparar_instancia(id_instancia)
        if not ok:
            self._mostrar_toast(mensagem, COR_VERMELHO)
        else:
            self._salvar()

    def _cancelar_modo(self) -> None:
        self.modo_posicionamento = None
        self.id_movendo = None

    def _colocar_estrada(self) -> None:
        mundo_x, mundo_y = self._mundo_do_mouse()
        col, row = self.mapa.tile_do_mundo(mundo_x, mundo_y)
        if self.mapa.tem_estrada(col, row):
            return
        if not self.mapa.pode_construir_estrada(col, row):
            return
        custo = {"madeira": 2.0, "pedra": 1.0}
        if not self.reino.pode_pagar(custo):
            self._mostrar_toast("Recursos insuficientes para estrada.", COR_VERMELHO)
            return
        for recurso, quantidade in custo.items():
            self.reino.recursos[recurso] -= quantidade
        self.mapa.construir_estrada(col, row)
        chunk = (col // TAMANHO_CHUNK, row // TAMANHO_CHUNK)
        self._terreno_chunks.pop(chunk, None)
        self._salvar()

    def _confirmar_posicionamento(self) -> None:
        tipo = self.modo_posicionamento
        if tipo is None:
            return
        anchor = self._anchor_posicionamento()
        if anchor is None:
            return
        col, row = anchor
        bloqueios = self.mundo.tiles_ocupados_unidades()
        if self.id_movendo is not None:
            id_movendo = self.id_movendo
            construcao = self.reino.construcoes.get(id_movendo)
            if construcao is None or id_movendo not in self.mapa.posicoes:
                self._cancelar_modo()
                return
            if not self.mapa.pode_posicionar(
                tipo, col, row, bloqueios, ignorar_id=id_movendo
            ):
                self._mostrar_toast(
                    "Local inválido para mover a estrutura.", COR_VERMELHO
                )
                return
            antigo = self.mapa.posicoes[id_movendo]
            self.mapa.remover(id_movendo)
            if not self.mapa.posicionar(
                id_movendo, tipo, col, row, bloqueios
            ):
                self.mapa.posicionar(id_movendo, tipo, antigo[0], antigo[1])
                self._mostrar_toast(
                    "Não foi possível mover a estrutura.", COR_VERMELHO
                )
                return
            self.mundo.reposicionar_funcionarios(id_movendo)
            self.mundo.revelar_construcao(
                id_movendo, raio_extra=2 if tipo == "posto" else 0
            )
            self._cancelar_modo()
            self.predio_sel = id_movendo
            self._mostrar_toast(
                f"{NOMES_CONSTRUCOES[tipo]} #{id_movendo} movida.",
                COR_VERDE,
            )
            self._salvar()
            return
        if not self.mapa.pode_posicionar(tipo, col, row, bloqueios):
            self._mostrar_toast(
                "Local inválido: terreno livre, sem unidades, dentro do reino.",
                COR_VERMELHO,
            )
            return
        custo = self.reino.custo_nova_instancia(tipo)
        ok, mensagem, id_instancia = self.reino.adicionar_instancia(tipo)
        if not ok or id_instancia is None:
            self._mostrar_toast(mensagem, COR_VERMELHO)
            return
        if not self.mapa.posicionar(id_instancia, tipo, col, row, bloqueios):
            self.reino.remover_instancia(id_instancia)
            for recurso, quantidade in custo.items():
                self.reino.recursos[recurso] += quantidade
            self._mostrar_toast("Não foi possível posicionar.", COR_VERMELHO)
            return
        self.modo_posicionamento = None
        self.mundo.revelar_construcao(
            id_instancia, raio_extra=2 if tipo == "posto" else 0
        )
        self.predio_sel = id_instancia
        self.cidadaos_sel = []
        self.soldados_sel = []
        self.arvore_sel = None
        self.rocha_sel = None
        self._mostrar_toast(
            f"{NOMES_CONSTRUCOES[tipo]} construída (#{id_instancia}).",
            COR_VERDE,
        )
        self._salvar()

    # ------------------------------------------------------------------
    # Seleção e ordens
    # ------------------------------------------------------------------
    def _clicar_mapa(self) -> None:
        mundo_x, mundo_y = self._mundo_do_mouse()
        caravana = self.mundo.caravana_em_ponto(mundo_x, mundo_y)
        if caravana is not None:
            self._limpar_selecao()
            self.caravana_sel = caravana
            return
        soldado = self.mundo.soldado_em_ponto(mundo_x, mundo_y)
        if soldado is not None:
            self.predio_sel = None
            self.arvore_sel = None
            self.rocha_sel = None
            self.caravana_sel = None
            self.cidadaos_sel = []
            if soldado not in self.soldados_sel:
                self.soldados_sel.append(soldado)
            return
        cidadao = self.mundo.cidadao_em_ponto(mundo_x, mundo_y)
        if cidadao is not None:
            self.predio_sel = None
            self.arvore_sel = None
            self.rocha_sel = None
            self.caravana_sel = None
            self.soldados_sel = []
            if cidadao not in self.cidadaos_sel:
                self.cidadaos_sel.append(cidadao)
            return
        arvore = self.mundo.arvore_em_ponto(mundo_x, mundo_y)
        if arvore is not None:
            self._limpar_selecao()
            self.arvore_sel = (arvore.col, arvore.row)
            return
        rocha = self.mundo.rocha_em_ponto(mundo_x, mundo_y)
        if rocha is not None:
            self._limpar_selecao()
            self.rocha_sel = (rocha.col, rocha.row)
            return
        id_predio = self.mapa.construcao_no_ponto(mundo_x, mundo_y)
        if id_predio is not None:
            self._limpar_selecao()
            self.predio_sel = id_predio
            return
        self._limpar_selecao()

    def _caixa_selecao(self) -> None:
        if self._caixa_inicio is None or self._caixa_atual is None:
            return
        p1 = self.camera.unproject(self._caixa_inicio)
        p2 = self.camera.unproject(self._caixa_atual)
        unidades = self.mundo.unidades_no_rect(p1.x, p1.y, p2.x, p2.y)
        self.cidadaos_sel = [u for u in unidades if isinstance(u, Cidadao)]
        self.soldados_sel = [u for u in unidades if isinstance(u, Soldado)]
        self.predio_sel = None
        self.arvore_sel = None
        self.rocha_sel = None
        self.caravana_sel = None
        self.caravana_sel = None

    def _ordenar(self) -> None:
        if self.caravana_sel is not None:
            mundo_x, mundo_y = self._mundo_do_mouse()
            mensagem = self.mundo.ordenar_caravana_mover(
                self.caravana_sel, mundo_x, mundo_y
            )
            self._marcador = (mundo_x, mundo_y, 0.7)
            if mensagem:
                self._mostrar_toast(mensagem, COR_DOURADO)
            return
        if not (self.cidadaos_sel or self.soldados_sel):
            self._mostrar_toast(
                "Selecione cidadãos ou soldados antes de dar ordens.",
                COR_TEXTO_SUAVE,
            )
            return
        mundo_x, mundo_y = self._mundo_do_mouse()
        inimigo = self.mundo.inimigo_em_ponto(mundo_x, mundo_y)
        arvore = self.mundo.arvore_em_ponto(mundo_x, mundo_y)
        rocha = self.mundo.rocha_em_ponto(mundo_x, mundo_y)
        predio = self.mapa.construcao_no_ponto(mundo_x, mundo_y)
        mensagem = None

        if inimigo is not None:
            if self.soldados_sel:
                self.mundo.ordenar_soldados_atacar(self.soldados_sel, inimigo)
                self._marcador = (inimigo.x, inimigo.y, 0.7)
            else:
                mensagem = "Somente soldados podem atacar."
            if mensagem:
                self._mostrar_toast(mensagem, COR_VERMELHO)
            return

        if self.cidadaos_sel:
            if arvore is not None:
                mensagem = self.mundo.ordenar_arvore(
                    self.cidadaos_sel, arvore.col, arvore.row
                )
            elif rocha is not None:
                mensagem = self.mundo.ordenar_rocha(
                    self.cidadaos_sel, rocha.col, rocha.row
                )
            elif predio is not None and predio != CASTELO_ID:
                mensagem = self.mundo.ordenar_predio(self.cidadaos_sel, predio)
            elif (
                self.mapa.tipo_tile(
                    *self.mapa.tile_do_mundo(mundo_x, mundo_y)
                )
                == AGUA
            ):
                col, row = self.mapa.tile_do_mundo(mundo_x, mundo_y)
                mensagem = self.mundo.ordenar_pesca(
                    self.cidadaos_sel, col, row
                )
            else:
                mensagem = self.mundo.ordenar_mover(
                    self.cidadaos_sel, mundo_x, mundo_y
                )

        if self.soldados_sel:
            if predio is not None:
                px, py = self.mapa.centro_mundo(predio)
                self.mundo.ordenar_soldados_mover(self.soldados_sel, px, py)
            else:
                self.mundo.ordenar_soldados_mover(
                    self.soldados_sel, mundo_x, mundo_y
                )

        self._marcador = (mundo_x, mundo_y, 0.7)
        if mensagem:
            self._mostrar_toast(mensagem, COR_DOURADO)

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------
    def on_draw(self) -> None:
        self.clear()
        self.camera.use()
        self._desenhar_mundo()
        self._desenhar_nevoa()
        self.default_camera.use()

        self._desenhar_noite()
        self._desenhar_caixa()
        self._desenhar_minimapa()
        self._desenhar_indicador_horda()
        self._desenhar_topo()
        if self.detalhe_aberto:
            self._desenhar_detalhe()
        if self.obras_aberto:
            self._desenhar_obras()
        if self.economia_aberto:
            self._desenhar_economia()
        self._desenhar_contexto()
        if self.toast_timer > 0 and not self.reino.derrota:
            self._desenhar_toast()
        tem_contexto = bool(
            self.cidadaos_sel or self.soldados_sel or self.predio_sel or self.arvore_sel or self.rocha_sel or self.caravana_sel is not None
        )
        if (
            not self.detalhe_aberto
            and not self.obras_aberto
            and not tem_contexto
            and not self.reino.derrota
        ):
            self.texto(
                "dica_global",
                "Tab detalhes · B obras · O ociosos · G soldados · "
                "V caravana · M mover · E economia · N minimapa · P estrada · "
                "X/Y entrega · U recolher · arraste seleciona · direito ordena",
                10,
                10,
                8.5,
                (120, 128, 140),
            )
        if self.reino.derrota:
            self._desenhar_derrota()

        self._desenhar_botoes()

    # ------------------------------------------------------------------
    # Mundo
    # ------------------------------------------------------------------
    def _limites_visiveis(self) -> tuple[float, float, float, float]:
        pos = self.camera.position
        meia_w = LARGURA / (2 * self.zoom)
        meia_h = ALTURA / (2 * self.zoom)
        return (
            pos.x - meia_w,
            pos.x + meia_w,
            pos.y - meia_h,
            pos.y + meia_h,
        )

    def _criar_chunk_terreno(self, cx: int, cy: int) -> ShapeElementList:
        formas = ShapeElementList()
        col0 = cx * TAMANHO_CHUNK
        row0 = cy * TAMANHO_CHUNK
        col1 = min(COLUNAS, col0 + TAMANHO_CHUNK)
        row1 = min(LINHAS, row0 + TAMANHO_CHUNK)
        for row in range(row0, row1):
            for col in range(col0, col1):
                tipo = self.mapa.tiles[row][col]
                x = col * TILE
                y = row * TILE
                variacao = (col * 7 + row * 13) % 3

                if tipo == AGUA:
                    cor = (48, 88, 132) if variacao else (54, 96, 144)
                elif tipo == ESTRADA:
                    cor = (116, 98, 76)
                elif tipo == TERRA:
                    cor = (124, 102, 74) if variacao else (132, 110, 80)
                else:
                    cor = (70, 104, 66) if variacao else (76, 112, 70)

                formas.append(
                    create_rectangle_filled(
                        x + TILE / 2, y + TILE / 2, TILE, TILE, (*cor, 255)
                    )
                )

                if tipo == AGUA:
                    if variacao == 0:
                        formas.append(
                            create_line(
                                x + 10,
                                y + 20,
                                x + TILE - 10,
                                y + 20,
                                (88, 132, 178, 255),
                                2,
                            )
                        )
                elif tipo == GRAMA and variacao == 0:
                    formas.append(
                        create_ellipse_filled(
                            x + TILE / 2, y + TILE / 2, 10, 10, (62, 96, 60, 255)
                        )
                    )
        return formas

    def _criar_chunk_arvores(self, cx: int, cy: int) -> ShapeElementList:
        formas = ShapeElementList()
        col0 = cx * TAMANHO_CHUNK
        row0 = cy * TAMANHO_CHUNK
        col1 = col0 + TAMANHO_CHUNK
        row1 = row0 + TAMANHO_CHUNK
        for (col, row), arvore in self.mundo.arvores.items():
            if not (col0 <= col < col1 and row0 <= row < row1):
                continue
            x = col * TILE + TILE / 2
            y = row * TILE + TILE / 2
            if arvore.estado == "adulta":
                variacao = (col * 5 + row * 11) % 3
                cor_copa = (
                    (44, 88, 50, 255)
                    if variacao == 0
                    else (54, 102, 58, 255)
                    if variacao == 1
                    else (64, 112, 62, 255)
                )
                formas.append(
                    create_rectangle_filled(x, y - 10, 10, 28, (92, 66, 42, 255))
                )
                formas.append(create_ellipse_filled(x, y + 6, 50, 50, cor_copa))
                formas.append(create_ellipse_filled(x - 14, y - 2, 32, 32, cor_copa))
                formas.append(create_ellipse_filled(x + 14, y - 2, 32, 32, cor_copa))
                formas.append(
                    create_ellipse_filled(x - 4, y + 14, 30, 30, (78, 126, 74, 255))
                )
            else:
                formas.append(
                    create_ellipse_filled(x, y - 10, 20, 14, (104, 74, 46, 255))
                )
        return formas

    def _desenhar_mundo(self) -> None:
        esquerda, direita, baixo, cima = self._limites_visiveis()
        for chunk in self.mapa.chunks_visiveis(esquerda, direita, baixo, cima):
            if chunk not in self._terreno_chunks:
                self._terreno_chunks[chunk] = self._criar_chunk_terreno(*chunk)
            self._terreno_chunks[chunk].draw()
        arcade.draw_lbwh_rectangle_outline(
            0, 0, LARGURA_MUNDO, ALTURA_MUNDO, (10, 12, 16), 4
        )
        self._desenhar_arvores()
        self._desenhar_rochas()
        self._desenhar_predios()
        self._desenhar_unidades()
        self._desenhar_tiros_postos()
        self._desenhar_caravanas()
        self._desenhar_fantasma()
        self._desenhar_marcador()

    def _desenhar_arvores(self) -> None:
        esquerda, direita, baixo, cima = self._limites_visiveis()
        for chunk in self.mapa.chunks_visiveis(esquerda, direita, baixo, cima):
            if chunk not in self._arvores_chunks:
                self._arvores_chunks[chunk] = self._criar_chunk_arvores(*chunk)
            self._arvores_chunks[chunk].draw()
        for (col, row), arvore in self.mundo.arvores.items():
            if arvore.estado != "adulta":
                continue
            if arvore.vida < arvore.vida_max or self.arvore_sel == (col, row):
                x = col * TILE + TILE / 2
                y = row * TILE + TILE / 2
                self._barra_hp(
                    x, y + 34, 32, arvore.vida / max(1, arvore.vida_max), COR_VERDE
                )
        if self.arvore_sel is not None and self.arvore_sel in self.mundo.arvores:
            col, row = self.arvore_sel
            x = col * TILE + TILE / 2
            y = row * TILE + TILE / 2
            arcade.draw_circle_outline(x, y, 30, (240, 204, 90), 3)

    def _criar_chunk_rochas(self, cx: int, cy: int) -> ShapeElementList:
        formas = ShapeElementList()
        col0 = cx * TAMANHO_CHUNK
        row0 = cy * TAMANHO_CHUNK
        col1 = col0 + TAMANHO_CHUNK
        row1 = row0 + TAMANHO_CHUNK
        for (col, row), rocha in self.mundo.rochas.items():
            if not (col0 <= col < col1 and row0 <= row < row1):
                continue
            x = col * TILE + TILE / 2
            y = row * TILE + TILE / 2
            if rocha.estado == "adulta":
                variacao = (col * 13 + row * 7) % 3
                cor = (118, 120, 126, 255) if variacao else (104, 106, 112, 255)
                formas.append(create_ellipse_filled(x, y - 6, 46, 34, cor))
                formas.append(
                    create_ellipse_filled(x - 12, y + 4, 28, 24, (132, 134, 140, 255))
                )
                formas.append(create_ellipse_filled(x + 14, y - 2, 22, 18, cor))
            else:
                formas.append(
                    create_ellipse_filled(x, y - 12, 16, 8, (92, 94, 100, 255))
                )
                formas.append(
                    create_ellipse_filled(x + 10, y - 8, 8, 5, (80, 82, 88, 255))
                )
        return formas

    def _desenhar_rochas(self) -> None:
        esquerda, direita, baixo, cima = self._limites_visiveis()
        for chunk in self.mapa.chunks_visiveis(esquerda, direita, baixo, cima):
            if chunk not in self._rochas_chunks:
                self._rochas_chunks[chunk] = self._criar_chunk_rochas(*chunk)
            self._rochas_chunks[chunk].draw()
        for (col, row), rocha in self.mundo.rochas.items():
            x = col * TILE + TILE / 2
            y = row * TILE + TILE / 2
            if rocha.estado == "adulta" and (
                rocha.vida < rocha.vida_max or self.rocha_sel == (col, row)
            ):
                self._barra_hp(
                    x, y + 28, 32, rocha.vida / max(1, rocha.vida_max), (170, 172, 178)
                )
            if self.rocha_sel == (col, row):
                arcade.draw_circle_outline(x, y, 30, (240, 204, 90), 3)

    def _desenhar_caravanas(self) -> None:
        for caravana in self.mundo.caravanas:
            arcade.draw_ellipse_filled(
                caravana.x, caravana.y - 8, 34, 12, (12, 14, 18, 140)
            )
            arcade.draw_lbwh_rectangle_filled(
                caravana.x - 14, caravana.y - 8, 28, 16, (126, 88, 48)
            )
            arcade.draw_lbwh_rectangle_outline(
                caravana.x - 14, caravana.y - 8, 28, 16, (58, 40, 24), 2
            )
            arcade.draw_circle_filled(
                caravana.x - 9, caravana.y - 8, 5, (58, 48, 38)
            )
            arcade.draw_circle_filled(
                caravana.x + 9, caravana.y - 8, 5, (58, 48, 38)
            )
            arcade.draw_lbwh_rectangle_filled(
                caravana.x - 5, caravana.y + 6, 10, 7, (170, 126, 72)
            )
            for indice, membro in enumerate(caravana.membros[:5]):
                angulo = indice * 1.2
                mx = caravana.x + math.cos(angulo) * 20
                my = caravana.y + math.sin(angulo) * 12
                if isinstance(membro, Soldado):
                    cor = (
                        (110, 180, 120)
                        if membro.classe == "arqueiro"
                        else (90, 150, 220)
                    )
                else:
                    cor = (200, 205, 215)
                arcade.draw_circle_filled(mx, my, 3, cor)
            if self.caravana_sel is caravana:
                arcade.draw_circle_outline(
                    caravana.x, caravana.y, 26, (240, 204, 90), 3
                )

    def _desenhar_nevoa(self) -> None:
        esquerda, direita, baixo, cima = self._limites_visiveis()
        tamanho = TAMANHO_CHUNK * TILE
        for cx, cy in self.mapa.chunks_visiveis(esquerda, direita, baixo, cima):
            if (cx, cy) not in self.mundo.fog:
                continue
            x = cx * tamanho
            y = cy * tamanho
            largura = min(tamanho, LARGURA_MUNDO - x)
            altura = min(tamanho, ALTURA_MUNDO - y)
            arcade.draw_lbwh_rectangle_filled(
                x, y, largura, altura, (12, 16, 24, 238)
            )
            for indice in range(4):
                ox = ((cx * 37 + cy * 17 + indice * 53) % 100) / 100
                oy = ((cx * 19 + cy * 41 + indice * 71) % 100) / 100
                raio = 24 + ((indice * 13 + cx + cy) % 18)
                arcade.draw_circle_filled(
                    x + ox * largura,
                    y + oy * altura,
                    raio,
                    (30, 36, 48, 220),
                )

    # ------------------------------------------------------------------
    # Minimapa
    # ------------------------------------------------------------------
    def _desenhar_noite(self) -> None:
        if self.reino.derrota:
            return
        fracao = self.reino.tempo_dia / DIA_SEGUNDOS
        if fracao < 0.5:
            return
        intensidade = min(1.0, (fracao - 0.5) / 0.4)
        alpha = int(130 * intensidade)
        if alpha <= 0:
            return
        arcade.draw_lbwh_rectangle_filled(
            0, 0, LARGURA, ALTURA, (18, 26, 58, alpha)
        )
        arcade.draw_circle_filled(
            LARGURA - 70, ALTURA - 80, 18, (220, 220, 190, 200)
        )

    def _minimapa_visivel(self) -> bool:
        return self.minimapa_aberto and not (
            self.detalhe_aberto
            or self.obras_aberto
            or self.economia_aberto
            or self.reino.derrota
        )

    def _ponto_minimapa(self, x: float, y: float) -> tuple[float, float]:
        return (
            MINI_X + (x / LARGURA_MUNDO) * MINI_W,
            MINI_Y + MINI_H - (y / ALTURA_MUNDO) * MINI_H,
        )

    def _mundo_do_minimapa(self, mx: float, my: float) -> tuple[float, float]:
        return (
            (mx - MINI_X) / MINI_W * LARGURA_MUNDO,
            (MINI_Y + MINI_H - my) / MINI_H * ALTURA_MUNDO,
        )

    def _cor_chunk_minimapa(self, cx: int, cy: int) -> tuple[int, int, int]:
        versao = self.mapa.versao_passabilidade
        if getattr(self, "_mini_versao", -1) != versao:
            self._mini_cores = {}
            self._mini_versao = versao
        chave = (cx, cy)
        if chave in self._mini_cores:
            return self._mini_cores[chave]
        total_r = total_g = total_b = total = 0
        col0 = cx * TAMANHO_CHUNK
        row0 = cy * TAMANHO_CHUNK
        for row in range(row0, min(LINHAS, row0 + TAMANHO_CHUNK)):
            for col in range(col0, min(COLUNAS, col0 + TAMANHO_CHUNK)):
                tipo = self.mapa.tiles[row][col]
                if tipo == AGUA:
                    cor = (48, 88, 132)
                elif tipo == ESTRADA:
                    cor = (116, 98, 76)
                elif tipo == TERRA:
                    cor = (124, 102, 74)
                elif tipo == ROCHA:
                    cor = (108, 110, 114)
                else:
                    cor = (74, 108, 70)
                total_r += cor[0]
                total_g += cor[1]
                total_b += cor[2]
                total += 1
        if total <= 0:
            cor_media = (40, 44, 52)
        else:
            cor_media = (
                total_r // total,
                total_g // total,
                total_b // total,
            )
        self._mini_cores[chave] = cor_media
        return cor_media

    def _desenhar_minimapa(self) -> None:
        if not self._minimapa_visivel():
            return
        arcade.draw_lbwh_rectangle_filled(
            MINI_X, MINI_Y, MINI_W, MINI_H, (16, 20, 28, 235)
        )
        arcade.draw_lbwh_rectangle_outline(
            MINI_X, MINI_Y, MINI_W, MINI_H, COR_BORDA, 1
        )
        largura_chunk = MINI_W * TAMANHO_CHUNK / COLUNAS
        altura_chunk = MINI_H * TAMANHO_CHUNK / LINHAS
        for cx in range(COLUNAS // TAMANHO_CHUNK):
            for cy in range(LINHAS // TAMANHO_CHUNK):
                if (cx, cy) in self.mundo.fog:
                    continue
                cor = self._cor_chunk_minimapa(cx, cy)
                mx, my = self._ponto_minimapa(
                    cx * TAMANHO_CHUNK * TILE,
                    (cy + 1) * TAMANHO_CHUNK * TILE,
                )
                arcade.draw_lbwh_rectangle_filled(
                    mx, my, largura_chunk, altura_chunk, cor
                )
        for id_instancia, pos in self.mapa.posicoes.items():
            if id_instancia == CASTELO_ID:
                cor = (240, 204, 90)
                raio = 3
            else:
                chunk = (pos[0] // TAMANHO_CHUNK, pos[1] // TAMANHO_CHUNK)
                if chunk in self.mundo.fog:
                    continue
                tipo = self.mapa.tipos.get(id_instancia)
                cor = (120, 200, 240) if tipo == "posto" else (210, 210, 210)
                raio = 2
            px, py = self.mapa.centro_mundo(id_instancia)
            mx, my = self._ponto_minimapa(px, py)
            arcade.draw_circle_filled(mx, my, raio, cor)
        for caravana in self.mundo.caravanas:
            mx, my = self._ponto_minimapa(caravana.x, caravana.y)
            arcade.draw_circle_filled(mx, my, 3, (200, 150, 80))
        for inimigo in self.mundo.inimigos:
            col, row = self.mapa.tile_do_mundo(inimigo.x, inimigo.y)
            if (col // TAMANHO_CHUNK, row // TAMANHO_CHUNK) in self.mundo.fog:
                continue
            mx, my = self._ponto_minimapa(inimigo.x, inimigo.y)
            arcade.draw_circle_filled(mx, my, 2, (226, 92, 92))
        for inimigo in self.mundo.errantes:
            col, row = self.mapa.tile_do_mundo(inimigo.x, inimigo.y)
            if (col // TAMANHO_CHUNK, row // TAMANHO_CHUNK) in self.mundo.fog:
                continue
            mx, my = self._ponto_minimapa(inimigo.x, inimigo.y)
            arcade.draw_circle_filled(mx, my, 2, (180, 100, 200))
        pos = self.camera.position
        meia_w = LARGURA / (2 * self.zoom)
        meia_h = ALTURA / (2 * self.zoom)
        esq = max(0.0, pos.x - meia_w)
        dir_ = min(LARGURA_MUNDO, pos.x + meia_w)
        baixo = max(0.0, pos.y - meia_h)
        cima = min(ALTURA_MUNDO, pos.y + meia_h)
        x1, y1 = self._ponto_minimapa(esq, cima)
        x2, y2 = self._ponto_minimapa(dir_, baixo)
        arcade.draw_lbwh_rectangle_outline(
            x1, y1, max(2, x2 - x1), max(2, y2 - y1), (240, 240, 240), 1
        )
        self.texto(
            "mini_dica",
            "N minimapa",
            MINI_X + 6,
            MINI_Y + MINI_H - 10,
            7.5,
            (170, 178, 190),
        )

    # ------------------------------------------------------------------
    # Economia
    # ------------------------------------------------------------------
    def _vender(self, recurso: str, quantidade: float) -> None:
        ok, mensagem = self.reino.vender_recurso(recurso, quantidade)
        if ok:
            self._mostrar_toast(
                f"Vendeu {fmt(quantidade)} {NOMES_RECURSOS.get(recurso, recurso)}.",
                COR_DOURADO,
            )
            self._salvar()
        else:
            self._mostrar_toast(mensagem, COR_VERMELHO)

    def _desenhar_economia(self) -> None:
        self.painel(ECON_X, ECON_Y, ECON_W, ECON_H, COR_PAINEL)
        self.texto(
            "econ_titulo",
            "Economia do Reino",
            ECON_X + 14,
            ECON_Y + ECON_H - 20,
            15,
            COR_TEXTO,
            negrito=True,
        )
        self.texto(
            "econ_fechar",
            "E para fechar",
            ECON_X + ECON_W - 14,
            ECON_Y + ECON_H - 20,
            8.5,
            COR_TEXTO_SUAVE,
            anchor_x="right",
        )
        producao = self.reino.taxas_producao()
        y = ECON_Y + ECON_H - 48
        self.texto(
            "econ_prod_titulo",
            "Produção por dia",
            ECON_X + 14,
            y,
            11,
            COR_TEXTO,
            negrito=True,
        )
        y -= 20
        for recurso in RECURSOS:
            taxa = producao.get(recurso, 0.0)
            if taxa <= 0 and recurso in ("troncos",):
                pass
            self.texto(
                f"econ_prod_{recurso}",
                f"{NOMES_RECURSOS[recurso]}: +{fmt(taxa, 2)}/dia",
                ECON_X + 20,
                y,
                9,
                COR_TEXTO if taxa > 0 else COR_TEXTO_SUAVE,
            )
            y -= 17
        y -= 6
        self.texto(
            "econ_consumo",
            f"Consumo de alimento: {fmt(self.reino.consumo_diario, 2)}/dia · "
            f"saldo {fmt(producao.get('alimento', 0.0) - self.reino.consumo_diario, 2)}/dia",
            ECON_X + 14,
            y,
            9,
            COR_TEXTO,
        )
        y -= 18
        crescimento = self.reino.taxa_crescimento()
        self.texto(
            "econ_cresc",
            f"Crescimento: +{fmt(crescimento['taxa'], 2)} cidadão/dia · "
            f"casas {fmt(crescimento['espaco'], 0)} · "
            f"comida {fmt(crescimento['comida'] * 100, 0)}% · "
            f"riqueza {fmt(crescimento['riqueza'] * 100, 0)}%",
            ECON_X + 14,
            y,
            9,
            COR_VERDE if crescimento["taxa"] > 0 else COR_TEXTO_SUAVE,
        )
        y -= 22
        self.texto(
            "econ_inst_titulo",
            "Produção por estrutura",
            ECON_X + 14,
            y,
            11,
            COR_TEXTO,
            negrito=True,
        )
        y -= 18
        for construcao in self.reino.instancias():
            taxas = self.reino.taxas_instancia(construcao)
            if construcao.tipo == "madeireira" and construcao.trabalhadores > 0:
                lista = f"{fmt(construcao.trabalhadores * 10, 1)} madeira/dia"
            else:
                lista = " · ".join(
                    f"{NOMES_RECURSOS[r]} {fmt(v, 2)}/dia"
                    for r, v in taxas.items()
                    if v > 0
                )
            if not lista:
                continue
            self.texto(
                f"econ_inst_{construcao.id}",
                f"{NOMES_CONSTRUCOES[construcao.tipo]} #{construcao.id}: {lista}",
                ECON_X + 20,
                y,
                8.5,
                COR_TEXTO_SUAVE,
            )
            y -= 15
            if y < ECON_Y + 130:
                break
        self.texto(
            "econ_raros_titulo",
            "Recursos raros",
            ECON_X + 14,
            ECON_Y + 148,
            10,
            COR_DOURADO,
            negrito=True,
        )
        raros_texto = " · ".join(
            f"{RECURSOS_RAROS.get(chave, chave)} {fmt(q, 0)}"
            for chave, q in self.reino.recursos_raros.items()
        )
        self.texto(
            "econ_raros",
            raros_texto,
            ECON_X + 20,
            ECON_Y + 130,
            8.5,
            COR_TEXTO,
        )
        if self.reino.mercador_dias > 0 and self.reino.mercador_precos:
            y = max(y, ECON_Y + 108)
            self.texto(
                "econ_mercador",
                f"Mercador viajante ({self.reino.mercador_dias} dia[s]) — "
                "venda recursos por dinheiro",
                ECON_X + 14,
                ECON_Y + 96,
                9.5,
                COR_DOURADO,
                negrito=True,
            )
            for indice, recurso in enumerate(
                ("madeira", "pedra", "ferro", "ouro")
            ):
                preco = self.reino.mercador_precos.get(recurso, 0.0)
                self.texto(
                    f"econ_preco_{recurso}",
                    f"{NOMES_RECURSOS[recurso]} {fmt(preco, 2)}",
                    ECON_X + 20 + indice * 130,
                    ECON_Y + 76,
                    8.5,
                    COR_TEXTO,
                )

    def _desenhar_predios(self) -> None:
        for id_instancia in self.mapa.posicoes:
            if id_instancia == CASTELO_ID:
                self._desenhar_castelo()
            else:
                self._desenhar_predio(id_instancia)

    def _desenhar_predio(self, id_instancia: int) -> None:
        if id_instancia not in self.mapa.posicoes:
            return
        construcao = self.reino.construcoes.get(id_instancia)
        if construcao is None or construcao.nivel <= 0:
            return
        tipo = construcao.tipo
        x, y, largura, altura = self.mapa.rect_mundo(id_instancia)
        cor = CORES_PREDIOS.get(tipo, (120, 120, 120))
        centro_x = x + largura / 2
        centro_y = y + altura / 2
        compacto = largura <= TILE and altura <= TILE
        if tipo == "muralha":
            arcade.draw_lbwh_rectangle_filled(
                x + 2, y + 2, largura - 4, altura - 4, cor
            )
            arcade.draw_lbwh_rectangle_outline(
                x + 2, y + 2, largura - 4, altura - 4, (50, 52, 58), 2
            )
            for passo in range(16, int(largura) - 4, 16):
                arcade.draw_line(x + passo, y + 3, x + passo, y + altura - 3, (86, 88, 96), 1)
            arcade.draw_line(x + 3, y + altura / 2, x + largura - 3, y + altura / 2, (86, 88, 96), 1)
        elif tipo == "barricada":
            arcade.draw_lbwh_rectangle_filled(
                x + 4, y + 4, largura - 8, altura - 10, (118, 82, 46)
            )
            for i in range(4):
                bx = x + 8 + i * (largura - 16) / 3
                arcade.draw_lbwh_rectangle_filled(bx - 4, y + 4, 8, altura - 12, (146, 100, 54))
                arcade.draw_triangle_filled(
                    bx - 4, y + altura - 8,
                    bx + 4, y + altura - 8,
                    bx, y + altura + 2,
                    (168, 118, 62),
                )
            arcade.draw_lbwh_rectangle_outline(
                x + 4, y + 4, largura - 8, altura - 10, (60, 42, 24), 2
            )
        elif tipo == "casas":
            arcade.draw_lbwh_rectangle_filled(
                x + 7, y + 7, largura - 14, altura - 14, cor
            )
            arcade.draw_lbwh_rectangle_filled(
                x + 5, y + altura * 0.54, largura - 10, altura * 0.38,
                (92, 68, 50),
            )
            arcade.draw_line(
                x + 8,
                y + altura * 0.73,
                x + largura - 8,
                y + altura * 0.73,
                (60, 42, 32),
                2,
            )
            arcade.draw_lbwh_rectangle_filled(
                centro_x - 5, y + 7, 10, altura * 0.30, (68, 48, 34)
            )
            arcade.draw_lbwh_rectangle_outline(
                x + 5, y + 5, largura - 10, altura - 10, (22, 24, 28), 2
            )
        elif tipo == "posto":
            arcade.draw_lbwh_rectangle_filled(
                x + 6, y + 6, largura - 12, altura - 12, cor
            )
            arcade.draw_lbwh_rectangle_outline(
                x + 6, y + 6, largura - 12, altura - 12, (30, 40, 52), 2
            )
            arcade.draw_lbwh_rectangle_filled(
                centro_x - 10, y + 6, 20, altura * 0.55, (70, 88, 112)
            )
            arcade.draw_line(
                centro_x, y + altura - 6, centro_x, y + altura + 28, (50, 48, 44), 2
            )
            arcade.draw_triangle_filled(
                centro_x, y + altura + 28,
                centro_x + 20, y + altura + 22,
                centro_x, y + altura + 16,
                (220, 184, 74),
            )
        else:
            arcade.draw_lbwh_rectangle_filled(x + 5, y + 5, largura - 10, altura - 10, cor)
            arcade.draw_lbwh_rectangle_filled(
                x + 5, y + altura - 22, largura - 10, 17, (58, 52, 46)
            )
            arcade.draw_lbwh_rectangle_outline(
                x + 5, y + 5, largura - 10, altura - 10, (22, 24, 28), 2
            )
        tamanho_sigla = 8.5 if compacto else 11
        self.texto(
            f"sigla_{id_instancia}",
            SIGLAS.get(tipo, tipo[:3]),
            centro_x,
            centro_y,
            tamanho_sigla,
            (240, 242, 246),
            anchor_x="center",
            negrito=True,
        )
        if not compacto or construcao.nivel > 1:
            nivel_y = y + altura + 10 if compacto else y + 12
            self.texto(
                f"nivel_{id_instancia}",
                f"Nv {construcao.nivel}",
                centro_x,
                nivel_y,
                7.5 if compacto else 9,
                (225, 225, 230),
                anchor_x="center",
            )
        vagas = self.reino.vagas_instancia(id_instancia)
        if vagas > 0:
            self.texto(
                f"trab_{id_instancia}",
                f"{construcao.trabalhadores}/{vagas}",
                centro_x,
                y + altura + 10,
                9,
                (210, 220, 235),
                anchor_x="center",
            )
        barras: list[tuple[float, tuple[int, int, int]]] = []
        if tipo == "casas":
            barras.append((self.reino.crescimento, (150, 200, 140)))
        else:
            taxas = self.reino.taxas_instancia(construcao)
            for recurso, progresso in construcao.progressos.items():
                if taxas.get(recurso, 0.0) > 0 or progresso > 0:
                    barras.append(
                        (progresso, CORES_RECURSOS.get(recurso, (200, 200, 200)))
                    )
            if tipo == "madeireira" and "madeira" in construcao.progressos:
                barras = [
                    (
                        construcao.progressos["madeira"],
                        CORES_RECURSOS["madeira"],
                    )
                ]
        if barras and (
            construcao.trabalhadores > 0 or tipo == "casas"
        ):
            base_y = y + altura + 22
            for indice, (fracao, cor_barra) in enumerate(barras[:3]):
                self._barra_hp(
                    centro_x,
                    base_y + indice * 7,
                    max(24, largura - 12),
                    max(0.0, min(1.0, fracao)),
                    cor_barra,
                )
        if construcao.hp_max > 0 and (
            construcao.hp < construcao.hp_max or self.predio_sel == id_instancia
        ):
            self._barra_hp(
                centro_x,
                y + altura + 22 + max(1, min(3, len(barras))) * 7 + 2,
                max(24, largura - 12),
                construcao.hp / max(1.0, construcao.hp_max),
                (150, 190, 230),
            )
        if self.predio_sel == id_instancia:
            arcade.draw_lbwh_rectangle_outline(
                x - 2, y - 2, largura + 4, altura + 4, (240, 204, 90), 3
            )

    def _desenhar_castelo(self) -> None:
        x, y, largura, altura = self.mapa.rect_mundo(CASTELO_ID)
        arcade.draw_lbwh_rectangle_filled(
            x + 5, y + 5, largura - 10, altura - 10, (108, 98, 128)
        )
        arcade.draw_lbwh_rectangle_filled(
            x + 5, y + altura - 26, largura - 10, 20, (78, 70, 96)
        )
        arcade.draw_lbwh_rectangle_outline(
            x + 5, y + 5, largura - 10, altura - 10, (28, 26, 34), 2
        )
        for i in range(10, int(largura) - 10, 24):
            arcade.draw_lbwh_rectangle_filled(
                x + i, y + altura - 6, 12, 12, (124, 114, 144)
            )
        centro_x = x + largura / 2
        arcade.draw_line(
            centro_x, y + altura, centro_x, y + altura + 44, (50, 48, 44), 3
        )
        arcade.draw_triangle_filled(
            centro_x,
            y + altura + 44,
            centro_x + 26,
            y + altura + 34,
            centro_x,
            y + altura + 24,
            (182, 72, 72),
        )
        self.texto(
            "castelo_nome",
            "Castelo",
            centro_x,
            y + altura / 2,
            11,
            (238, 234, 246),
            anchor_x="center",
            negrito=True,
        )
        hp = max(0.0, self.reino.hp_castelo)
        hp_max = self.reino.hp_castelo_max
        proporcao = hp / hp_max if hp_max else 0.0
        cor = COR_VERDE if proporcao > 0.6 else COR_DOURADO if proporcao > 0.3 else COR_VERMELHO
        barra_y = y + altura + 10
        arcade.draw_lbwh_rectangle_filled(x, barra_y, largura, 10, (30, 32, 38, 230))
        arcade.draw_lbwh_rectangle_filled(
            x, barra_y, max(1.0, largura * proporcao), 10, cor
        )
        arcade.draw_lbwh_rectangle_outline(x, barra_y, largura, 10, (16, 18, 22), 1)
        self.texto(
            "castelo_hp",
            f"{fmt(hp)}/{fmt(hp_max)}",
            centro_x,
            barra_y + 22,
            9,
            (230, 232, 238),
            anchor_x="center",
        )

    def _desenhar_unidades(self) -> None:
        for cidadao in self.mundo.cidadaos:
            cor = CORES_PROFISSAO.get(cidadao.profissao, (200, 200, 200))
            if cidadao.rei:
                cor = (240, 204, 90)
            arcade.draw_ellipse_filled(
                cidadao.x, cidadao.y - 7, 22, 10, (12, 14, 18, 120)
            )
            arcade.draw_circle_filled(cidadao.x, cidadao.y, 10, cor)
            arcade.draw_circle_outline(cidadao.x, cidadao.y, 10, (20, 22, 26), 2)
            if cidadao.rei:
                arcade.draw_triangle_filled(
                    cidadao.x - 6, cidadao.y + 12,
                    cidadao.x + 6, cidadao.y + 12,
                    cidadao.x, cidadao.y + 22,
                    (250, 220, 100),
                )
                arcade.draw_circle_outline(
                    cidadao.x, cidadao.y, 13, (250, 220, 100), 2
                )
            arcade.draw_circle_filled(
                cidadao.x - 3, cidadao.y + 3, 3, (246, 246, 250)
            )
            if cidadao.troncos > 0:
                arcade.draw_lbwh_rectangle_filled(
                    cidadao.x + 9, cidadao.y - 5, 9, 9, (120, 82, 46)
                )
                arcade.draw_lbwh_rectangle_outline(
                    cidadao.x + 9, cidadao.y - 5, 9, 9, (60, 40, 22), 1
                )
            if any(cidadao is c for c in self.cidadaos_sel):
                arcade.draw_circle_outline(
                    cidadao.x, cidadao.y, 15, (240, 204, 90), 3
                )

        for soldado in self.mundo.soldados:
            cor_soldado = CLASSES_TROPA.get(
                soldado.classe, {"cor": (90, 150, 220)}
            )["cor"]
            arcade.draw_ellipse_filled(
                soldado.x, soldado.y - 8, 26, 11, (12, 14, 18, 140)
            )
            arcade.draw_circle_filled(soldado.x, soldado.y, 12, cor_soldado)
            arcade.draw_circle_outline(soldado.x, soldado.y, 12, (24, 40, 68), 2)
            arcade.draw_circle_filled(
                soldado.x - 3, soldado.y + 3, 3, (220, 235, 255)
            )
            self._barra_hp(
                soldado.x,
                soldado.y + 21,
                32,
                soldado.hp / soldado.hp_max if soldado.hp_max else 0,
                cor_soldado,
            )
            if any(soldado is s for s in self.soldados_sel):
                arcade.draw_circle_outline(
                    soldado.x, soldado.y, 17, (240, 204, 90), 3
                )

        for inimigo in self.mundo.inimigos:
            arcade.draw_ellipse_filled(
                inimigo.x, inimigo.y - 8, 26, 11, (12, 14, 18, 140)
            )
            arcade.draw_circle_filled(inimigo.x, inimigo.y, 12, (206, 72, 72))
            arcade.draw_circle_outline(inimigo.x, inimigo.y, 12, (120, 30, 30), 2)
            self._barra_hp(
                inimigo.x,
                inimigo.y + 21,
                32,
                inimigo.hp / inimigo.hp_max if inimigo.hp_max else 0,
                (214, 92, 92),
            )
            if any(
                s.ordem_ataque and s.alvo is inimigo
                for s in self.mundo.soldados
            ):
                arcade.draw_circle_outline(
                    inimigo.x, inimigo.y, 17, (240, 140, 80), 2
                )

        for inimigo in self.mundo.errantes:
            arcade.draw_ellipse_filled(
                inimigo.x, inimigo.y - 8, 26, 11, (12, 14, 18, 140)
            )
            arcade.draw_circle_filled(inimigo.x, inimigo.y, 11, (150, 80, 170))
            arcade.draw_circle_outline(
                inimigo.x, inimigo.y, 11, (80, 40, 90), 2
            )
            self._barra_hp(
                inimigo.x,
                inimigo.y + 20,
                30,
                inimigo.hp / inimigo.hp_max if inimigo.hp_max else 0,
                (190, 110, 210),
            )

    def _desenhar_tiros_postos(self) -> None:
        for tiro in self.mundo.tiros_postos:
            arcade.draw_line(
                tiro["x1"],
                tiro["y1"],
                tiro["x2"],
                tiro["y2"],
                (246, 220, 120, 210),
                2,
            )
            arcade.draw_circle_filled(
                tiro["x2"], tiro["y2"], 3, (250, 236, 170)
            )

    def _barra_hp(self, x, y, largura, proporcao, cor) -> None:
        proporcao = limitar(proporcao, 0.0, 1.0)
        arcade.draw_lbwh_rectangle_filled(x - largura / 2, y, largura, 4, (30, 32, 38))
        arcade.draw_lbwh_rectangle_filled(
            x - largura / 2, y, max(1.0, largura * proporcao), 4, cor
        )

    def _desenhar_fantasma(self) -> None:
        nome = self.modo_posicionamento
        if nome is None:
            return
        centro_x, centro_y = self.mapa.centro_mundo(CASTELO_ID)
        arcade.draw_circle_outline(
            centro_x,
            centro_y,
            RAIO_CONSTRUCAO * TILE,
            (230, 220, 150, 90),
            2,
        )
        for posto in self.reino.instancias("posto"):
            if posto.id in self.mapa.posicoes:
                px, py = self.mapa.centro_mundo(posto.id)
                arcade.draw_circle_outline(
                    px,
                    py,
                    RAIO_POSTO * TILE,
                    (140, 190, 230, 80),
                    1,
                )
        anchor = self._anchor_posicionamento()
        if anchor is None:
            return
        col, row = anchor
        largura, altura = PEGADAS[nome]
        x = col * TILE
        y = row * TILE
        w = largura * TILE
        h = altura * TILE
        valido = self.mapa.pode_posicionar(
            nome, col, row, self.mundo.tiles_ocupados_unidades()
        )
        if valido:
            cor_preenchimento = (70, 200, 110, 80)
            cor_borda = (100, 230, 140)
        else:
            cor_preenchimento = (220, 80, 80, 90)
            cor_borda = (240, 110, 110)
        arcade.draw_lbwh_rectangle_filled(x, y, w, h, cor_preenchimento)
        arcade.draw_lbwh_rectangle_outline(x, y, w, h, cor_borda, 2)
        self.texto(
            "fantasma_nome",
            SIGLAS.get(nome, nome[:3]),
            x + w / 2,
            y + h / 2,
            11,
            (240, 242, 246),
            anchor_x="center",
            negrito=True,
        )
        custo = self.reino.custo_nova_instancia(nome)
        texto_custo = "  ".join(
            f"{ABREVIACOES[r]} {fmt(q)}" for r, q in custo.items()
        )
        self.texto(
            "fantasma_custo",
            texto_custo,
            x + w / 2,
            y + h + 12,
            9,
            cor_borda,
            anchor_x="center",
        )

    def _desenhar_marcador(self) -> None:
        if self._marcador is None:
            return
        x, y, tempo = self._marcador
        alpha = int(255 * max(0.0, min(1.0, tempo / 0.7)))
        arcade.draw_circle_outline(x, y, 12, (240, 204, 90, alpha), 2)
        arcade.draw_line(x - 14, y, x + 14, y, (240, 204, 90, alpha), 1)
        arcade.draw_line(x, y - 14, x, y + 14, (240, 204, 90, alpha), 1)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def _desenhar_topo(self) -> None:
        arcade.draw_lbwh_rectangle_filled(0, TOPO_Y, LARGURA, TOPO_H, (20, 24, 30, 242))
        arcade.draw_line(0, TOPO_Y, LARGURA, TOPO_Y, COR_BORDA, 1)

        self.texto(
            "dia",
            f"Dia {self.reino.dia}",
            12,
            TOPO_Y + 27,
            14.5,
            COR_TEXTO,
            negrito=True,
        )
        proximo = self.reino.proximo_ataque_dia
        if self.mundo.raid_ativo:
            ataque, cor = f"Horda: {self.mundo.raid_origem}", COR_VERMELHO
        elif self.reino.aviso_ataque:
            ataque, cor = f"ATAQUE DIA {proximo}!", COR_VERMELHO
        elif not self.reino.ataques_ativos:
            ataque, cor = "Ataques desligados", COR_TEXTO_SUAVE
        else:
            ataque, cor = f"Ataque: dia {proximo}", COR_TEXTO_SUAVE
        self.texto("ataque_topo", ataque, 12, TOPO_Y + 10, 8.5, cor)

        x = 105
        for recurso in RECURSOS_TOPO:
            arcade.draw_circle_filled(x + 4, TOPO_Y + 22, 4, CORES_RECURSOS[recurso])
            self.texto(
                f"topo_nome_{recurso}",
                ABREVIACOES[recurso],
                x + 12,
                TOPO_Y + 29,
                7.5,
                COR_TEXTO_SUAVE,
            )
            self.texto(
                f"topo_val_{recurso}",
                fmt(self.reino.recursos[recurso], 1),
                x,
                TOPO_Y + 13,
                10.5,
                COR_TEXTO,
                negrito=True,
            )
            x += 66

        self.texto("topo_pop_lbl", "Pop", 574, TOPO_Y + 29, 7.5, COR_TEXTO_SUAVE)
        self.texto(
            "topo_pop_val",
            f"{self.reino.populacao}/{self.reino.capacidade_populacao}",
            574,
            TOPO_Y + 13,
            10,
            COR_TEXTO,
            negrito=True,
        )
        self.texto("topo_sold_lbl", "Tropas", 634, TOPO_Y + 29, 7.5, COR_TEXTO_SUAVE)
        self.texto(
            "topo_sold_val",
            f"{self.reino.total_tropas}/{self.reino.max_total_tropas}",
            634,
            TOPO_Y + 13,
            10,
            COR_TEXTO,
            negrito=True,
        )

    def _desenhar_detalhe(self) -> None:
        self.painel(DET_X, DET_Y, DET_W, DET_H)
        self.texto(
            "det_titulo",
            "Reino — detalhes",
            DET_X + 12,
            DET_Y + DET_H - 18,
            13,
            COR_TEXTO,
            negrito=True,
        )
        self.texto(
            "det_fechar",
            "Tab para fechar",
            DET_X + DET_W - 12,
            DET_Y + DET_H - 18,
            8.5,
            COR_TEXTO_SUAVE,
            anchor_x="right",
        )

        producao = self.reino.taxas_producao()
        y = DET_Y + DET_H - 48
        for recurso in RECURSOS:
            arcade.draw_circle_filled(DET_X + 20, y, 4, CORES_RECURSOS[recurso])
            self.texto(
                f"det_nome_{recurso}",
                NOMES_RECURSOS[recurso],
                DET_X + 32,
                y,
                9.5,
                COR_TEXTO_SUAVE,
            )
            self.texto(
                f"det_val_{recurso}",
                fmt(self.reino.recursos[recurso], 1),
                DET_X + 150,
                y,
                11,
                COR_TEXTO,
                negrito=True,
            )
            taxa = producao[recurso]
            extra = "" if recurso != "troncos" else f" /{fmt(self.reino.capacidade_troncos)}"
            self.texto(
                f"det_taxa_{recurso}",
                f"+{fmt(taxa, 1)}/dia" if taxa > 0 else "—",
                DET_X + DET_W - 12,
                y,
                8.5,
                COR_VERDE if taxa > 0 else COR_TEXTO_SUAVE,
                anchor_x="right",
            )
            if extra:
                self.texto(
                    "det_troncos_cap",
                    extra,
                    DET_X + DET_W - 62,
                    y,
                    8,
                    COR_TEXTO_SUAVE,
                    anchor_x="right",
                )
            y -= 30

        y -= 6
        self.texto(
            "det_comida",
            f"Comida: {fmt(self.reino.dias_de_comida, 1)} dias "
            f"(consumo {fmt(self.reino.consumo_diario, 1)}/dia)",
            DET_X + 12,
            y,
            9,
            COR_TEXTO,
        )
        y -= 20
        self.texto(
            "det_pop",
            f"População: {self.reino.populacao}/{self.reino.capacidade_populacao} · "
            f"livres {len([c for c in self.mundo.cidadaos if c.profissao == 'ocioso'])}",
            DET_X + 12,
            y,
            9,
            COR_TEXTO,
        )
        y -= 20
        crescimento = self.reino.taxa_crescimento()
        if crescimento["espaco"] <= 0:
            texto_crescimento = "Crescimento: sem vagas em Casas"
        else:
            texto_crescimento = (
                f"Crescimento: +{fmt(crescimento['taxa'], 2)} cidadão/dia · "
                f"casas {fmt(crescimento['espaco'], 0)} · "
                f"comida {fmt(crescimento['comida'] * 100, 0)}% · "
                f"riqueza {fmt(crescimento['riqueza'] * 100, 0)}%"
            )
        self.texto(
            "det_cresc",
            texto_crescimento,
            DET_X + 12,
            y,
            9,
            COR_VERDE if crescimento["taxa"] > 0 else COR_TEXTO_SUAVE,
        )
        y -= 20
        self.texto(
            "det_trab",
            f"Ocupados: {self.reino.trabalhadores_empregados} · "
            f"Sold {self.reino.soldados} · Arq {self.reino.arqueiros} · "
            f"Mag {self.reino.magos} · Cur {self.reino.curandeiros}",
            DET_X + 12,
            y,
            9,
            COR_TEXTO,
        )
        y -= 20
        self.texto(
            "det_def",
            f"Defesa: {fmt(self.reino.poder_defesa, 1)} · "
            f"Recorde: {self.reino.recorde_dias} dias",
            DET_X + 12,
            y,
            9,
            COR_TEXTO,
        )
        y -= 20
        self.texto(
            "det_castelo",
            f"Castelo Nv {self.reino.nivel_castelo}"
            f"{' · Recolhido' if self.reino.toque_de_recolher else ''} · "
            f"{'Noite' if self.mundo.eh_noite else 'Dia'} · "
            f"perdidos {self.reino.castelos_perdidos} · "
            f"melhor período {self.reino.melhor_periodo} dias",
            DET_X + 12,
            y,
            9,
            COR_DOURADO,
        )
        y -= 26

        self.texto(
            "det_log_titulo",
            "Registro",
            DET_X + 12,
            y,
            10,
            COR_TEXTO,
            negrito=True,
        )
        y -= 18
        linhas = list(self.reino.log)[-10:]
        for indice, linha in enumerate(linhas):
            cor = COR_TEXTO_SUAVE
            if "DERROTA" in linha or "ATAQUE" in linha or "FOME" in linha or "horda" in linha:
                cor = COR_VERMELHO
            elif "novo" in linha or "refugiado" in linha or "Colheita" in linha:
                cor = COR_VERDE
            elif "Mercador" in linha or "guilda" in linha:
                cor = COR_DOURADO
            texto = linha if len(linha) <= 58 else linha[:57] + "…"
            self.texto(f"det_log_{indice}", texto, DET_X + 12, y, 8, cor)
            y -= 16

        y -= 4
        self.texto(
            "det_legenda1",
            "Madeireiro marrom · Serrador laranja · Fazendeiro verde",
            DET_X + 12,
            y,
            7.5,
            COR_TEXTO_SUAVE,
        )
        y -= 12
        self.texto(
            "det_legenda2",
            "Minerador/Pedreiro cinza · Pescador azul · Comerciante dourado · Soldado azul",
            DET_X + 12,
            y,
            7.5,
            COR_TEXTO_SUAVE,
        )

    def _desenhar_obras(self) -> None:
        self.painel(OBRAS_X, OBRAS_Y, OBRAS_W, OBRAS_H)
        self.texto(
            "obras_titulo",
            "Construções",
            OBRAS_X + 12,
            OBRAS_Y + OBRAS_H - 16,
            13,
            COR_TEXTO,
            negrito=True,
        )
        topo = 574
        tipos = list(CONSTRUCOES)[
            self.obras_scroll:self.obras_scroll + OBRAS_LINHAS_VISIVEIS
        ]
        total = len(CONSTRUCOES)
        self.texto(
            "obras_scroll",
            f"{self.obras_scroll + 1}-"
            f"{min(total, self.obras_scroll + OBRAS_LINHAS_VISIVEIS)}/{total}"
            " · roda do mouse",
            OBRAS_X + OBRAS_W - 12,
            OBRAS_Y + OBRAS_H - 16,
            7.5,
            COR_TEXTO_SUAVE,
            anchor_x="right",
        )
        for tipo in tipos:
            quantidade = self.reino.quantidade_instancias(tipo)
            custo = self.reino.custo_nova_instancia(tipo)
            cor_fundo = COR_PAINEL_CLARO if quantidade > 0 else (28, 32, 40, 225)
            arcade.draw_lbwh_rectangle_filled(
                OBRAS_X + 4, topo - 37, OBRAS_W - 8, 35, cor_fundo
            )
            cor_nome = COR_TEXTO if quantidade > 0 else COR_TEXTO_SUAVE
            self.texto(
                f"obras_nome_{tipo}",
                NOMES_CONSTRUCOES[tipo],
                OBRAS_X + 10,
                topo - 8,
                9,
                cor_nome,
                negrito=True,
            )
            instancias = self.reino.instancias(tipo)
            vagas_total = sum(
                self.reino.vagas_instancia(c.id) for c in instancias
            )
            trabalhadores = sum(c.trabalhadores for c in instancias)
            if quantidade <= 0:
                info = "não construída"
            elif vagas_total > 0:
                info = f"{quantidade}x · trab {trabalhadores}/{vagas_total}"
            else:
                info = f"{quantidade}x construída(s)"
            self.texto(
                f"obras_info_{tipo}",
                info,
                OBRAS_X + 10,
                topo - 19,
                7.2,
                COR_TEXTO_SUAVE,
            )
            instancia_unica = (
                self.reino.primeira_instancia(tipo) if PEGADAS.get(tipo, (0, 0))[0] <= 0 else None
            )
            if instancia_unica is not None:
                if instancia_unica.nivel >= MAX_NIVEL:
                    texto_custo, cor_custo = "Nível máximo", COR_TEXTO_SUAVE
                else:
                    custo_melhoria = self.reino.custo_melhoria(instancia_unica.id)
                    partes = [
                        f"{ABREVIACOES[r]} {fmt(q)}"
                        for r, q in custo_melhoria.items()
                    ]
                    texto_custo = "Melhorar: " + "  ".join(partes)
                    cor_custo = (
                        COR_DOURADO
                        if self.reino.pode_melhorar(instancia_unica.id)
                        else COR_TEXTO_SUAVE
                    )
            else:
                partes = [f"{ABREVIACOES[r]} {fmt(q)}" for r, q in custo.items()]
                texto_custo = "Próxima: " + "  ".join(partes)
                cor_custo = (
                    COR_DOURADO
                    if self.reino.pode_construir_nova(tipo)
                    else COR_TEXTO_SUAVE
                )
            self.texto(
                f"obras_custo_{tipo}",
                texto_custo,
                OBRAS_X + 10,
                topo - 29,
                7.2,
                cor_custo,
            )
            topo -= 42

    def _desenhar_indicador_horda(self) -> None:
        if not self.mundo.raid_ativo or not self.mundo.inimigos:
            return
        media_x = sum(i.x for i in self.mundo.inimigos) / len(self.mundo.inimigos)
        media_y = sum(i.y for i in self.mundo.inimigos) / len(self.mundo.inimigos)
        pos = self.camera.position
        sx = (media_x - pos.x) * self.zoom + LARGURA / 2
        sy = (media_y - pos.y) * self.zoom + ALTURA / 2
        margem = 34
        dentro = (
            margem <= sx <= LARGURA - margem
            and margem <= sy <= ALTURA - margem
        )
        if dentro:
            return
        cx = min(max(sx, margem), LARGURA - margem)
        cy = min(max(sy, margem), ALTURA - margem)
        dx = sx - LARGURA / 2
        dy = sy - ALTURA / 2
        comprimento = math.hypot(dx, dy) or 1.0
        ux, uy = dx / comprimento, dy / comprimento
        perpendicular = (-uy, ux)
        tamanho = 14
        arcade.draw_triangle_filled(
            cx + ux * tamanho,
            cy + uy * tamanho,
            cx - ux * tamanho * 0.4 + perpendicular[0] * tamanho * 0.7,
            cy - uy * tamanho * 0.4 + perpendicular[1] * tamanho * 0.7,
            cx - ux * tamanho * 0.4 - perpendicular[0] * tamanho * 0.7,
            cy - uy * tamanho * 0.4 - perpendicular[1] * tamanho * 0.7,
            (226, 92, 92),
        )
        self.texto(
            "horda_seta",
            self.mundo.raid_origem,
            cx,
            cy - 22,
            9,
            (240, 150, 150),
            anchor_x="center",
            negrito=True,
        )

    def _desenhar_contexto(self) -> None:
        if not (self.cidadaos_sel or self.soldados_sel or self.predio_sel or self.arvore_sel or self.rocha_sel or self.caravana_sel is not None):
            return
        self.painel(CTX_X, CTX_Y, CTX_W, CTX_H, (24, 29, 37, 242))

        if self.caravana_sel is not None:
            caravana = self.caravana_sel
            membros = len(caravana.membros)
            soldados = sum(
                1 for m in caravana.membros if isinstance(m, Soldado)
            )
            civis = membros - soldados
            comida = caravana.carga.get("alimento", 0.0)
            dias = (
                comida / (membros * 0.4)
                if membros > 0 and comida > 0
                else 0.0
            )
            self.texto(
                "ctx_caravana_titulo",
                f"Caravana #{caravana.id} — {membros} membro(s)",
                CTX_X + 12,
                CTX_Y + CTX_H - 18,
                13,
                COR_TEXTO,
                negrito=True,
            )
            self.texto(
                "ctx_caravana_membros",
                f"{civis} cidadão(s) · {soldados} soldado(s) · "
                f"comida {fmt(comida, 1)} ({fmt(dias, 1)} dias)",
                CTX_X + 12,
                CTX_Y + CTX_H - 38,
                9,
                COR_TEXTO_SUAVE,
            )
            carga_texto = "  ".join(
                f"{ABREVIACOES.get(r, r)} {fmt(q)}"
                for r, q in caravana.carga.items()
                if q > 0
            )
            total_carga = sum(caravana.carga.values())
            self.texto(
                "ctx_caravana_carga",
                f"Carga ({fmt(total_carga)}/{fmt(caravana.capacidade)}): "
                + (carga_texto or "vazia"),
                CTX_X + 12,
                CTX_Y + CTX_H - 58,
                8.5,
                COR_TEXTO,
            )
            posto = self.mundo.posto_perto(caravana.x, caravana.y)
            if posto is not None:
                detalhe_posto = (
                    f"Posto #{posto.id} por perto · armazém "
                    f"{fmt(self.reino.total_armazem(posto))}/"
                    f"{fmt(self.reino.capacidade_armazem(posto))} · "
                    "X recolhe"
                )
            else:
                detalhe_posto = (
                    "Botão direito move · F funda posto · "
                    "X recolhe · Y entrega no castelo"
                )
            self.texto(
                "ctx_caravana_dica",
                detalhe_posto,
                CTX_X + 12,
                CTX_Y + CTX_H - 78,
                8.5,
                COR_TEXTO_SUAVE,
            )
            return

        if self.predio_sel is not None:
            id_instancia = self.predio_sel
            construcao = self.reino.construcoes.get(id_instancia)
            if id_instancia == CASTELO_ID:
                nomes = {
                    1: "Choupana",
                    2: "Casa",
                    3: "Solar",
                    4: "Forte",
                    5: "Fortaleza",
                }
                self.texto(
                    "ctx_castelo",
                    f"Castelo — {nomes.get(self.reino.nivel_castelo, 'Castelo')} "
                    f"(Nv {self.reino.nivel_castelo})",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 18,
                    13,
                    COR_DOURADO,
                    negrito=True,
                )
                self.texto(
                    "ctx_castelo_hp",
                    f"HP {fmt(self.reino.hp_castelo)}/"
                    f"{fmt(self.reino.hp_castelo_max)} · população "
                    f"{self.reino.populacao} · Rei vivo",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 38,
                    9,
                    COR_TEXTO_SUAVE,
                )
                if self.reino.hp_castelo <= 0:
                    self.texto(
                        "ctx_castelo_estado",
                        "Destruído! Repare o castelo ou faça o Êxodo do Rei.",
                        CTX_X + 12,
                        CTX_Y + CTX_H - 58,
                        9,
                        COR_VERMELHO,
                    )
                else:
                    self.texto(
                        "ctx_castelo_estado",
                        "Proteja o Rei. Enquanto ele viver, o reino continua.",
                        CTX_X + 12,
                        CTX_Y + CTX_H - 58,
                        9,
                        COR_TEXTO_SUAVE,
                    )
                if self.reino.nivel_castelo < 5:
                    custo = self.reino.custo_melhoria_castelo()
                    partes = [
                        f"{ABREVIACOES[r]} {fmt(q)}" for r, q in custo.items()
                    ]
                    self.texto(
                        "ctx_castelo_custo",
                        "Melhorar: " + "  ".join(partes),
                        CTX_X + 12,
                        CTX_Y + CTX_H - 78,
                        8.5,
                        COR_TEXTO_SUAVE,
                    )
                self.texto(
                    "ctx_castelo_extra",
                    f"Castelos perdidos: {self.reino.castelos_perdidos} · "
                    f"Melhor período: {self.reino.melhor_periodo} dias · "
                    f"Recorde: {self.reino.recorde_dias}",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 98,
                    8.5,
                    COR_TEXTO_SUAVE,
                )
                return
            if construcao is None or construcao.nivel <= 0:
                return
            tipo = construcao.tipo
            titulo_predio = (
                f"{NOMES_CONSTRUCOES[tipo]} #{id_instancia} — Nível "
                f"{construcao.nivel}"
            )
            if tipo == "posto":
                defesa = self.reino.defesa_posto(construcao)
                titulo_predio += (
                    f" · Def {fmt(defesa['dano'], 0)}"
                    f" · Alc {fmt(defesa['alcance'], 1)}"
                )
            if construcao.hp_max > 0 and construcao.hp < construcao.hp_max:
                titulo_predio += (
                    f" · HP {fmt(construcao.hp)}/{fmt(construcao.hp_max)}"
                )
            self.texto(
                "ctx_titulo",
                titulo_predio,
                CTX_X + 12,
                CTX_Y + CTX_H - 18,
                13,
                COR_TEXTO,
                negrito=True,
            )
            self.texto(
                "ctx_efeito",
                self._texto_efeito(id_instancia),
                CTX_X + 12,
                CTX_Y + CTX_H - 38,
                9,
                COR_TEXTO_SUAVE,
            )
            vagas = self.reino.vagas_instancia(id_instancia)
            funcionarios = self.mundo.funcionarios_instancia(id_instancia)
            if tipo in TRABALHO_POR_PREDIO and vagas > 0 and tipo != "posto":
                self.texto(
                    "ctx_trab",
                    f"Trabalhadores: {construcao.trabalhadores}/{vagas} · "
                    f"{len(self.reino.instancias(tipo))} instância(s) · M mover",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 58,
                    8.5,
                    COR_TEXTO,
                )
            elif tipo in TROPAS_POR_PREDIO:
                classes = TROPAS_POR_PREDIO[tipo]
                base_tropa = classes[0]
                base_nome = CLASSES_TROPA[base_tropa]["base"]
                contagem = {
                    "soldado": self.reino.soldados,
                    "arqueiro": self.reino.arqueiros,
                    "mago": self.reino.magos,
                    "curandeiro": self.reino.curandeiros,
                }.get(base_nome, 0)
                limite = {
                    "soldado": self.reino.max_soldados,
                    "arqueiro": self.reino.max_arqueiros,
                    "mago": self.reino.max_magos,
                    "curandeiro": self.reino.max_curandeiros,
                }.get(base_nome, 0)
                tem_ocioso = any(
                    c.profissao == "ocioso"
                    and c.estado == "ocioso"
                    and not c.rei
                    for c in self.mundo.cidadaos
                )
                if not tem_ocioso:
                    status = "sem cidadão ocioso"
                elif contagem >= limite:
                    status = "lotado"
                elif not self.reino.pode_treinar_tropa(base_tropa):
                    status = "recursos insuficientes"
                else:
                    status = "pronto para treinar"
                self.texto(
                    f"ctx_tropa_{tipo}",
                    f"{CLASSES_TROPA[base_tropa]['nome']}: {contagem}/{limite} · "
                    f"{status}",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 58,
                    8.5,
                    COR_TEXTO,
                )
                partes_especiais = []
                for classe_especial in classes[1:]:
                    custos = CUSTO_TROPA.get(classe_especial, {})
                    raros = ", ".join(
                        f"{RECURSOS_RAROS.get(chave, chave)} {fmt(q, 0)}"
                        for chave, q in custos.items()
                        if chave in RECURSOS_RAROS
                    )
                    partes_especiais.append(
                        f"{CLASSES_TROPA[classe_especial]['nome']}: "
                        f"{raros or 'sem raros'}"
                    )
                texto_especiais = "Especiais — " + " · ".join(partes_especiais)
                if len(texto_especiais) > 78:
                    texto_especiais = texto_especiais[:77] + "…"
                self.texto(
                    f"ctx_especiais_{tipo}",
                    texto_especiais,
                    CTX_X + 12,
                    CTX_Y + CTX_H - 98,
                    7.5,
                    COR_TEXTO_SUAVE,
                )
            elif tipo in ("muralha", "barricada"):
                self.texto(
                    "ctx_defesa",
                    f"HP: {fmt(construcao.hp)}/{fmt(construcao.hp_max)} · "
                    "M para mover",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 58,
                    8.5,
                    COR_TEXTO,
                )
            elif tipo == "posto":
                trabalhadores = construcao.trabalhadores
                comida = construcao.armazem.get("alimento", 0.0)
                consumo = trabalhadores * CONSUMO_POR_PESSOA
                if consumo > 0:
                    dias_comida = comida / consumo
                    texto_comida = f"{fmt(comida, 0)} ({fmt(dias_comida, 1)}d)"
                else:
                    texto_comida = f"{fmt(comida, 0)} (sem colonos)"
                self.texto(
                    "ctx_posto",
                    f"Colonos: {trabalhadores}/{vagas} · comida local "
                    f"{texto_comida} · M move",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 58,
                    8.5,
                    COR_TEXTO,
                )
            else:
                self.texto(
                    "ctx_sem_vagas",
                    "Este prédio não emprega cidadãos.",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 58,
                    8.5,
                    COR_TEXTO_SUAVE,
                )
            if construcao.nivel < MAX_NIVEL:
                custo = self.reino.custo_melhoria(id_instancia)
                partes = [f"{ABREVIACOES[r]} {fmt(q)}" for r, q in custo.items()]
                self.texto(
                    "ctx_custo",
                    "Melhorar: " + "  ".join(partes),
                    CTX_X + 12,
                    CTX_Y + CTX_H - 78,
                    8.5,
                    COR_TEXTO_SUAVE,
                )
            else:
                self.texto(
                    "ctx_custo",
                    "Nível máximo",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 78,
                    8.5,
                    COR_TEXTO_SUAVE,
                )
            if funcionarios:
                self.texto(
                    "ctx_func_titulo",
                    f"Funcionários ({len(funcionarios)}/{vagas})",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 100,
                    9,
                    COR_TEXTO,
                    negrito=True,
                )
                y_func = CTX_Y + CTX_H - 118
                for cidadao in funcionarios[:3]:
                    nivel = nivel_por_xp(
                        cidadao.experiencia.get(cidadao.profissao, 0.0)
                    )
                    estado = {
                        "trabalhando": "trabalhando",
                        "indo_predio": "indo",
                    }.get(cidadao.estado, cidadao.estado)
                    self.texto(
                        f"ctx_func_{cidadao.id}",
                        f"#{cidadao.id} · {NOMES_PROFISSAO.get(cidadao.profissao, cidadao.profissao)} "
                        f"Nv {nivel} · {estado}",
                        CTX_X + 20,
                        y_func,
                        8,
                        COR_TEXTO_SUAVE,
                    )
                    y_func -= 16
            return

        if self.arvore_sel is not None:
            arvore = self.mundo.arvores.get(self.arvore_sel)
            if arvore is None:
                return
            if arvore.estado == "adulta":
                titulo = "Árvore adulta"
                estado = (
                    f"Pronta para corte · vida {arvore.vida}/{arvore.vida_max}"
                )
            else:
                titulo = "Toco"
                estado = f"Rebrota em {fmt(arvore.regrow, 1)} dia(s)"
            self.texto(
                "ctx_titulo",
                titulo,
                CTX_X + 12,
                CTX_Y + CTX_H - 18,
                13,
                COR_TEXTO,
                negrito=True,
            )
            self.texto(
                "ctx_efeito",
                estado,
                CTX_X + 12,
                CTX_Y + CTX_H - 38,
                9,
                COR_TEXTO_SUAVE,
            )
            self.texto(
                "ctx_trab",
                "Selecione cidadãos e clique com o botão direito para cortar.",
                CTX_X + 12,
                CTX_Y + CTX_H - 58,
                8.5,
                COR_TEXTO,
            )
            return

        if self.rocha_sel is not None:
            rocha = self.mundo.rochas.get(self.rocha_sel)
            if rocha is None:
                return
            if rocha.estado == "adulta":
                titulo = "Pedra"
                estado = f"Vida: {rocha.vida}/{rocha.vida_max} · pronta para coleta"
            else:
                titulo = "Pedra esgotada"
                estado = f"Regenera em {fmt(rocha.regrow, 1)} dia(s)"
            self.texto(
                "ctx_titulo",
                titulo,
                CTX_X + 12,
                CTX_Y + CTX_H - 18,
                13,
                COR_TEXTO,
                negrito=True,
            )
            self.texto(
                "ctx_efeito",
                estado,
                CTX_X + 12,
                CTX_Y + CTX_H - 38,
                9,
                COR_TEXTO_SUAVE,
            )
            self.texto(
                "ctx_trab",
                "Selecione cidadãos e clique com o botão direito para minerar.",
                CTX_X + 12,
                CTX_Y + CTX_H - 58,
                8.5,
                COR_TEXTO,
            )
            return

        titulo = []
        if self.cidadaos_sel:
            titulo.append(f"{len(self.cidadaos_sel)} cidadão(s)")
        if self.soldados_sel:
            n_soldados = sum(
                1 for s in self.soldados_sel if s.classe == "soldado"
            )
            n_arqueiros = len(self.soldados_sel) - n_soldados
            if n_soldados:
                titulo.append(f"{n_soldados} soldado(s)")
            if n_arqueiros:
                titulo.append(f"{n_arqueiros} arqueiro(s)")
        self.texto(
            "ctx_titulo",
            " + ".join(titulo),
            CTX_X + 12,
            CTX_Y + CTX_H - 18,
            13,
            COR_TEXTO,
            negrito=True,
        )

        if self.cidadaos_sel:
            contagem: dict[str, int] = {}
            for cidadao in self.cidadaos_sel:
                contagem[cidadao.profissao] = contagem.get(cidadao.profissao, 0) + 1
            resumo = " · ".join(
                f"{NOMES_PROFISSAO.get(p, p)}: {n}" for p, n in contagem.items()
            )
            self.texto(
                "ctx_efeito",
                resumo,
                CTX_X + 12,
                CTX_Y + CTX_H - 38,
                9,
                COR_TEXTO_SUAVE,
            )
            troncos = sum(c.troncos for c in self.cidadaos_sel)
            pedras = sum(c.pedras for c in self.cidadaos_sel)
            partes_carga = []
            if troncos > 0:
                partes_carga.append(f"{troncos} troncos")
            if pedras > 0:
                partes_carga.append(f"{pedras} pedras")
            if partes_carga:
                texto_carga = "Carregando: " + " · ".join(partes_carga) + " · "
            else:
                texto_carga = ""
            self.texto(
                "ctx_trab",
                f"{texto_carga}direito: mover, cortar árvore, minerar ou trabalhar",
                CTX_X + 12,
                CTX_Y + CTX_H - 58,
                8.5,
                COR_TEXTO,
            )
            if len(self.cidadaos_sel) == 1:
                c = self.cidadaos_sel[0]
                xp = c.experiencia.get(c.profissao, 0.0)
                nivel = nivel_por_xp(xp)
                falta = xp_para_proximo_nivel(xp)
                pontos = self.mundo.pontos_disponiveis_cidadao(c)
                self.texto(
                    "ctx_xp",
                    f"XP {NOMES_PROFISSAO.get(c.profissao, c.profissao)}: "
                    f"Nv {nivel}"
                    + (
                        f" · faltam {fmt(falta, 0)} XP"
                        if falta > 0
                        else " · nível máximo"
                    )
                    + f" · HP {fmt(c.hp)}/{fmt(c.hp_max)} · pontos {pontos}",
                    CTX_X + 12,
                    CTX_Y + CTX_H - 78,
                    8.5,
                    COR_DOURADO,
                )
        if self.soldados_sel:
            hp_medio = sum(s.hp for s in self.soldados_sel) / len(self.soldados_sel)
            if len(self.soldados_sel) == 1:
                soldado = self.soldados_sel[0]
                pontos = self.mundo.pontos_disponiveis_soldado(soldado)
                linha_soldado = (
                    f"HP {fmt(soldado.hp)}/{fmt(soldado.hp_max)} · "
                    f"pontos {pontos} · "
                    f"vida+{soldado.atributos.get('vida', 0)} "
                    f"dano+{soldado.atributos.get('dano', 0)} "
                    f"vel+{soldado.atributos.get('velocidade', 0)}"
                )
            else:
                linha_soldado = (
                    f"HP médio: {fmt(hp_medio)} · direito: mover ou atacar inimigo"
                )
            self.texto(
                "ctx_sold",
                linha_soldado,
                CTX_X + 12,
                CTX_Y + CTX_H - (78 if self.cidadaos_sel else 38),
                8.5,
                COR_TEXTO,
            )

    def _texto_efeito(self, id_instancia: int) -> str:
        construcao = self.reino.construcoes.get(id_instancia)
        if construcao is None:
            return ""
        tipo = construcao.tipo
        nivel = construcao.nivel
        eficiencia = (
            1.0 + 0.10 * (nivel - 1)
        ) * construcao.bonus_producao
        trabalhadores = construcao.trabalhadores
        if tipo == "madeireira":
            return (
                f"Refino: {fmt(trabalhadores * 10 * eficiencia, 1)} madeira/dia · "
                f"Troncos {fmt(self.reino.recursos['troncos'], 0)}/"
                f"{fmt(self.reino.capacidade_troncos, 0)}"
            )
        if tipo == "mina":
            return (
                f"Produção: {fmt(trabalhadores * 3.0 * eficiencia, 1)} ferro/dia · "
                f"{fmt(trabalhadores * 1.0 * eficiencia, 1)} ouro/dia · "
                f"{fmt(trabalhadores * 4.0 * eficiencia, 1)} pedra/dia"
            )
        if tipo == "fazenda":
            return f"Produção: {fmt(trabalhadores * 3.0 * eficiencia, 1)} alimento/dia"
        if tipo == "mercado":
            return f"Produção: {fmt(trabalhadores * 3.0 * eficiencia, 1)} dinheiro/dia"
        if tipo == "ferraria":
            return f"Força por soldado: {fmt(self.reino.forca_soldado, 2)}"
        if tipo == "quartel":
            return f"Soldados máximos: {self.reino.max_soldados}"
        if tipo == "arquearia":
            return f"Arqueiros máximos: {self.reino.max_arqueiros}"
        if tipo == "torre_magia":
            return f"Magos máximos: {self.reino.max_magos}"
        if tipo == "santuario":
            return f"Curandeiros máximos: {self.reino.max_curandeiros}"
        if tipo == "casas":
            dados = self.reino.taxa_crescimento()
            return (
                f"Capacidade: {self.reino.capacidade_populacao} · "
                f"crescimento +{fmt(dados['taxa'], 2)}/dia"
            )
        if tipo == "celeiro":
            return f"Estoque de alimento: {fmt(self.reino.capacidade_alimento)}"
        if tipo in ("muralha", "barricada"):
            return "Estrutura defensiva · bloqueia a passagem"
        if tipo == "posto":
            producao = self.reino.producao_posto(construcao)
            if producao:
                partes = " ".join(
                    f"{ABREVIACOES.get(r, r)} {fmt(v, 1)}"
                    for r, v in producao.items()
                )
            else:
                partes = "sem colonos"
            return (
                f"Produção/dia: {partes} · Armazém "
                f"{fmt(self.reino.total_armazem(construcao), 0)}/"
                f"{fmt(self.reino.capacidade_armazem(construcao), 0)}"
            )
        return ""

    def _desenhar_caixa(self) -> None:
        if self._caixa_inicio is None or self._caixa_atual is None:
            return
        x1, y1 = self._caixa_inicio
        x2, y2 = self._caixa_atual
        if abs(x2 - x1) < 5 and abs(y2 - y1) < 5:
            return
        esquerda, direita = min(x1, x2), max(x1, x2)
        baixo, cima = min(y1, y2), max(y1, y2)
        arcade.draw_lbwh_rectangle_filled(
            esquerda,
            baixo,
            direita - esquerda,
            cima - baixo,
            (240, 204, 90, 40),
        )
        arcade.draw_lbwh_rectangle_outline(
            esquerda,
            baixo,
            direita - esquerda,
            cima - baixo,
            (240, 204, 90),
            1,
        )

    def _desenhar_toast(self) -> None:
        largura = 620
        x = (LARGURA - largura) / 2
        tem_selecao = bool(
            self.cidadaos_sel or self.soldados_sel or self.predio_sel or self.arvore_sel or self.rocha_sel or self.caravana_sel is not None
        )
        if tem_selecao:
            y = CTX_Y + CTX_H + 10
        elif self.detalhe_aberto or self.obras_aberto:
            y = 148
        else:
            y = TOPO_Y - 50
        if self.detalhe_aberto or self.obras_aberto:
            largura = 440
            x = 340
        texto_toast = self.toast_texto
        limite = 64 if largura < 600 else 90
        if len(texto_toast) > limite:
            texto_toast = texto_toast[: limite - 1] + "…"
        arcade.draw_lbwh_rectangle_filled(x, y, largura, 36, (22, 26, 33, 238))
        arcade.draw_lbwh_rectangle_outline(x, y, largura, 36, self.toast_cor, 2)
        self.texto(
            "toast",
            texto_toast,
            x + largura / 2,
            y + 18,
            9.5 if largura < 600 else 10.5,
            self.toast_cor,
            anchor_x="center",
            negrito=True,
        )

    def _desenhar_botoes(self) -> None:
        mx, my = self.mouse
        for indice, botao in enumerate(self.botoes):
            sobre = botao.contem(mx, my)
            pressionado = botao is self.botao_pressionado and sobre
            if not botao.habilitado:
                cor = COR_DESABILITADO
                cor_texto = (110, 115, 125)
            else:
                cor = botao.cor
                if pressionado:
                    cor = tuple(max(0, c - 30) for c in cor)
                elif sobre:
                    cor = tuple(min(255, c + 25) for c in cor)
                cor_texto = COR_TEXTO
            arcade.draw_lbwh_rectangle_filled(
                botao.x, botao.y, botao.largura, botao.altura, cor
            )
            arcade.draw_lbwh_rectangle_outline(
                botao.x, botao.y, botao.largura, botao.altura, COR_BORDA, 1
            )
            self.texto(
                f"botao_{indice}_{botao.tamanho_fonte}",
                botao.rotulo,
                botao.x + botao.largura / 2,
                botao.y + botao.altura / 2,
                botao.tamanho_fonte,
                cor_texto,
                anchor_x="center",
                negrito=True,
            )

    def _desenhar_derrota(self) -> None:
        arcade.draw_lbwh_rectangle_filled(0, 0, LARGURA, ALTURA, (0, 0, 0, 200))
        self.texto(
            "derrota_titulo",
            "O REINO CAIU",
            LARGURA / 2,
            430,
            40,
            COR_VERMELHO,
            anchor_x="center",
            negrito=True,
        )
        motivo = ""
        for linha in reversed(self.reino.log):
            if "DERROTA" in linha:
                motivo = linha.split(":", 1)[-1].strip()
                break
        self.texto(
            "derrota_motivo",
            motivo,
            LARGURA / 2,
            385,
            14,
            COR_TEXTO,
            anchor_x="center",
        )
        self.texto(
            "derrota_dias",
            f"Dias sobrevividos: {self.reino.dia}",
            LARGURA / 2,
            345,
            18,
            COR_DOURADO,
            anchor_x="center",
            negrito=True,
        )
        self.texto(
            "derrota_recorde",
            f"Recorde geral: {self.reino.recorde_dias} dias",
            LARGURA / 2,
            318,
            12,
            COR_TEXTO_SUAVE,
            anchor_x="center",
        )
        self.texto(
            "derrota_extras",
            f"Castelos perdidos: {self.reino.castelos_perdidos} · "
            f"Melhor período: {self.reino.melhor_periodo} dias",
            LARGURA / 2,
            236,
            11,
            COR_TEXTO_SUAVE,
            anchor_x="center",
        )

    # ------------------------------------------------------------------
    # Entrada
    # ------------------------------------------------------------------
    def _em_hud(self, x: float, y: float) -> bool:
        if y >= TOPO_Y:
            return True
        if self.detalhe_aberto and DET_X <= x <= DET_X + DET_W and DET_Y <= y <= DET_Y + DET_H:
            return True
        if (
            self.economia_aberto
            and ECON_X <= x <= ECON_X + ECON_W
            and ECON_Y <= y <= ECON_Y + ECON_H
        ):
            return True
        if (
            self._minimapa_visivel()
            and MINI_X <= x <= MINI_X + MINI_W
            and MINI_Y <= y <= MINI_Y + MINI_H
        ):
            return True
        if self.obras_aberto and OBRAS_X <= x <= OBRAS_X + OBRAS_W and OBRAS_Y <= y <= OBRAS_Y + OBRAS_H:
            return True
        if (
            (self.cidadaos_sel or self.soldados_sel or self.predio_sel or self.arvore_sel or self.rocha_sel or self.caravana_sel is not None)
            and CTX_X <= x <= CTX_X + CTX_W
            and CTX_Y <= y <= CTX_Y + CTX_H
        ):
            return True
        return False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse = (x, y)
        if self._caixa_inicio is not None:
            self._caixa_atual = (x, y)
        if self.modo_estrada and self._mouse_esquerdo and not self._em_hud(x, y):
            mundo_x, mundo_y = self._mundo_do_mouse()
            tile = self.mapa.tile_do_mundo(mundo_x, mundo_y)
            if tile != self._ultimo_tile_estrada:
                self._ultimo_tile_estrada = tile
                self._colocar_estrada()
        if self._arrastando_camera:
            delta_x = x - self._ultimo_mouse[0]
            delta_y = y - self._ultimo_mouse[1]
            px, py = self.camera.position
            self.camera.position = (
                px - delta_x / self.zoom,
                py - delta_y / self.zoom,
            )
            self._limitar_camera()
        self._ultimo_mouse = (x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        self.mouse = (x, y)
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.botao_pressionado = None
            for botao in reversed(self.botoes):
                if botao.habilitado and botao.contem(x, y):
                    self.botao_pressionado = botao
                    return
            if (
                self._minimapa_visivel()
                and MINI_X <= x <= MINI_X + MINI_W
                and MINI_Y <= y <= MINI_Y + MINI_H
            ):
                wx, wy = self._mundo_do_minimapa(x, y)
                self.camera.position = (wx, wy)
                self._limitar_camera()
                return
            if self._em_hud(x, y):
                return
            if self.modo_estrada:
                self._mouse_esquerdo = True
                self._colocar_estrada()
                return
            if self.modo_posicionamento is not None:
                self._confirmar_posicionamento()
                return
            self._caixa_inicio = (x, y)
            self._caixa_atual = (x, y)
            self._ultimo_mouse = (x, y)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            if self.modo_posicionamento is not None:
                self._cancelar_modo()
                self._mostrar_toast("Posicionamento cancelado.", COR_TEXTO_SUAVE)
                return
            if not self._em_hud(x, y):
                self._ordenar()
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self._arrastando_camera = True
            self._ultimo_mouse = (x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._mouse_esquerdo = False
            botao = self.botao_pressionado
            self.botao_pressionado = None
            if botao is not None:
                if botao.habilitado and botao.contem(x, y):
                    botao.acao()
                return
            if self._caixa_inicio is None:
                return
            inicio = self._caixa_inicio
            self._caixa_inicio = None
            self._caixa_atual = None
            if abs(x - inicio[0]) > 6 or abs(y - inicio[1]) > 6:
                self._caixa_inicio = inicio
                self._caixa_atual = (x, y)
                self._caixa_selecao()
                self._caixa_inicio = None
                self._caixa_atual = None
            else:
                self._clicar_mapa()
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self._arrastando_camera = False

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        if (
            self.obras_aberto
            and OBRAS_X <= x <= OBRAS_X + OBRAS_W
            and OBRAS_Y <= y <= OBRAS_Y + OBRAS_H
        ):
            maximo = max(0, len(CONSTRUCOES) - OBRAS_LINHAS_VISIVEIS)
            passo = 1 if scroll_y < 0 else -1
            self.obras_scroll = max(0, min(maximo, self.obras_scroll + passo))
            return
        fator = 1.1 if scroll_y > 0 else 1 / 1.1
        self.zoom = limitar(self.zoom * fator, 0.5, 1.6)
        self.camera.zoom = self.zoom
        self._limitar_camera()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self._teclas.add(symbol)
        if symbol == arcade.key.SPACE:
            self._alternar_pausa()
        elif symbol == arcade.key.KEY_1:
            self._definir_velocidade(1)
        elif symbol == arcade.key.KEY_2:
            self._definir_velocidade(2)
        elif symbol == arcade.key.KEY_3:
            self._definir_velocidade(4)
        elif symbol == arcade.key.TAB:
            self._alternar_detalhe()
        elif symbol == arcade.key.B:
            self._alternar_obras()
        elif symbol == arcade.key.C:
            self._centralizar()
        elif symbol == arcade.key.T:
            self._treinar_soldado()
        elif symbol == arcade.key.Q:
            self._treinar_arqueiro()
        elif symbol == arcade.key.R:
            construcao = (
                self.reino.construcoes.get(self.predio_sel)
                if self.predio_sel is not None
                else None
            )
            if (
                construcao is not None
                and construcao.hp_max > 0
                and construcao.hp < construcao.hp_max
            ):
                self._reparar_estrutura(self.predio_sel)
            else:
                self.reparar_castelo()
        elif symbol == arcade.key.O:
            self._selecionar_ociosos()
        elif symbol == arcade.key.G:
            self._selecionar_soldados()
        elif symbol == arcade.key.M:
            if self.predio_sel is not None:
                self._iniciar_mover(self.predio_sel)
        elif symbol == arcade.key.E:
            self._alternar_economia()
        elif symbol == arcade.key.N:
            self._alternar_minimapa()
        elif symbol == arcade.key.X:
            if self.caravana_sel is not None:
                self._coletar_posto_caravana()
        elif symbol == arcade.key.U:
            self._alternar_recolher()
        elif symbol == arcade.key.Y:
            if self.caravana_sel is not None:
                self._entregar_caravana()
        elif symbol == arcade.key.P:
            self.modo_estrada = not self.modo_estrada
            if self.modo_estrada:
                self._cancelar_modo()
                self._mostrar_toast(
                    "Modo estrada: clique/arraste no mapa. P sai.",
                    COR_DOURADO,
                )
        elif symbol == arcade.key.K:
            self._alternar_ataques()
        elif symbol == arcade.key.V:
            if self.cidadaos_sel or self.soldados_sel:
                self._criar_caravana()
        elif symbol == arcade.key.F:
            if self.caravana_sel is not None:
                self._fundar_posto_caravana()
        elif symbol == arcade.key.ESCAPE:
            if self.modo_posicionamento is not None:
                self._cancelar_modo()
            elif self.modo_estrada:
                self.modo_estrada = False
            else:
                self._limpar_selecao()

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self._teclas.discard(symbol)

    def on_close(self) -> None:
        self._salvar()
        super().on_close()


def main() -> None:
    Jogo()
    arcade.run()


if __name__ == "__main__":
    main()
