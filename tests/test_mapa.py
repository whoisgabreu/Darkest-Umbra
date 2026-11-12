"""Testes do mapa espacial e da persistência."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mapa import CASTELO_ID, COLUNAS, FLORESTA, LINHAS, RAIO_CONSTRUCAO, RAIO_POSTO, Mapa, PEGADAS, TILE
from persistencia import carregar_jogo, novo_jogo, salvar_jogo
from reino import Reino


def test_geracao_deterministica():
    a = Mapa(seed=123)
    b = Mapa(seed=123)
    assert a.tiles == b.tiles
    assert a.castelo_pos == b.castelo_pos


def test_castelo_ocupa_area():
    mapa = Mapa(seed=1)
    col, row = mapa.castelo_pos
    largura, altura = PEGADAS["castelo"]
    for x in range(col, col + largura):
        for y in range(row, row + altura):
            assert mapa.ocupacao[(x, y)] == CASTELO_ID
    assert mapa.construcao_no_ponto(col * TILE + 1, row * TILE + 1) == CASTELO_ID


def test_pegadas_recomendadas():
    assert PEGADAS["castelo"] == (4, 4)
    assert PEGADAS["casas"] == (1, 1)
    assert PEGADAS["fazenda"] == (3, 2)
    assert PEGADAS["quartel"] == (2, 2)
    assert PEGADAS["posto"] == (2, 1)
    assert PEGADAS["torre_magia"] == (1, 1)
    assert PEGADAS["muralha"] == (1, 1)


def test_casa_1x1_ocupa_um_tile():
    mapa = Mapa(seed=40)
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("casas", col, row)
    )
    col, row = pos
    assert mapa.posicionar(41, "casas", col, row)
    assert mapa.ocupacao[(col, row)] == 41
    assert mapa.ocupacao.get((col + 1, row)) != 41
    mapa.remover(41)
    assert (col, row) not in mapa.ocupacao


def test_posicionamento_e_remocao():
    mapa = Mapa(seed=2)
    achou = None
    for row in range(LINHAS):
        for col in range(COLUNAS):
            if mapa.pode_posicionar("madeireira", col, row):
                achou = (col, row)
                break
        if achou:
            break
    assert achou is not None
    col, row = achou
    assert mapa.posicionar(99, "madeireira", col, row)
    assert mapa.ocupacao[(col, row)] == 99
    assert mapa.ocupacao[(col + 1, row)] == 99
    assert not mapa.pode_posicionar("madeireira", col, row)
    mapa.remover(99)
    assert 99 not in mapa.posicoes
    assert (col, row) not in mapa.ocupacao


def test_fora_do_raio_e_terreno_bloqueado():
    mapa = Mapa(seed=3)
    assert not mapa.pode_posicionar("casas", 0, 0)
    bloqueado = None
    for row in range(LINHAS):
        for col in range(COLUNAS):
            if mapa.tiles[row][col] not in (0, 1):
                bloqueado = (col, row)
                break
        if bloqueado:
            break
    if bloqueado:
        assert not mapa.pode_posicionar("casas", bloqueado[0], bloqueado[1])


def test_colocar_iniciais():
    mapa = Mapa(seed=4)
    mapa.colocar_iniciais([(1, "madeireira"), (2, "fazenda"), (3, "casas")])
    for id_instancia in (1, 2, 3):
        assert id_instancia in mapa.posicoes
    assert CASTELO_ID in mapa.posicoes
    ocupados = len(mapa.ocupacao)
    total = sum(
        PEGADAS[n][0] * PEGADAS[n][1]
        for n in ("madeireira", "fazenda", "casas", "castelo")
    )
    assert ocupados == total


def test_novo_jogo_coloca_construcoes_iniciais():
    reino, mapa, mundo = novo_jogo(seed=7)
    for construcao in reino.instancias():
        if PEGADAS.get(construcao.tipo, (0, 0))[0] > 0:
            assert construcao.id in mapa.posicoes
    assert len(mundo.cidadaos) == reino.populacao
    assert mundo.arvores


def test_salvar_e_carregar():
    reino, mapa, mundo = novo_jogo(seed=8)
    reino.dia = 21
    reino.recursos["madeira"] = 321.5
    reino.recursos["madeira"] += 1000
    ok, _, id_mina = reino.adicionar_instancia("mina")
    assert ok
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("mina", col, row)
    )
    assert mapa.posicionar(id_mina, "mina", *pos)
    ok, _, id_casas = reino.adicionar_instancia("casas")
    assert ok
    pos_casas = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("casas", col, row)
    )
    assert mapa.posicionar(id_casas, "casas", *pos_casas)
    caminho = os.path.join(tempfile.gettempdir(), "reino_mapa_teste.json")
    salvar_jogo(reino, mapa, mundo, caminho, camera=(700.0, 500.0))
    lido_reino, lido_mapa, lido_mundo, camera = carregar_jogo(caminho)
    os.remove(caminho)

    assert lido_reino.dia == 21
    assert lido_reino.instancias("mina")
    assert lido_mapa.tiles == mapa.tiles
    assert lido_mapa.posicoes[id_mina] == pos
    assert lido_mapa.posicoes[id_casas] == pos_casas
    assert lido_mapa.ocupacao[pos_casas] == id_casas
    assert len(lido_mundo.cidadaos) + len(lido_mundo.soldados) == lido_reino.populacao
    assert camera == (700.0, 500.0)


def test_migracao_save_antigo():
    reino = Reino()
    reino.dia = 30
    dados_reino = reino.to_dict()
    dados_reino["construcoes"] = {
        "lenhador": {"nivel": 2, "trabalhadores": 2},
        "fazenda": {"nivel": 1, "trabalhadores": 3},
        "casas": {"nivel": 1, "trabalhadores": 0},
        "quartel": {"nivel": 1, "trabalhadores": 0},
    }
    dados_reino["populacao"] = 12
    dados_reino["soldados"] = 2
    dados_reino["recursos"].pop("troncos", None)
    dados_mapa = {
        "seed": 1,
        "tiles": [[0] * 48 for _ in range(36)],
        "posicoes": {"castelo": [22, 16], "lenhador": [20, 15]},
    }
    caminho = os.path.join(tempfile.gettempdir(), "reino_v1_teste.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump({"versao": 3, "reino": dados_reino, "mapa": dados_mapa}, arquivo)
    lido_reino, lido_mapa, lido_mundo, camera = carregar_jogo(caminho)
    os.remove(caminho)

    assert lido_reino.dia == 30
    assert camera is None
    assert lido_reino.quantidade_instancias("madeireira") == 1
    assert lido_reino.primeira_instancia("madeireira").nivel == 2
    for construcao in lido_reino.instancias():
        if PEGADAS.get(construcao.tipo, (0, 0))[0] > 0:
            assert construcao.id in lido_mapa.posicoes
    assert len(lido_mundo.cidadaos) + len(lido_mundo.soldados) == lido_reino.populacao




def test_migracao_mapa_antigo_v4():
    reino, mapa, mundo = novo_jogo(seed=25)
    reino.dia = 40
    caminho = os.path.join(tempfile.gettempdir(), "mapa_antigo_v4.json")
    salvar_jogo(reino, mapa, mundo, caminho)
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    dados["mapa"]["tiles"] = [[0] * 32 for _ in range(24)]
    dados["mapa"]["posicoes"] = {"castelo": [14, 10]}
    dados["mapa"]["tipos"] = {"castelo": "castelo"}
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo)
    lido_reino, lido_mapa, lido_mundo, camera = carregar_jogo(caminho)
    os.remove(caminho)
    assert lido_reino.dia == 40
    assert camera is None
    assert len(lido_mundo.cidadaos) + len(lido_mundo.soldados) == lido_reino.populacao
    for construcao in lido_reino.instancias():
        if PEGADAS.get(construcao.tipo, (0, 0))[0] > 0:
            assert construcao.id in lido_mapa.posicoes



def test_posto_expande_territorio():
    mapa = Mapa(seed=30)
    pos = next(
        (col, row)
        for row in range(LINHAS - 2)
        for col in range(COLUNAS - 2)
        if mapa.pode_posicionar("posto", col, row)
    )
    assert mapa.posicionar(50, "posto", *pos)
    cx, cy = mapa.centro_castelo
    p_col, p_row = pos
    p_cx = p_col + PEGADAS["posto"][0] / 2
    p_cy = p_row + PEGADAS["posto"][1] / 2
    largura_casa, altura_casa = PEGADAS["casas"]
    candidato = None
    for row in range(LINHAS):
        for col in range(COLUNAS):
            centro_x = col + largura_casa / 2
            centro_y = row + altura_casa / 2
            dist_castelo = ((centro_x - cx) ** 2 + (centro_y - cy) ** 2) ** 0.5
            dist_posto = ((centro_x - p_cx) ** 2 + (centro_y - p_cy) ** 2) ** 0.5
            if dist_castelo > RAIO_CONSTRUCAO and dist_posto <= RAIO_POSTO:
                candidato = (col, row)
                break
        if candidato:
            break
    assert candidato is not None
    assert mapa.dentro_do_raio("casas", *candidato)



def test_estradas():
    mapa = Mapa(seed=31)
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_construir_estrada(col, row)
    )
    assert mapa.construir_estrada(*pos)
    assert mapa.tem_estrada(*pos)
    x, y = mapa.centro_tile_mundo(*pos)
    assert mapa.fator_movimento(x, y) == 1.5
    assert mapa.tile_passavel(*pos)

if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for teste in testes:
        teste()
        print(f"OK  {teste.__name__}")
    print(f"\n{len(testes)} testes passaram.")
