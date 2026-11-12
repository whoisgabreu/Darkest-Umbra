"""Salvamento e carregamento do jogo (reino + mapa + mundo)."""

from __future__ import annotations

import json
import os
import random

from mapa import COLUNAS, LINHAS, PEGADAS, Mapa
from mundo import Mundo
from reino import Reino

VERSAO_SAVE = 4


def _mapa_compativel(dados_mapa: dict) -> bool:
    tiles = dados_mapa.get("tiles")
    return (
        isinstance(tiles, list)
        and len(tiles) == LINHAS
        and all(isinstance(linha, list) and len(linha) == COLUNAS for linha in tiles)
    )


def _colocar_construcoes(mapa: Mapa, reino: Reino) -> None:
    for id_instancia in list(mapa.posicoes):
        if id_instancia == 0:
            continue
        construcao = reino.construcoes.get(id_instancia)
        if construcao is None:
            mapa.remover(id_instancia)

    faltantes = [
        (construcao.id, construcao.tipo)
        for construcao in reino.instancias()
        if PEGADAS.get(construcao.tipo, (0, 0))[0] > 0
        and construcao.id not in mapa.posicoes
    ]
    if faltantes:
        mapa.colocar_iniciais(faltantes)


def _ids_por_tipo(reino: Reino) -> dict[str, int]:
    ids: dict[str, int] = {}
    for construcao in reino.instancias():
        ids.setdefault(construcao.tipo, construcao.id)
    return ids


def novo_jogo(seed: int | None = None) -> tuple[Reino, Mapa, Mundo]:
    reino = Reino()
    mapa = Mapa(seed)
    iniciais = [
        (construcao.id, construcao.tipo)
        for construcao in reino.instancias()
        if PEGADAS.get(construcao.tipo, (0, 0))[0] > 0
    ]
    mapa.colocar_iniciais(iniciais)
    mundo = Mundo(reino, mapa)
    mundo.inicializar_novo()
    return reino, mapa, mundo


def salvar_jogo(
    reino: Reino,
    mapa: Mapa,
    mundo: Mundo,
    caminho: str,
    camera: tuple[float, float] | None = None,
) -> None:
    dados: dict = {
        "versao": VERSAO_SAVE,
        "reino": reino.to_dict(),
        "mapa": mapa.to_dict(),
        "mundo": mundo.to_dict(),
    }
    if camera is not None:
        dados["camera"] = [float(camera[0]), float(camera[1])]

    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, caminho)


def carregar_jogo(
    caminho: str,
) -> tuple[Reino, Mapa, Mundo, tuple[float, float] | None]:
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    migrado = False
    if isinstance(dados.get("reino"), dict):
        reino = Reino.from_dict(dados["reino"])
        dados_mapa = dados.get("mapa", {})
        mapa = Mapa.from_dict(dados_mapa, _ids_por_tipo(reino))
        migrado = (
            "mundo" not in dados
            or int(dados.get("versao", 0)) < VERSAO_SAVE
            or not _mapa_compativel(dados_mapa)
        )
    else:
        reino = Reino.from_dict(dados)
        mapa = Mapa.from_dict({}, _ids_por_tipo(reino))
        migrado = True

    _colocar_construcoes(mapa, reino)

    if migrado:
        mundo = Mundo(reino, mapa)
        mundo.migrar()
        if reino.dia >= reino.proximo_ataque_dia:
            reino.proximo_ataque_dia = reino.dia + random.randint(8, 12)
            reino.aviso_ataque = False
    else:
        mundo = Mundo.from_dict(reino, mapa, dados.get("mundo", {}))

    camera = dados.get("camera")
    if not migrado and isinstance(camera, (list, tuple)) and len(camera) >= 2:
        camera = (float(camera[0]), float(camera[1]))
    else:
        camera = None

    return reino, mapa, mundo, camera
