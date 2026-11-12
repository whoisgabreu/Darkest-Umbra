"""Testes da lógica econômica do reino. Execute: python tests/test_reino.py"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reino import DIA_SEGUNDOS, ESCALA_CUSTO_INSTANCIAS, Reino


def _primeira(reino, tipo):
    return reino.primeira_instancia(tipo)


def test_estado_inicial():
    r = Reino()
    assert r.dia == 1
    assert r.populacao == 1
    assert r.nivel_castelo == 1
    assert r.quantidade_instancias("madeireira") == 0
    assert sum(r.taxas_producao().values()) == 0


def test_custo_escalonado_novas_instancias():
    r = Reino()
    base = r.custo_nova_instancia("madeireira")["madeira"]
    assert base == 25  # nenhuma madeireira ainda
    r.recursos["madeira"] = 1000
    ok, _, id2 = r.adicionar_instancia("madeireira")
    assert ok
    assert id2 is not None
    terceira = r.custo_nova_instancia("madeireira")["madeira"]
    assert terceira == int(25 * ESCALA_CUSTO_INSTANCIAS + 0.999)


def test_custo_melhoria_escala_com_quantidade():
    r = Reino()
    r.recursos["madeira"] = 1000
    id1 = r._criar_instancia("madeireira", 1)
    custo_um = r.custo_melhoria(id1)["madeira"]
    ok, _, id2 = r.adicionar_instancia("madeireira")
    assert ok
    custo_dois = r.custo_melhoria(id1)["madeira"]
    assert custo_dois == int(custo_um * ESCALA_CUSTO_INSTANCIAS + 0.999)
    assert custo_dois > custo_um


def test_melhorar_instancia():
    r = Reino()
    r.recursos["madeira"] = 1000
    id1 = r._criar_instancia("madeireira", 1)
    custo = r.custo_melhoria(id1)["madeira"]
    ok, _ = r.melhorar_instancia(id1)
    assert ok
    assert r.construcoes[id1].nivel == 2
    assert abs(r.recursos["madeira"] - (1000 - custo)) < 0.01


def test_producao_diaria():
    r = Reino()
    fazenda = r.construcoes[r._criar_instancia("fazenda", 1)]
    fazenda.trabalhadores = 3
    antes = r.recursos["alimento"]
    r._produzir(DIA_SEGUNDOS)
    assert abs(r.recursos["alimento"] - (antes + 9.0)) < 0.01


def test_consumo_e_fome():
    r = Reino()
    r.recursos["alimento"] = 0
    r.tempo_dia = DIA_SEGUNDOS
    populacao_antes = r.populacao
    r.atualizar(0.01)
    assert r.populacao < populacao_antes
    assert any("FOME" in linha for linha in r.log)


def test_cobrar_treinamento():
    r = Reino()
    r._criar_instancia("quartel", 1)
    r.recursos["dinheiro"] = 50
    r.recursos["ouro"] = 50
    ok, msg = r.cobrar_treinamento()
    assert ok, msg
    assert r.soldados == 0
    assert r.recursos["dinheiro"] == 42
    assert r.recursos["ouro"] == 48


def test_derrota_com_rei_morto():
    r = Reino()
    r.rei_morto = True
    r._verificar_derrota()
    assert r.derrota
    assert r.melhor_periodo >= r.dia


def test_reparar_castelo():
    r = Reino()
    r.hp_castelo = 100
    r.recursos["madeira"] = 100
    r.recursos["ferro"] = 100
    ok, _ = r.reparar_castelo()
    assert ok and r.hp_castelo > 100
    assert r.recursos["madeira"] == 75
    assert r.recursos["ferro"] == 90


def test_disponibilidade_crescimento():
    r = Reino()
    dados = r.taxa_crescimento()
    assert dados["taxa"] > 0
    assert dados["espaco"] > 0
    r.populacao = r.capacidade_populacao
    assert r.taxa_crescimento()["taxa"] == 0


def test_save_load():
    r = Reino()
    r.dia = 12
    r.populacao = 10
    mina = r._criar_instancia("mina", 2)
    r.construcoes[mina].trabalhadores = 2
    r.recorde_dias = 12
    caminho = os.path.join(tempfile.gettempdir(), "reino_teste.json")
    r.salvar(caminho)
    lido = Reino.carregar(caminho)
    os.remove(caminho)
    assert lido.dia == r.dia
    assert lido.populacao == r.populacao
    minas = lido.instancias("mina")
    assert len(minas) == 1
    assert minas[0].nivel == 2
    assert minas[0].trabalhadores == 2
    assert lido.recorde_dias == 12




def test_sem_limite_de_instancias():
    r = Reino()
    r.recursos["madeira"] = 10000000
    for _ in range(12):
        ok, msg, _ = r.adicionar_instancia("madeireira")
        assert ok, msg
    assert r.quantidade_instancias("madeireira") == 12
    r.recursos.update({"pedra": 100000, "dinheiro": 100000, "ouro": 100000})
    for _ in range(5):
        ok, msg, _ = r.adicionar_instancia("torre_magia")
        assert ok, msg
    assert r.quantidade_instancias("torre_magia") == 5



def test_mina_produz_pedra():
    r = Reino()
    mina = r._criar_instancia("mina", 1)
    r.construcoes[mina].trabalhadores = 1
    antes = r.recursos["pedra"]
    r._produzir(DIA_SEGUNDOS)
    assert abs(r.recursos["pedra"] - (antes + 4.0)) < 0.01



def test_estruturas_defensivas_e_posto():
    r = Reino()
    r.recursos["madeira"] = 1000
    r.recursos["pedra"] = 1000
    r.recursos["dinheiro"] = 1000
    barricada = r._criar_instancia("barricada", 1)
    muralha = r._criar_instancia("muralha", 1)
    assert r.construcoes[barricada].hp_max > 0
    assert r.construcoes[muralha].hp_max > r.construcoes[barricada].hp_max
    r.construcoes[barricada].hp = 1
    assert r.pode_reparar_instancia(barricada)
    ok, msg = r.reparar_instancia(barricada)
    assert ok, msg
    assert r.construcoes[barricada].hp > 1
    capacidade = r.capacidade_populacao
    ok, _, posto = r.adicionar_instancia("posto")
    assert ok
    assert r.capacidade_populacao == capacidade + 4


def test_custo_muralha_nao_escala_por_segmento():
    r = Reino()
    r.recursos["madeira"] = 1000
    r.recursos["pedra"] = 1000
    custo1 = r.custo_nova_instancia("muralha")
    ok, _, id1 = r.adicionar_instancia("muralha")
    assert ok
    custo2 = r.custo_nova_instancia("muralha")
    assert custo1 == custo2



def test_arquearia_e_arqueiros():
    r = Reino()
    arquearia = r._criar_instancia("arquearia", 1)
    assert r.max_arqueiros == 3
    r.recursos["dinheiro"] = 100
    r.recursos["ouro"] = 100
    ok, msg = r.cobrar_treinamento_arqueiro()
    assert ok, msg
    assert r.recursos["dinheiro"] == 90
    assert r.recursos["ouro"] == 98



def test_toggle_ataques_salvo():
    r = Reino()
    r.ataques_ativos = False
    caminho = os.path.join(tempfile.gettempdir(), "reino_toggle.json")
    r.salvar(caminho)
    lido = Reino.carregar(caminho)
    os.remove(caminho)
    assert lido.ataques_ativos is False


def test_conforto_das_casas():
    r = Reino()
    taxa1 = r.taxa_crescimento()["taxa"]
    casas = r._criar_instancia("casas", 1)
    r.construcoes[casas].nivel = 3
    taxa2 = r.taxa_crescimento()["taxa"]
    assert taxa2 > taxa1


def test_producao_discreta():
    r = Reino()
    fazenda = r.construcoes[r._criar_instancia("fazenda", 1)]
    fazenda.trabalhadores = 3
    antes = r.recursos["alimento"]
    r._produzir(DIA_SEGUNDOS)
    assert abs(r.recursos["alimento"] - (antes + 9.0)) < 0.01
    assert abs(fazenda.progressos.get("alimento", 0.0)) < 0.001



def test_mercador_e_venda():
    r = Reino()
    r.mercador_dias = 3
    r.mercador_precos = {"madeira": 2.0}
    r.recursos["madeira"] = 100
    dinheiro = r.recursos["dinheiro"]
    ok, msg = r.vender_recurso("madeira", 50)
    assert ok, msg
    assert r.recursos["madeira"] == 50
    assert r.recursos["dinheiro"] == dinheiro + 100

    caminho = os.path.join(tempfile.gettempdir(), "reino_mercador.json")
    r.salvar(caminho)
    lido = Reino.carregar(caminho)
    os.remove(caminho)
    assert lido.mercador_dias == 3
    assert lido.mercador_precos["madeira"] == 2.0


def test_venda_sem_mercador():
    r = Reino()
    r.recursos["madeira"] = 100
    ok, _ = r.vender_recurso("madeira", 10)
    assert not ok



def test_tropas_especiais_e_recursos_raros():
    r = Reino()
    r._criar_instancia("quartel", 1)
    r.recursos["dinheiro"] = 200
    r.recursos["ouro"] = 100
    r.recursos_raros["minerio_arcano"] = 3
    assert r.pode_treinar_tropa("defensor")
    ok, msg = r.cobrar_treinamento_tropa("defensor")
    assert ok, msg
    assert r.recursos_raros["minerio_arcano"] == 0
    r.adicionar_recurso_raro("ambar", 2)
    assert r.recursos_raros["ambar"] == 2

    caminho = os.path.join(tempfile.gettempdir(), "reino_raros.json")
    r.salvar(caminho)
    lido = Reino.carregar(caminho)
    os.remove(caminho)
    assert lido.recursos_raros["ambar"] == 2



def test_posto_produz_para_armazem_local():
    r = Reino()
    posto = r._criar_instancia("posto", 1)
    r.construcoes[posto].trabalhadores = 2
    antes = dict(r.recursos)
    r._produzir(DIA_SEGUNDOS * 2)
    for recurso in ("madeira", "pedra", "alimento"):
        assert r.recursos[recurso] == antes[recurso]
    construcao = r.construcoes[posto]
    assert r.total_armazem(construcao) > 0
    assert r.total_armazem(construcao) <= r.capacidade_armazem(construcao)



def test_defesa_do_posto_escala_com_nivel():
    r = Reino()
    posto = r._criar_instancia("posto", 1)
    nivel1 = r.defesa_posto(r.construcoes[posto])
    r.construcoes[posto].nivel = 3
    nivel3 = r.defesa_posto(r.construcoes[posto])
    assert nivel1["dano"] > 0
    assert nivel3["dano"] > nivel1["dano"]
    assert nivel3["alcance"] > nivel1["alcance"]


def test_posto_sem_colonos_nao_produz():
    r = Reino()
    posto = r._criar_instancia("posto", 1)
    r._produzir(DIA_SEGUNDOS)
    assert r.total_armazem(r.construcoes[posto]) == 0.0


def test_consumo_exclui_colonos_de_postos():
    r = Reino()
    r.populacao = 6
    antes = r.consumo_diario
    posto = r._criar_instancia("posto", 1)
    r.construcoes[posto].trabalhadores = 2
    assert r.trabalhadores_postos == 2
    assert r.consumo_diario < antes


def test_toque_de_recolher():
    r = Reino()
    assert not r.toque_disponivel
    r.construcoes[0].nivel = 3
    assert r.toque_disponivel
    r.toque_de_recolher = True
    caminho = os.path.join(tempfile.gettempdir(), "reino_recolher.json")
    r.salvar(caminho)
    lido = Reino.carregar(caminho)
    os.remove(caminho)
    assert lido.toque_de_recolher is True
    assert lido.nivel_castelo == 3

if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for teste in testes:
        teste()
        print(f"OK  {teste.__name__}")
    print(f"\n{len(testes)} testes passaram.")
