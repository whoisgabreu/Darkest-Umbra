"""Testes do mundo (cidadãos, árvores, combate e persistência)."""

import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from caminho import buscar_caminho
from mapa import AGUA, CASTELO_ID, COLUNAS, FLORESTA, GRAMA, LINHAS, ROCHA, TAMANHO_CHUNK, TILE
from persistencia import carregar_jogo, novo_jogo, salvar_jogo
from unidades import Inimigo
from reino import CONSTRUCOES, DIA_SEGUNDOS
from mundo import PEDRA_POR_GOLPE, ROCHA_VIDA_MAX, TRONCOS_POR_ARVORE


def _com_estruturas(seed: int):
    reino, mapa, mundo = novo_jogo(seed=seed)
    reino.recursos.update(
        {
            "madeira": 2000,
            "pedra": 1000,
            "ferro": 500,
            "ouro": 200,
            "dinheiro": 1000,
            "alimento": 500,
        }
    )
    for tipo in ("madeireira", "fazenda", "casas"):
        instancia = reino._criar_instancia(tipo, 1)
        pos = next(
            (col, row)
            for row in range(LINHAS)
            for col in range(COLUNAS)
            if mapa.pode_posicionar(tipo, col, row)
        )
        mapa.posicionar(instancia, tipo, *pos)
    for _ in range(8):
        x, y = mundo._ponto_livre(CASTELO_ID)
        mundo._criar_cidadao(x, y)
    reino.populacao = 1 + 8
    madeireira = reino.primeira_instancia("madeireira")
    fazenda = reino.primeira_instancia("fazenda")
    idle = [
        c for c in mundo.cidadaos if c.estado == "ocioso" and not c.rei
    ]
    if madeireira is not None and idle:
        cidadao = idle.pop()
        cidadao.profissao = "serrador"
        cidadao.estado = "trabalhando"
        cidadao.alvo_predio = madeireira.id
    if fazenda is not None:
        for cidadao in idle[:3]:
            cidadao.profissao = "fazendeiro"
            cidadao.estado = "trabalhando"
            cidadao.alvo_predio = fazenda.id
    mundo._sincronizar()
    return reino, mapa, mundo


def _arvore_livre(mundo):
    for (col, row), arvore in mundo.arvores.items():
        if arvore.estado == "adulta" and not mundo._unidade_na_tile(col, row):
            return arvore
    return None


def test_novo_jogo_popula():
    reino, mapa, mundo = novo_jogo(seed=11)
    assert reino.populacao == 1
    assert any(c.rei for c in mundo.cidadaos)
    assert mundo.arvores
    assert sum(c.trabalhadores for c in reino.construcoes.values()) == 0


def test_sincronizacao_populacional():
    reino, mapa, mundo = _com_estruturas(12)
    total = len(mundo.cidadaos) + len(mundo.soldados)
    reino.populacao = total + 2
    mundo._sincronizar()
    assert len(mundo.cidadaos) + len(mundo.soldados) == total + 2
    reino.populacao = total
    mundo._sincronizar()
    assert len(mundo.cidadaos) + len(mundo.soldados) == total


def test_refino_da_madeireira():
    reino, mapa, mundo = _com_estruturas(13)
    reino.recursos["troncos"] = 10.0
    reino.recursos["madeira"] = 0.0
    madeireira = reino.primeira_instancia("madeireira")
    serrador = next(
        c for c in mundo.cidadaos if c.alvo_predio == madeireira.id
    )
    serrador.estado = "trabalhando"
    mundo._atualizar_refino(DIA_SEGUNDOS / 2)
    assert reino.recursos["troncos"] < 10.0
    assert reino.recursos["madeira"] > 0.0


def test_corte_e_rebrota():
    random.seed(14)
    reino, mapa, mundo = _com_estruturas(14)
    arvore = _arvore_livre(mundo)
    assert arvore is not None
    mundo._cortar_arvore(arvore)
    assert arvore.estado == "toco"
    assert mapa.tiles[arvore.row][arvore.col] == GRAMA
    arvore.regrow = 0.01
    mundo._atualizar_arvores(0.02 * DIA_SEGUNDOS)
    assert arvore.estado == "adulta"
    assert mapa.tiles[arvore.row][arvore.col] == FLORESTA


def test_madeireiro_corta_e_entrega():
    random.seed(15)
    reino, mapa, mundo = _com_estruturas(15)
    arvore = _arvore_livre(mundo)
    assert arvore is not None
    cidadao = next(c for c in mundo.cidadaos if c.profissao == "ocioso")
    arvore.vida = 1
    cidadao.profissao = "madeireiro"
    cidadao.estado = "cortando"
    cidadao.tempo = 0.0
    cidadao.alvo_arvore = (arvore.col, arvore.row)
    mundo._atualizar_cidadaos(0.01)
    assert arvore.estado == "toco"
    assert cidadao.troncos == TRONCOS_POR_ARVORE
    reino.recursos["troncos"] = 0.0
    mundo._entregar_troncos(cidadao)
    assert reino.recursos["troncos"] == 5.0
    assert cidadao.troncos == 0


def test_treinar_soldado_converte_cidadao():
    random.seed(16)
    reino, mapa, mundo = _com_estruturas(16)
    quartel = reino._criar_instancia("quartel", 1)
    if quartel not in mapa.posicoes:
        pos = next(
            (col, row)
            for row in range(LINHAS)
            for col in range(COLUNAS)
            if mapa.pode_posicionar("quartel", col, row)
        )
        mapa.posicionar(quartel, "quartel", *pos)
    antes_pop = reino.populacao
    antes_cid = len(mundo.cidadaos)
    ok, msg = mundo.treinar_soldado()
    assert ok, msg
    assert len(mundo.soldados) == 1
    assert len(mundo.cidadaos) == antes_cid - 1
    assert reino.populacao == antes_pop


def test_raid_e_combate():
    random.seed(17)
    reino, mapa, mundo = _com_estruturas(17)
    reino.dia = 20
    reino.proximo_ataque_dia = 20
    reino._criar_instancia("quartel", 2)
    centro_x, centro_y = mapa.centro_mundo(CASTELO_ID)
    for i in range(5):
        mundo._criar_soldado(centro_x - 80 + i * 20, centro_y - 150)
    mundo._verificar_raid()
    assert mundo.raid_ativo
    assert mundo.inimigos
    for _ in range(int(90 * 60)):
        mundo.atualizar(1 / 60)
        if not mundo.raid_ativo or reino.derrota:
            break
    assert not reino.derrota
    assert not mundo.raid_ativo
    assert reino.ultimo_combate is not None
    assert reino.ultimo_combate["vitoria"]


def test_save_load_mundo():
    random.seed(18)
    reino, mapa, mundo = _com_estruturas(18)
    arvore = _arvore_livre(mundo)
    mundo._cortar_arvore(arvore)
    mundo.cidadaos[0].experiencia["fazendeiro"] = 123.0
    caminho = os.path.join(tempfile.gettempdir(), "mundo_teste.json")
    salvar_jogo(reino, mapa, mundo, caminho, camera=(600.0, 500.0))
    lido_reino, lido_mapa, lido_mundo, camera = carregar_jogo(caminho)
    os.remove(caminho)
    assert lido_mundo.arvores[(arvore.col, arvore.row)].estado == "toco"
    assert len(lido_mundo.cidadaos) == len(mundo.cidadaos)
    assert lido_mundo.cidadaos[0].experiencia.get("fazendeiro") == 123.0
    assert lido_mundo.rochas
    assert lido_mundo.fog == mundo.fog
    assert len(lido_mundo.cidadaos) + len(lido_mundo.soldados) == lido_reino.populacao
    assert camera == (600.0, 500.0)


def test_caminho_basico():
    reino, mapa, mundo = _com_estruturas(19)
    for row in range(LINHAS):
        for col in range(COLUNAS):
            if mapa.tile_passavel(col, row):
                for dc, dr in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    if mapa.tile_passavel(col + dc, row + dr):
                        caminho = buscar_caminho(
                            mapa, (col, row), (col + dc, row + dr)
                        )
                        assert caminho is not None
                        assert len(caminho) == 1
                        return
    raise AssertionError("não encontrou tiles passáveis adjacentes")


def test_caminho_bloqueado():
    reino, mapa, mundo = _com_estruturas(20)
    floresta = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.tiles[row][col] == FLORESTA
    )
    passavel = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.tile_passavel(col, row)
    )
    assert buscar_caminho(mapa, passavel, floresta) is None




def test_funcionarios_e_liberar():
    reino, mapa, mundo = _com_estruturas(21)
    fazenda = reino.primeira_instancia("fazenda")
    funcionarios = mundo.funcionarios_instancia(fazenda.id)
    assert funcionarios
    mundo.liberar_instancia(fazenda.id)
    mundo._sincronizar()
    assert not mundo.funcionarios_instancia(fazenda.id)
    assert fazenda.trabalhadores == 0


def test_xp_aumenta_bonus_de_producao():
    reino, mapa, mundo = _com_estruturas(22)
    fazenda = reino.primeira_instancia("fazenda")
    for cidadao in mundo.funcionarios_instancia(fazenda.id):
        cidadao.experiencia["fazendeiro"] = 500.0
    mundo._sincronizar()
    assert fazenda.bonus_producao > 1.0
    base = reino.taxas_producao()["alimento"]
    for cidadao in mundo.funcionarios_instancia(fazenda.id):
        cidadao.experiencia["fazendeiro"] = 0.0
    mundo._sincronizar()
    assert reino.taxas_producao()["alimento"] < base


def test_separacao_entre_unidades():
    reino, mapa, mundo = _com_estruturas(23)
    a = mundo.cidadaos[0]
    b = mundo.cidadaos[1]
    tile = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.tile_passavel(col, row)
    )
    x, y = mapa.centro_tile_mundo(*tile)
    a.x = b.x = x
    a.y = b.y = y
    for _ in range(30):
        mundo._separar_unidades(1 / 60)
    assert ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5 > 1.0



def test_durabilidade_da_arvore():
    random.seed(26)
    reino, mapa, mundo = _com_estruturas(26)
    arvore = _arvore_livre(mundo)
    cidadao = next(c for c in mundo.cidadaos if c.profissao == "ocioso")
    cidadao.profissao = "madeireiro"
    cidadao.estado = "cortando"
    cidadao.tempo = 0.0
    cidadao.alvo_arvore = (arvore.col, arvore.row)
    vida_antes = arvore.vida
    mundo._atualizar_cidadaos(0.01)
    assert arvore.vida == vida_antes - 1
    assert arvore.estado == "adulta"
    assert cidadao.troncos >= TRONCOS_POR_ARVORE


def test_pedreiro_minera_e_entrega():
    random.seed(27)
    reino, mapa, mundo = _com_estruturas(27)
    rocha = next(r for r in mundo.rochas.values() if r.estado == "adulta")
    rocha.vida = 1
    cidadao = next(c for c in mundo.cidadaos if c.profissao == "ocioso")
    cidadao.profissao = "pedreiro"
    cidadao.estado = "minerando"
    cidadao.tempo = 0.0
    cidadao.alvo_rocha = (rocha.col, rocha.row)
    mundo._atualizar_cidadaos(0.01)
    assert rocha.estado == "esgotada"
    assert mapa.tiles[rocha.row][rocha.col] == GRAMA
    assert cidadao.pedras >= PEDRA_POR_GOLPE
    reino.recursos["pedra"] = 0.0
    mundo._entregar_pedra(cidadao)
    assert reino.recursos["pedra"] >= PEDRA_POR_GOLPE
    assert cidadao.pedras == 0


def test_rocha_regenera():
    random.seed(28)
    reino, mapa, mundo = _com_estruturas(28)
    rocha = next(
        r for r in mundo.rochas.values()
        if r.estado == "adulta" and not mundo._unidade_na_tile(r.col, r.row)
    )
    mundo._esgotar_rocha(rocha)
    rocha.regrow = 0.01
    mundo._atualizar_rochas(0.02 * DIA_SEGUNDOS)
    assert rocha.estado == "adulta"
    assert mapa.tiles[rocha.row][rocha.col] == ROCHA
    assert rocha.vida == ROCHA_VIDA_MAX



def test_destruicao_de_estrutura():
    random.seed(31)
    reino, mapa, mundo = _com_estruturas(31)
    reino.recursos["madeira"] = 1000
    ok, msg, barricada = reino.adicionar_instancia("barricada")
    assert ok, msg
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("barricada", col, row)
    )
    assert mapa.posicionar(barricada, "barricada", *pos)
    mundo._destruir_estrutura(barricada)
    assert barricada not in reino.construcoes
    assert barricada not in mapa.posicoes



def test_inimigo_destroi_barricada():
    random.seed(32)
    reino, mapa, mundo = _com_estruturas(32)
    reino.recursos["madeira"] = 1000
    ok, msg, barricada = reino.adicionar_instancia("barricada")
    assert ok, msg
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("barricada", col, row)
    )
    assert mapa.posicionar(barricada, "barricada", *pos)
    cx, cy = mapa.centro_mundo(barricada)
    inimigo = Inimigo(
        id=999,
        x=cx + 10,
        y=cy,
        hp=100,
        hp_max=100,
        ataque=100,
        alcance=72,
    )
    for _ in range(3):
        mundo._atacar_estrutura(inimigo, barricada, 1.0)
    assert barricada not in reino.construcoes
    assert barricada not in mapa.posicoes



def test_treinar_arqueiro():
    random.seed(33)
    reino, mapa, mundo = _com_estruturas(33)
    arquearia = reino._criar_instancia("arquearia", 1)
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("arquearia", col, row)
    )
    mapa.posicionar(arquearia, "arquearia", *pos)
    reino.recursos["dinheiro"] = 100
    reino.recursos["ouro"] = 100
    antes = len(mundo.cidadaos)
    ok, msg = mundo.treinar_arqueiro()
    assert ok, msg
    assert len(mundo.cidadaos) == antes - 1
    assert any(s.classe == "arqueiro" for s in mundo.soldados)
    assert reino.arqueiros == 1


def test_inimigo_mata_cidadao():
    random.seed(34)
    reino, mapa, mundo = _com_estruturas(34)
    cidadao = next(c for c in mundo.cidadaos if not c.rei)
    cidadao.hp = 1
    inimigo = Inimigo(
        id=998,
        x=cidadao.x + 5,
        y=cidadao.y,
        hp=100,
        hp_max=100,
        ataque=5,
        alcance=72,
    )
    mundo.inimigos = [inimigo]
    populacao = reino.populacao
    mundo._atacar_cidadao(inimigo, cidadao, 1.0)
    assert cidadao not in mundo.cidadaos
    assert reino.populacao == populacao - 1



def test_fog_inicial_e_revelar():
    reino, mapa, mundo = _com_estruturas(35)
    assert mundo.fog
    antes = len(mundo.fog)
    alvo = next(
        (c, r) for r in range(LINHAS) for c in range(COLUNAS)
        if (c // TAMANHO_CHUNK, r // TAMANHO_CHUNK) in mundo.fog
    )
    x, y = mapa.centro_tile_mundo(*alvo)
    mundo.revelar_ao_redor(x, y, raio=1)
    assert len(mundo.fog) < antes


def test_criar_e_dispensar_caravana():
    random.seed(36)
    reino, mapa, mundo = _com_estruturas(36)
    reino.recursos.update(
        {"madeira": 500, "pedra": 500, "dinheiro": 500, "alimento": 200}
    )
    populacao = reino.populacao
    membros = [c for c in mundo.cidadaos if c.profissao == "ocioso"][:2]
    ok, msg, caravana = mundo.criar_caravana(membros, [])
    assert ok, msg
    assert len(mundo.caravanas) == 1
    assert caravana.membros
    assert reino.populacao == populacao
    mundo.dispensar_caravana(caravana)
    assert not mundo.caravanas
    assert reino.populacao == populacao
    assert len(mundo.cidadaos) >= len(membros)


def test_fundar_posto_com_caravana():
    random.seed(37)
    reino, mapa, mundo = _com_estruturas(37)
    reino.recursos.update(
        {"madeira": 1000, "pedra": 1000, "dinheiro": 1000, "alimento": 300}
    )
    membros = [c for c in mundo.cidadaos if c.profissao == "ocioso"][:2]
    ok, msg, caravana = mundo.criar_caravana(membros, [])
    assert ok, msg
    custo = CONSTRUCOES["posto"]["custo"]
    for recurso, quantidade in custo.items():
        caravana.carga[recurso] = float(quantidade)
    pos = next(
        (c, r)
        for r in range(LINHAS - 2)
        for c in range(COLUNAS - 2)
        if mapa.pode_posicionar("posto", c, r, ignorar_territorio=True)
    )
    caravana.x, caravana.y = mapa.centro_tile_mundo(
        pos[0] + 1, pos[1] + 1
    )
    ok, msg = mundo.fundar_posto_caravana(caravana)
    assert ok, msg
    postos = reino.instancias("posto")
    assert len(postos) == 1
    assert postos[0].id in mapa.posicoes


def test_caravana_fome_reduz_populacao():
    random.seed(38)
    reino, mapa, mundo = _com_estruturas(38)
    reino.recursos["alimento"] = 100
    membros = [c for c in mundo.cidadaos if c.profissao == "ocioso"][:2]
    ok, msg, caravana = mundo.criar_caravana(membros, [])
    assert ok, msg
    caravana.carga["alimento"] = 0.0
    membros_antes = len(caravana.membros)
    populacao = reino.populacao
    mundo._processar_dia_caravanas()
    assert len(caravana.membros) < membros_antes
    assert reino.populacao < populacao



def test_mover_preserva_profissao():
    random.seed(39)
    reino, mapa, mundo = _com_estruturas(39)
    fazendeiro = next(
        c for c in mundo.cidadaos if c.profissao == "fazendeiro"
    )
    mundo.ordenar_mover([fazendeiro], fazendeiro.x + 40, fazendeiro.y + 40)
    assert fazendeiro.profissao == "fazendeiro"
    assert fazendeiro.estado == "indo_mover"
    for _ in range(int(5 * 60)):
        mundo.atualizar(1 / 60)
        if fazendeiro.estado != "indo_mover":
            break
    assert fazendeiro.profissao == "fazendeiro"


def test_drop_de_inimigo():
    random.seed(40)
    reino, mapa, mundo = _com_estruturas(40)
    ouro = reino.recursos["ouro"]
    pedra = reino.recursos["pedra"]
    inimigo = Inimigo(
        id=997, x=100, y=100, hp=1, hp_max=1, ataque=1
    )
    mundo.inimigos = [inimigo]
    mundo._matar_inimigo(inimigo)
    assert not mundo.inimigos
    assert reino.recursos["ouro"] > ouro
    assert reino.recursos["pedra"] > pedra


def test_toggle_e_origem_da_raid():
    random.seed(41)
    reino, mapa, mundo = _com_estruturas(41)
    reino.dia = 30
    reino.proximo_ataque_dia = 30
    reino.ataques_ativos = False
    mundo._verificar_raid()
    assert not mundo.raid_ativo
    reino.ataques_ativos = True
    mundo._verificar_raid()
    assert mundo.raid_ativo
    assert mundo.raid_origem in ("Norte", "Sul", "Leste", "Oeste")



def test_descanso_e_cura():
    random.seed(42)
    reino, mapa, mundo = _com_estruturas(42)
    cidadao = next(c for c in mundo.cidadaos if c.profissao == "fazendeiro")
    cidadao.hp = 3.0
    hp_max = cidadao.hp_max
    for _ in range(int(30 * 60)):
        mundo.atualizar(1 / 60)
        if cidadao.hp >= hp_max - 0.5:
            break
    assert cidadao.profissao == "fazendeiro"
    assert cidadao.hp > 3.0


def test_evolucao_de_cidadao():
    random.seed(43)
    reino, mapa, mundo = _com_estruturas(43)
    cidadao = mundo.cidadaos[0]
    cidadao.experiencia["fazendeiro"] = 250.0
    pontos = mundo.pontos_disponiveis_cidadao(cidadao)
    assert pontos >= 2
    hp_max = cidadao.hp_max
    assert mundo.evoluir_cidadao(cidadao, "vida")
    assert cidadao.hp_max == hp_max + 5.0
    assert cidadao.pontos_usados == 1


def test_evolucao_de_soldado():
    random.seed(44)
    reino, mapa, mundo = _com_estruturas(44)
    soldado = mundo._criar_soldado(*mapa.centro_mundo(CASTELO_ID))
    soldado.xp = 150.0
    assert mundo.pontos_disponiveis_soldado(soldado) >= 1
    ataque = soldado.ataque
    assert mundo.evoluir_soldado(soldado, "dano")
    assert soldado.ataque > ataque
    assert soldado.pontos_usados == 1



def test_pescador_gera_alimento():
    random.seed(45)
    reino, mapa, mundo = _com_estruturas(45)
    cidadao = next(
        c for c in mundo.cidadaos
        if c.profissao == "ocioso" and not c.rei
    )
    agua = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.tiles[row][col] == AGUA
        and any(
            mapa.tile_passavel(nx, ny)
            for nx, ny in (
                (col - 1, row), (col + 1, row),
                (col, row - 1), (col, row + 1),
            )
        )
    )
    cidadao.profissao = "pescador"
    cidadao.estado = "pescando"
    cidadao.tempo = 0.0
    cidadao.alvo_pesca = agua
    reino.recursos["alimento"] = 0.0
    mundo._atualizar_cidadaos(0.01)
    assert reino.recursos["alimento"] > 0


def test_noite_faz_ociosos_dormirem():
    random.seed(46)
    reino, mapa, mundo = _com_estruturas(46)
    cidadao = next(
        c for c in mundo.cidadaos
        if c.profissao == "ocioso" and not c.rei
    )
    cidadao.hp = cidadao.hp_max
    reino.tempo_dia = DIA_SEGUNDOS * 0.8
    mundo._atualizar_cidadaos(0.01)
    assert cidadao.estado in ("indo_dormir", "dormindo")


def test_nivel_area_e_errantes():
    random.seed(47)
    reino, mapa, mundo = novo_jogo(seed=47)
    centro = mapa.centro_mundo(CASTELO_ID)
    longe = (centro[0] + TILE * 40, centro[1])
    assert mundo.nivel_area(*longe) > mundo.nivel_area(*centro)
    mundo._atualizar_errantes_dia()
    assert mundo.errantes



def test_treinar_mago_na_torre():
    random.seed(48)
    reino, mapa, mundo = novo_jogo(seed=48)
    reino.recursos.update(
        {"dinheiro": 500, "ouro": 200, "madeira": 500, "pedra": 500}
    )
    reino.recursos_raros["minerio_arcano"] = 1
    torre = reino._criar_instancia("torre_magia", 1)
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("torre_magia", col, row)
    )
    mapa.posicionar(torre, "torre_magia", *pos)
    x, y = mundo._ponto_livre(CASTELO_ID)
    mundo._criar_cidadao(x, y)
    reino.populacao = 2
    ok, msg = mundo.treinar_tropa("mago")
    assert ok, msg
    assert any(s.classe == "mago" for s in mundo.soldados)
    assert reino.magos == 1



def test_habilidades_especiais():
    random.seed(49)
    reino, mapa, mundo = novo_jogo(seed=49)
    cx, cy = mapa.centro_mundo(CASTELO_ID)
    a = Inimigo(id=900, x=cx, y=cy, hp=500, hp_max=500, ataque=1)
    b = Inimigo(id=901, x=cx + 20, y=cy, hp=500, hp_max=500, ataque=1)
    mundo.inimigos = [a, b]
    destruidor = mundo._criar_tropa("destruidor", cx, cy)
    mundo._executar_ataque(destruidor, a, 10)
    assert b.hp < 500

    gelo = mundo._criar_tropa("mago_gelo", cx, cy)
    mundo._executar_ataque(gelo, a, 1)
    assert a.slow_timer > 0


def test_protetor_e_curandeiro():
    random.seed(50)
    reino, mapa, mundo = novo_jogo(seed=50)
    cx, cy = mapa.centro_mundo(CASTELO_ID)
    aliado = mundo._criar_tropa("soldado", cx, cy)
    aliado.hp = 10
    curandeiro = mundo._criar_tropa("curandeiro", cx + 10, cy)
    mundo._suporte_curandeiro(curandeiro, 10)
    assert aliado.hp > 10
    soldado = mundo._criar_tropa("soldado", cx + 20, cy)
    soldado.escudo = 0
    protetor2 = mundo._criar_tropa("protetor", cx + 25, cy)
    mundo._suporte_curandeiro(protetor2, 10)
    assert soldado.escudo > 0



def _posto_com_colonos(seed: int, colonos: int = 2):
    reino, mapa, mundo = _com_estruturas(seed)
    posto = reino._criar_instancia("posto", 1)
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("posto", col, row, ignorar_territorio=True)
    )
    mapa.posicionar(posto, "posto", *pos, ignorar_territorio=True)
    candidatos = [
        c
        for c in mundo.cidadaos
        if c.estado == "ocioso" and not c.rei and c.profissao == "ocioso"
    ][:colonos]
    for cidadao in candidatos:
        cidadao.profissao = "colonizador"
        cidadao.estado = "trabalhando"
        cidadao.alvo_predio = posto
    mundo._sincronizar()
    return reino, mapa, mundo, reino.construcoes[posto]


def test_colonos_produzem_no_armazem_do_posto():
    random.seed(41)
    reino, mapa, mundo, posto = _posto_com_colonos(41)
    assert posto.trabalhadores == 2
    for construcao in reino.construcoes.values():
        if construcao.id != posto.id:
            construcao.trabalhadores = 0
    reino.recursos["alimento"] = reino.capacidade_alimento
    antes = dict(reino.recursos)
    reino._produzir(DIA_SEGUNDOS)
    assert reino.total_armazem(posto) > 0
    for recurso in ("madeira", "pedra", "alimento"):
        assert reino.recursos[recurso] == antes[recurso]


def test_posto_consome_comida_local_e_colono_morre():
    random.seed(42)
    reino, mapa, mundo, posto = _posto_com_colonos(42)
    posto.armazem["alimento"] = 10.0
    mundo._processar_dia_postos()
    esperado = 10.0 - posto.trabalhadores * 0.4
    assert abs(posto.armazem["alimento"] - esperado) < 0.01
    posto.armazem["alimento"] = 0.0
    populacao = reino.populacao
    cidadaos = len(mundo.cidadaos)
    mundo._processar_dia_postos()
    assert len(mundo.cidadaos) == cidadaos - 1
    assert reino.populacao == populacao - 1


def test_save_load_posto_com_colonos():
    random.seed(43)
    reino, mapa, mundo, posto = _posto_com_colonos(43)
    posto.armazem = {"madeira": 5.0, "alimento": 7.0}
    caminho = os.path.join(tempfile.gettempdir(), "mundo_posto.json")
    salvar_jogo(reino, mapa, mundo, caminho)
    lido_reino, lido_mapa, lido_mundo, _ = carregar_jogo(caminho)
    os.remove(caminho)
    lido_posto = lido_reino.construcoes[posto.id]
    assert lido_posto.armazem["madeira"] == 5.0
    assert lido_posto.armazem["alimento"] == 7.0
    assert sum(
        1 for c in lido_mundo.cidadaos if c.profissao == "colonizador"
    ) == 2


def test_defesa_do_posto_atinge_inimigo_proximo():
    random.seed(44)
    reino, mapa, mundo, posto = _posto_com_colonos(44)
    cx, cy = mapa.centro_mundo(posto.id)
    inimigo = Inimigo(
        id=999,
        x=cx + 40,
        y=cy,
        hp=100.0,
        hp_max=100.0,
        ataque=5.0,
    )
    mundo.inimigos.append(inimigo)
    mundo._atualizar_defesas_postos(0.1)
    assert inimigo.hp < 100.0
    assert mundo.tiros_postos


def test_raid_posto_mira_o_posto():
    from unittest.mock import patch

    random.seed(45)
    reino, mapa, mundo, posto = _posto_com_colonos(45)
    reino.dia = 10
    with patch("mundo.random.random", return_value=0.0):
        mundo._iniciar_raid()
    assert mundo.raid_ativo
    assert mundo.raid_posto_id == posto.id
    assert mundo.inimigos
    assert all(i.alvo_estrutura == posto.id for i in mundo.inimigos)
    assert "Posto" in mundo.raid_origem


def test_finalizar_raid_do_posto_registra_alvo():
    random.seed(47)
    reino, mapa, mundo, posto = _posto_com_colonos(47)
    mundo.raid_ativo = True
    mundo.raid_posto_id = posto.id
    mundo.raid_origem = f"Posto #{posto.id}"
    mundo._raid_inimigos = 3
    reino.recursos["ouro"] = 0
    mundo._finalizar_raid()
    assert reino.ultimo_combate["alvo"] == f"Posto #{posto.id}"
    assert reino.ultimo_combate["vitoria"]
    assert reino.recursos["ouro"] > 0
    assert mundo.raid_posto_id is None


def test_destruir_posto_libera_colonos_e_perde_armazem():
    random.seed(46)
    reino, mapa, mundo, posto = _posto_com_colonos(46)
    posto.armazem = {"madeira": 10.0, "alimento": 5.0}
    mundo._destruir_estrutura(posto.id)
    assert posto.id not in reino.construcoes
    assert posto.id not in mapa.posicoes
    assert not any(
        c.profissao == "colonizador" for c in mundo.cidadaos
    )


def test_carroca_coleta_posto_e_entrega_no_reino():
    random.seed(51)
    reino, mapa, mundo = _com_estruturas(51)
    posto = reino._criar_instancia("posto", 1)
    pos = next(
        (col, row)
        for row in range(LINHAS)
        for col in range(COLUNAS)
        if mapa.pode_posicionar("posto", col, row, ignorar_territorio=True)
    )
    mapa.posicionar(posto, "posto", *pos, ignorar_territorio=True)
    reino.construcoes[posto].armazem = {"madeira": 40.0, "pedra": 10.0}
    membros = [
        c for c in mundo.cidadaos
        if c.profissao == "ocioso" and not c.rei
    ][:1]
    ok, msg, caravana = mundo.criar_caravana(membros, [])
    assert ok, msg
    caravana.x, caravana.y = mapa.centro_mundo(posto)
    assert mundo.pode_coletar_posto(caravana)
    ok, msg = mundo.coletar_posto_caravana(caravana)
    assert ok, msg
    assert caravana.carga.get("madeira", 0) >= 40.0
    assert reino.total_armazem(reino.construcoes[posto]) == 0.0

    caravana.x, caravana.y = mapa.centro_mundo(CASTELO_ID)
    madeira_antes = reino.recursos["madeira"]
    carga_madeira = caravana.carga.get("madeira", 0.0)
    ok, msg = mundo.entregar_caravana(caravana)
    assert ok, msg
    assert reino.recursos["madeira"] >= madeira_antes + carga_madeira - 0.01
    assert sum(caravana.carga.values()) == 0



def test_toque_de_recolher_esconde_civis():
    random.seed(52)
    reino, mapa, mundo = novo_jogo(seed=52)
    reino.construcoes[CASTELO_ID].nivel = 3
    reino.toque_de_recolher = True
    x, y = mundo._ponto_livre(CASTELO_ID)
    cidadao = mundo._criar_cidadao(x, y)
    cidadao.profissao = "fazendeiro"
    cidadao.estado = "trabalhando"
    reino.populacao = 2
    for _ in range(int(10 * 60)):
        mundo.atualizar(1 / 60)
    assert cidadao.estado in ("indo_recolher", "recolhido")

    inimigo = Inimigo(
        id=999, x=cidadao.x, y=cidadao.y, hp=100, hp_max=100, ataque=1
    )
    assert mundo._escolher_cidadao(inimigo) is None

    reino.toque_de_recolher = False
    for _ in range(int(5 * 60)):
        mundo.atualizar(1 / 60)
    assert cidadao.estado not in ("indo_recolher", "recolhido")

if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for teste in testes:
        teste()
        print(f"OK  {teste.__name__}")
    print(f"\n{len(testes)} testes passaram.")
