"""Camada de carregamento e desenho dos assets visuais."""

from __future__ import annotations

import json
import os
from pathlib import Path

import arcade
from PIL import Image

RAIZ_PROJETO = Path(__file__).resolve().parent
PASTA_ASSETS = RAIZ_PROJETO / "assets"
CAMINHO_MANIFESTO = PASTA_ASSETS / "manifest.json"


class BancoAssets:
    def __init__(self) -> None:
        self.manifesto: dict = {}
        self.entradas: dict[str, dict] = {}
        self._imagens: dict[str, Image.Image] = {}
        self._texturas: dict[tuple[str, int], arcade.Texture] = {}
        self._fatias: dict[tuple[str, int], dict[str, arcade.Texture]] = {}
        self._caixas: dict[tuple[str, int], tuple[int, int, int, int]] = {}
        self.ativo = os.environ.get("REINO_ASSETS", "1") != "0"
        self.erro = ""
        if not self.ativo:
            self.erro = "desativado por REINO_ASSETS=0"
            return
        if not CAMINHO_MANIFESTO.exists():
            self.ativo = False
            self.erro = "manifest.json ausente"
            return
        try:
            self.manifesto = json.loads(CAMINHO_MANIFESTO.read_text(encoding="utf-8"))
            for entrada in self.manifesto.get("assets", []):
                identificador = entrada.get("id")
                if isinstance(identificador, str):
                    self.entradas[identificador] = entrada
        except (OSError, json.JSONDecodeError) as erro:
            self.ativo = False
            self.erro = str(erro)

    def tem(self, asset_id: str) -> bool:
        return self.ativo and asset_id in self.entradas

    def entrada(self, asset_id: str) -> dict | None:
        return self.entradas.get(asset_id)

    def frames(self, asset_id: str) -> int:
        entrada = self.entradas.get(asset_id)
        return max(1, int(entrada.get("frames", 1))) if entrada else 1

    def largura_frame(self, asset_id: str) -> int:
        entrada = self.entradas.get(asset_id)
        if not entrada:
            return 0
        return int(entrada.get("largura_frame") or entrada.get("largura", 0))

    def altura(self, asset_id: str) -> int:
        entrada = self.entradas.get(asset_id)
        return int(entrada.get("altura", 0)) if entrada else 0

    def caixa_conteudo(self, asset_id: str, frame: int = 0) -> tuple[int, int, int, int]:
        chave = (asset_id, frame)
        if chave in self._caixas:
            return self._caixas[chave]
        imagem = self._imagem(asset_id)
        if imagem is None:
            return (0, 0, 0, 0)
        largura = self.largura_frame(asset_id)
        altura = imagem.height
        recorte = imagem.crop(
            (frame * largura, 0, frame * largura + largura, altura)
        )
        caixa = recorte.getbbox()
        if caixa is None:
            resultado = (0, 0, largura, altura)
        else:
            esquerda, topo, direita, baixo = caixa
            resultado = (
                esquerda,
                altura - baixo,
                direita - esquerda,
                baixo - topo,
            )
        self._caixas[chave] = resultado
        return resultado

    def _imagem(self, asset_id: str) -> Image.Image | None:
        if asset_id in self._imagens:
            return self._imagens[asset_id]
        entrada = self.entradas.get(asset_id)
        if entrada is None:
            return None
        caminho = PASTA_ASSETS / entrada["arquivo"]
        try:
            imagem = Image.open(caminho).convert("RGBA")
        except (OSError, KeyError):
            return None
        self._imagens[asset_id] = imagem
        return imagem

    def textura(self, asset_id: str, frame: int = 0) -> arcade.Texture | None:
        if not self.tem(asset_id):
            return None
        total = self.frames(asset_id)
        frame = int(frame) % total
        chave = (asset_id, frame)
        if chave in self._texturas:
            return self._texturas[chave]
        imagem = self._imagem(asset_id)
        if imagem is None:
            return None
        largura = self.largura_frame(asset_id)
        altura = imagem.height
        x = frame * largura
        recorte = imagem.crop((x, 0, x + largura, altura))
        try:
            textura = arcade.Texture(
                recorte,
                hash=f"reino:{asset_id}:{frame}",
                hit_box_algorithm=None,
            )
        except TypeError:
            textura = arcade.Texture(recorte)
        self._texturas[chave] = textura
        return textura

    def desenhar(
        self,
        asset_id: str,
        x: float,
        y: float,
        largura: float | None = None,
        altura: float | None = None,
        ancora: str = "centro",
        frame: int = 0,
        alpha: int = 255,
    ) -> bool:
        textura = self.textura(asset_id, frame)
        if textura is None:
            return False
        if largura is None:
            largura = self.largura_frame(asset_id)
        if altura is None:
            altura = self.altura(asset_id)
        if ancora == "centro":
            esquerda = x - largura / 2
            baixo = y - altura / 2
        elif ancora in ("base", "centro-base"):
            esquerda = x - largura / 2
            baixo = y
        elif ancora == "topo":
            esquerda = x - largura / 2
            baixo = y - altura
        elif ancora == "topo-esquerda":
            esquerda = x
            baixo = y - altura
        else:
            esquerda = x
            baixo = y
        arcade.draw_texture_rect(
            textura,
            arcade.LBWH(esquerda, baixo, largura, altura),
            pixelated=True,
            alpha=alpha,
        )
        return True

    def desenhar_animacao(
        self,
        asset_id: str,
        x: float,
        y: float,
        largura: float | None = None,
        altura: float | None = None,
        ancora: str = "centro",
        fps: float = 8.0,
        tempo: float = 0.0,
        fase: float = 0.0,
        alpha: int = 255,
    ) -> bool:
        total = self.frames(asset_id)
        frame = int((tempo * fps + fase) % total)
        return self.desenhar(
            asset_id,
            x,
            y,
            largura=largura,
            altura=altura,
            ancora=ancora,
            frame=frame,
            alpha=alpha,
        )

    def desenhar_9slice(
        self,
        asset_id: str,
        x: float,
        y: float,
        largura: float,
        altura: float,
        margem: int = 12,
        alpha: int = 255,
    ) -> bool:
        imagem = self._imagem(asset_id)
        if imagem is None:
            return False
        fonte_l, fonte_a = imagem.size
        margem = max(1, min(margem, fonte_l // 2, fonte_a // 2))
        if largura < margem * 2 or altura < margem * 2:
            return self.desenhar(
                asset_id, x + largura / 2, y + altura / 2, largura, altura, "centro", alpha=alpha
            )
        chave = (asset_id, margem)
        if chave not in self._fatias:
            fatias = {}
            xs = (0, margem, fonte_l - margem, fonte_l)
            ys = (0, margem, fonte_a - margem, fonte_a)
            nomes = (
                ("tl", 0, 0), ("tc", 1, 0), ("tr", 2, 0),
                ("ml", 0, 1), ("mc", 1, 1), ("mr", 2, 1),
                ("bl", 0, 2), ("bc", 1, 2), ("br", 2, 2),
            )
            for nome, ix, iy in nomes:
                recorte = imagem.crop((xs[ix], ys[iy], xs[ix + 1], ys[iy + 1]))
                fatias[nome] = arcade.Texture(
                    recorte,
                    hash=f"reino:{asset_id}:9:{margem}:{nome}",
                    hit_box_algorithm=None,
                )
            self._fatias[chave] = fatias
        fatias = self._fatias[chave]
        largura_meio = max(1, largura - margem * 2)
        altura_meio = max(1, altura - margem * 2)
        destinos = {
            "tl": (x, y + altura - margem, margem, margem),
            "tc": (x + margem, y + altura - margem, largura_meio, margem),
            "tr": (x + largura - margem, y + altura - margem, margem, margem),
            "ml": (x, y + margem, margem, altura_meio),
            "mc": (x + margem, y + margem, largura_meio, altura_meio),
            "mr": (x + largura - margem, y + margem, margem, altura_meio),
            "bl": (x, y, margem, margem),
            "bc": (x + margem, y, largura_meio, margem),
            "br": (x + largura - margem, y, margem, margem),
        }
        for nome, (dx, dy, dw, dh) in destinos.items():
            arcade.draw_texture_rect(
                fatias[nome],
                arcade.LBWH(dx, dy, dw, dh),
                pixelated=True,
                alpha=alpha,
            )
        return True
