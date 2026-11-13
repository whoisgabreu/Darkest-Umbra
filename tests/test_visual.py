"""Testes do manifesto e da camada visual. Execute: python tests/test_visual.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visual import BancoAssets, CAMINHO_MANIFESTO, PASTA_ASSETS


def test_manifesto_e_arquivos():
    assert CAMINHO_MANIFESTO.exists()
    banco = BancoAssets()
    assert banco.ativo, banco.erro
    assert len(banco.entradas) >= 200
    for entrada in banco.entradas.values():
        caminho = PASTA_ASSETS / entrada["arquivo"]
        assert caminho.exists(), caminho
        assert entrada["largura"] > 0
        assert entrada["altura"] > 0
        assert entrada["frames"] >= 1


def test_spritesheets_e_caixas():
    banco = BancoAssets()
    assert banco.frames("tropa_soldado_andar") == 6
    assert banco.frames("cidadao_fazendeiro_idle") == 4
    assert banco.frames("efeito_explosao") == 8
    assert banco.largura_frame("tropa_soldado_idle") == 48
    esquerda, baixo, largura, altura = banco.caixa_conteudo("predio_casas_nivel_1")
    assert largura > 0 and altura > 0
    assert esquerda >= 0 and baixo >= 0


def test_desativar_assets_por_ambiente():
    anterior = os.environ.get("REINO_ASSETS")
    os.environ["REINO_ASSETS"] = "0"
    try:
        banco = BancoAssets()
        assert not banco.ativo
        assert banco.erro
    finally:
        if anterior is None:
            os.environ.pop("REINO_ASSETS", None)
        else:
            os.environ["REINO_ASSETS"] = anterior


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for teste in testes:
        teste()
        print(f"OK  {teste.__name__}")
    print(f"\n{len(testes)} testes passaram.")
