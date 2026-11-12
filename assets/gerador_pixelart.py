"""Gerador flexível de pixel art para os assets do jogo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

Color = tuple[int, int, int, int]

PASTA_ASSETS = Path(__file__).resolve().parent

CORES_NOMEADAS = {
    "transparente": (0, 0, 0, 0),
    "transparent": (0, 0, 0, 0),
    "none": (0, 0, 0, 0),
    "branco": (255, 255, 255, 255),
    "white": (255, 255, 255, 255),
    "preto": (0, 0, 0, 255),
    "black": (0, 0, 0, 255),
}

CASA_TELHADO = (122, 54, 44, 255)
CASA_TELHADO_ESCURO = (86, 38, 32, 255)
CASA_PAREDE = (200, 158, 112, 255)
CASA_PAREDE_ESCURA = (164, 122, 82, 255)
CASA_CONTORNO = (54, 36, 30, 255)
CASA_JANELA = (150, 206, 230, 255)
CASA_PORTA = (76, 50, 34, 255)

MEDIEVAL_PAREDE = (224, 208, 174, 255)
MEDIEVAL_PAREDE_ESCURA = (190, 172, 138, 255)
MEDIEVAL_MADEIRA = (104, 66, 42, 255)
MEDIEVAL_MADEIRA_ESCURA = (74, 48, 32, 255)
MEDIEVAL_TELHA = (122, 60, 44, 255)
MEDIEVAL_TELHA_ESCURA = (86, 42, 34, 255)
MEDIEVAL_TELHA_CLARA = (150, 80, 56, 255)
MEDIEVAL_PEDRA = (144, 138, 128, 255)
MEDIEVAL_PEDRA_ESCURA = (100, 96, 88, 255)
MEDIEVAL_JANELA = (190, 218, 220, 255)
MEDIEVAL_FERRO = (62, 58, 54, 255)
MEDIEVAL_CONTORNO = (42, 30, 24, 255)


def cor_de_texto(texto: str) -> Color:
    valor = texto.strip().lower()
    if valor in CORES_NOMEADAS:
        return CORES_NOMEADAS[valor]
    if valor.startswith("#"):
        hexadecimal = valor[1:]
        if len(hexadecimal) == 6:
            return (
                int(hexadecimal[0:2], 16),
                int(hexadecimal[2:4], 16),
                int(hexadecimal[4:6], 16),
                255,
            )
        if len(hexadecimal) == 8:
            return (
                int(hexadecimal[0:2], 16),
                int(hexadecimal[2:4], 16),
                int(hexadecimal[4:6], 16),
                int(hexadecimal[6:8], 16),
            )
    if "," in valor:
        partes = [int(parte.strip()) for parte in valor.split(",")]
        if len(partes) == 3:
            return (partes[0], partes[1], partes[2], 255)
        if len(partes) == 4:
            return (partes[0], partes[1], partes[2], partes[3])
    raise ValueError(f"Cor inválida: {texto}")


def normalizar_cor(cor) -> Color:
    if isinstance(cor, str):
        return cor_de_texto(cor)
    if isinstance(cor, (tuple, list)) and len(cor) in (3, 4):
        valores = [int(valor) for valor in cor]
        if len(valores) == 3:
            valores.append(255)
        return (valores[0], valores[1], valores[2], valores[3])
    raise ValueError(f"Cor inválida: {cor!r}")


class PixelCanvas:
    def __init__(
        self,
        largura: int,
        altura: int,
        fundo: Color = (0, 0, 0, 0),
    ) -> None:
        if largura <= 0 or altura <= 0:
            raise ValueError("Largura e altura devem ser positivas.")
        self.largura = largura
        self.altura = altura
        self.imagem = Image.new("RGBA", (largura, altura), fundo)
        self._pixels = self.imagem.load()

    def pixel(self, x: int, y: int, cor) -> None:
        if 0 <= x < self.largura and 0 <= y < self.altura:
            self._pixels[x, y] = normalizar_cor(cor)

    def retangulo(
        self,
        x: int,
        y: int,
        largura: int,
        altura: int,
        cor,
        preenchido: bool = True,
    ) -> None:
        if largura <= 0 or altura <= 0:
            return
        cor_rgba = normalizar_cor(cor)
        if preenchido:
            for py in range(y, y + altura):
                for px in range(x, x + largura):
                    self.pixel(px, py, cor_rgba)
            return
        for px in range(x, x + largura):
            self.pixel(px, y, cor_rgba)
            self.pixel(px, y + altura - 1, cor_rgba)
        for py in range(y, y + altura):
            self.pixel(x, py, cor_rgba)
            self.pixel(x + largura - 1, py, cor_rgba)

    def poligono(
        self,
        pontos: list[tuple[int, int]],
        cor,
        preenchido: bool = True,
    ) -> None:
        if len(pontos) < 3:
            return
        cor_rgba = normalizar_cor(cor)
        desenho = ImageDraw.Draw(self.imagem)
        if preenchido:
            desenho.polygon(pontos, fill=cor_rgba)
        else:
            desenho.line([*pontos, pontos[0]], fill=cor_rgba, width=1)
        self._pixels = self.imagem.load()

    def linha(self, x0: int, y0: int, x1: int, y1: int, cor) -> None:
        cor_rgba = normalizar_cor(cor)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        erro = dx - dy
        while True:
            self.pixel(x0, y0, cor_rgba)
            if x0 == x1 and y0 == y1:
                break
            erro_duplo = erro * 2
            if erro_duplo > -dy:
                erro -= dy
                x0 += sx
            if erro_duplo < dx:
                erro += dx
                y0 += sy

    def aplicar_fundo(self, fundo) -> "PixelCanvas":
        cor = normalizar_cor(fundo)
        if cor[3] == 0:
            return self
        base = Image.new("RGBA", (self.largura, self.altura), cor)
        base.alpha_composite(self.imagem)
        self.imagem = base
        self._pixels = self.imagem.load()
        return self

    def redimensionar(self, fator: int) -> "PixelCanvas":
        if fator < 1:
            raise ValueError("A escala deve ser pelo menos 1.")
        if fator == 1:
            return self
        novo = PixelCanvas(self.largura * fator, self.altura * fator)
        novo.imagem = self.imagem.resize(
            (novo.largura, novo.altura), Image.Resampling.NEAREST
        )
        novo._pixels = novo.imagem.load()
        return novo

    def salvar(self, caminho: str | Path) -> Path:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        self.imagem.save(destino, format="PNG")
        return destino

    @classmethod
    def from_grid(cls, linhas: list[str], paleta: dict[str, object]) -> "PixelCanvas":
        if not linhas:
            raise ValueError("O grid precisa ter pelo menos uma linha.")
        largura = max(len(linha) for linha in linhas)
        canvas = cls(largura, len(linhas))
        for y, linha in enumerate(linhas):
            for x, caractere in enumerate(linha):
                if caractere in paleta:
                    canvas.pixel(x, y, paleta[caractere])
                elif caractere not in (" ", "."):
                    raise ValueError(f"Caractere sem cor na paleta: {caractere!r}")
        return canvas


def template_casa() -> PixelCanvas:
    canvas = PixelCanvas(16, 16)
    for indice in range(6):
        canvas.retangulo(
            7 - indice,
            2 + indice,
            2 + indice * 2,
            1,
            CASA_TELHADO,
        )
    canvas.retangulo(1, 8, 14, 1, CASA_TELHADO_ESCURO)
    canvas.retangulo(1, 9, 14, 6, CASA_PAREDE)
    canvas.retangulo(1, 9, 14, 6, CASA_CONTORNO, preenchido=False)
    canvas.retangulo(3, 10, 2, 2, CASA_JANELA)
    canvas.retangulo(11, 10, 2, 2, CASA_JANELA)
    canvas.retangulo(7, 12, 2, 3, CASA_PORTA)
    return canvas


def template_casa_isometrica() -> PixelCanvas:
    canvas = PixelCanvas(32, 32)
    topo = (16, 3)
    esquerda = (2, 12)
    frente = (16, 21)
    direita = (30, 12)
    esquerda_baixo = (2, 20)
    frente_baixo = (16, 29)
    direita_baixo = (30, 20)

    canvas.poligono(
        [esquerda, frente, frente_baixo, esquerda_baixo],
        CASA_PAREDE,
    )
    canvas.poligono(
        [frente, direita, direita_baixo, frente_baixo],
        CASA_PAREDE_ESCURA,
    )
    canvas.poligono([topo, esquerda, frente], CASA_TELHADO)
    canvas.poligono([topo, frente, direita], CASA_TELHADO_ESCURO)

    canvas.poligono(
        [esquerda, frente, frente_baixo, esquerda_baixo],
        CASA_CONTORNO,
        preenchido=False,
    )
    canvas.poligono(
        [frente, direita, direita_baixo, frente_baixo],
        CASA_CONTORNO,
        preenchido=False,
    )
    canvas.poligono([topo, esquerda, frente], CASA_CONTORNO, preenchido=False)
    canvas.poligono([topo, frente, direita], CASA_CONTORNO, preenchido=False)

    canvas.poligono(
        [(7, 18), (11, 20), (11, 25), (7, 23)],
        CASA_PORTA,
    )
    canvas.poligono(
        [(4, 14), (7, 15), (7, 17), (4, 16)],
        CASA_JANELA,
    )
    canvas.poligono(
        [(20, 20), (23, 18), (23, 20), (20, 22)],
        CASA_JANELA,
    )
    return canvas


def template_casa_frontal_45() -> PixelCanvas:
    canvas = PixelCanvas(32, 32)
    fachada = [(5, 18), (27, 18), (27, 29), (5, 29)]
    telhado = [(10, 5), (22, 5), (30, 18), (2, 18)]

    canvas.poligono(fachada, CASA_PAREDE)
    canvas.poligono(telhado, CASA_TELHADO)

    canvas.retangulo(5, 18, 22, 1, CASA_TELHADO_ESCURO)
    for y in (9, 12, 15):
        esquerda = int(round(10 - (y - 5) * 8 / 13))
        direita = int(round(22 + (y - 5) * 8 / 13))
        canvas.linha(esquerda + 2, y, direita - 2, y, CASA_TELHADO_ESCURO)

    canvas.poligono(fachada, CASA_CONTORNO, preenchido=False)
    canvas.poligono(telhado, CASA_CONTORNO, preenchido=False)
    canvas.linha(9, 5, 23, 5, CASA_CONTORNO)

    canvas.retangulo(23, 6, 3, 5, CASA_PAREDE_ESCURA)
    canvas.retangulo(23, 6, 3, 5, CASA_CONTORNO, preenchido=False)
    canvas.retangulo(23, 6, 3, 1, CASA_CONTORNO)

    canvas.retangulo(13, 22, 6, 7, CASA_PORTA)
    canvas.retangulo(13, 22, 6, 7, CASA_CONTORNO, preenchido=False)
    canvas.retangulo(7, 21, 4, 4, CASA_JANELA)
    canvas.retangulo(7, 21, 4, 4, CASA_CONTORNO, preenchido=False)
    canvas.retangulo(21, 21, 4, 4, CASA_JANELA)
    canvas.retangulo(21, 21, 4, 4, CASA_CONTORNO, preenchido=False)
    canvas.retangulo(12, 29, 8, 1, CASA_PAREDE_ESCURA)
    return canvas


def template_casa_medieval() -> PixelCanvas:
    canvas = PixelCanvas(32, 32)
    fachada = [(5, 18), (27, 18), (27, 29), (5, 29)]
    telhado = [(9, 4), (23, 4), (31, 18), (1, 18)]

    canvas.poligono(fachada, MEDIEVAL_PAREDE)
    canvas.retangulo(5, 27, 22, 2, MEDIEVAL_PEDRA)
    canvas.poligono(fachada, MEDIEVAL_CONTORNO, preenchido=False)
    canvas.retangulo(5, 27, 22, 2, MEDIEVAL_PEDRA_ESCURA, preenchido=False)
    for x in (9, 14, 19, 24):
        canvas.linha(x, 27, x, 28, MEDIEVAL_PEDRA_ESCURA)

    canvas.poligono(telhado, MEDIEVAL_TELHA)
    for y in (7, 10, 13, 16):
        esquerda = int(round(9 - (y - 4) * 8 / 14))
        direita = int(round(23 + (y - 4) * 8 / 14))
        canvas.linha(esquerda + 1, y, direita - 1, y, MEDIEVAL_TELHA_ESCURA)
        if y in (10, 16):
            canvas.linha(
                esquerda + 2, y - 1, direita - 2, y - 1, MEDIEVAL_TELHA_CLARA
            )
    canvas.poligono(telhado, MEDIEVAL_CONTORNO, preenchido=False)
    canvas.linha(8, 4, 24, 4, MEDIEVAL_TELHA_ESCURA)

    canvas.retangulo(23, 2, 4, 8, MEDIEVAL_PEDRA)
    canvas.retangulo(23, 2, 4, 8, MEDIEVAL_CONTORNO, preenchido=False)
    canvas.retangulo(22, 2, 6, 1, MEDIEVAL_PEDRA_ESCURA)
    canvas.linha(24, 4, 25, 4, MEDIEVAL_PEDRA_ESCURA)
    canvas.linha(24, 7, 25, 7, MEDIEVAL_PEDRA_ESCURA)

    canvas.retangulo(5, 18, 22, 1, MEDIEVAL_MADEIRA)
    canvas.retangulo(5, 19, 22, 1, MEDIEVAL_PAREDE_ESCURA)
    canvas.retangulo(5, 25, 22, 1, MEDIEVAL_MADEIRA)
    for x in (5, 11, 20, 26):
        canvas.retangulo(x, 18, 1, 9, MEDIEVAL_MADEIRA)
    canvas.linha(6, 24, 10, 20, MEDIEVAL_MADEIRA)
    canvas.linha(26, 24, 22, 20, MEDIEVAL_MADEIRA)

    canvas.retangulo(13, 22, 6, 7, MEDIEVAL_MADEIRA)
    canvas.retangulo(14, 21, 4, 1, MEDIEVAL_MADEIRA)
    canvas.retangulo(13, 22, 6, 7, MEDIEVAL_CONTORNO, preenchido=False)
    canvas.linha(14, 21, 17, 21, MEDIEVAL_CONTORNO)
    canvas.linha(13, 25, 17, 25, MEDIEVAL_FERRO)
    canvas.linha(13, 28, 17, 28, MEDIEVAL_FERRO)
    canvas.retangulo(17, 25, 1, 1, MEDIEVAL_FERRO)

    for x in (7, 21):
        canvas.retangulo(x, 21, 4, 4, MEDIEVAL_JANELA)
        canvas.retangulo(x, 21, 4, 4, MEDIEVAL_MADEIRA, preenchido=False)
        canvas.linha(x + 2, 21, x + 2, 24, MEDIEVAL_MADEIRA)
        canvas.linha(x, 22, x + 3, 22, MEDIEVAL_MADEIRA)
    return canvas


def template_checker() -> PixelCanvas:
    canvas = PixelCanvas(16, 16)
    cores = ((58, 92, 136, 255), (86, 128, 176, 255))
    for y in range(16):
        for x in range(16):
            canvas.pixel(x, y, cores[(x // 4 + y // 4) % 2])
    return canvas


TEMPLATES = {
    "casa": (template_casa, "Casa 16×16 com telhado, porta e janelas."),
    "casa_isometrica": (
        template_casa_isometrica,
        "Casa 32×32 em perspectiva isométrica.",
    ),
    "casa_frontal_45": (
        template_casa_frontal_45,
        "Casa 32×32 com frente e topo em visão elevada de 45°.",
    ),
    "casa_medieval": (
        template_casa_medieval,
        "Casa medieval 32×32 com enxaimel, telhado de telhas e base de pedra.",
    ),
    "checker": (template_checker, "Padrão xadrez 16×16 para testar cores."),
}


def escala_positiva(valor: str) -> int:
    numero = int(valor)
    if numero < 1:
        raise argparse.ArgumentTypeError("A escala deve ser pelo menos 1.")
    return numero


def carregar_grid(caminho: Path) -> tuple[PixelCanvas, str]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    linhas = dados.get("linhas")
    paleta = dados.get("paleta")
    if not isinstance(linhas, list) or not isinstance(paleta, dict):
        raise ValueError("O JSON precisa conter 'linhas' e 'paleta'.")
    canvas = PixelCanvas.from_grid(linhas, paleta)
    return canvas, str(dados.get("nome", "grid"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera pixel art PNG com Pillow.",
        epilog=(
            "Grid JSON: {\"nome\": \"teste\", \"paleta\": {\".\": \"#00000000\", "
            "\"R\": \"#7a362c\"}, \"linhas\": [\"..R..\", \".RRR.\"]}"
        ),
    )
    parser.add_argument("--template", default="casa")
    parser.add_argument("--listar-templates", action="store_true")
    parser.add_argument("--escala", type=escala_positiva, default=4)
    parser.add_argument("--saida")
    parser.add_argument("--fundo", default="transparente")
    parser.add_argument("--grid", type=Path)
    parser.add_argument("--forcar", action="store_true")
    parser.add_argument(
        "--lote",
        help="Gera um lote completo: estruturas, personagens, mapa, efeitos, ui, eventos, fundo ou todos.",
    )
    parser.add_argument("--listar-lotes", action="store_true")
    args = parser.parse_args(argv)

    if args.listar_lotes:
        from pixelart.catalogo import LOTES

        for nome in (*LOTES, "todos"):
            print(nome)
        return 0

    if args.lote:
        from pixelart.catalogo import executar_lote

        total = executar_lote(args.lote, forcar=args.forcar)
        print(f"Lote '{args.lote}' concluído: {total} assets processados.")
        return 0

    if args.listar_templates:
        for nome, (_, descricao) in sorted(TEMPLATES.items()):
            print(f"{nome}: {descricao}")
        return 0

    try:
        if args.grid is not None:
            canvas, nome = carregar_grid(args.grid)
        else:
            template = TEMPLATES.get(args.template)
            if template is None:
                parser.error(
                    f"Template desconhecido: {args.template}. "
                    f"Disponíveis: {', '.join(sorted(TEMPLATES))}"
                )
            canvas = template[0]()
            nome = args.template
        canvas.aplicar_fundo(cor_de_texto(args.fundo))
    except (ValueError, OSError, json.JSONDecodeError) as erro:
        parser.error(str(erro))

    canvas = canvas.redimensionar(args.escala)
    destino = (
        Path(args.saida)
        if args.saida
        else PASTA_ASSETS / f"teste_pixelart_{nome}.png"
    )
    if destino.suffix == "":
        destino = destino.with_suffix(".png")
    if destino.exists() and not args.forcar:
        parser.error(f"Arquivo já existe: {destino} (use --forcar)")

    canvas.salvar(destino)
    with Image.open(destino) as imagem:
        print(
            f"Gerado: {destino} | "
            f"{imagem.width}x{imagem.height} | {imagem.mode}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
