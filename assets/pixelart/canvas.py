"""Canvas RGBA e primitivas de pixel art."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .paleta import TRANSPARENTE, Color


def rgba(cor) -> Color:
    if isinstance(cor, str):
        valor = cor.strip().lower().lstrip("#")
        if len(valor) == 6:
            return (
                int(valor[0:2], 16),
                int(valor[2:4], 16),
                int(valor[4:6], 16),
                255,
            )
        if len(valor) == 8:
            return (
                int(valor[0:2], 16),
                int(valor[2:4], 16),
                int(valor[4:6], 16),
                int(valor[6:8], 16),
            )
        raise ValueError(f"Cor inválida: {cor}")
    if isinstance(cor, (tuple, list)) and len(cor) in (3, 4):
        valores = [int(valor) for valor in cor]
        if len(valores) == 3:
            valores.append(255)
        return (valores[0], valores[1], valores[2], valores[3])
    raise ValueError(f"Cor inválida: {cor!r}")


class Canvas:
    def __init__(
        self,
        largura: int,
        altura: int,
        fundo: Color = TRANSPARENTE,
    ) -> None:
        if largura <= 0 or altura <= 0:
            raise ValueError("Dimensões inválidas.")
        self.largura = int(largura)
        self.altura = int(altura)
        self.imagem = Image.new("RGBA", (self.largura, self.altura), fundo)
        self.desenho = ImageDraw.Draw(self.imagem)

    def pixel(self, x: int, y: int, cor) -> None:
        if 0 <= x < self.largura and 0 <= y < self.altura:
            self.imagem.putpixel((int(x), int(y)), rgba(cor))

    def retangulo(
        self,
        x: int,
        y: int,
        largura: int,
        altura: int,
        cor=None,
        contorno=None,
        largura_contorno: int = 1,
    ) -> None:
        if largura <= 0 or altura <= 0:
            return
        x1 = x + largura - 1
        y1 = y + altura - 1
        self.desenho.rectangle(
            [x, y, x1, y1],
            fill=rgba(cor) if cor is not None else None,
            outline=rgba(contorno) if contorno is not None else None,
            width=max(1, largura_contorno),
        )

    def linha(self, x0: int, y0: int, x1: int, y1: int, cor, largura: int = 1) -> None:
        self.desenho.line(
            [(int(x0), int(y0)), (int(x1), int(y1))],
            fill=rgba(cor),
            width=max(1, largura),
        )

    def polilinha(self, pontos: list[tuple[int, int]], cor, largura: int = 1) -> None:
        if len(pontos) < 2:
            return
        self.desenho.line(
            [(int(x), int(y)) for x, y in pontos],
            fill=rgba(cor),
            width=max(1, largura),
        )

    def poligono(
        self,
        pontos: list[tuple[int, int]],
        cor=None,
        contorno=None,
        largura_contorno: int = 1,
    ) -> None:
        if len(pontos) < 3:
            return
        self.desenho.polygon(
            [(int(x), int(y)) for x, y in pontos],
            fill=rgba(cor) if cor is not None else None,
            outline=rgba(contorno) if contorno is not None else None,
        )
        if contorno is not None and largura_contorno > 1:
            self.desenho.line(
                [(int(x), int(y)) for x, y in [*pontos, pontos[0]]],
                fill=rgba(contorno),
                width=max(1, largura_contorno),
            )

    def elipse(
        self,
        x: int,
        y: int,
        largura: int,
        altura: int,
        cor=None,
        contorno=None,
        largura_contorno: int = 1,
    ) -> None:
        if largura <= 0 or altura <= 0:
            return
        self.desenho.ellipse(
            [x, y, x + largura - 1, y + altura - 1],
            fill=rgba(cor) if cor is not None else None,
            outline=rgba(contorno) if contorno is not None else None,
            width=max(1, largura_contorno),
        )

    def circulo(
        self,
        cx: int,
        cy: int,
        raio: int,
        cor=None,
        contorno=None,
        largura_contorno: int = 1,
    ) -> None:
        self.elipse(
            cx - raio,
            cy - raio,
            raio * 2,
            raio * 2,
            cor=cor,
            contorno=contorno,
            largura_contorno=largura_contorno,
        )

    def colar(self, outro: "Canvas", x: int, y: int) -> None:
        self.imagem.alpha_composite(outro.imagem, (int(x), int(y)))
        self.desenho = ImageDraw.Draw(self.imagem)

    def recortar(self) -> "Canvas":
        caixa = self.imagem.getbbox()
        if caixa is None:
            return Canvas(1, 1)
        recorte = self.imagem.crop(caixa)
        novo = Canvas(recorte.width, recorte.height)
        novo.imagem = recorte
        novo.desenho = ImageDraw.Draw(novo.imagem)
        return novo

    def escala(self, fator: int) -> "Canvas":
        if fator < 1:
            raise ValueError("Escala inválida.")
        if fator == 1:
            return self
        novo = Canvas(self.largura * fator, self.altura * fator)
        novo.imagem = self.imagem.resize(
            (novo.largura, novo.altura), Image.Resampling.NEAREST
        )
        novo.desenho = ImageDraw.Draw(novo.imagem)
        return novo

    def redimensionar_para(self, largura: int, altura: int) -> "Canvas":
        novo = Canvas(largura, altura)
        novo.imagem = self.imagem.resize(
            (int(largura), int(altura)), Image.Resampling.NEAREST
        )
        novo.desenho = ImageDraw.Draw(novo.imagem)
        return novo

    def ajustar_em(self, largura: int, altura: int) -> "Canvas":
        recorte = self.recortar()
        fator = min(largura / recorte.largura, altura / recorte.altura)
        novo_largura = max(1, int(round(recorte.largura * fator)))
        novo_altura = max(1, int(round(recorte.altura * fator)))
        ajustado = recorte.redimensionar_para(novo_largura, novo_altura)
        novo = Canvas(largura, altura)
        x = (largura - ajustado.largura) // 2
        y = (altura - ajustado.altura) // 2
        novo.imagem.alpha_composite(ajustado.imagem, (x, y))
        novo.desenho = ImageDraw.Draw(novo.imagem)
        return novo

    def salvar(self, caminho: str | Path) -> Path:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        self.imagem.save(destino, format="PNG")
        return destino

    @classmethod
    def folha(cls, frames: list["Canvas"], espacamento: int = 0) -> "Canvas":
        if not frames:
            raise ValueError("Folha sem frames.")
        largura = sum(frame.largura for frame in frames)
        largura += espacamento * (len(frames) - 1)
        altura = max(frame.altura for frame in frames)
        folha = cls(largura, altura)
        x = 0
        for frame in frames:
            folha.imagem.alpha_composite(
                frame.imagem, (x, (altura - frame.altura) // 2)
            )
            x += frame.largura + espacamento
        folha.desenho = ImageDraw.Draw(folha.imagem)
        return folha
