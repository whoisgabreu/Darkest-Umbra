"""Entidades móveis do mundo: cidadãos, soldados, inimigos e árvores."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TRABALHO_POR_PREDIO = {
    "madeireira": "serrador",
    "fazenda": "fazendeiro",
    "mina": "minerador",
    "mercado": "comerciante",
    "posto": "colonizador",
}

CORES_PROFISSAO = {
    "ocioso": (200, 205, 215),
    "madeireiro": (168, 118, 66),
    "serrador": (214, 150, 70),
    "fazendeiro": (110, 190, 96),
    "minerador": (150, 160, 176),
    "comerciante": (230, 196, 92),
    "pedreiro": (150, 145, 138),
    "pescador": (96, 170, 200),
    "colonizador": (120, 200, 210),
    "soldado": (90, 150, 220),
}

NOMES_PROFISSAO = {
    "ocioso": "Ocioso",
    "madeireiro": "Madeireiro",
    "serrador": "Serrador",
    "fazendeiro": "Fazendeiro",
    "minerador": "Minerador",
    "comerciante": "Comerciante",
    "pedreiro": "Pedreiro",
    "pescador": "Pescador",
    "colonizador": "Colonizador",
    "soldado": "Soldado",
}


def distancia(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(bx - ax, by - ay)


CLASSES_TROPA = {
    "soldado": {"base": "soldado", "nome": "Soldado", "hp": 70, "atk": 16, "alcance": 72, "cd": 0.9, "cor": (90, 150, 220), "custo": {"dinheiro": 8, "ouro": 2}},
    "arqueiro": {"base": "arqueiro", "nome": "Arqueiro", "hp": 50, "atk": 10, "alcance": 250, "cd": 1.0, "cor": (110, 180, 120), "custo": {"dinheiro": 10, "ouro": 2}},
    "mago": {"base": "mago", "nome": "Mago", "hp": 45, "atk": 10, "alcance": 220, "cd": 1.1, "cor": (150, 120, 210), "custo": {"dinheiro": 15, "ouro": 4, "minerio_arcano": 1}},
    "curandeiro": {"base": "curandeiro", "nome": "Curandeiro", "hp": 50, "atk": 0, "alcance": 0, "cd": 2.5, "cor": (240, 220, 160), "custo": {"dinheiro": 15, "ouro": 4, "ambar": 1}},
    "defensor": {"base": "soldado", "nome": "Defensor", "hp": 130, "atk": 12, "alcance": 72, "cd": 1.0, "cor": (120, 170, 240), "custo": {"dinheiro": 15, "ouro": 5, "minerio_arcano": 3}},
    "destruidor": {"base": "soldado", "nome": "Destruidor", "hp": 80, "atk": 14, "alcance": 72, "cd": 1.1, "cor": (220, 130, 100), "custo": {"dinheiro": 15, "ouro": 5, "essencia_sombria": 2}},
    "patrulheiro": {"base": "arqueiro", "nome": "Patrulheiro", "hp": 60, "atk": 10, "alcance": 270, "cd": 0.45, "cor": (140, 210, 130), "custo": {"dinheiro": 15, "ouro": 5, "ambar": 3}},
    "guardiao": {"base": "arqueiro", "nome": "Guardião", "hp": 85, "atk": 22, "alcance": 330, "cd": 1.3, "cor": (90, 190, 170), "custo": {"dinheiro": 20, "ouro": 8, "cristal_runico": 3}},
    "mago_eletrico": {"base": "mago", "nome": "Mago Elétrico", "hp": 50, "atk": 9, "alcance": 230, "cd": 1.2, "cor": (200, 180, 90), "custo": {"ouro": 10, "minerio_arcano": 4, "cristal_runico": 2}},
    "mago_gelo": {"base": "mago", "nome": "Mago de Gelo", "hp": 50, "atk": 6, "alcance": 230, "cd": 1.1, "cor": (130, 200, 240), "custo": {"ouro": 10, "cristal_runico": 4, "essencia_sombria": 1}},
    "bardo": {"base": "curandeiro", "nome": "Bardo", "hp": 55, "atk": 0, "alcance": 0, "cd": 2.0, "cor": (240, 200, 120), "custo": {"ouro": 8, "ambar": 3, "essencia_sombria": 1}},
    "protetor": {"base": "curandeiro", "nome": "Protetor", "hp": 65, "atk": 0, "alcance": 0, "cd": 3.0, "cor": (180, 210, 240), "custo": {"ouro": 8, "cristal_runico": 3, "minerio_arcano": 2}},
}

BASE_TROPA = {classe: dados["base"] for classe, dados in CLASSES_TROPA.items()}

CUSTO_TROPA = {classe: dados["custo"] for classe, dados in CLASSES_TROPA.items()}

RECURSOS_RAROS = {
    "minerio_arcano": "Minério Arcano",
    "ambar": "Âmbar",
    "cristal_runico": "Cristal Rúnico",
    "essencia_sombria": "Essência Sombria",
}

NIVEL_XP_MAX = 10


def nivel_por_xp(xp: float) -> int:
    return max(1, min(NIVEL_XP_MAX, 1 + int(max(0.0, xp) // 100)))


def xp_para_proximo_nivel(xp: float) -> float:
    nivel = nivel_por_xp(xp)
    if nivel >= NIVEL_XP_MAX:
        return 0.0
    return nivel * 100 - xp


def bonus_xp(experiencia: dict[str, float], profissao: str) -> float:
    return 1.0 + 0.08 * (nivel_por_xp(experiencia.get(profissao, 0.0)) - 1)


@dataclass
class Cidadao:
    id: int
    x: float
    y: float
    profissao: str = "ocioso"
    estado: str = "ocioso"
    caminho: list[tuple[float, float]] = field(default_factory=list)
    alvo_predio: int | None = None
    alvo_arvore: tuple[int, int] | None = None
    alvo_rocha: tuple[int, int] | None = None
    alvo_pesca: tuple[int, int] | None = None
    alvo_mover: tuple[float, float] | None = None
    troncos: int = 0
    pedras: int = 0
    hp: float = 30.0
    hp_max: float = 30.0
    tempo: float = 0.0
    tempo_xp: float = 0.0
    experiencia: dict[str, float] = field(default_factory=dict)
    atributos: dict[str, int] = field(default_factory=dict)
    pontos_usados: int = 0
    rei: bool = False
    velocidade: float = 190.0


@dataclass
class Soldado:
    id: int
    x: float
    y: float
    hp: float
    hp_max: float
    ataque: float
    classe: str = "soldado"
    velocidade: float = 200.0
    alcance: float = 72.0
    cooldown: float = 0.0
    cooldown_max: float = 0.9
    escudo: float = 0.0
    habilidade_timer: float = 0.0
    caminho: list[tuple[float, float]] = field(default_factory=list)
    poste: tuple[float, float] = (0.0, 0.0)
    alvo: Inimigo | None = None
    ordem_ataque: bool = False
    tempo_recalculo: float = 0.0
    xp: float = 0.0
    atributos: dict[str, int] = field(default_factory=dict)
    pontos_usados: int = 0


@dataclass
class Inimigo:
    id: int
    x: float
    y: float
    hp: float
    hp_max: float
    ataque: float
    velocidade: float = 170.0
    velocidade_base: float = 170.0
    alcance: float = 72.0
    cooldown: float = 0.0
    slow_timer: float = 0.0
    caminho: list[tuple[float, float]] = field(default_factory=list)
    alvo_soldado: Soldado | None = None
    alvo_estrutura: int | None = None
    alvo_cidadao: Cidadao | None = None
    lar: tuple[float, float] = (0.0, 0.0)
    tempo_recalculo: float = 0.0


@dataclass
class Caravana:
    id: int
    x: float
    y: float
    caminho: list[tuple[float, float]] = field(default_factory=list)
    velocidade: float = 165.0
    membros: list = field(default_factory=list)
    carga: dict[str, float] = field(default_factory=dict)
    capacidade: float = 250.0
    estado: str = "parada"
    tempo: float = 0.0


@dataclass
class Arvore:
    col: int
    row: int
    estado: str = "adulta"
    regrow: float = 0.0
    vida: int = 3
    vida_max: int = 3


@dataclass
class Rocha:
    col: int
    row: int
    estado: str = "adulta"
    regrow: float = 0.0
    vida: int = 3
    vida_max: int = 3


def mover_entidade(entidade, dt: float, mapa=None) -> bool:
    """Segue o caminho (pontos em mundo). Retorna True ao chegar ao fim."""
    restante = dt
    while restante > 0 and entidade.caminho:
        fator = mapa.fator_movimento(entidade.x, entidade.y) if mapa else 1.0
        alvo_x, alvo_y = entidade.caminho[0]
        dx = alvo_x - entidade.x
        dy = alvo_y - entidade.y
        dist = math.hypot(dx, dy)
        if dist < 0.001:
            entidade.caminho.pop(0)
            continue
        passo = entidade.velocidade * restante * fator
        if passo >= dist:
            entidade.x = alvo_x
            entidade.y = alvo_y
            entidade.caminho.pop(0)
            restante -= dist / (entidade.velocidade * fator)
        else:
            entidade.x += dx / dist * passo
            entidade.y += dy / dist * passo
            restante = 0.0
    return not entidade.caminho
