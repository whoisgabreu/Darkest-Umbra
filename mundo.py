"""Simulação do mundo: cidadãos, árvores, coleta, combate e sincronização."""

from __future__ import annotations

import math
import random

from caminho import adjacentes, buscar_caminho, melhor_adjacente
from mapa import (
    AGUA,
    ALTURA_MUNDO,
    CASTELO_ID,
    COLUNAS,
    FLORESTA,
    GRAMA,
    LINHAS,
    PEGADAS,
    ROCHA,
    TAMANHO_CHUNK,
    TILE,
    Mapa,
)
from reino import (
    CONSTRUCOES,
    CONSUMO_POR_PESSOA,
    DIA_SEGUNDOS,
    NOMES_CONSTRUCOES,
    RECURSOS,
    Reino,
)
from unidades import (
    Arvore,
    BASE_TROPA,
    CLASSES_TROPA,
    Caravana,
    Cidadao,
    Inimigo,
    Rocha,
    Soldado,
    TRABALHO_POR_PREDIO,
    bonus_xp,
    distancia,
    mover_entidade,
    nivel_por_xp,
    xp_para_proximo_nivel,
)

CURA_POR_DIA = 0.35
LIMIAR_DESCANSO = 0.5
PESCA_SEGUNDOS = 12.0
PEIXES_POR_CICLO = 5
AGGRO_ERRANTE = 4 * TILE
FATOR_NOITE = 0.6
CHOP_SEGUNDOS = 12.0
TRONCOS_POR_ARVORE = 5
REGROW_MIN = 3.0
REGROW_MAX = 5.0
MINE_SEGUNDOS = 10.0
PEDRA_POR_GOLPE = 4
ROCHA_VIDA_MAX = 3
ROCHA_REGROW_MIN = 4.0
ROCHA_REGROW_MAX = 8.0
REFINO_POR_DIA = 10.0
AGGRO_SOLDADO = 10 * TILE
AGGRO_INIMIGO = 5 * TILE
AGGRO_CIVIL = 4 * TILE
RAIO_ESTRUTURA = 6 * TILE
ALCANCE_ATAQUE = 46
TEMPO_RECALCULO = 0.5


PREDIO_POR_TRABALHO = {v: k for k, v in TRABALHO_POR_PREDIO.items()}


class Mundo:
    def __init__(self, reino: Reino, mapa: Mapa) -> None:
        self.reino = reino
        self.mapa = mapa
        self.arvores: dict[tuple[int, int], Arvore] = {}
        self.rochas: dict[tuple[int, int], Rocha] = {}
        self.cidadaos: list[Cidadao] = []
        self.caravanas: list[Caravana] = []
        self.errantes: list[Inimigo] = []
        self.soldados: list[Soldado] = []
        self.inimigos: list[Inimigo] = []
        self.raid_ativo = False
        self.raid_origem = ""
        self.raid_posto_id: int | None = None
        self.cooldowns_postos: dict[int, float] = {}
        self.tiros_postos: list[dict] = []
        self.proximo_id = 1
        self.tempo_anim = 0.0
        self.versao_arvores = 0
        self.chunks_arvores_dirty: set[tuple[int, int]] = set()
        self.chunks_rochas_dirty: set[tuple[int, int]] = set()
        self._raid_inimigos = 0
        self._raid_dano = 0
        self._raid_perdas = 0
        self._gerar_arvores()
        self._gerar_rochas()
        self._dia_anterior = reino.dia
        self.fog: set[tuple[int, int]] = set()
        self._inicializar_fog()

    # ------------------------------------------------------------------
    # Fog of War
    # ------------------------------------------------------------------
    def _inicializar_fog(self) -> None:
        self.fog = {
            (cx, cy)
            for cx in range(COLUNAS // TAMANHO_CHUNK)
            for cy in range(LINHAS // TAMANHO_CHUNK)
        }
        rx, ry, rw, rh = self.mapa.rect_mundo(CASTELO_ID)
        self.revelar_rect(rx, ry, rw, rh, margem=TILE)
        for id_instancia in self.mapa.posicoes:
            if id_instancia == CASTELO_ID:
                continue
            bx, by, bw, bh = self.mapa.rect_mundo(id_instancia)
            self.revelar_rect(bx, by, bw, bh, margem=8.0)
        for caravana in self.caravanas:
            self.revelar_ao_redor(caravana.x, caravana.y, raio=1)

    def revelar_rect(
        self, x: float, y: float, largura: float, altura: float, margem: float = 0.0
    ) -> None:
        col0 = int((x - margem) // TILE)
        row0 = int((y - margem) // TILE)
        col1 = int((x + largura + margem) // TILE)
        row1 = int((y + altura + margem) // TILE)
        for cx in range(col0 // TAMANHO_CHUNK, col1 // TAMANHO_CHUNK + 1):
            for cy in range(row0 // TAMANHO_CHUNK, row1 // TAMANHO_CHUNK + 1):
                self.fog.discard((cx, cy))

    def revelar_construcao(
        self, id_instancia: int, raio_extra: int = 0
    ) -> None:
        if id_instancia not in self.mapa.posicoes:
            return
        x, y, largura, altura = self.mapa.rect_mundo(id_instancia)
        self.revelar_rect(x, y, largura, altura, margem=TILE)
        if raio_extra > 0:
            cx, cy = self.mapa.centro_mundo(id_instancia)
            self.revelar_ao_redor(cx, cy, raio=raio_extra)

    def revelar_ao_redor(self, x: float, y: float, raio: int = 1) -> None:
        col, row = self.mapa.tile_do_mundo(x, y)
        centro_cx = col // TAMANHO_CHUNK
        centro_cy = row // TAMANHO_CHUNK
        for cx in range(centro_cx - raio, centro_cx + raio + 1):
            for cy in range(centro_cy - raio, centro_cy + raio + 1):
                self.fog.discard((cx, cy))

    @property
    def eh_noite(self) -> bool:
        return (
            not self.reino.derrota
            and (self.reino.tempo_dia / DIA_SEGUNDOS) >= FATOR_NOITE
        )

    # ------------------------------------------------------------------
    # Criação e povoamento
    # ------------------------------------------------------------------
    def _gerar_arvores(self) -> None:
        self.arvores = {}
        for row in range(LINHAS):
            for col in range(COLUNAS):
                if self.mapa.tiles[row][col] == FLORESTA:
                    if (col, row) in self.mapa.ocupacao:
                        continue
                    self.arvores[(col, row)] = Arvore(col=col, row=row)

    def _gerar_rochas(self) -> None:
        self.rochas = {}
        for row in range(LINHAS):
            for col in range(COLUNAS):
                if self.mapa.tiles[row][col] == ROCHA:
                    if (col, row) in self.mapa.ocupacao:
                        continue
                    self.rochas[(col, row)] = Rocha(
                        col=col, row=row, vida=ROCHA_VIDA_MAX,
                        vida_max=ROCHA_VIDA_MAX,
                    )

    def _novo_id(self) -> int:
        valor = self.proximo_id
        self.proximo_id += 1
        return valor

    def _ponto_livre(self, id_predio: int | None = None) -> tuple[float, float]:
        if id_predio is not None and id_predio in self.mapa.posicoes:
            col, row = self.mapa.posicoes[id_predio]
            tipo = self.mapa.tipos[id_predio]
            largura, altura = PEGADAS[tipo]
            opcoes = adjacentes(col, row, largura, altura)
            tile = melhor_adjacente(self.mapa, opcoes, self.mapa.centro_castelo)
        else:
            tile = None
            col, row = self.mapa.castelo_pos
            largura, altura = PEGADAS["castelo"]
            opcoes = adjacentes(col, row, largura, altura)
            tile = melhor_adjacente(self.mapa, opcoes, self.mapa.centro_castelo)
        if tile is None:
            tile = self.mapa.tile_livre_proximo(
                *self.mapa.castelo_pos, raio_max=12
            )
        if tile is None:
            tile = (int(self.mapa.centro_castelo[0]), int(self.mapa.centro_castelo[1]))
        x, y = self.mapa.centro_tile_mundo(*tile)
        return (x + random.uniform(-10, 10), y + random.uniform(-10, 10))

    def _criar_cidadao(
        self,
        x: float,
        y: float,
        profissao: str = "ocioso",
        alvo_predio: int | None = None,
        estado: str = "ocioso",
        rei: bool = False,
    ) -> Cidadao:
        cidadao = Cidadao(
            id=self._novo_id(),
            x=x,
            y=y,
            profissao=profissao,
            alvo_predio=alvo_predio,
            estado=estado,
            rei=rei,
        )
        self.cidadaos.append(cidadao)
        return cidadao

    def _poste_soldado(self) -> tuple[float, float]:
        cx, cy = self.mapa.centro_mundo(CASTELO_ID)
        angulo = len(self.soldados) * 2.399963
        px = cx + math.cos(angulo) * 190
        py = cy + math.sin(angulo) * 190
        tile = self.mapa.tile_livre_proximo(
            *self.mapa.tile_do_mundo(px, py), raio_max=6
        )
        if tile is not None:
            return self.mapa.centro_tile_mundo(*tile)
        return (cx, cy)

    def _criar_tropa(self, classe: str, x: float, y: float) -> Soldado:
        dados = CLASSES_TROPA.get(classe, CLASSES_TROPA["soldado"])
        hp_max = float(dados["hp"])
        soldado = Soldado(
            id=self._novo_id(),
            x=x,
            y=y,
            hp=hp_max,
            hp_max=hp_max,
            ataque=float(dados["atk"]),
            classe=classe,
            velocidade=200.0 if dados["base"] == "soldado" else 190.0,
            alcance=float(dados["alcance"]),
            cooldown_max=float(dados["cd"]),
            poste=self._poste_soldado(),
        )
        self.soldados.append(soldado)
        return soldado

    def _criar_soldado(self, x: float, y: float) -> Soldado:
        return self._criar_tropa("soldado", x, y)

    def _criar_arqueiro(self, x: float, y: float) -> Soldado:
        return self._criar_tropa("arqueiro", x, y)

    def inicializar_novo(self) -> None:
        self.cidadaos = []
        self.soldados = []
        self._gerar_arvores()
        self._gerar_rochas()
        self.proximo_id = 1
        x, y = self._ponto_livre(CASTELO_ID)
        self._criar_cidadao(x, y, rei=True)
        total = 1
        while total < self.reino.populacao:
            x, y = self._ponto_livre(CASTELO_ID)
            self._criar_cidadao(x, y)
            total += 1
        self._sincronizar()
        self._atualizar_errantes_dia()
        self._log(
            "O Rei fundou a Choupana. Coletem recursos e façam o reino crescer."
        )
        self._log(
            "Selecione o Rei e clique com o botão direito em árvores ou pedras."
        )

    def migrar(self) -> None:
        self.cidadaos = []
        self.soldados = []
        self._gerar_arvores()
        self._gerar_rochas()
        self.proximo_id = 1
        total = 0
        for construcao in self.reino.instancias():
            job = TRABALHO_POR_PREDIO.get(construcao.tipo)
            if job is None or construcao.id not in self.mapa.posicoes:
                continue
            quantidade = min(
                construcao.trabalhadores,
                self.reino.vagas_instancia(construcao.id),
            )
            for _ in range(quantidade):
                x, y = self._ponto_livre(construcao.id)
                self._criar_cidadao(
                    x, y, profissao=job, alvo_predio=construcao.id,
                    estado="trabalhando",
                )
                total += 1
        quartel = self.reino.primeira_instancia("quartel")
        id_quartel = quartel.id if quartel is not None else None
        for _ in range(self.reino.soldados):
            x, y = self._ponto_livre(id_quartel)
            self._criar_soldado(x, y)
            total += 1
        arquearia = self.reino.primeira_instancia("arquearia")
        id_arquearia = arquearia.id if arquearia is not None else id_quartel
        for _ in range(self.reino.arqueiros):
            x, y = self._ponto_livre(id_arquearia)
            self._criar_arqueiro(x, y)
            total += 1
        casas = self.reino.primeira_instancia("casas")
        id_casas = casas.id if casas is not None else None
        while total < self.reino.populacao:
            x, y = self._ponto_livre(id_casas)
            self._criar_cidadao(x, y)
            total += 1
        self._garantir_rei()
        self._sincronizar()

    def _garantir_rei(self) -> None:
        if any(c.rei for c in self.cidadaos):
            return
        if self.cidadaos:
            self.cidadaos[0].rei = True
        else:
            x, y = self._ponto_livre(CASTELO_ID)
            self._criar_cidadao(x, y, rei=True)

    # ------------------------------------------------------------------
    # Sincronização com o reino
    # ------------------------------------------------------------------
    def _sincronizar(self) -> None:
        for construcao in self.reino.construcoes.values():
            construcao.trabalhadores = 0
            construcao.bonus_producao = 1.0
        soma_bonus: dict[int, float] = {}
        contagem: dict[int, int] = {}
        for cidadao in self.cidadaos:
            if (
                cidadao.estado == "trabalhando"
                and cidadao.alvo_predio in self.reino.construcoes
            ):
                construcao = self.reino.construcoes[cidadao.alvo_predio]
                construcao.trabalhadores += 1
                soma_bonus[cidadao.alvo_predio] = (
                    soma_bonus.get(cidadao.alvo_predio, 0.0)
                    + bonus_xp(cidadao.experiencia, cidadao.profissao)
                    * (
                        1.0
                        + 0.03 * cidadao.atributos.get("eficiencia", 0)
                    )
                )
                contagem[cidadao.alvo_predio] = (
                    contagem.get(cidadao.alvo_predio, 0) + 1
                )
        for id_instancia, total_bonus in soma_bonus.items():
            self.reino.construcoes[id_instancia].bonus_producao = (
                total_bonus / max(1, contagem[id_instancia])
            )
        self.reino.soldados = sum(
            1 for s in self.soldados if BASE_TROPA.get(s.classe) == "soldado"
        )
        self.reino.arqueiros = sum(
            1 for s in self.soldados if BASE_TROPA.get(s.classe) == "arqueiro"
        )
        self.reino.magos = sum(
            1 for s in self.soldados if BASE_TROPA.get(s.classe) == "mago"
        )
        self.reino.curandeiros = sum(
            1 for s in self.soldados if BASE_TROPA.get(s.classe) == "curandeiro"
        )

        desejada = max(0, int(self.reino.populacao))
        atual = (
            len(self.cidadaos)
            + len(self.soldados)
            + sum(len(c.membros) for c in self.caravanas)
        )
        if atual < desejada:
            casas = self.reino.primeira_instancia("casas")
            id_casas = casas.id if casas is not None else None
            for _ in range(desejada - atual):
                x, y = self._ponto_livre(id_casas)
                self._criar_cidadao(x, y)
        elif atual > desejada:
            self._remover_excedentes(atual - desejada)

        self.reino.populacao = (
            len(self.cidadaos)
            + len(self.soldados)
            + sum(len(c.membros) for c in self.caravanas)
        )
        if self.reino.populacao <= 0 and not self.reino.derrota:
            self.reino._derrota("A população chegou a zero.")

    def _remover_excedentes(self, excesso: int) -> None:
        prioridade = {"ocioso": 0, "madeireiro": 1}
        for _ in range(excesso):
            if self.cidadaos:
                cidadao = min(
                    self.cidadaos,
                    key=lambda c: (c.rei, prioridade.get(c.profissao, 2)),
                )
                self.cidadaos.remove(cidadao)
                if cidadao.rei:
                    self.reino.rei_morto = True
                    self.reino._derrota("O Rei morreu.")
            elif self.soldados:
                self.soldados.pop()
            elif self.caravanas:
                caravana = self.caravanas[-1]
                if caravana.membros:
                    caravana.membros.pop()
                if not caravana.membros:
                    self.caravanas.remove(caravana)
            else:
                break

    def _log(self, mensagem: str) -> None:
        self.reino._log(mensagem)

    # ------------------------------------------------------------------
    # Utilidades de mapa e caminho
    # ------------------------------------------------------------------
    def tiles_ocupados_unidades(self) -> set[tuple[int, int]]:
        tiles: set[tuple[int, int]] = set()
        for entidade in [*self.cidadaos, *self.soldados, *self.inimigos]:
            tiles.add(self.mapa.tile_do_mundo(entidade.x, entidade.y))
        return tiles

    def _unidade_na_tile(self, col: int, row: int) -> bool:
        x = col * TILE
        y = row * TILE
        for entidade in [*self.cidadaos, *self.soldados, *self.inimigos]:
            if x <= entidade.x < x + TILE and y <= entidade.y < y + TILE:
                return True
        return False

    def _caminho_para_tile(self, entidade, tile: tuple[int, int]) -> bool:
        inicio = self.mapa.tile_do_mundo(entidade.x, entidade.y)
        caminho = buscar_caminho(self.mapa, inicio, tile)
        if caminho is None:
            return False
        entidade.caminho = [
            self.mapa.centro_tile_mundo(col, row) for col, row in caminho
        ]
        return True

    def _caminho_para_ponto(self, entidade, x: float, y: float) -> bool:
        tile = self.mapa.tile_do_mundo(x, y)
        destino = self.mapa.tile_livre_proximo(*tile, raio_max=4)
        if destino is None:
            return False
        return self._caminho_para_tile(entidade, destino)

    def _caminho_para_predio(self, entidade, id_predio: int) -> bool:
        if id_predio not in self.mapa.posicoes:
            return False
        tipo = self.mapa.tipos[id_predio]
        col, row = self.mapa.posicoes[id_predio]
        largura, altura = PEGADAS[tipo]
        opcoes = adjacentes(col, row, largura, altura)
        opcoes.sort(
            key=lambda t: distancia(
                entidade.x, entidade.y, *self.mapa.centro_tile_mundo(*t)
            )
        )
        for destino in opcoes:
            if self._caminho_para_tile(entidade, destino):
                return True
        return False

    def _caminho_para_arvore(self, entidade, col: int, row: int) -> bool:
        opcoes = adjacentes(col, row)
        opcoes.sort(
            key=lambda t: distancia(
                entidade.x, entidade.y, *self.mapa.centro_tile_mundo(*t)
            )
        )
        for destino in opcoes:
            if self._caminho_para_tile(entidade, destino):
                return True
        return False

    def _mover_direto(self, entidade, x: float, y: float, dt: float) -> None:
        dx = x - entidade.x
        dy = y - entidade.y
        dist = math.hypot(dx, dy)
        if dist <= 0.001:
            return
        passo = min(dist, entidade.velocidade * dt)
        entidade.x += dx / dist * passo
        entidade.y += dy / dist * passo
        entidade.caminho = []

    # ------------------------------------------------------------------
    # Ordens do jogador
    # ------------------------------------------------------------------
    def ordenar_mover(self, cidadaos: list[Cidadao], x: float, y: float) -> str | None:
        if not cidadaos:
            return "Nenhum cidadão selecionado."
        for cidadao in cidadaos:
            tile = self.mapa.tile_do_mundo(x, y)
            destino = self.mapa.tile_livre_proximo(*tile, raio_max=6)
            if destino is None or not self._caminho_para_tile(cidadao, destino):
                continue
            cidadao.estado = "indo_mover"
            cidadao.alvo_predio = None
            cidadao.alvo_arvore = None
            cidadao.alvo_rocha = None
            cidadao.alvo_pesca = None
            cidadao.alvo_mover = (x, y)
        return None

    def ordenar_arvore(
        self, cidadaos: list[Cidadao], col: int, row: int
    ) -> str | None:
        arvore = self.arvores.get((col, row))
        if arvore is None or arvore.estado != "adulta":
            return "A árvore não está pronta para corte."
        if not cidadaos:
            return "Nenhum cidadão selecionado."
        for cidadao in cidadaos:
            if not self._caminho_para_arvore(cidadao, col, row):
                continue
            cidadao.profissao = "madeireiro"
            cidadao.estado = "indo_arvore"
            cidadao.alvo_predio = None
            cidadao.alvo_rocha = None
            cidadao.alvo_pesca = None
            cidadao.alvo_arvore = (col, row)
        return None

    def ordenar_rocha(
        self, cidadaos: list[Cidadao], col: int, row: int
    ) -> str | None:
        rocha = self.rochas.get((col, row))
        if rocha is None or rocha.estado != "adulta":
            return "A pedra não está pronta para coleta."
        if not cidadaos:
            return "Nenhum cidadão selecionado."
        for cidadao in cidadaos:
            if not self._caminho_para_arvore(cidadao, col, row):
                continue
            cidadao.profissao = "pedreiro"
            cidadao.estado = "indo_rocha"
            cidadao.alvo_predio = None
            cidadao.alvo_arvore = None
            cidadao.alvo_pesca = None
            cidadao.alvo_rocha = (col, row)
        return None

    def ordenar_predio(
        self, cidadaos: list[Cidadao], id_predio: int
    ) -> str | None:
        construcao = self.reino.construcoes.get(id_predio)
        if construcao is None or id_predio not in self.mapa.posicoes:
            return "Prédio indisponível."
        if construcao.nivel <= 0:
            return "Prédio não construído."
        job = TRABALHO_POR_PREDIO.get(construcao.tipo)
        if job is None:
            return "Este prédio não emprega cidadãos."
        if not cidadaos:
            return "Nenhum cidadão selecionado."
        vagas = self.reino.vagas_instancia(id_predio)
        selecionados = set(id(c) for c in cidadaos)
        ocupados = sum(
            1
            for c in self.cidadaos
            if c.alvo_predio == id_predio
            and c.estado in ("trabalhando", "indo_predio")
            and id(c) not in selecionados
        )
        livres = max(0, vagas - ocupados)
        if livres <= 0:
            return "Todas as vagas deste prédio estão ocupadas."
        atribuidos = 0
        for cidadao in cidadaos:
            if atribuidos >= livres:
                break
            if not self._caminho_para_predio(cidadao, id_predio):
                continue
            cidadao.profissao = job
            cidadao.estado = "indo_predio"
            cidadao.alvo_predio = id_predio
            cidadao.alvo_arvore = None
            cidadao.alvo_rocha = None
            cidadao.alvo_pesca = None
            atribuidos += 1
        if atribuidos == 0:
            return "Não foi possível chegar ao prédio."
        if atribuidos < len(cidadaos):
            return "Algumas vagas estavam ocupadas."
        return None

    def ordenar_parar(self, cidadaos: list[Cidadao]) -> None:
        for cidadao in cidadaos:
            cidadao.estado = "ocioso"
            cidadao.profissao = "ocioso"
            cidadao.caminho = []
            cidadao.alvo_predio = None
            cidadao.alvo_arvore = None
            cidadao.alvo_rocha = None
            cidadao.alvo_pesca = None
            cidadao.alvo_mover = None
            cidadao.tempo = 0.0

    def ordenar_soldados_mover(
        self, soldados: list[Soldado], x: float, y: float
    ) -> None:
        for soldado in soldados:
            soldado.alvo = None
            soldado.ordem_ataque = False
            tile = self.mapa.tile_do_mundo(x, y)
            destino = self.mapa.tile_livre_proximo(*tile, raio_max=6)
            if destino is not None:
                self._caminho_para_tile(soldado, destino)
                soldado.poste = self.mapa.centro_tile_mundo(*destino)

    def ordenar_soldados_atacar(
        self, soldados: list[Soldado], inimigo: Inimigo
    ) -> None:
        for soldado in soldados:
            soldado.alvo = inimigo
            soldado.ordem_ataque = True

    def _cidadao_ocioso(self) -> Cidadao | None:
        for cidadao in self.cidadaos:
            if (
                cidadao.estado == "ocioso"
                and cidadao.profissao == "ocioso"
                and not cidadao.rei
            ):
                return cidadao
        return None

    def pode_treinar_tropa(self, classe: str) -> bool:
        return (
            self.reino.pode_treinar_tropa(classe)
            and self._cidadao_ocioso() is not None
        )

    def treinar_tropa(self, classe: str) -> tuple[bool, str]:
        cidadao = self._cidadao_ocioso()
        if cidadao is None:
            return False, "Nenhum cidadão ocioso para recrutar."
        ok, mensagem = self.reino.cobrar_treinamento_tropa(classe)
        if not ok:
            return False, mensagem
        base = BASE_TROPA.get(classe, "soldado")
        predio_tipo = {
            "soldado": "quartel",
            "arqueiro": "arquearia",
            "mago": "torre_magia",
            "curandeiro": "santuario",
        }.get(base)
        instancia = (
            self.reino.primeira_instancia(predio_tipo)
            if predio_tipo
            else None
        )
        id_predio = instancia.id if instancia is not None else None
        x, y = self._ponto_livre(id_predio)
        self.cidadaos.remove(cidadao)
        self._criar_tropa(classe, x, y)
        self._log(
            f"{CLASSES_TROPA[classe]['nome']} treinado "
            f"({len(self.soldados)} tropa(s))."
        )
        self._sincronizar()
        return True, "ok"

    def pode_treinar_arqueiro(self) -> bool:
        return self.pode_treinar_tropa("arqueiro")

    def treinar_arqueiro(self) -> tuple[bool, str]:
        return self.treinar_tropa("arqueiro")

    def pode_treinar_soldado(self) -> bool:
        return self.pode_treinar_tropa("soldado")

    def treinar_soldado(self) -> tuple[bool, str]:
        return self.treinar_tropa("soldado")

    # ------------------------------------------------------------------
    # Atualização principal
    # ------------------------------------------------------------------
    def atualizar(self, dt: float) -> None:
        if self.reino.pausado or self.reino.derrota:
            return
        sim_dt = dt * self.reino.velocidade
        self.tempo_anim += sim_dt

        self._sincronizar()
        self._atualizar_arvores(sim_dt)
        self._atualizar_rochas(sim_dt)
        self._atualizar_caravanas(sim_dt)
        for posto in self.reino.instancias("posto"):
            if posto.id in self.mapa.posicoes:
                px, py = self.mapa.centro_mundo(posto.id)
                self.revelar_ao_redor(px, py, raio=1)
        self._atualizar_cidadaos(sim_dt)
        self._atualizar_defesas_postos(sim_dt)
        self._atualizar_refino(sim_dt)
        self._atualizar_inimigos(sim_dt)
        self._atualizar_errantes(sim_dt)
        self._atualizar_soldados(sim_dt)
        self._limpar_soldados_mortos()
        self._separar_unidades(sim_dt)

        self.reino.atualizar(dt)
        if self.reino.dia != self._dia_anterior:
            self._dia_anterior = self.reino.dia
            self._processar_dia_caravanas()
            self._processar_dia_postos()
            self._atualizar_errantes_dia()
        self._sincronizar()
        self._verificar_raid()

    # ------------------------------------------------------------------
    # Árvores
    # ------------------------------------------------------------------
    def _cortar_arvore(self, arvore: Arvore) -> None:
        arvore.estado = "toco"
        arvore.regrow = random.uniform(REGROW_MIN, REGROW_MAX)
        self.mapa.definir_tile(arvore.col, arvore.row, GRAMA)
        self.versao_arvores += 1
        self.chunks_arvores_dirty.add(
            (arvore.col // TAMANHO_CHUNK, arvore.row // TAMANHO_CHUNK)
        )
        ax, ay = self.mapa.centro_tile_mundo(arvore.col, arvore.row)
        nivel = self.nivel_area(ax, ay)
        if random.random() < min(0.5, 0.06 * nivel):
            self.reino.adicionar_recurso_raro("ambar", 1)

    def _atualizar_arvores(self, dt: float) -> None:
        fator = dt / DIA_SEGUNDOS
        remover: list[tuple[int, int]] = []
        for chave, arvore in self.arvores.items():
            if arvore.estado != "toco":
                continue
            arvore.regrow -= fator
            if arvore.regrow > 0:
                continue
            if chave in self.mapa.ocupacao:
                remover.append(chave)
            elif self._unidade_na_tile(arvore.col, arvore.row):
                arvore.regrow = 0.25
            else:
                arvore.estado = "adulta"
                arvore.regrow = 0.0
                arvore.vida = arvore.vida_max
                self.mapa.definir_tile(arvore.col, arvore.row, FLORESTA)
                self.versao_arvores += 1
                self.chunks_arvores_dirty.add(
                    (arvore.col // TAMANHO_CHUNK, arvore.row // TAMANHO_CHUNK)
                )
        for chave in remover:
            self.arvores.pop(chave, None)
            self.versao_arvores += 1
            self.chunks_arvores_dirty.add(
                (chave[0] // TAMANHO_CHUNK, chave[1] // TAMANHO_CHUNK)
            )

    def arvore_em_ponto(self, x: float, y: float) -> Arvore | None:
        return self.arvores.get(self.mapa.tile_do_mundo(x, y))

    # ------------------------------------------------------------------
    # Cidadãos
    # ------------------------------------------------------------------
    def _atualizar_cidadaos(self, dt: float) -> None:
        for cidadao in list(self.cidadaos):
            if cidadao.caminho:
                mover_entidade(cidadao, dt, self.mapa)

            if self.reino.toque_de_recolher and self.reino.toque_disponivel:
                if cidadao.estado not in ("indo_recolher", "recolhido"):
                    self._ir_recolher(cidadao)
            elif cidadao.estado in ("indo_recolher", "recolhido"):
                self._retomar_apos_descanso(cidadao)

            if cidadao.estado not in ("indo_recolher", "recolhido"):
                if (
                    cidadao.hp < cidadao.hp_max * LIMIAR_DESCANSO
                    and cidadao.estado
                    not in ("indo_descanso", "descansando")
                ):
                    self._ir_descansar(cidadao)

                if self.eh_noite and cidadao.estado == "ocioso":
                    self._ir_dormir(cidadao)
                elif (
                    not self.eh_noite
                    and cidadao.estado in ("indo_dormir", "dormindo")
                ):
                    cidadao.estado = "ocioso"
                    cidadao.caminho = []

            if cidadao.estado == "indo_mover":
                if not cidadao.caminho:
                    self._retomar_funcao(cidadao)
            elif cidadao.estado == "indo_descanso":
                if not cidadao.caminho:
                    cidadao.estado = "descansando"
            elif cidadao.estado == "indo_recolher":
                if not cidadao.caminho:
                    cidadao.estado = "recolhido"
            elif cidadao.estado == "recolhido":
                pass
            elif cidadao.estado == "indo_dormir":
                if not cidadao.caminho:
                    cidadao.estado = "dormindo"
            elif cidadao.estado == "dormindo":
                pass
            elif cidadao.estado == "indo_pesca":
                if not cidadao.caminho:
                    cidadao.estado = "pescando"
                    bonus = bonus_xp(cidadao.experiencia, "pescador")
                    cidadao.tempo = PESCA_SEGUNDOS / max(0.5, bonus)
            elif cidadao.estado == "pescando":
                cidadao.tempo -= dt
                if cidadao.tempo <= 0:
                    bonus = bonus_xp(cidadao.experiencia, "pescador")
                    peixes = int(PEIXES_POR_CICLO * bonus)
                    self.reino.recursos["alimento"] = min(
                        self.reino.capacidade_alimento,
                        self.reino.recursos["alimento"] + peixes,
                    )
                    cidadao.experiencia["pescador"] = (
                        cidadao.experiencia.get("pescador", 0.0) + 10.0
                    )
                    cidadao.tempo = PESCA_SEGUNDOS / max(0.5, bonus)
            elif cidadao.estado == "descansando":
                cidadao.hp = min(
                    cidadao.hp_max,
                    cidadao.hp
                    + cidadao.hp_max * CURA_POR_DIA * dt / DIA_SEGUNDOS,
                )
                if cidadao.hp >= cidadao.hp_max - 0.01:
                    self._retomar_apos_descanso(cidadao)
            elif cidadao.estado == "indo_predio":
                if not cidadao.caminho:
                    if cidadao.alvo_predio in self.mapa.posicoes:
                        cidadao.estado = "trabalhando"
                        cidadao.x, cidadao.y = self._ponto_servico(
                            cidadao.alvo_predio, cidadao.id
                        )
                    else:
                        cidadao.estado = "ocioso"
                        cidadao.profissao = "ocioso"
            elif cidadao.estado == "indo_arvore":
                if not cidadao.caminho:
                    arvore = self.arvores.get(cidadao.alvo_arvore or (-1, -1))
                    if arvore is not None and arvore.estado == "adulta":
                        cidadao.estado = "cortando"
                        bonus = bonus_xp(cidadao.experiencia, "madeireiro")
                        cidadao.tempo = CHOP_SEGUNDOS / max(0.5, bonus)
                    else:
                        self._procurar_arvore(cidadao)
            elif cidadao.estado == "cortando":
                cidadao.tempo -= dt
                if cidadao.tempo <= 0:
                    arvore = self.arvores.get(cidadao.alvo_arvore or (-1, -1))
                    if arvore is not None and arvore.estado == "adulta":
                        arvore.vida -= 1
                        nivel = nivel_por_xp(
                            cidadao.experiencia.get("madeireiro", 0.0)
                        )
                        extras = max(0, (nivel - 1) // 5)
                        cidadao.troncos += TRONCOS_POR_ARVORE + extras
                        cidadao.experiencia["madeireiro"] = (
                            cidadao.experiencia.get("madeireiro", 0.0) + 12.0
                        )
                        if arvore.vida <= 0:
                            self._cortar_arvore(arvore)
                            cidadao.alvo_arvore = None
                            self._ir_entregar(cidadao)
                        else:
                            bonus = bonus_xp(
                                cidadao.experiencia, "madeireiro"
                            )
                            cidadao.tempo = CHOP_SEGUNDOS / max(0.5, bonus)
                    else:
                        self._procurar_arvore(cidadao)
            elif cidadao.estado == "indo_rocha":
                if not cidadao.caminho:
                    rocha = self.rochas.get(cidadao.alvo_rocha or (-1, -1))
                    if rocha is not None and rocha.estado == "adulta":
                        cidadao.estado = "minerando"
                        bonus = bonus_xp(cidadao.experiencia, "pedreiro")
                        cidadao.tempo = MINE_SEGUNDOS / max(0.5, bonus)
                    else:
                        self._procurar_rocha(cidadao)
            elif cidadao.estado == "minerando":
                cidadao.tempo -= dt
                if cidadao.tempo <= 0:
                    rocha = self.rochas.get(cidadao.alvo_rocha or (-1, -1))
                    if rocha is not None and rocha.estado == "adulta":
                        rocha.vida -= 1
                        nivel = nivel_por_xp(
                            cidadao.experiencia.get("pedreiro", 0.0)
                        )
                        extras = max(0, (nivel - 1) // 5)
                        cidadao.pedras += PEDRA_POR_GOLPE + extras
                        cidadao.experiencia["pedreiro"] = (
                            cidadao.experiencia.get("pedreiro", 0.0) + 15.0
                        )
                        if rocha.vida <= 0:
                            self._esgotar_rocha(rocha)
                            cidadao.alvo_rocha = None
                            self._ir_entregar_pedra(cidadao)
                        else:
                            bonus = bonus_xp(
                                cidadao.experiencia, "pedreiro"
                            )
                            cidadao.tempo = MINE_SEGUNDOS / max(0.5, bonus)
                    else:
                        self._procurar_rocha(cidadao)
            elif cidadao.estado == "trabalhando":
                cidadao.tempo_xp += dt
                if cidadao.tempo_xp >= DIA_SEGUNDOS:
                    cidadao.experiencia[cidadao.profissao] = (
                        cidadao.experiencia.get(cidadao.profissao, 0.0) + 8.0
                    )
                    cidadao.tempo_xp = 0.0
            elif cidadao.estado == "indo_entrega":
                if not cidadao.caminho:
                    self._entregar_troncos(cidadao)
            elif cidadao.estado == "indo_entrega_pedra":
                if not cidadao.caminho:
                    self._entregar_pedra(cidadao)
            elif cidadao.estado == "aguardando":
                cidadao.tempo -= dt
                if cidadao.tempo <= 0:
                    if cidadao.pedras > 0:
                        self._ir_entregar_pedra(cidadao)
                    elif cidadao.troncos > 0:
                        self._ir_entregar(cidadao)
                    elif cidadao.profissao == "pedreiro":
                        self._procurar_rocha(cidadao)
                    else:
                        self._procurar_arvore(cidadao)

    def _retomar_funcao(self, cidadao: Cidadao) -> None:
        if cidadao.profissao == "madeireiro":
            self._procurar_arvore(cidadao)
        elif cidadao.profissao == "pedreiro":
            self._procurar_rocha(cidadao)
        elif cidadao.profissao == "pescador":
            self._procurar_pesca(cidadao)
        else:
            cidadao.estado = "ocioso"

    def _retomar_apos_descanso(self, cidadao: Cidadao) -> None:
        if cidadao.profissao in ("madeireiro", "pedreiro", "pescador"):
            self._retomar_funcao(cidadao)
            return
        tipo = PREDIO_POR_TRABALHO.get(cidadao.profissao)
        if tipo is None:
            cidadao.estado = "ocioso"
            return
        candidatos = [
            c
            for c in self.reino.instancias(tipo)
            if c.id in self.mapa.posicoes
            and c.trabalhadores < self.reino.vagas_instancia(c.id)
        ]
        candidatos.sort(
            key=lambda c: distancia(
                cidadao.x, cidadao.y, *self.mapa.centro_mundo(c.id)
            )
        )
        for construcao in candidatos:
            if self._caminho_para_predio(cidadao, construcao.id):
                cidadao.estado = "indo_predio"
                cidadao.alvo_predio = construcao.id
                return
        cidadao.estado = "ocioso"

    def _ir_descansar(self, cidadao: Cidadao) -> None:
        cidadao.alvo_predio = None
        cidadao.alvo_arvore = None
        cidadao.alvo_rocha = None
        cidadao.alvo_mover = None
        destinos = []
        casas = self.reino.primeira_instancia("casas")
        if casas is not None and casas.id in self.mapa.posicoes:
            destinos.append(casas.id)
        if CASTELO_ID in self.mapa.posicoes:
            destinos.append(CASTELO_ID)
        for id_predio in destinos:
            if self._caminho_para_predio(cidadao, id_predio):
                cidadao.estado = "indo_descanso"
                cidadao.alvo_predio = id_predio
                return
        cidadao.caminho = []
        cidadao.estado = "descansando"

    def _ir_dormir(self, cidadao: Cidadao) -> None:
        cidadao.alvo_predio = None
        cidadao.alvo_arvore = None
        cidadao.alvo_rocha = None
        cidadao.alvo_pesca = None
        cidadao.alvo_mover = None
        for id_predio in self._destinos_descanso():
            if self._caminho_para_predio(cidadao, id_predio):
                cidadao.estado = "indo_dormir"
                cidadao.alvo_predio = id_predio
                return
        cidadao.caminho = []
        cidadao.estado = "dormindo"

    def _limpar_alvos_cidadao(self, cidadao: Cidadao) -> None:
        for outro in [*self.inimigos, *self.errantes]:
            if outro.alvo_cidadao is cidadao:
                outro.alvo_cidadao = None
                outro.caminho = []

    def _ir_recolher(self, cidadao: Cidadao) -> None:
        cidadao.alvo_predio = None
        cidadao.alvo_arvore = None
        cidadao.alvo_rocha = None
        cidadao.alvo_pesca = None
        cidadao.alvo_mover = None
        self._limpar_alvos_cidadao(cidadao)
        destinos: list[int] = []
        if CASTELO_ID in self.mapa.posicoes:
            destinos.append(CASTELO_ID)
        casas = self.reino.primeira_instancia("casas")
        if casas is not None and casas.id in self.mapa.posicoes:
            destinos.append(casas.id)
        for id_predio in destinos:
            if self._caminho_para_predio(cidadao, id_predio):
                cidadao.estado = "indo_recolher"
                cidadao.alvo_predio = id_predio
                return
        cidadao.caminho = []
        cidadao.estado = "recolhido"

    def _destinos_descanso(self) -> list[int]:
        destinos: list[int] = []
        casas = self.reino.primeira_instancia("casas")
        if casas is not None and casas.id in self.mapa.posicoes:
            destinos.append(casas.id)
        if CASTELO_ID in self.mapa.posicoes:
            destinos.append(CASTELO_ID)
        return destinos

    def ordenar_pesca(
        self, cidadaos: list[Cidadao], col: int, row: int
    ) -> str | None:
        if self.mapa.tipo_tile(col, row) != AGUA:
            return "O alvo não é água."
        if not cidadaos:
            return "Nenhum cidadão selecionado."
        atribuidos = 0
        for cidadao in cidadaos:
            if not self._caminho_para_arvore(cidadao, col, row):
                continue
            cidadao.profissao = "pescador"
            cidadao.estado = "indo_pesca"
            cidadao.alvo_predio = None
            cidadao.alvo_arvore = None
            cidadao.alvo_rocha = None
            cidadao.alvo_pesca = (col, row)
            atribuidos += 1
        if atribuidos == 0:
            return "Não há terra firme ao lado dessa água."
        return None

    def _procurar_pesca(self, cidadao: Cidadao) -> None:
        aguas = []
        for row in range(LINHAS):
            for col in range(COLUNAS):
                if self.mapa.tiles[row][col] != AGUA:
                    continue
                aguas.append((col, row))
        aguas.sort(
            key=lambda t: distancia(
                cidadao.x, cidadao.y, *self.mapa.centro_tile_mundo(*t)
            )
        )
        for col, row in aguas[:40]:
            if self._caminho_para_arvore(cidadao, col, row):
                cidadao.profissao = "pescador"
                cidadao.estado = "indo_pesca"
                cidadao.alvo_predio = None
                cidadao.alvo_arvore = None
                cidadao.alvo_rocha = None
                cidadao.alvo_pesca = (col, row)
                return
        cidadao.estado = "aguardando"
        cidadao.tempo = 5.0

    def pontos_disponiveis_cidadao(self, cidadao: Cidadao) -> int:
        ganhos = sum(
            nivel_por_xp(xp) - 1 for xp in cidadao.experiencia.values()
        )
        return max(0, ganhos - cidadao.pontos_usados)

    def evoluir_cidadao(self, cidadao: Cidadao, atributo: str) -> bool:
        if self.pontos_disponiveis_cidadao(cidadao) <= 0:
            return False
        cidadao.pontos_usados += 1
        cidadao.atributos[atributo] = cidadao.atributos.get(atributo, 0) + 1
        if atributo == "vida":
            cidadao.hp_max += 5.0
            cidadao.hp += 5.0
        elif atributo == "velocidade":
            cidadao.velocidade *= 1.03
        return True

    def pontos_disponiveis_soldado(self, soldado: Soldado) -> int:
        return max(0, nivel_por_xp(soldado.xp) - 1 - soldado.pontos_usados)

    def evoluir_soldado(self, soldado: Soldado, atributo: str) -> bool:
        if self.pontos_disponiveis_soldado(soldado) <= 0:
            return False
        soldado.pontos_usados += 1
        soldado.atributos[atributo] = soldado.atributos.get(atributo, 0) + 1
        if atributo == "vida":
            soldado.hp_max += 10.0
            soldado.hp += 10.0
        elif atributo == "dano":
            soldado.ataque *= 1.05
        elif atributo == "velocidade":
            soldado.velocidade *= 1.03
        return True

    def _procurar_arvore(self, cidadao: Cidadao) -> None:
        adultas = [
            arvore
            for arvore in self.arvores.values()
            if arvore.estado == "adulta"
        ]
        adultas.sort(
            key=lambda a: distancia(
                cidadao.x, cidadao.y, *self.mapa.centro_tile_mundo(a.col, a.row)
            )
        )
        for arvore in adultas[:20]:
            if self._caminho_para_arvore(cidadao, arvore.col, arvore.row):
                cidadao.profissao = "madeireiro"
                cidadao.estado = "indo_arvore"
                cidadao.alvo_predio = None
                cidadao.alvo_rocha = None
                cidadao.alvo_arvore = (arvore.col, arvore.row)
                return
        cidadao.estado = "aguardando"
        cidadao.tempo = 5.0

    def _procurar_rocha(self, cidadao: Cidadao) -> None:
        adultas = [
            rocha
            for rocha in self.rochas.values()
            if rocha.estado == "adulta"
        ]
        adultas.sort(
            key=lambda r: distancia(
                cidadao.x, cidadao.y, *self.mapa.centro_tile_mundo(r.col, r.row)
            )
        )
        for rocha in adultas[:20]:
            if self._caminho_para_arvore(cidadao, rocha.col, rocha.row):
                cidadao.profissao = "pedreiro"
                cidadao.estado = "indo_rocha"
                cidadao.alvo_predio = None
                cidadao.alvo_arvore = None
                cidadao.alvo_rocha = (rocha.col, rocha.row)
                return
        cidadao.estado = "aguardando"
        cidadao.tempo = 5.0

    def _esgotar_rocha(self, rocha: Rocha) -> None:
        rocha.estado = "esgotada"
        rocha.regrow = random.uniform(ROCHA_REGROW_MIN, ROCHA_REGROW_MAX)
        self.mapa.definir_tile(rocha.col, rocha.row, GRAMA)
        self.chunks_rochas_dirty.add(
            (rocha.col // TAMANHO_CHUNK, rocha.row // TAMANHO_CHUNK)
        )
        rx, ry = self.mapa.centro_tile_mundo(rocha.col, rocha.row)
        nivel = self.nivel_area(rx, ry)
        if random.random() < min(0.5, 0.06 * nivel):
            self.reino.adicionar_recurso_raro("cristal_runico", 1)

    def _atualizar_rochas(self, dt: float) -> None:
        fator = dt / DIA_SEGUNDOS
        remover: list[tuple[int, int]] = []
        for chave, rocha in self.rochas.items():
            if rocha.estado != "esgotada":
                continue
            rocha.regrow -= fator
            if rocha.regrow > 0:
                continue
            if chave in self.mapa.ocupacao:
                remover.append(chave)
            elif self._unidade_na_tile(rocha.col, rocha.row):
                rocha.regrow = 0.25
            else:
                rocha.estado = "adulta"
                rocha.regrow = 0.0
                rocha.vida = rocha.vida_max
                self.mapa.definir_tile(rocha.col, rocha.row, ROCHA)
                self.chunks_rochas_dirty.add(
                    (rocha.col // TAMANHO_CHUNK, rocha.row // TAMANHO_CHUNK)
                )
        for chave in remover:
            self.rochas.pop(chave, None)
            self.chunks_rochas_dirty.add(
                (chave[0] // TAMANHO_CHUNK, chave[1] // TAMANHO_CHUNK)
            )

    def rocha_em_ponto(self, x: float, y: float) -> Rocha | None:
        return self.rochas.get(self.mapa.tile_do_mundo(x, y))

    def _ir_entregar_pedra(self, cidadao: Cidadao) -> None:
        destinos = [
            c
            for c in self.reino.instancias("mina")
            if c.id in self.mapa.posicoes
        ]
        destinos.sort(
            key=lambda c: distancia(
                cidadao.x, cidadao.y, *self.mapa.centro_mundo(c.id)
            )
        )
        for construcao in destinos:
            if self._caminho_para_predio(cidadao, construcao.id):
                cidadao.estado = "indo_entrega_pedra"
                cidadao.alvo_predio = construcao.id
                return
        if self._caminho_para_predio(cidadao, CASTELO_ID):
            cidadao.estado = "indo_entrega_pedra"
            cidadao.alvo_predio = CASTELO_ID
            return
        cidadao.estado = "aguardando"
        cidadao.tempo = 3.0

    def _entregar_pedra(self, cidadao: Cidadao) -> None:
        self.reino.recursos["pedra"] += cidadao.pedras
        cidadao.pedras = 0
        self._procurar_rocha(cidadao)

    def _ir_entregar(self, cidadao: Cidadao) -> None:
        madeireiras = [
            c
            for c in self.reino.instancias("madeireira")
            if c.id in self.mapa.posicoes
        ]
        madeireiras.sort(
            key=lambda c: distancia(
                cidadao.x, cidadao.y, *self.mapa.centro_mundo(c.id)
            )
        )
        for construcao in madeireiras:
            if self._caminho_para_predio(cidadao, construcao.id):
                cidadao.estado = "indo_entrega"
                cidadao.alvo_predio = construcao.id
                return
        cidadao.estado = "aguardando"
        cidadao.tempo = 5.0 if not madeireiras else 3.0

    def _entregar_troncos(self, cidadao: Cidadao) -> None:
        espaco = max(
            0.0,
            self.reino.capacidade_troncos - self.reino.recursos["troncos"],
        )
        depositado = min(cidadao.troncos, espaco)
        self.reino.recursos["troncos"] += depositado
        cidadao.troncos -= depositado
        if cidadao.troncos > 0:
            cidadao.estado = "aguardando"
            cidadao.tempo = 2.0
        else:
            self._procurar_arvore(cidadao)

    def _atualizar_refino(self, dt: float) -> None:
        for construcao in self.reino.instancias("madeireira"):
            serradores = [
                cidadao
                for cidadao in self.cidadaos
                if cidadao.estado == "trabalhando"
                and cidadao.alvo_predio == construcao.id
            ]
            if not serradores:
                continue
            bonus_total = sum(
                bonus_xp(cidadao.experiencia, "serrador")
                for cidadao in serradores
            ) * (1.0 + 0.10 * (construcao.nivel - 1))
            taxa = REFINO_POR_DIA * bonus_total
            progresso = (
                construcao.progressos.get("madeira", 0.0)
                + taxa * dt / DIA_SEGUNDOS
            )
            produzido = int(progresso)
            construcao.progressos["madeira"] = progresso - produzido
            if produzido <= 0:
                continue
            disponivel = self.reino.recursos["troncos"]
            usado = min(float(produzido), disponivel)
            if usado > 0:
                self.reino.recursos["troncos"] -= usado
                self.reino.recursos["madeira"] += usado
            progresso_xp = usado / max(0.0001, bonus_total)
            for cidadao in serradores:
                cidadao.experiencia["serrador"] = (
                    cidadao.experiencia.get("serrador", 0.0)
                    + progresso_xp * 4.0
                )

    # ------------------------------------------------------------------
    # Caravanas
    # ------------------------------------------------------------------
    def criar_caravana(
        self, cidadaos: list[Cidadao], soldados: list[Soldado]
    ) -> tuple[bool, str, Caravana | None]:
        membros = [
            membro
            for membro in [*cidadaos, *soldados]
            if not (isinstance(membro, Cidadao) and membro.rei)
        ]
        if not membros:
            return False, "Selecione cidadãos ou soldados (o Rei fica).", None
        x = sum(m.x for m in membros) / len(membros)
        y = sum(m.y for m in membros) / len(membros)
        carga: dict[str, float] = {}
        for recurso, quantidade in CONSTRUCOES["posto"]["custo"].items():
            retirado = min(float(quantidade), self.reino.recursos[recurso])
            if retirado > 0:
                self.reino.recursos[recurso] -= retirado
                carga[recurso] = carga.get(recurso, 0.0) + retirado
        comida = min(
            self.reino.recursos["alimento"],
            max(10.0, 3.0 * len(membros)),
        )
        self.reino.recursos["alimento"] -= comida
        carga["alimento"] = comida + carga.get("alimento", 0.0)
        for cidadao in cidadaos:
            if cidadao in self.cidadaos:
                self.cidadaos.remove(cidadao)
        for soldado in soldados:
            if soldado in self.soldados:
                self.soldados.remove(soldado)
        caravana = Caravana(
            id=self._novo_id(),
            x=x,
            y=y,
            membros=membros,
            carga=carga,
        )
        self.caravanas.append(caravana)
        self.revelar_ao_redor(x, y, raio=1)
        self._log(
            f"Caravana #{caravana.id} formada com {len(membros)} membro(s)."
        )
        self._sincronizar()
        return True, "ok", caravana

    def ordenar_caravana_mover(
        self, caravana: Caravana, x: float, y: float
    ) -> str | None:
        tile = self.mapa.tile_do_mundo(x, y)
        destino = self.mapa.tile_livre_proximo(*tile, raio_max=6)
        if destino is None:
            return "Destino inválido."
        if not self._caminho_para_tile(caravana, destino):
            return "Não foi possível traçar o caminho."
        caravana.estado = "viajando"
        return None

    def _atualizar_caravanas(self, dt: float) -> None:
        for caravana in list(self.caravanas):
            if caravana.caminho:
                mover_entidade(caravana, dt, self.mapa)
                if not caravana.caminho:
                    caravana.estado = "parada"
            self.revelar_ao_redor(caravana.x, caravana.y, raio=1)

    def _processar_dia_caravanas(self) -> None:
        for caravana in list(self.caravanas):
            membros = len(caravana.membros)
            if membros <= 0:
                self.caravanas.remove(caravana)
                continue
            consumo = membros * CONSUMO_POR_PESSOA
            comida = caravana.carga.get("alimento", 0.0)
            if comida >= consumo:
                caravana.carga["alimento"] = comida - consumo
                continue
            caravana.carga["alimento"] = 0.0
            mortos = min(membros, max(1, math.ceil(membros * 0.1)))
            for _ in range(mortos):
                if caravana.membros:
                    caravana.membros.pop()
                    self.reino.populacao = max(0, self.reino.populacao - 1)
            self._log(
                f"Caravana #{caravana.id} sem comida: {mortos} membro(s) morreram."
            )
            if not caravana.membros:
                self.caravanas.remove(caravana)

    def _processar_dia_postos(self) -> None:
        for posto in self.reino.instancias("posto"):
            trabalhadores = posto.trabalhadores
            if trabalhadores <= 0:
                continue
            consumo = trabalhadores * CONSUMO_POR_PESSOA
            comida = posto.armazem.get("alimento", 0.0)
            if comida >= consumo:
                posto.armazem["alimento"] = comida - consumo
                continue
            posto.armazem["alimento"] = 0.0
            mortos = min(trabalhadores, max(1, math.ceil(trabalhadores * 0.1)))
            removidos = 0
            for cidadao in list(self.cidadaos):
                if removidos >= mortos:
                    break
                if (
                    cidadao.alvo_predio == posto.id
                    and cidadao.estado == "trabalhando"
                ):
                    self.cidadaos.remove(cidadao)
                    self._limpar_alvos_cidadao(cidadao)
                    removidos += 1
                    self.reino.populacao = max(0, self.reino.populacao - 1)
                    if cidadao.rei:
                        self.reino.rei_morto = True
                        self.reino._derrota("O Rei morreu de fome no posto.")
            if removidos:
                self._log(
                    f"Posto #{posto.id} sem comida: {removidos} colono(s) morreram."
                )

    def pode_fundar_posto_caravana(self, caravana: Caravana) -> bool:
        custo = CONSTRUCOES["posto"]["custo"]
        for recurso, quantidade in custo.items():
            if caravana.carga.get(recurso, 0.0) < quantidade:
                return False
        col = int(caravana.x // TILE) - 1
        row = int(caravana.y // TILE) - 1
        return self.mapa.pode_posicionar(
            "posto",
            col,
            row,
            self.tiles_ocupados_unidades(),
            ignorar_territorio=True,
        )

    def fundar_posto_caravana(
        self, caravana: Caravana
    ) -> tuple[bool, str]:
        custo = CONSTRUCOES["posto"]["custo"]
        for recurso, quantidade in custo.items():
            if caravana.carga.get(recurso, 0.0) < quantidade:
                return False, "A caravana não tem recursos suficientes."
        col = int(caravana.x // TILE) - 1
        row = int(caravana.y // TILE) - 1
        bloqueios = self.tiles_ocupados_unidades()
        if not self.mapa.pode_posicionar(
            "posto", col, row, bloqueios, ignorar_territorio=True
        ):
            return False, "Local inválido para fundar o posto."
        for recurso, quantidade in custo.items():
            caravana.carga[recurso] -= quantidade
        identificador = self.reino._criar_instancia("posto", 1)
        if not self.mapa.posicionar(
            identificador,
            "posto",
            col,
            row,
            bloqueios,
            ignorar_territorio=True,
        ):
            self.reino.remover_instancia(identificador)
            for recurso, quantidade in custo.items():
                caravana.carga[recurso] = (
                    caravana.carga.get(recurso, 0.0) + quantidade
                )
            return False, "Não foi possível posicionar o posto."
        cx, cy = self.mapa.centro_mundo(identificador)
        self.revelar_ao_redor(cx, cy, raio=2)
        self._log(
            f"Posto avançado #{identificador} fundado pela caravana "
            f"#{caravana.id}."
        )
        return True, "ok"

    def posto_perto(self, x: float, y: float, raio: float = 4 * TILE):
        melhor = None
        melhor_dist = raio
        for posto in self.reino.instancias("posto"):
            if posto.id not in self.mapa.posicoes:
                continue
            px, py = self.mapa.centro_mundo(posto.id)
            dist = distancia(x, y, px, py)
            if dist < melhor_dist:
                melhor = posto
                melhor_dist = dist
        return melhor

    def pode_coletar_posto(self, caravana: Caravana) -> bool:
        posto = self.posto_perto(caravana.x, caravana.y)
        if posto is None:
            return False
        if self.reino.total_armazem(posto) <= 0:
            return False
        return sum(caravana.carga.values()) < caravana.capacidade

    def coletar_posto_caravana(self, caravana: Caravana) -> tuple[bool, str]:
        posto = self.posto_perto(caravana.x, caravana.y)
        if posto is None:
            return False, "Nenhum posto avançado por perto."
        if self.reino.total_armazem(posto) <= 0:
            return False, "O armazém do posto está vazio."
        for recurso, quantidade in list(posto.armazem.items()):
            if quantidade <= 0:
                continue
            espaco = caravana.capacidade - sum(caravana.carga.values())
            if espaco <= 0:
                break
            retirado = min(quantidade, espaco)
            caravana.carga[recurso] = (
                caravana.carga.get(recurso, 0.0) + retirado
            )
            posto.armazem[recurso] = quantidade - retirado
        self._log(f"Caravana #{caravana.id} recolheu do posto #{posto.id}.")
        return True, "ok"

    def perto_do_reino(self, caravana: Caravana) -> bool:
        cx, cy = self.mapa.centro_mundo(CASTELO_ID)
        return distancia(caravana.x, caravana.y, cx, cy) <= TILE * 12

    def pode_entregar_caravana(self, caravana: Caravana) -> bool:
        return self.perto_do_reino(caravana) and sum(caravana.carga.values()) > 0

    def entregar_caravana(self, caravana: Caravana) -> tuple[bool, str]:
        if not self.perto_do_reino(caravana):
            return False, "Leve a caravana até o castelo para entregar."
        if sum(caravana.carga.values()) <= 0:
            return False, "A caravana está vazia."
        entregue = 0
        for recurso, quantidade in list(caravana.carga.items()):
            if quantidade <= 0:
                continue
            if recurso == "alimento":
                self.reino.recursos["alimento"] = min(
                    self.reino.capacidade_alimento,
                    self.reino.recursos["alimento"] + quantidade,
                )
            elif recurso in self.reino.recursos:
                self.reino.recursos[recurso] += quantidade
            else:
                self.reino.recursos_raros[recurso] = (
                    self.reino.recursos_raros.get(recurso, 0.0) + quantidade
                )
            entregue += quantidade
            caravana.carga[recurso] = 0.0
        caravana.carga = {
            recurso: valor
            for recurso, valor in caravana.carga.items()
            if valor > 0
        }
        self._log(
            f"Caravana #{caravana.id} entregou {entregue:.0f} recursos ao reino."
        )
        return True, "ok"

    def dispensar_caravana(self, caravana: Caravana) -> None:
        perdido = sum(caravana.carga.values())
        if perdido > 0:
            self._log(
                f"Caravana #{caravana.id} dispensada e perdeu "
                f"{perdido:.0f} recursos não entregues."
            )
        caravana.carga = {}
        for membro in caravana.membros:
            membro.x = caravana.x
            membro.y = caravana.y
            if isinstance(membro, Soldado):
                membro.poste = (caravana.x, caravana.y)
                self.soldados.append(membro)
            else:
                membro.estado = "ocioso"
                membro.profissao = "ocioso"
                membro.caminho = []
                membro.alvo_predio = None
                membro.alvo_arvore = None
                membro.alvo_rocha = None
                self.cidadaos.append(membro)
        self._log(f"Caravana #{caravana.id} dispensada.")
        self.caravanas.remove(caravana)
        self._sincronizar()

    def caravana_em_ponto(
        self, x: float, y: float, raio: float = 22
    ) -> Caravana | None:
        for caravana in self.caravanas:
            if distancia(x, y, caravana.x, caravana.y) <= raio:
                return caravana
        return None

    # ------------------------------------------------------------------
    # Combate
    # ------------------------------------------------------------------
    def _atualizar_defesas_postos(self, dt: float) -> None:
        for tiro in list(self.tiros_postos):
            tiro["tempo"] -= dt
            if tiro["tempo"] <= 0:
                self.tiros_postos.remove(tiro)
        for posto in self.reino.instancias("posto"):
            if posto.id not in self.mapa.posicoes or posto.hp <= 0:
                self.cooldowns_postos.pop(posto.id, None)
                continue
            dados = self.reino.defesa_posto(posto)
            dano = dados["dano"]
            if dano <= 0:
                continue
            cx, cy = self.mapa.centro_mundo(posto.id)
            alcance = dados["alcance"] * TILE
            alvo = None
            menor = alcance
            for inimigo in [*self.inimigos, *self.errantes]:
                dist = distancia(cx, cy, inimigo.x, inimigo.y)
                if dist < menor:
                    menor = dist
                    alvo = inimigo
            if alvo is None:
                self.cooldowns_postos[posto.id] = 0.0
                continue
            cooldown = self.cooldowns_postos.get(posto.id, 0.0) - dt
            if cooldown <= 0.0:
                self._dano_inimigo(alvo, dano)
                self.tiros_postos.append(
                    {
                        "x1": cx,
                        "y1": cy,
                        "x2": alvo.x,
                        "y2": alvo.y,
                        "tempo": 0.18,
                    }
                )
                cooldown = dados["intervalo"]
            self.cooldowns_postos[posto.id] = cooldown

    def _verificar_raid(self) -> None:
        if self.reino.derrota:
            return
        if (
            not self.raid_ativo
            and self.reino.ataques_ativos
            and self.reino.dia >= self.reino.proximo_ataque_dia
        ):
            self._iniciar_raid()
        elif self.raid_ativo and not self.inimigos:
            self._finalizar_raid()

    def _postos_validos_raid(self) -> list:
        return [
            posto
            for posto in self.reino.instancias("posto")
            if posto.id in self.mapa.posicoes and posto.hp > 0
        ]

    def _ponto_raid_posto(self, id_posto: int) -> tuple[float, float]:
        cx, cy = self.mapa.centro_mundo(id_posto)
        for _ in range(80):
            angulo = random.uniform(0.0, math.tau)
            dist = random.uniform(TILE * 6, TILE * 10)
            px = cx + math.cos(angulo) * dist
            py = cy + math.sin(angulo) * dist
            col, row = self.mapa.tile_do_mundo(px, py)
            if not (0 <= col < COLUNAS and 0 <= row < LINHAS):
                continue
            if not self.mapa.tile_passavel(col, row):
                continue
            livre = self.mapa.tile_livre_proximo(col, row, raio_max=2)
            if livre is None:
                continue
            return self.mapa.centro_tile_mundo(*livre)
        return self.mapa.ponto_borda(random)

    def _iniciar_raid(self) -> None:
        self.raid_ativo = True
        self.reino.aviso_ataque = False
        self.raid_posto_id = None
        postos = self._postos_validos_raid()
        alvo_posto = None
        if (
            postos
            and self.reino.dia >= 4
            and random.random() < 0.45
        ):
            alvo_posto = random.choice(postos)
            self.raid_posto_id = alvo_posto.id
            x, y = self._ponto_raid_posto(alvo_posto.id)
            self.raid_origem = f"Posto #{alvo_posto.id}"
            quantidade = max(2, min(6, 2 + self.reino.dia // 12))
            self._log(
                f"Uma horda de {quantidade} inimigo(s) ataca o "
                f"Posto #{alvo_posto.id}!"
            )
        else:
            quantidade = max(2, min(8, 2 + self.reino.dia // 8))
            x, y = self.mapa.ponto_borda(random)
            margem = 80
            if y <= margem:
                self.raid_origem = "Norte"
            elif y >= ALTURA_MUNDO - margem:
                self.raid_origem = "Sul"
            elif x <= margem:
                self.raid_origem = "Oeste"
            else:
                self.raid_origem = "Leste"
            col, row = self.mapa.tile_do_mundo(x, y)
            livre = self.mapa.tile_livre_proximo(col, row, raio_max=8)
            if livre is not None:
                x, y = self.mapa.centro_tile_mundo(*livre)
            self._log(
                f"Uma horda de {quantidade} inimigo(s) ataca o reino!"
            )
        self.inimigos = []
        self._raid_inimigos = quantidade
        self._raid_dano = 0
        self._raid_perdas = 0
        for _ in range(quantidade):
            inimigo = Inimigo(
                id=self._novo_id(),
                x=x + random.uniform(-50, 50),
                y=y + random.uniform(-50, 50),
                hp=40.0 + self.reino.dia * 1.8,
                hp_max=40.0 + self.reino.dia * 1.8,
                ataque=4.0 + self.reino.dia * 0.2,
                velocidade=170.0,
                velocidade_base=170.0,
            )
            inimigo.tempo_recalculo = 0.0
            if alvo_posto is not None:
                inimigo.alvo_estrutura = alvo_posto.id
            self.inimigos.append(inimigo)

    def _finalizar_raid(self) -> None:
        self.raid_ativo = False
        posto_alvo = (
            self.reino.construcoes.get(self.raid_posto_id)
            if self.raid_posto_id is not None
            else None
        )
        defendeu_posto = (
            self.raid_posto_id is None
            or (
                posto_alvo is not None
                and posto_alvo.id in self.mapa.posicoes
            )
        )
        if defendeu_posto:
            recompensa_ouro = 10 + self.reino.dia
            recompensa_alimento = 15 + self.reino.dia * 2
            self.reino.recursos["ouro"] += recompensa_ouro
            self.reino.recursos["alimento"] = min(
                self.reino.capacidade_alimento,
                self.reino.recursos["alimento"] + recompensa_alimento,
            )
        else:
            recompensa_ouro = 0
            recompensa_alimento = 0
        alvo = (
            "Castelo"
            if self.raid_posto_id is None
            else f"Posto #{self.raid_posto_id}"
        )
        self.reino.ultimo_combate = {
            "vitoria": defendeu_posto,
            "alvo": alvo,
            "inimigos": self._raid_inimigos,
            "perdas": self._raid_perdas,
            "dano_castelo": int(self._raid_dano),
            "ouro": recompensa_ouro,
            "alimento": recompensa_alimento,
        }
        if defendeu_posto:
            self._log(
                f"{alvo} defendido! {self._raid_inimigos} inimigo(s) "
                f"derrotado(s). Perdas: {self._raid_perdas} soldado(s)."
            )
        else:
            self._log(
                f"O ataque ao {alvo} terminou, mas o posto foi destruído."
            )
        self.reino.proximo_ataque_dia = self.reino.dia + random.randint(10, 15)
        self.reino.aviso_ataque = False
        self.raid_origem = ""
        self.raid_posto_id = None
        for soldado in self.soldados:
            soldado.ordem_ataque = False
            soldado.alvo = None

    def _alvo_vivo(self, alvo) -> bool:
        if alvo is None:
            return False
        return any(
            entidade is alvo for entidade in [*self.inimigos, *self.errantes]
        )

    def _distancia_rect(
        self,
        x: float,
        y: float,
        rect_x: float,
        rect_y: float,
        rect_w: float,
        rect_h: float,
    ) -> float:
        dx = max(rect_x - x, 0.0, x - (rect_x + rect_w))
        dy = max(rect_y - y, 0.0, y - (rect_y + rect_h))
        return math.hypot(dx, dy)

    def _escolher_estrutura(
        self,
        inimigo,
        apenas_defensivas: bool = False,
        raio: float | None = None,
    ) -> int | None:
        estruturas = []
        for construcao in self.reino.instancias():
            if construcao.id not in self.mapa.posicoes or construcao.hp <= 0:
                continue
            if apenas_defensivas and construcao.tipo not in ("muralha", "barricada"):
                continue
            dist = distancia(
                inimigo.x, inimigo.y, *self.mapa.centro_mundo(construcao.id)
            )
            if raio is not None and dist > raio:
                continue
            estruturas.append((dist, construcao.id))
        estruturas.sort()
        for _, id_estrutura in estruturas:
            if self._caminho_para_predio(inimigo, id_estrutura):
                return id_estrutura
        return None

    def _escolher_cidadao(self, inimigo) -> Cidadao | None:
        melhor = None
        melhor_dist = AGGRO_CIVIL
        for cidadao in self.cidadaos:
            if cidadao.estado in ("indo_recolher", "recolhido"):
                continue
            dist = distancia(inimigo.x, inimigo.y, cidadao.x, cidadao.y)
            if dist < melhor_dist:
                melhor = cidadao
                melhor_dist = dist
        return melhor

    def _atacar_cidadao(self, inimigo, cidadao: Cidadao, dt: float) -> bool:
        if not any(c is cidadao for c in self.cidadaos):
            return False
        if cidadao.estado in ("indo_recolher", "recolhido"):
            return False
        dist = distancia(inimigo.x, inimigo.y, cidadao.x, cidadao.y)
        if dist > inimigo.alcance:
            inimigo.tempo_recalculo -= dt
            if inimigo.tempo_recalculo <= 0 or not inimigo.caminho:
                achou = self._caminho_para_ponto(
                    inimigo, cidadao.x, cidadao.y
                )
                inimigo.tempo_recalculo = TEMPO_RECALCULO
                if not achou:
                    self._mover_direto(inimigo, cidadao.x, cidadao.y, dt)
            else:
                mover_entidade(inimigo, dt, self.mapa)
            return True
        inimigo.caminho = []
        inimigo.cooldown -= dt
        if inimigo.cooldown <= 0:
            cidadao.hp -= inimigo.ataque
            inimigo.cooldown = 1.0
            if cidadao.hp <= 0:
                self.cidadaos.remove(cidadao)
                self.reino.populacao = max(0, self.reino.populacao - 1)
                if cidadao.rei:
                    self.reino.rei_morto = True
                    self._log("O Rei foi morto em combate!")
                    self.reino._derrota("O Rei morreu.")
                else:
                    self._log("Um cidadão foi morto por inimigos.")
                for outro in [*self.inimigos, *self.errantes]:
                    if outro.alvo_cidadao is cidadao:
                        outro.alvo_cidadao = None
                        outro.caminho = []
                if self.reino.populacao <= 0:
                    self.reino._derrota("A população chegou a zero.")
        return True

    def _atacar_estrutura(
        self, inimigo, id_estrutura: int, dt: float
    ) -> bool:
        construcao = self.reino.construcoes.get(id_estrutura)
        if construcao is None or id_estrutura not in self.mapa.posicoes:
            return False
        x, y, largura, altura = self.mapa.rect_mundo(id_estrutura)
        dist_rect = self._distancia_rect(
            inimigo.x, inimigo.y, x, y, largura, altura
        )
        if dist_rect <= max(inimigo.alcance, TILE * 1.4):
            inimigo.caminho = []
            inimigo.cooldown -= dt
            if inimigo.cooldown <= 0:
                construcao.hp -= inimigo.ataque
                inimigo.cooldown = 1.0
                if construcao.hp <= 0:
                    self._destruir_estrutura(id_estrutura)
            return True
        inimigo.tempo_recalculo -= dt
        if inimigo.tempo_recalculo <= 0 or not inimigo.caminho:
            achou = self._caminho_para_predio(inimigo, id_estrutura)
            inimigo.tempo_recalculo = TEMPO_RECALCULO
            if not achou:
                cx, cy = self.mapa.centro_mundo(id_estrutura)
                self._mover_direto(inimigo, cx, cy, dt)
        else:
            mover_entidade(inimigo, dt, self.mapa)
        return True

    def _destruir_estrutura(self, id_estrutura: int) -> None:
        construcao = self.reino.construcoes.get(id_estrutura)
        if construcao is None:
            return
        nome = NOMES_CONSTRUCOES.get(construcao.tipo, construcao.tipo)
        self.reino.remover_instancia(id_estrutura)
        self.mapa.remover(id_estrutura)
        self._log(f"{nome} #{id_estrutura} foi destruída.")
        for inimigo in self.inimigos:
            if inimigo.alvo_estrutura == id_estrutura:
                inimigo.alvo_estrutura = None
                inimigo.caminho = []
        self.cooldowns_postos.pop(id_estrutura, None)
        for cidadao in self.cidadaos:
            if cidadao.alvo_predio == id_estrutura:
                cidadao.alvo_predio = None
                cidadao.caminho = []
                cidadao.estado = "ocioso"
                cidadao.profissao = "ocioso"

    def nivel_area(self, x: float, y: float) -> int:
        cx, cy = self.mapa.centro_mundo(CASTELO_ID)
        dist = math.hypot(x - cx, y - cy) / (TILE * 12)
        return max(1, self.reino.dia // 10 + int(dist))

    def _atualizar_errantes_dia(self) -> None:
        for mina in self.reino.instancias("mina"):
            if mina.id not in self.mapa.posicoes:
                continue
            mx, my = self.mapa.centro_mundo(mina.id)
            nivel = self.nivel_area(mx, my)
            if random.random() < min(0.8, 0.12 * nivel) * mina.nivel:
                self.reino.adicionar_recurso_raro("minerio_arcano", 1)
        alvo = min(4, 1 + self.reino.dia // 10)
        if len(self.errantes) >= alvo:
            return
        faltam = alvo - len(self.errantes)
        cx, cy = self.mapa.centro_mundo(CASTELO_ID)
        for _ in range(faltam):
            for _tentativa in range(60):
                col = random.randrange(0, COLUNAS)
                row = random.randrange(0, LINHAS)
                px, py = self.mapa.centro_tile_mundo(col, row)
                if math.hypot(px - cx, py - cy) < TILE * 16:
                    continue
                if not self.mapa.tile_passavel(col, row):
                    continue
                quantidade = random.randint(2, 4)
                nivel = self.nivel_area(px, py)
                for _ in range(quantidade):
                    inimigo = Inimigo(
                        id=self._novo_id(),
                        x=px + random.uniform(-40, 40),
                        y=py + random.uniform(-40, 40),
                        hp=30.0 + nivel * 15.0,
                        hp_max=30.0 + nivel * 15.0,
                        ataque=3.0 + nivel * 2.0,
                        velocidade=150.0,
                        velocidade_base=150.0,
                        lar=(px, py),
                    )
                    self.errantes.append(inimigo)
                self._log("Inimigos rondam as áreas distantes do reino.")
                break

    def _matar_errante(self, inimigo) -> None:
        if not any(a is inimigo for a in self.errantes):
            return
        self.errantes.remove(inimigo)
        nivel = self.nivel_area(inimigo.x, inimigo.y)
        if random.random() < min(0.7, 0.1 * nivel):
            self.reino.adicionar_recurso_raro("essencia_sombria", 1)
        ouro = 2 + self.reino.dia // 4
        self.reino.recursos["ouro"] += ouro
        if random.random() < 0.5:
            self.reino.recursos["pedra"] += 1 + self.reino.dia // 6
        self._log(f"Inimigo errante derrotado: +{ouro} ouro.")

    def _atacar_soldado_errante(self, inimigo, soldado, dt: float) -> bool:
        if not any(s is soldado for s in self.soldados):
            return False
        dist = distancia(inimigo.x, inimigo.y, soldado.x, soldado.y)
        if dist > inimigo.alcance:
            inimigo.tempo_recalculo -= dt
            if inimigo.tempo_recalculo <= 0 or not inimigo.caminho:
                achou = self._caminho_para_ponto(inimigo, soldado.x, soldado.y)
                inimigo.tempo_recalculo = TEMPO_RECALCULO
                if not achou:
                    self._mover_direto(inimigo, soldado.x, soldado.y, dt)
            else:
                mover_entidade(inimigo, dt, self.mapa)
            return True
        inimigo.caminho = []
        inimigo.cooldown -= dt
        if inimigo.cooldown <= 0:
            self._dano_soldado(soldado, inimigo.ataque)
            inimigo.cooldown = 1.0
        return True

    def _atualizar_errantes(self, dt: float) -> None:
        if not self.errantes:
            return
        for inimigo in list(self.errantes):
            if inimigo.hp <= 0:
                self._matar_errante(inimigo)
                continue
            self._aplicar_slow(inimigo, dt)
            cidadao = None
            melhor = AGGRO_ERRANTE
            for c in self.cidadaos:
                dist = distancia(inimigo.x, inimigo.y, c.x, c.y)
                if dist < melhor:
                    melhor = dist
                    cidadao = c
            soldado = None
            melhor = AGGRO_ERRANTE
            for s in self.soldados:
                dist = distancia(inimigo.x, inimigo.y, s.x, s.y)
                if dist < melhor:
                    melhor = dist
                    soldado = s
            if cidadao is not None:
                self._atacar_cidadao(inimigo, cidadao, dt)
                continue
            if soldado is not None:
                self._atacar_soldado_errante(inimigo, soldado, dt)
                continue
            inimigo.tempo_recalculo -= dt
            if inimigo.tempo_recalculo <= 0 or not inimigo.caminho:
                lar_col, lar_row = self.mapa.tile_do_mundo(*inimigo.lar)
                alvo_col = lar_col + random.randint(-6, 6)
                alvo_row = lar_row + random.randint(-6, 6)
                destino = self.mapa.tile_livre_proximo(alvo_col, alvo_row, raio_max=4)
                if destino is not None:
                    self._caminho_para_tile(inimigo, destino)
                inimigo.tempo_recalculo = random.uniform(2.5, 4.5)
            else:
                mover_entidade(inimigo, dt, self.mapa)

    def _dano_soldado(self, soldado, dano: float) -> None:
        if soldado.escudo > 0:
            absorvido = min(soldado.escudo, dano)
            soldado.escudo -= absorvido
            dano -= absorvido
        soldado.hp -= max(0.0, dano)

    def _dano_inimigo(self, inimigo, dano: float) -> None:
        inimigo.hp -= dano
        if inimigo.hp > 0:
            return
        if any(a is inimigo for a in self.inimigos):
            self._matar_inimigo(inimigo)
        elif any(a is inimigo for a in self.errantes):
            self._matar_errante(inimigo)

    def _aplicar_slow(self, inimigo, dt: float) -> None:
        if inimigo.slow_timer > 0:
            inimigo.slow_timer -= dt
            inimigo.velocidade = max(20.0, inimigo.velocidade_base * 0.55)
        else:
            inimigo.velocidade = inimigo.velocidade_base

    def _atualizar_inimigos(self, dt: float) -> None:
        if not self.inimigos:
            return
        castle_x, castle_y, castle_w, castle_h = self.mapa.rect_mundo(CASTELO_ID)
        castle_cx = castle_x + castle_w / 2
        castle_cy = castle_y + castle_h / 2

        for inimigo in list(self.inimigos):
            self._aplicar_slow(inimigo, dt)
            alvo = None
            melhor = AGGRO_INIMIGO
            for soldado in self.soldados:
                dist = distancia(inimigo.x, inimigo.y, soldado.x, soldado.y)
                if dist < melhor:
                    alvo = soldado
                    melhor = dist
            inimigo.alvo_soldado = alvo

            if alvo is not None:
                dist = distancia(inimigo.x, inimigo.y, alvo.x, alvo.y)
                if dist > inimigo.alcance:
                    inimigo.tempo_recalculo -= dt
                    if inimigo.tempo_recalculo <= 0 or not inimigo.caminho:
                        achou = self._caminho_para_ponto(inimigo, alvo.x, alvo.y)
                        inimigo.tempo_recalculo = TEMPO_RECALCULO
                        if not achou:
                            self._mover_direto(inimigo, alvo.x, alvo.y, dt)
                    else:
                        mover_entidade(inimigo, dt, self.mapa)
                else:
                    inimigo.caminho = []
                    inimigo.cooldown -= dt
                    if inimigo.cooldown <= 0:
                        self._dano_soldado(alvo, inimigo.ataque)
                        inimigo.cooldown = 1.0
            else:
                if inimigo.alvo_cidadao is not None:
                    if self._atacar_cidadao(
                        inimigo, inimigo.alvo_cidadao, dt
                    ):
                        continue
                    inimigo.alvo_cidadao = None

                cidadao = self._escolher_cidadao(inimigo)
                if cidadao is not None:
                    inimigo.alvo_cidadao = cidadao
                    self._atacar_cidadao(inimigo, cidadao, dt)
                    continue

                if inimigo.alvo_estrutura is not None:
                    if self._atacar_estrutura(
                        inimigo, inimigo.alvo_estrutura, dt
                    ):
                        continue
                    inimigo.alvo_estrutura = None

                estrutura_proxima = self._escolher_estrutura(
                    inimigo, raio=RAIO_ESTRUTURA
                )
                if estrutura_proxima is not None:
                    inimigo.alvo_estrutura = estrutura_proxima
                    self._atacar_estrutura(
                        inimigo, estrutura_proxima, dt
                    )
                    continue

                dist_rect = self._distancia_rect(
                    inimigo.x,
                    inimigo.y,
                    castle_x,
                    castle_y,
                    castle_w,
                    castle_h,
                )
                if dist_rect <= max(inimigo.alcance, TILE * 1.4):
                    inimigo.caminho = []
                    inimigo.cooldown -= dt
                    if inimigo.cooldown <= 0:
                        self.reino.hp_castelo = max(
                            0.0, self.reino.hp_castelo - inimigo.ataque
                        )
                        self._raid_dano += inimigo.ataque
                        inimigo.cooldown = 1.0
                else:
                    inimigo.tempo_recalculo -= dt
                    if inimigo.tempo_recalculo <= 0 or not inimigo.caminho:
                        opcoes = adjacentes(
                            *self.mapa.posicoes[CASTELO_ID],
                            *PEGADAS["castelo"],
                        )
                        destino = melhor_adjacente(
                            self.mapa,
                            opcoes,
                            (inimigo.x, inimigo.y),
                        )
                        if destino is not None:
                            achou = self._caminho_para_tile(inimigo, destino)
                        else:
                            achou = False
                        inimigo.tempo_recalculo = TEMPO_RECALCULO * 2
                        if not achou:
                            estrutura = self._escolher_estrutura(
                                inimigo, apenas_defensivas=True
                            )
                            if estrutura is None:
                                estrutura = self._escolher_estrutura(inimigo)
                            if estrutura is not None:
                                inimigo.alvo_estrutura = estrutura
                            else:
                                self._mover_direto(
                                    inimigo, castle_cx, castle_cy, dt
                                )
                    else:
                        mover_entidade(inimigo, dt, self.mapa)

            if inimigo.hp <= 0:
                self._matar_inimigo(inimigo)

    def _matar_inimigo(self, inimigo) -> None:
        if not any(a is inimigo for a in self.inimigos):
            return
        self.inimigos.remove(inimigo)
        nivel = self.nivel_area(inimigo.x, inimigo.y)
        if random.random() < min(0.6, 0.08 * nivel):
            self.reino.adicionar_recurso_raro("essencia_sombria", 1)
        ouro = 2 + self.reino.dia // 3
        self.reino.recursos["ouro"] += ouro
        pedra = 1 + self.reino.dia // 5
        self.reino.recursos["pedra"] += pedra
        if random.random() < 0.5:
            alimento = 2 + self.reino.dia // 4
            self.reino.recursos["alimento"] = min(
                self.reino.capacidade_alimento,
                self.reino.recursos["alimento"] + alimento,
            )
        self._log(f"Inimigo derrotado: +{ouro} ouro, +{pedra} pedra.")

    def _limpar_soldados_mortos(self) -> None:
        vivos = []
        for soldado in self.soldados:
            if soldado.hp <= 0:
                self._raid_perdas += 1
                self.reino.populacao = max(0, self.reino.populacao - 1)
                self._log("Um soldado morreu em combate.")
            else:
                vivos.append(soldado)
        self.soldados = vivos

    def _executar_ataque(self, soldado, alvo, dano: float) -> None:
        self._dano_inimigo(alvo, dano)
        classe = soldado.classe
        if classe == "destruidor":
            for outro in [*self.inimigos, *self.errantes]:
                if outro is alvo:
                    continue
                if distancia(alvo.x, alvo.y, outro.x, outro.y) <= 70:
                    self._dano_inimigo(outro, dano * 0.5)
        elif classe == "mago_eletrico":
            candidatos = sorted(
                (
                    distancia(alvo.x, alvo.y, o.x, o.y),
                    o,
                )
                for o in [*self.inimigos, *self.errantes]
                if o is not alvo
            )[:2]
            for dist, outro in candidatos:
                if dist <= TILE * 3:
                    self._dano_inimigo(outro, dano * 0.7)
        elif classe == "mago_gelo":
            alvo.slow_timer = 2.0

    def _suporte_curandeiro(self, soldado, dt: float) -> None:
        soldado.habilidade_timer -= dt
        if soldado.habilidade_timer <= 0:
            for aliado in self.soldados:
                if aliado is soldado:
                    continue
                if distancia(soldado.x, soldado.y, aliado.x, aliado.y) > TILE * 3:
                    continue
                if soldado.classe == "protetor":
                    aliado.escudo = min(45.0, aliado.escudo + 12.0)
                else:
                    aliado.hp = min(
                        aliado.hp_max, aliado.hp + aliado.hp_max * 0.12
                    )
            soldado.habilidade_timer = soldado.cooldown_max
            soldado.xp += 2.0

    def _atualizar_soldados(self, dt: float) -> None:
        if not self.soldados:
            return
        for soldado in list(self.soldados):
            if soldado.hp <= 0:
                continue
            base = BASE_TROPA.get(soldado.classe, "soldado")
            if base == "curandeiro":
                self._suporte_curandeiro(soldado, dt)
                dist = distancia(soldado.x, soldado.y, *soldado.poste)
                if dist > 24:
                    if not soldado.caminho:
                        self._caminho_para_ponto(
                            soldado, soldado.poste[0], soldado.poste[1]
                        )
                    mover_entidade(soldado, dt, self.mapa)
                continue

            alvo = None
            if soldado.ordem_ataque and self._alvo_vivo(soldado.alvo):
                alvo = soldado.alvo
            else:
                melhor = AGGRO_SOLDADO
                for inimigo in [*self.inimigos, *self.errantes]:
                    dist = distancia(soldado.x, soldado.y, inimigo.x, inimigo.y)
                    if dist < melhor:
                        melhor = dist
                        alvo = inimigo
            soldado.alvo = alvo

            if alvo is not None:
                dist = distancia(soldado.x, soldado.y, alvo.x, alvo.y)
                if dist > soldado.alcance:
                    soldado.tempo_recalculo -= dt
                    if soldado.tempo_recalculo <= 0 or not soldado.caminho:
                        achou = self._caminho_para_ponto(soldado, alvo.x, alvo.y)
                        soldado.tempo_recalculo = TEMPO_RECALCULO
                        if not achou:
                            self._mover_direto(soldado, alvo.x, alvo.y, dt)
                    else:
                        mover_entidade(soldado, dt, self.mapa)
                else:
                    soldado.caminho = []
                    soldado.cooldown -= dt
                    if soldado.cooldown <= 0:
                        nivel = nivel_por_xp(soldado.xp)
                        dano = soldado.ataque * (1.0 + 0.05 * (nivel - 1))
                        vivo = any(
                            a is alvo for a in [*self.inimigos, *self.errantes]
                        )
                        if vivo:
                            self._executar_ataque(soldado, alvo, dano)
                            soldado.xp += 4.0
                            if not any(
                                a is alvo
                                for a in [*self.inimigos, *self.errantes]
                            ):
                                soldado.xp += 12.0
                                soldado.alvo = None
                                soldado.ordem_ataque = False
                        soldado.cooldown = soldado.cooldown_max
            else:
                dist = distancia(soldado.x, soldado.y, *soldado.poste)
                if dist <= 24:
                    soldado.hp = min(
                        soldado.hp_max,
                        soldado.hp
                        + soldado.hp_max * CURA_POR_DIA * dt / DIA_SEGUNDOS,
                    )
                    soldado.escudo = max(0.0, soldado.escudo - 1.0 * dt)
                if dist > 24:
                    if not soldado.caminho:
                        self._caminho_para_ponto(
                            soldado, soldado.poste[0], soldado.poste[1]
                        )
                    mover_entidade(soldado, dt, self.mapa)

    def _ponto_servico(
        self, id_predio: int, id_cidadao: int
    ) -> tuple[float, float]:
        if id_predio not in self.mapa.posicoes:
            return (self.mapa.centro_castelo[0] * TILE, self.mapa.centro_castelo[1] * TILE)
        tipo = self.mapa.tipos[id_predio]
        col, row = self.mapa.posicoes[id_predio]
        largura, altura = PEGADAS[tipo]
        opcoes = adjacentes(col, row, largura, altura)
        validos = [
            tile for tile in opcoes if self.mapa.tile_passavel(*tile)
        ]
        if not validos:
            return self.mapa.centro_mundo(id_predio)
        validos.sort()
        tile = validos[(id_predio * 7 + id_cidadao) % len(validos)]
        x, y = self.mapa.centro_tile_mundo(*tile)
        return (x, y)

    def funcionarios_instancia(self, id_predio: int) -> list[Cidadao]:
        construcao = self.reino.construcoes.get(id_predio)
        if construcao is None:
            return []
        job = TRABALHO_POR_PREDIO.get(construcao.tipo)
        if job is None:
            return []
        return [
            c
            for c in self.cidadaos
            if c.alvo_predio == id_predio
            and c.profissao == job
            and c.estado in ("trabalhando", "indo_predio")
        ]

    def reposicionar_funcionarios(self, id_predio: int) -> None:
        for cidadao in self.cidadaos:
            if cidadao.alvo_predio != id_predio:
                continue
            cidadao.caminho = []
            if not self._caminho_para_predio(cidadao, id_predio):
                cidadao.estado = "ocioso"
                cidadao.profissao = "ocioso"
                cidadao.alvo_predio = None
            elif cidadao.estado == "trabalhando":
                cidadao.estado = "indo_predio"

    def liberar_instancia(self, id_predio: int) -> None:
        funcionarios = self.funcionarios_instancia(id_predio)
        self.ordenar_parar(funcionarios)

    def _separar_unidades(self, dt: float) -> None:
        entidades = [*self.cidadaos, *self.soldados, *self.inimigos]
        if len(entidades) < 2:
            return
        tamanho_celula = 48
        buckets: dict[tuple[int, int], list] = {}
        for entidade in entidades:
            chave = (
                int(entidade.x // tamanho_celula),
                int(entidade.y // tamanho_celula),
            )
            buckets.setdefault(chave, []).append(entidade)

        max_empurrao = max(1.0, 30.0 * dt)
        for entidade in entidades:
            chave = (
                int(entidade.x // tamanho_celula),
                int(entidade.y // tamanho_celula),
            )
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for outra in buckets.get((chave[0] + dx, chave[1] + dy), []):
                        if outra is entidade:
                            continue
                        if id(outra) < id(entidade):
                            continue
                        delta_x = entidade.x - outra.x
                        delta_y = entidade.y - outra.y
                        dist = math.hypot(delta_x, delta_y)
                        minimo = 24.0
                        if dist >= minimo:
                            continue
                        if dist < 0.01:
                            angulo = (id(entidade) % 360) * math.pi / 180
                            delta_x = math.cos(angulo)
                            delta_y = math.sin(angulo)
                            dist = 1.0
                        empurrao = min(max_empurrao, (minimo - dist) / 2)
                        novo_x = entidade.x + delta_x / dist * empurrao
                        novo_y = entidade.y + delta_y / dist * empurrao
                        col, row = self.mapa.tile_do_mundo(novo_x, novo_y)
                        if self.mapa.tile_passavel(col, row):
                            entidade.x = novo_x
                            entidade.y = novo_y
                        outro_x = outra.x - delta_x / dist * empurrao
                        outro_y = outra.y - delta_y / dist * empurrao
                        col2, row2 = self.mapa.tile_do_mundo(outro_x, outro_y)
                        if self.mapa.tile_passavel(col2, row2):
                            outra.x = outro_x
                            outra.y = outro_y

    # ------------------------------------------------------------------
    # Seleção
    # ------------------------------------------------------------------
    def cidadao_em_ponto(self, x: float, y: float, raio: float = 16) -> Cidadao | None:
        for cidadao in self.cidadaos:
            if distancia(x, y, cidadao.x, cidadao.y) <= raio:
                return cidadao
        return None

    def soldado_em_ponto(self, x: float, y: float, raio: float = 18) -> Soldado | None:
        for soldado in self.soldados:
            if distancia(x, y, soldado.x, soldado.y) <= raio:
                return soldado
        return None

    def inimigo_em_ponto(self, x: float, y: float, raio: float = 18) -> Inimigo | None:
        for inimigo in self.inimigos:
            if distancia(x, y, inimigo.x, inimigo.y) <= raio:
                return inimigo
        return None

    def unidades_no_rect(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> list:
        esquerda, direita = min(x1, x2), max(x1, x2)
        baixo, cima = min(y1, y2), max(y1, y2)
        selecionadas = []
        for entidade in [*self.cidadaos, *self.soldados]:
            if esquerda <= entidade.x <= direita and baixo <= entidade.y <= cima:
                selecionadas.append(entidade)
        return selecionadas

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def _serializar_membro(self, membro) -> dict:
        if isinstance(membro, Soldado):
            return {
                "tipo": "soldado",
                "x": membro.x,
                "y": membro.y,
                "hp": membro.hp,
                "hp_max": membro.hp_max,
                "ataque": membro.ataque,
                "classe": membro.classe,
                "xp": membro.xp,
                "poste": list(membro.poste),
                "atributos": membro.atributos,
                "pontos_usados": membro.pontos_usados,
            }
        return {
            "tipo": "cidadao",
            "x": membro.x,
            "y": membro.y,
            "profissao": membro.profissao,
            "troncos": membro.troncos,
            "pedras": membro.pedras,
            "hp": membro.hp,
            "hp_max": membro.hp_max,
            "experiencia": membro.experiencia,
            "atributos": membro.atributos,
            "pontos_usados": membro.pontos_usados,
            "rei": membro.rei,
        }

    def _desserializar_membro(self, info: dict):
        if info.get("tipo") == "soldado":
            soldado = Soldado(
                id=self._novo_id(),
                x=float(info.get("x", 0)),
                y=float(info.get("y", 0)),
                hp=float(info.get("hp", 50)),
                hp_max=float(info.get("hp_max", 50)),
                ataque=float(info.get("ataque", 10)),
                classe=str(info.get("classe", "soldado")),
                xp=float(info.get("xp", 0.0)),
                atributos={
                    str(chave): int(valor)
                    for chave, valor in info.get("atributos", {}).items()
                }
                if isinstance(info.get("atributos"), dict)
                else {},
                pontos_usados=int(info.get("pontos_usados", 0)),
            )
            poste = info.get("poste")
            if isinstance(poste, (list, tuple)) and len(poste) == 2:
                soldado.poste = (float(poste[0]), float(poste[1]))
            else:
                soldado.poste = (soldado.x, soldado.y)
            return soldado
        experiencia = info.get("experiencia", {})
        return Cidadao(
            id=self._novo_id(),
            x=float(info.get("x", 0)),
            y=float(info.get("y", 0)),
            profissao=str(info.get("profissao", "ocioso")),
            troncos=int(info.get("troncos", 0)),
            pedras=int(info.get("pedras", 0)),
            hp=float(info.get("hp", 30)),
            hp_max=float(info.get("hp_max", 30)),
            experiencia={
                str(chave): float(valor)
                for chave, valor in experiencia.items()
            }
            if isinstance(experiencia, dict)
            else {},
            atributos={
                str(chave): int(valor)
                for chave, valor in info.get("atributos", {}).items()
            }
            if isinstance(info.get("atributos"), dict)
            else {},
            pontos_usados=int(info.get("pontos_usados", 0)),
            rei=bool(info.get("rei", False)),
        )

    def to_dict(self) -> dict:
        return {
            "arvores": [
                {
                    "col": arvore.col,
                    "row": arvore.row,
                    "estado": arvore.estado,
                    "regrow": arvore.regrow,
                    "vida": arvore.vida,
                    "vida_max": arvore.vida_max,
                }
                for arvore in self.arvores.values()
            ],
            "rochas": [
                {
                    "col": rocha.col,
                    "row": rocha.row,
                    "estado": rocha.estado,
                    "regrow": rocha.regrow,
                    "vida": rocha.vida,
                    "vida_max": rocha.vida_max,
                }
                for rocha in self.rochas.values()
            ],
            "cidadaos": [
                {
                    "x": cidadao.x,
                    "y": cidadao.y,
                    "profissao": cidadao.profissao,
                    "estado": cidadao.estado,
                    "alvo_predio": cidadao.alvo_predio,
                    "alvo_arvore": list(cidadao.alvo_arvore)
                    if cidadao.alvo_arvore
                    else None,
                    "troncos": cidadao.troncos,
                    "pedras": cidadao.pedras,
                    "hp": cidadao.hp,
                    "hp_max": cidadao.hp_max,
                    "alvo_rocha": list(cidadao.alvo_rocha)
                    if cidadao.alvo_rocha
                    else None,
                    "alvo_pesca": list(cidadao.alvo_pesca)
                    if cidadao.alvo_pesca
                    else None,
                    "experiencia": cidadao.experiencia,
                    "atributos": cidadao.atributos,
                    "pontos_usados": cidadao.pontos_usados,
                    "rei": cidadao.rei,
                }
                for cidadao in self.cidadaos
            ],
            "soldados": [
                {
                    "x": soldado.x,
                    "y": soldado.y,
                    "hp": soldado.hp,
                    "hp_max": soldado.hp_max,
                    "ataque": soldado.ataque,
                    "classe": soldado.classe,
                    "poste": list(soldado.poste),
                    "xp": soldado.xp,
                    "atributos": soldado.atributos,
                    "pontos_usados": soldado.pontos_usados,
                }
                for soldado in self.soldados
            ],
            "caravanas": [
                {
                    "id": caravana.id,
                    "x": caravana.x,
                    "y": caravana.y,
                    "estado": caravana.estado,
                    "carga": caravana.carga,
                    "membros": [
                        self._serializar_membro(membro)
                        for membro in caravana.membros
                    ],
                }
                for caravana in self.caravanas
            ],
            "fog": [list(chunk) for chunk in self.fog],
            "proximo_id": self.proximo_id,
        }

    @classmethod
    def from_dict(cls, reino: Reino, mapa: Mapa, dados: dict) -> "Mundo":
        mundo = cls(reino, mapa)
        mundo.arvores = {}
        mundo.cidadaos = []
        mundo.soldados = []
        mundo.caravanas = []
        mundo.inimigos = []
        mundo.raid_ativo = False
        mundo._dia_anterior = reino.dia

        for info in dados.get("arvores", []):
            col, row = int(info["col"]), int(info["row"])
            if not (0 <= col < COLUNAS and 0 <= row < LINHAS):
                continue
            arvore = Arvore(
                col=col,
                row=row,
                estado=str(info.get("estado", "adulta")),
                regrow=float(info.get("regrow", 0.0)),
                vida=int(info.get("vida", 3)),
                vida_max=int(info.get("vida_max", 3)),
            )
            mundo.arvores[(col, row)] = arvore
            if arvore.estado == "adulta":
                mapa.definir_tile(col, row, FLORESTA)
            else:
                mapa.definir_tile(col, row, GRAMA)

        for row in range(LINHAS):
            for col in range(COLUNAS):
                if (
                    mapa.tiles[row][col] == FLORESTA
                    and (col, row) not in mundo.arvores
                    and (col, row) not in mapa.ocupacao
                ):
                    mundo.arvores[(col, row)] = Arvore(col=col, row=row)

        ids_por_tipo: dict[str, int] = {}
        for construcao in reino.instancias():
            ids_por_tipo.setdefault(construcao.tipo, construcao.id)

        mundo.rochas = {}
        for info in dados.get("rochas", []):
            col, row = int(info["col"]), int(info["row"])
            if not (0 <= col < COLUNAS and 0 <= row < LINHAS):
                continue
            rocha = Rocha(
                col=col,
                row=row,
                estado=str(info.get("estado", "adulta")),
                regrow=float(info.get("regrow", 0.0)),
                vida=int(info.get("vida", ROCHA_VIDA_MAX)),
                vida_max=int(info.get("vida_max", ROCHA_VIDA_MAX)),
            )
            mundo.rochas[(col, row)] = rocha
            if rocha.estado == "adulta":
                mapa.definir_tile(col, row, ROCHA)
            else:
                mapa.definir_tile(col, row, GRAMA)
        for row in range(LINHAS):
            for col in range(COLUNAS):
                if (
                    mapa.tiles[row][col] == ROCHA
                    and (col, row) not in mundo.rochas
                    and (col, row) not in mapa.ocupacao
                ):
                    mundo.rochas[(col, row)] = Rocha(
                        col=col, row=row, vida=ROCHA_VIDA_MAX,
                        vida_max=ROCHA_VIDA_MAX,
                    )

        for info in dados.get("cidadaos", []):
            experiencia = info.get("experiencia", {})
            cidadao = Cidadao(
                id=mundo._novo_id(),
                x=float(info.get("x", 0)),
                y=float(info.get("y", 0)),
                profissao=str(info.get("profissao", "ocioso")),
                estado="ocioso",
                troncos=int(info.get("troncos", 0)),
                pedras=int(info.get("pedras", 0)),
                hp=float(info.get("hp", 30.0)),
                hp_max=float(info.get("hp_max", 30.0)),
                experiencia={
                    str(chave): float(valor)
                    for chave, valor in experiencia.items()
                }
                if isinstance(experiencia, dict)
                else {},
                atributos={
                    str(chave): int(valor)
                    for chave, valor in info.get("atributos", {}).items()
                }
                if isinstance(info.get("atributos"), dict)
                else {},
                pontos_usados=int(info.get("pontos_usados", 0)),
                rei=bool(info.get("rei", False)),
            )
            alvo = info.get("alvo_arvore")
            if isinstance(alvo, (list, tuple)) and len(alvo) == 2:
                cidadao.alvo_arvore = (int(alvo[0]), int(alvo[1]))
            alvo_rocha = info.get("alvo_rocha")
            if isinstance(alvo_rocha, (list, tuple)) and len(alvo_rocha) == 2:
                cidadao.alvo_rocha = (int(alvo_rocha[0]), int(alvo_rocha[1]))
            alvo_pesca = info.get("alvo_pesca")
            if isinstance(alvo_pesca, (list, tuple)) and len(alvo_pesca) == 2:
                cidadao.alvo_pesca = (int(alvo_pesca[0]), int(alvo_pesca[1]))
            predio = info.get("alvo_predio")
            if isinstance(predio, str):
                cidadao.alvo_predio = ids_por_tipo.get(predio)
            elif isinstance(predio, int):
                cidadao.alvo_predio = predio
            mundo.cidadaos.append(cidadao)

        for info in dados.get("soldados", []):
            hp_max = float(info.get("hp_max", 70))
            soldado = Soldado(
                id=mundo._novo_id(),
                x=float(info.get("x", 0)),
                y=float(info.get("y", 0)),
                hp=float(info.get("hp", hp_max)),
                hp_max=hp_max,
                ataque=float(info.get("ataque", 16)),
                classe=str(info.get("classe", "soldado")),
                xp=float(info.get("xp", 0.0)),
                atributos={
                    str(chave): int(valor)
                    for chave, valor in info.get("atributos", {}).items()
                }
                if isinstance(info.get("atributos"), dict)
                else {},
                pontos_usados=int(info.get("pontos_usados", 0)),
            )
            poste = info.get("poste")
            if isinstance(poste, (list, tuple)) and len(poste) == 2:
                soldado.poste = (float(poste[0]), float(poste[1]))
            mundo.soldados.append(soldado)

        for info in dados.get("caravanas", []):
            caravana = Caravana(
                id=mundo._novo_id(),
                x=float(info.get("x", 0)),
                y=float(info.get("y", 0)),
                estado=str(info.get("estado", "parada")),
                carga={
                    str(recurso): float(valor)
                    for recurso, valor in info.get("carga", {}).items()
                }
                if isinstance(info.get("carga"), dict)
                else {},
            )
            for membro_info in info.get("membros", []):
                caravana.membros.append(
                    mundo._desserializar_membro(membro_info)
                )
            if caravana.membros:
                mundo.caravanas.append(caravana)

        if isinstance(dados.get("fog"), list):
            mundo.fog = {
                (int(chunk[0]), int(chunk[1]))
                for chunk in dados["fog"]
                if isinstance(chunk, (list, tuple)) and len(chunk) == 2
            }

        mundo.proximo_id = max(
            int(dados.get("proximo_id", 1)),
            mundo.proximo_id,
        )
        mundo._retomar_cidadaos()
        mundo._sincronizar()
        return mundo

    def _retomar_cidadaos(self) -> None:
        for cidadao in self.cidadaos:
            if cidadao.alvo_predio and cidadao.alvo_predio in self.reino.construcoes:
                construcao = self.reino.construcoes[cidadao.alvo_predio]
                job = TRABALHO_POR_PREDIO.get(construcao.tipo)
                if job is not None and self._caminho_para_predio(
                    cidadao, cidadao.alvo_predio
                ):
                    cidadao.profissao = job
                    cidadao.estado = "indo_predio"
                    continue
            if cidadao.alvo_arvore:
                arvore = self.arvores.get(cidadao.alvo_arvore)
                if arvore is not None and arvore.estado == "adulta":
                    if self._caminho_para_arvore(cidadao, *cidadao.alvo_arvore):
                        cidadao.profissao = "madeireiro"
                        cidadao.estado = "indo_arvore"
                        continue
            if cidadao.alvo_rocha:
                rocha = self.rochas.get(cidadao.alvo_rocha)
                if rocha is not None and rocha.estado == "adulta":
                    if self._caminho_para_arvore(cidadao, *cidadao.alvo_rocha):
                        cidadao.profissao = "pedreiro"
                        cidadao.estado = "indo_rocha"
                        continue
            if cidadao.pedras > 0:
                cidadao.estado = "aguardando"
                cidadao.profissao = "pedreiro"
                cidadao.tempo = 0.1
            elif cidadao.troncos > 0:
                cidadao.estado = "aguardando"
                cidadao.profissao = "madeireiro"
                cidadao.tempo = 0.1
            else:
                cidadao.estado = "ocioso"
                cidadao.profissao = "ocioso"
            cidadao.alvo_predio = None
            cidadao.alvo_arvore = None
            cidadao.alvo_rocha = None
