"""Busca de caminho (A*) na grade do mapa."""

from __future__ import annotations

import heapq
import math

from mapa import COLUNAS, LINHAS, Mapa

DIRECOES = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)


def _heuristica(a: tuple[int, int], b: tuple[int, int]) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def buscar_caminho(
    mapa: Mapa,
    inicio: tuple[int, int],
    destino: tuple[int, int],
    bloqueios: set[tuple[int, int]] | None = None,
    max_nos: int = 9000,
) -> list[tuple[int, int]] | None:
    if not mapa.tile_passavel(*destino, bloqueios):
        return None
    if not mapa.tile_passavel(*inicio, bloqueios):
        candidato = mapa.tile_livre_proximo(*inicio, raio_max=4, bloqueios=bloqueios)
        if candidato is None:
            return None
        inicio = candidato
    if inicio == destino:
        return []

    abertos: list[tuple[float, tuple[int, int]]] = [(0.0, inicio)]
    veio_de: dict[tuple[int, int], tuple[int, int]] = {}
    custo: dict[tuple[int, int], float] = {inicio: 0.0}
    visitados: set[tuple[int, int]] = set()

    expandidos = 0
    while abertos:
        if expandidos > max_nos:
            return None
        _, atual = heapq.heappop(abertos)
        if atual == destino:
            caminho: list[tuple[int, int]] = []
            while atual in veio_de:
                caminho.append(atual)
                atual = veio_de[atual]
            caminho.reverse()
            return caminho
        if atual in visitados:
            continue
        visitados.add(atual)
        expandidos += 1

        for dx, dy in DIRECOES:
            vizinho = (atual[0] + dx, atual[1] + dy)
            if not (0 <= vizinho[0] < COLUNAS and 0 <= vizinho[1] < LINHAS):
                continue
            if not mapa.tile_passavel(*vizinho, bloqueios):
                continue
            if dx != 0 and dy != 0:
                if not mapa.tile_passavel(atual[0] + dx, atual[1], bloqueios):
                    continue
                if not mapa.tile_passavel(atual[0], atual[1] + dy, bloqueios):
                    continue

            passo = math.sqrt(2) if dx != 0 and dy != 0 else 1.0
            novo_custo = custo[atual] + passo
            if novo_custo < custo.get(vizinho, float("inf")):
                custo[vizinho] = novo_custo
                veio_de[vizinho] = atual
                prioridade = novo_custo + _heuristica(vizinho, destino)
                heapq.heappush(abertos, (prioridade, vizinho))

    return None


def adjacentes(
    col: int, row: int, largura: int = 1, altura: int = 1
) -> list[tuple[int, int]]:
    tiles: set[tuple[int, int]] = set()
    for x in range(col - 1, col + largura + 1):
        for y in range(row - 1, row + altura + 1):
            dentro_x = col <= x < col + largura
            dentro_y = row <= y < row + altura
            if dentro_x and dentro_y:
                continue
            if 0 <= x < COLUNAS and 0 <= y < LINHAS:
                tiles.add((x, y))
    return list(tiles)


def melhor_adjacente(
    mapa: Mapa,
    tiles: list[tuple[int, int]],
    origem: tuple[float, float],
    bloqueios: set[tuple[int, int]] | None = None,
) -> tuple[int, int] | None:
    validos = [
        tile
        for tile in tiles
        if mapa.tile_passavel(tile[0], tile[1], bloqueios)
    ]
    if not validos:
        return None
    return min(
        validos,
        key=lambda t: (
            (t[0] * 64 + 32 - origem[0]) ** 2 + (t[1] * 64 + 32 - origem[1]) ** 2
        ),
    )
