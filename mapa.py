"""Mapa top-down do reino.

Trabalha com tiles, coordenadas de mundo e instâncias de construção por ID.
Nada gráfico aqui: a interface (main.py) desenha a partir deste estado.
"""

from __future__ import annotations

import math
import random
from collections import deque

TILE = 64
COLUNAS = 128
LINHAS = 96
LARGURA_MUNDO = COLUNAS * TILE
ALTURA_MUNDO = LINHAS * TILE
TAMANHO_CHUNK = 8

GRAMA = 0
TERRA = 1
FLORESTA = 2
AGUA = 3
ROCHA = 4
ESTRADA = 5

TIPOS_CONSTRUIVEIS = {GRAMA, TERRA}
TIPOS_PASSIVEIS = {GRAMA, TERRA, ESTRADA}

CASTELO_ID = 0

PEGADAS = {
    "castelo": (4, 4),
    "madeireira": (2, 1),
    "mina": (2, 1),
    "fazenda": (3, 2),
    "mercado": (2, 1),
    "ferraria": (1, 1),
    "quartel": (2, 2),
    "casas": (1, 1),
    "celeiro": (2, 1),
    "muralha": (1, 1),
    "barricada": (1, 1),
    "posto": (2, 1),
    "arquearia": (2, 1),
    "torre_magia": (1, 1),
    "santuario": (2, 1),
}

PREFERENCIA_TERRENO = {
    "madeireira": FLORESTA,
    "fazenda": AGUA,
    "mina": ROCHA,
}

RAIO_CONSTRUCAO = 10.5
RAIO_POSTO = 8.0

ALIAS_TIPOS = {"lenhador": "madeireira"}


class Mapa:
    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed if seed is not None else random.randrange(1, 1_000_000_000)
        self.tiles: list[list[int]] = [[GRAMA] * COLUNAS for _ in range(LINHAS)]
        self.ocupacao: dict[tuple[int, int], int] = {}
        self.posicoes: dict[int, tuple[int, int]] = {}
        self.tipos: dict[int, str] = {}
        self.castelo_pos = (COLUNAS // 2 - 2, LINHAS // 2 - 2)
        self._versao_passabilidade = 0
        self._versao_alcancaveis = -1
        self._alcancaveis: set[tuple[int, int]] = set()
        self._gerar()
        self._ocupar_castelo()

    # ------------------------------------------------------------------
    # Geração
    # ------------------------------------------------------------------
    @property
    def centro_castelo(self) -> tuple[float, float]:
        col, row = self.castelo_pos
        largura, altura = PEGADAS["castelo"]
        return (col + largura / 2, row + altura / 2)

    @property
    def versao_passabilidade(self) -> int:
        return self._versao_passabilidade

    def chunk_do_tile(self, col: int, row: int) -> tuple[int, int]:
        return (col // TAMANHO_CHUNK, row // TAMANHO_CHUNK)

    def chunks_visiveis(
        self,
        esquerda: float,
        direita: float,
        baixo: float,
        cima: float,
    ) -> list[tuple[int, int]]:
        c0 = max(0, int(esquerda // (TAMANHO_CHUNK * TILE)))
        c1 = min(COLUNAS // TAMANHO_CHUNK - 1, int(direita // (TAMANHO_CHUNK * TILE)))
        r0 = max(0, int(baixo // (TAMANHO_CHUNK * TILE)))
        r1 = min(LINHAS // TAMANHO_CHUNK - 1, int(cima // (TAMANHO_CHUNK * TILE)))
        return [
            (cx, cy)
            for cy in range(r0, r1 + 1)
            for cx in range(c0, c1 + 1)
        ]

    def _gerar(self) -> None:
        rng = random.Random(self.seed)
        cx, cy = self.centro_castelo

        for y in range(LINHAS):
            for x in range(COLUNAS):
                distancia = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if distancia <= 7:
                    self.tiles[y][x] = TERRA if rng.random() < 0.35 else GRAMA

        linha_central = int(cy)
        for x in range(COLUNAS):
            if rng.random() < 0.92:
                self.tiles[linha_central][x] = TERRA
                if rng.random() < 0.5 and linha_central + 1 < LINHAS:
                    self.tiles[linha_central + 1][x] = TERRA
        coluna_central = int(cx)
        for y in range(LINHAS):
            if rng.random() < 0.92:
                self.tiles[y][coluna_central] = TERRA
                if rng.random() < 0.5 and coluna_central + 1 < COLUNAS:
                    self.tiles[y][coluna_central + 1] = TERRA

        self._cluster(rng, AGUA, 9, 2, 5, 11)
        self._cluster(rng, FLORESTA, 34, 2, 5, 8)
        self._cluster(rng, ROCHA, 14, 1, 3, 8)

    def _cluster(
        self,
        rng: random.Random,
        tipo: int,
        quantidade: int,
        raio_min: int,
        raio_max: int,
        distancia_minima: float,
    ) -> None:
        cx, cy = self.centro_castelo
        for _ in range(quantidade):
            for _tentativa in range(80):
                x = rng.randrange(3, COLUNAS - 3)
                y = rng.randrange(3, LINHAS - 3)
                if math.hypot(x - cx, y - cy) < distancia_minima:
                    continue
                raio = rng.randint(raio_min, raio_max)
                for dy in range(-raio, raio + 1):
                    for dx in range(-raio, raio + 1):
                        if dx * dx + dy * dy > raio * raio:
                            continue
                        if rng.random() > 0.82:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < COLUNAS and 0 <= ny < LINHAS:
                            self.tiles[ny][nx] = tipo
                break

    def _ocupar_castelo(self) -> None:
        self.posicoes[CASTELO_ID] = self.castelo_pos
        self.tipos[CASTELO_ID] = "castelo"
        largura, altura = PEGADAS["castelo"]
        col, row = self.castelo_pos
        for x in range(col, col + largura):
            for y in range(row, row + altura):
                self.ocupacao[(x, y)] = CASTELO_ID

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def tipo_tile(self, col: int, row: int) -> int:
        if 0 <= col < COLUNAS and 0 <= row < LINHAS:
            return self.tiles[row][col]
        return ROCHA

    def tile_do_mundo(self, x: float, y: float) -> tuple[int, int]:
        return (int(x // TILE), int(y // TILE))

    def centro_tile_mundo(self, col: int, row: int) -> tuple[float, float]:
        return (col * TILE + TILE / 2, row * TILE + TILE / 2)

    def definir_tile(self, col: int, row: int, tipo: int) -> None:
        if 0 <= col < COLUNAS and 0 <= row < LINHAS:
            self.tiles[row][col] = tipo
            self._versao_passabilidade += 1

    def pode_construir_estrada(self, col: int, row: int) -> bool:
        if not (0 <= col < COLUNAS and 0 <= row < LINHAS):
            return False
        if (col, row) in self.ocupacao:
            return False
        return self.tiles[row][col] in (GRAMA, TERRA)

    def construir_estrada(self, col: int, row: int) -> bool:
        if not self.pode_construir_estrada(col, row):
            return False
        self.definir_tile(col, row, ESTRADA)
        return True

    def tem_estrada(self, col: int, row: int) -> bool:
        return (
            0 <= col < COLUNAS
            and 0 <= row < LINHAS
            and self.tiles[row][col] == ESTRADA
        )

    def fator_movimento(self, x: float, y: float) -> float:
        col, row = self.tile_do_mundo(x, y)
        return 1.5 if self.tem_estrada(col, row) else 1.0

    def _adjacentes_castelo(self) -> list[tuple[int, int]]:
        col, row = self.castelo_pos
        largura, altura = PEGADAS["castelo"]
        return [
            tile
            for tile in (
                (col - 1, row + y)
                for y in range(altura)
            )
            if True
        ] + [
            tile
            for tile in (
                (col + largura, row + y)
                for y in range(altura)
            )
        ] + [
            (x, row - 1) for x in range(col, col + largura)
        ] + [
            (x, row + altura) for x in range(col, col + largura)
        ]

    def _computar_alcancaveis(self) -> None:
        if self._versao_alcancaveis == self._versao_passabilidade:
            return
        fila: deque[tuple[int, int]] = deque()
        alcancaveis: set[tuple[int, int]] = set()
        for tile in self._adjacentes_castelo():
            if self.tile_passavel(*tile):
                if tile not in alcancaveis:
                    alcancaveis.add(tile)
                    fila.append(tile)
        while fila:
            col, row = fila.popleft()
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                vizinho = (col + dx, row + dy)
                if vizinho in alcancaveis:
                    continue
                if not self.tile_passavel(*vizinho):
                    continue
                if dx != 0 and dy != 0:
                    if not self.tile_passavel(col + dx, row):
                        continue
                    if not self.tile_passavel(col, row + dy):
                        continue
                alcancaveis.add(vizinho)
                fila.append(vizinho)
        self._alcancaveis = alcancaveis
        self._versao_alcancaveis = self._versao_passabilidade

    def tile_alcancavel(self, col: int, row: int) -> bool:
        self._computar_alcancaveis()
        return (col, row) in self._alcancaveis

    def tile_passavel(
        self, col: int, row: int, bloqueios: set[tuple[int, int]] | None = None
    ) -> bool:
        if not (0 <= col < COLUNAS and 0 <= row < LINHAS):
            return False
        if self.tiles[row][col] not in TIPOS_PASSIVEIS:
            return False
        if (col, row) in self.ocupacao:
            return False
        if bloqueios is not None and (col, row) in bloqueios:
            return False
        return True

    def tile_livre_proximo(
        self,
        col: int,
        row: int,
        raio_max: int = 12,
        bloqueios: set[tuple[int, int]] | None = None,
    ) -> tuple[int, int] | None:
        if self.tile_passavel(col, row, bloqueios):
            return (col, row)
        for raio in range(1, raio_max + 1):
            for dy in range(-raio, raio + 1):
                for dx in range(-raio, raio + 1):
                    if max(abs(dx), abs(dy)) != raio:
                        continue
                    nx, ny = col + dx, row + dy
                    if self.tile_passavel(nx, ny, bloqueios):
                        return (nx, ny)
        return None

    def tile_construivel(
        self, col: int, row: int, ignorar_id: int | None = None
    ) -> bool:
        if not (0 <= col < COLUNAS and 0 <= row < LINHAS):
            return False
        if self.tiles[row][col] not in TIPOS_CONSTRUIVEIS:
            return False
        ocupante = self.ocupacao.get((col, row))
        return ocupante is None or ocupante == ignorar_id

    def dentro_do_raio(self, tipo: str, col: int, row: int) -> bool:
        largura, altura = PEGADAS[tipo]
        centro_x = col + largura / 2
        centro_y = row + altura / 2
        centros: list[tuple[float, float, float]] = [
            (*self.centro_castelo, RAIO_CONSTRUCAO)
        ]
        for id_instancia, tipo_salvo in self.tipos.items():
            if tipo_salvo != "posto" or id_instancia not in self.posicoes:
                continue
            c_col, c_row = self.posicoes[id_instancia]
            p_larg, p_alt = PEGADAS["posto"]
            centros.append(
                (
                    c_col + p_larg / 2,
                    c_row + p_alt / 2,
                    RAIO_POSTO,
                )
            )
        for cx, cy, raio in centros:
            if math.hypot(centro_x - cx, centro_y - cy) <= raio:
                return True
        return False

    def pode_posicionar(
        self,
        tipo: str,
        col: int,
        row: int,
        bloqueios: set[tuple[int, int]] | None = None,
        ignorar_id: int | None = None,
        ignorar_territorio: bool = False,
    ) -> bool:
        if tipo not in PEGADAS or tipo == "castelo":
            return False
        largura, altura = PEGADAS[tipo]
        if largura <= 0 or altura <= 0:
            return False
        if not ignorar_territorio and not self.dentro_do_raio(tipo, col, row):
            return False
        for x in range(col, col + largura):
            for y in range(row, row + altura):
                if not self.tile_construivel(x, y, ignorar_id):
                    return False
                if bloqueios is not None and (x, y) in bloqueios:
                    return False
        if ignorar_territorio:
            return True
        self._computar_alcancaveis()
        opcoes = [
            tile
            for tile in (
                (x, y)
                for x in range(col - 1, col + largura + 1)
                for y in range(row - 1, row + altura + 1)
                if not (col <= x < col + largura and row <= y < row + altura)
            )
            if self.tile_passavel(*tile)
        ]
        return any(tile in self._alcancaveis for tile in opcoes)

    def posicionar(
        self,
        id_instancia: int,
        tipo: str,
        col: int,
        row: int,
        bloqueios: set[tuple[int, int]] | None = None,
        ignorar_territorio: bool = False,
    ) -> bool:
        if id_instancia == CASTELO_ID:
            return False
        if id_instancia in self.posicoes:
            self.remover(id_instancia)
        if not self.pode_posicionar(
            tipo, col, row, bloqueios, ignorar_territorio=ignorar_territorio
        ):
            return False
        largura, altura = PEGADAS[tipo]
        self.posicoes[id_instancia] = (col, row)
        self.tipos[id_instancia] = tipo
        for x in range(col, col + largura):
            for y in range(row, row + altura):
                self.ocupacao[(x, y)] = id_instancia
        self._versao_passabilidade += 1
        return True

    def remover(self, id_instancia: int) -> None:
        if id_instancia == CASTELO_ID or id_instancia not in self.posicoes:
            return
        tipo = self.tipos.get(id_instancia)
        if tipo is None or tipo not in PEGADAS:
            self.posicoes.pop(id_instancia, None)
            self.tipos.pop(id_instancia, None)
            return
        largura, altura = PEGADAS[tipo]
        col, row = self.posicoes.pop(id_instancia)
        self.tipos.pop(id_instancia, None)
        for x in range(col, col + largura):
            for y in range(row, row + altura):
                if self.ocupacao.get((x, y)) == id_instancia:
                    del self.ocupacao[(x, y)]
        self._versao_passabilidade += 1

    def existe_espaco(
        self, tipo: str, bloqueios: set[tuple[int, int]] | None = None
    ) -> bool:
        largura, altura = PEGADAS.get(tipo, (0, 0))
        if largura <= 0:
            return False
        cx, cy = self.centro_castelo
        raio = int(RAIO_CONSTRUCAO) + 2
        row0 = max(0, int(cy) - raio)
        row1 = min(LINHAS - altura, int(cy) + raio)
        col0 = max(0, int(cx) - raio)
        col1 = min(COLUNAS - largura, int(cx) + raio)
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                if self.pode_posicionar(tipo, col, row, bloqueios):
                    return True
        return False

    def construcao_no_ponto(self, x: float, y: float) -> int | None:
        col, row = self.tile_do_mundo(x, y)
        return self.ocupacao.get((col, row))

    def rect_mundo(self, id_instancia: int) -> tuple[float, float, float, float]:
        col, row = self.posicoes[id_instancia]
        tipo = self.tipos[id_instancia]
        largura, altura = PEGADAS[tipo]
        return (col * TILE, row * TILE, largura * TILE, altura * TILE)

    def centro_mundo(self, id_instancia: int) -> tuple[float, float]:
        x, y, largura, altura = self.rect_mundo(id_instancia)
        return (x + largura / 2, y + altura / 2)

    def ponto_borda(self, rng: random.Random) -> tuple[float, float]:
        lado = rng.randrange(4)
        margem = 60
        if lado == 0:
            return (rng.uniform(margem, LARGURA_MUNDO - margem), margem)
        if lado == 1:
            return (rng.uniform(margem, LARGURA_MUNDO - margem), ALTURA_MUNDO - margem)
        if lado == 2:
            return (margem, rng.uniform(margem, ALTURA_MUNDO - margem))
        return (LARGURA_MUNDO - margem, rng.uniform(margem, ALTURA_MUNDO - margem))

    # ------------------------------------------------------------------
    # Posicionamento inicial
    # ------------------------------------------------------------------
    def colocar_iniciais(self, itens: list[tuple[int, str]]) -> None:
        for id_instancia, tipo in itens:
            if id_instancia in self.posicoes or tipo not in PEGADAS:
                continue
            self._posicionar_melhor(id_instancia, tipo)

    def _posicionar_melhor(self, id_instancia: int, tipo: str) -> None:
        largura, altura = PEGADAS[tipo]
        if largura <= 0:
            return
        melhor: tuple[float, int, int] | None = None
        cx, cy = self.centro_castelo
        raio = int(RAIO_CONSTRUCAO) + 2
        row0 = max(0, int(cy) - raio)
        row1 = min(LINHAS - altura, int(cy) + raio)
        col0 = max(0, int(cx) - raio)
        col1 = min(COLUNAS - largura, int(cx) + raio)
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                if not self.pode_posicionar(tipo, col, row):
                    continue
                pontos = self._pontuacao(tipo, col, row)
                if melhor is None or pontos > melhor[0]:
                    melhor = (pontos, col, row)
        if melhor is None:
            self._abrir_espaco(id_instancia, tipo)
            return
        _, col, row = melhor
        self.posicionar(id_instancia, tipo, col, row)

    def _pontuacao(self, tipo: str, col: int, row: int) -> float:
        largura, altura = PEGADAS[tipo]
        cx, cy = self.centro_castelo
        centro_x = col + largura / 2
        centro_y = row + altura / 2
        distancia = math.hypot(centro_x - cx, centro_y - cy)
        pontos = -distancia * 2.0

        tipo_preferido = PREFERENCIA_TERRENO.get(tipo)
        if tipo_preferido is not None:
            adjacencia = 0
            for x in range(col - 2, col + largura + 2):
                for y in range(row - 2, row + altura + 2):
                    if self.tipo_tile(x, y) == tipo_preferido:
                        adjacencia += 1
            pontos += adjacencia * 6.0
        return pontos

    def _abrir_espaco(self, id_instancia: int, tipo: str) -> None:
        largura, altura = PEGADAS[tipo]
        cx, cy = self.centro_castelo
        for raio in range(0, 12):
            for row in range(int(cy) - raio, int(cy) + raio + 1):
                for col in range(int(cx) - raio, int(cx) + raio + 1):
                    if not (0 <= col < COLUNAS and 0 <= row < LINHAS):
                        continue
                    for x in range(col, col + largura):
                        for y in range(row, row + altura):
                            if 0 <= x < COLUNAS and 0 <= y < LINHAS:
                                if self.ocupacao.get((x, y)) is None:
                                    self.definir_tile(x, y, TERRA)
                    if self.pode_posicionar(tipo, col, row):
                        self.posicionar(id_instancia, tipo, col, row)
                        return

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "tiles": self.tiles,
            "posicoes": {
                str(id_instancia): [col, row]
                for id_instancia, (col, row) in self.posicoes.items()
            },
            "tipos": {
                str(id_instancia): tipo for id_instancia, tipo in self.tipos.items()
            },
        }

    @classmethod
    def from_dict(
        cls,
        dados: dict,
        ids_por_tipo: dict[str, int] | None = None,
    ) -> "Mapa":
        mapa = cls(seed=int(dados.get("seed", random.randrange(1, 1_000_000_000))))
        tiles = dados.get("tiles")
        tiles_ok = (
            isinstance(tiles, list)
            and len(tiles) == LINHAS
            and all(isinstance(linha, list) and len(linha) == COLUNAS for linha in tiles)
        )
        if tiles_ok:
            mapa.tiles = [[int(valor) for valor in linha] for linha in tiles]

        mapa.ocupacao = {}
        mapa.posicoes = {}
        mapa.tipos = {}
        mapa.castelo_pos = (COLUNAS // 2 - 2, LINHAS // 2 - 2)
        if not tiles_ok:
            mapa._ocupar_castelo()
            return mapa

        tipos_salvos = dados.get("tipos", {})
        for chave, pos in dados.get("posicoes", {}).items():
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                continue
            col, row = int(pos[0]), int(pos[1])
            try:
                id_instancia = int(chave)
                tipo = tipos_salvos.get(str(chave), tipos_salvos.get(chave))
            except (TypeError, ValueError):
                tipo = ALIAS_TIPOS.get(str(chave), str(chave))
                id_instancia = None
                if ids_por_tipo is not None:
                    id_instancia = ids_por_tipo.get(tipo)
            if id_instancia is None or tipo not in PEGADAS:
                continue
            if id_instancia == CASTELO_ID:
                continue
            largura, altura = PEGADAS[tipo]
            if (
                col < 0
                or row < 0
                or col + largura > COLUNAS
                or row + altura > LINHAS
            ):
                continue
            valido = True
            for x in range(col, col + largura):
                for y in range(row, row + altura):
                    if mapa.tiles[y][x] not in TIPOS_CONSTRUIVEIS:
                        valido = False
                    if (x, y) in mapa.ocupacao:
                        valido = False
            if not valido:
                continue
            mapa.posicoes[id_instancia] = (col, row)
            mapa.tipos[id_instancia] = tipo
            for x in range(col, col + largura):
                for y in range(row, row + altura):
                    mapa.ocupacao[(x, y)] = id_instancia

        mapa._ocupar_castelo()
        return mapa
