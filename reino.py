"""Lógica econômica do reino.

Este módulo não importa nada gráfico. Construções são instâncias com ID,
permitindo várias estruturas do mesmo tipo. Custos escalam com a quantidade.
"""

from __future__ import annotations

import json
import math
import os
import random
from collections import deque
from dataclasses import dataclass, field

from unidades import BASE_TROPA, CLASSES_TROPA, CUSTO_TROPA, RECURSOS_RAROS

DIA_SEGUNDOS = 30.0
CONSUMO_POR_PESSOA = 0.4
MAX_NIVEL = 10
SAVE_VERSION = 4
INTERVALO_ATAQUE = (10, 15)
PRIMEIRO_ATAQUE = (10, 14)
CUSTO_SOLDADO = {"dinheiro": 8.0, "ouro": 2.0}
ESCALA_CUSTO_INSTANCIAS = 1.4
CASTELO_ID = 0

RECURSOS = ("madeira", "troncos", "pedra", "ferro", "ouro", "dinheiro", "alimento")

NOMES_RECURSOS = {
    "madeira": "Madeira",
    "troncos": "Troncos",
    "pedra": "Pedra",
    "ferro": "Ferro",
    "ouro": "Ouro",
    "dinheiro": "Dinheiro",
    "alimento": "Alimento",
}

NOMES_CONSTRUCOES = {
    "madeireira": "Madeireira",
    "mina": "Mina",
    "fazenda": "Fazenda",
    "mercado": "Mercado",
    "ferraria": "Ferraria",
    "quartel": "Quartel",
    "casas": "Casas",
    "celeiro": "Celeiro",
    "muralha": "Muralha",
    "barricada": "Barricada",
    "posto": "Posto Avançado",
    "arquearia": "Arquearia",
    "torre_magia": "Torre de Magia",
    "santuario": "Santuário",
}

CONSTRUCOES = {
    "madeireira": {
        "custo": {"madeira": 25},
        "crescimento": 1.55,
        "vagas": 2,
        "tipo": "refino",
    },
    "mina": {
        "custo": {"madeira": 35},
        "crescimento": 1.55,
        "vagas": 3,
        "tipo": "mina",
        "taxa_ferro": 3.0,
        "taxa_ouro": 1.0,
        "taxa_pedra": 4.0,
    },
    "fazenda": {
        "custo": {"madeira": 25},
        "crescimento": 1.55,
        "vagas": 4,
        "tipo": "producao",
        "recurso": "alimento",
        "taxa": 3.0,
    },
    "mercado": {
        "custo": {"madeira": 45},
        "crescimento": 1.6,
        "vagas": 3,
        "tipo": "producao",
        "recurso": "dinheiro",
        "taxa": 3.0,
    },
    "ferraria": {
        "custo": {"madeira": 60, "ferro": 20},
        "crescimento": 1.6,
        "vagas": 0,
        "tipo": "bonus",
    },
    "quartel": {
        "custo": {"madeira": 60, "dinheiro": 25},
        "crescimento": 1.7,
        "vagas": 0,
        "tipo": "soldados",
    },
    "casas": {
        "custo": {"madeira": 30},
        "crescimento": 1.55,
        "vagas": 0,
        "tipo": "populacao",
    },
    "celeiro": {
        "custo": {"madeira": 35},
        "crescimento": 1.55,
        "vagas": 0,
        "tipo": "estoque",
    },
    "muralha": {
        "custo": {"pedra": 20, "madeira": 10},
        "crescimento": 1.5,
        "vagas": 0,
        "tipo": "defesa",
        "escala_custo": 1.0,
        "hp_base": 220.0,
        "hp_nivel": 60.0,
    },
    "barricada": {
        "custo": {"madeira": 15},
        "crescimento": 1.4,
        "vagas": 0,
        "tipo": "defesa",
        "escala_custo": 1.0,
        "hp_base": 80.0,
        "hp_nivel": 20.0,
    },
    "posto": {
        "custo": {"madeira": 80, "pedra": 60, "dinheiro": 40},
        "crescimento": 1.6,
        "vagas": 2,
        "tipo": "posto",
        "producao": {"madeira": 1.5, "pedra": 1.5, "alimento": 2.0, "ouro": 0.15},
        "armazem_base": 200.0,
        "defesa_dano": 6.0,
        "defesa_alcance": 3.0,
        "defesa_intervalo": 1.1,
    },
    "arquearia": {
        "custo": {"madeira": 70, "pedra": 30, "dinheiro": 30},
        "crescimento": 1.65,
        "vagas": 0,
        "tipo": "arqueiros",
    },
    "torre_magia": {
        "custo": {"madeira": 80, "pedra": 60, "dinheiro": 50, "ouro": 10},
        "crescimento": 1.7,
        "vagas": 0,
        "tipo": "magos",
    },
    "santuario": {
        "custo": {"madeira": 70, "pedra": 50, "dinheiro": 50},
        "crescimento": 1.65,
        "vagas": 0,
        "tipo": "curandeiros",
    },
}


@dataclass
class Construcao:
    id: int
    tipo: str
    nivel: int = 1
    trabalhadores: int = 0
    bonus_producao: float = 1.0
    hp: float = 0.0
    hp_max: float = 0.0
    progressos: dict[str, float] = field(default_factory=dict)
    armazem: dict[str, float] = field(default_factory=dict)


class Reino:
    def __init__(self) -> None:
        self.recursos: dict[str, float] = {
            "madeira": 80.0,
            "troncos": 0.0,
            "pedra": 20.0,
            "ferro": 0.0,
            "ouro": 5.0,
            "dinheiro": 30.0,
            "alimento": 60.0,
        }
        self.populacao = 1
        self.soldados = 0
        self.arqueiros = 0
        self.magos = 0
        self.curandeiros = 0
        self.dia = 1
        self.tempo_dia = 0.0
        self.hp_castelo = 300.0
        self.proximo_id_construcao = 1
        self.construcoes: dict[int, Construcao] = {
            CASTELO_ID: Construcao(
                id=CASTELO_ID,
                tipo="castelo",
                nivel=1,
                hp=300.0,
                hp_max=300.0,
            )
        }
        self.recursos_raros: dict[str, float] = {
            chave: 0.0 for chave in RECURSOS_RAROS
        }
        self.castelos_perdidos = 0
        self.melhor_periodo = 1
        self.rei_morto = False

        self.crescimento = 0.0
        self.dias_sem_comida = 0
        self.recorde_dias = 1
        self.proximo_ataque_dia = random.randint(*PRIMEIRO_ATAQUE)
        self.aviso_ataque = False
        self.ataques_ativos = True
        self.toque_de_recolher = False
        self.mercador_dias = 0
        self.mercador_precos: dict[str, float] = {}
        self.ultimo_combate: dict | None = None
        self.pausado = False
        self.velocidade = 1
        self.derrota = False
        self.log: deque[str] = deque(maxlen=160)
        self.log.append("O reino foi fundado. Sobreviva o máximo de dias possível.")

    # ------------------------------------------------------------------
    # Instâncias de construção
    # ------------------------------------------------------------------
    def _criar_instancia(self, tipo: str, nivel: int = 1) -> int:
        identificador = self.proximo_id_construcao
        self.proximo_id_construcao += 1
        hp_max = self._hp_max_tipo(tipo, nivel)
        self.construcoes[identificador] = Construcao(
            id=identificador,
            tipo=tipo,
            nivel=nivel,
            hp=hp_max,
            hp_max=hp_max,
        )
        return identificador

    def _hp_max_tipo(self, tipo: str, nivel: int) -> float:
        config = self._config(tipo)
        if config is None:
            return 0.0
        hp_base = float(config.get("hp_base", 120.0))
        hp_nivel = float(config.get("hp_nivel", 40.0))
        return hp_base + hp_nivel * (nivel - 1)

    def instancias(self, tipo: str | None = None) -> list[Construcao]:
        if tipo is None:
            return [
                c for c in self.construcoes.values() if c.tipo != "castelo"
            ]
        return [c for c in self.construcoes.values() if c.tipo == tipo]

    def primeira_instancia(self, tipo: str) -> Construcao | None:
        for construcao in self.construcoes.values():
            if construcao.tipo == tipo and construcao.nivel > 0:
                return construcao
        return None

    def quantidade_instancias(self, tipo: str) -> int:
        return sum(1 for c in self.construcoes.values() if c.tipo == tipo and c.nivel > 0)

    def _soma_niveis(self, tipo: str) -> int:
        return sum(c.nivel for c in self.construcoes.values() if c.tipo == tipo)

    def _config(self, tipo: str) -> dict | None:
        return CONSTRUCOES.get(tipo)

    def vagas_instancia(self, id_instancia: int) -> int:
        construcao = self.construcoes.get(id_instancia)
        if construcao is None:
            return 0
        config = self._config(construcao.tipo)
        if config is None:
            return 0
        return config["vagas"] * construcao.nivel

    # ------------------------------------------------------------------
    # Custos escalonados
    # ------------------------------------------------------------------
    def _custo_base_nivel(self, tipo: str, nivel: int) -> dict[str, float]:
        config = self._config(tipo)
        if config is None:
            return {}
        fator = config["crescimento"] ** nivel
        return {r: float(q) * fator for r, q in config["custo"].items()}

    def custo_nova_instancia(self, tipo: str) -> dict[str, float]:
        if tipo not in CONSTRUCOES:
            return {}
        config = self._config(tipo)
        escala = float(config.get("escala_custo", ESCALA_CUSTO_INSTANCIAS)) if config else ESCALA_CUSTO_INSTANCIAS
        quantidade = self.quantidade_instancias(tipo)
        multiplicador = escala ** quantidade
        base = self._custo_base_nivel(tipo, 0)
        return {r: float(math.ceil(q * multiplicador)) for r, q in base.items()}

    def custo_melhoria(self, id_instancia: int) -> dict[str, float]:
        construcao = self.construcoes.get(id_instancia)
        if construcao is None or construcao.tipo not in CONSTRUCOES:
            return {}
        config = self._config(construcao.tipo)
        escala = float(config.get("escala_custo", ESCALA_CUSTO_INSTANCIAS)) if config else ESCALA_CUSTO_INSTANCIAS
        quantidade = self.quantidade_instancias(construcao.tipo)
        multiplicador = escala ** max(0, quantidade - 1)
        base = self._custo_base_nivel(construcao.tipo, construcao.nivel)
        return {r: float(math.ceil(q * multiplicador)) for r, q in base.items()}

    def pode_pagar(self, custo: dict[str, float]) -> bool:
        return all(self.recursos[r] >= q for r, q in custo.items())

    def pode_construir_nova(self, tipo: str) -> bool:
        if tipo not in CONSTRUCOES:
            return False
        return self.pode_pagar(self.custo_nova_instancia(tipo))

    def adicionar_instancia(self, tipo: str) -> tuple[bool, str, int | None]:
        if tipo not in CONSTRUCOES:
            return False, "Tipo inválido.", None
        custo = self.custo_nova_instancia(tipo)
        if not self.pode_pagar(custo):
            return False, "Recursos insuficientes.", None
        for recurso, quantidade in custo.items():
            self.recursos[recurso] -= quantidade
        identificador = self._criar_instancia(tipo, 1)
        self._log(f"{NOMES_CONSTRUCOES[tipo]} construída (#{identificador}).")
        return True, "ok", identificador

    def pode_melhorar(self, id_instancia: int) -> bool:
        construcao = self.construcoes.get(id_instancia)
        if construcao is None or construcao.tipo not in CONSTRUCOES:
            return False
        if construcao.nivel >= MAX_NIVEL:
            return False
        return self.pode_pagar(self.custo_melhoria(id_instancia))

    def melhorar_instancia(self, id_instancia: int) -> tuple[bool, str]:
        construcao = self.construcoes.get(id_instancia)
        if construcao is None or construcao.tipo not in CONSTRUCOES:
            return False, "Construção inválida."
        if construcao.nivel >= MAX_NIVEL:
            return False, "Nível máximo alcançado."
        custo = self.custo_melhoria(id_instancia)
        if not self.pode_pagar(custo):
            return False, "Recursos insuficientes."
        for recurso, quantidade in custo.items():
            self.recursos[recurso] -= quantidade
        hp_antes = construcao.hp_max
        construcao.nivel += 1
        if construcao.hp_max > 0:
            construcao.hp_max = self._hp_max_tipo(construcao.tipo, construcao.nivel)
            construcao.hp = min(
                construcao.hp_max, construcao.hp + (construcao.hp_max - hp_antes)
            )
        self._log(
            f"{NOMES_CONSTRUCOES[construcao.tipo]} #{id_instancia} "
            f"melhorada para nível {construcao.nivel}."
        )
        return True, "ok"

    def remover_instancia(self, id_instancia: int) -> Construcao | None:
        if id_instancia == CASTELO_ID:
            return None
        construcao = self.construcoes.pop(id_instancia, None)
        return construcao

    # ------------------------------------------------------------------
    # Propriedades derivadas
    # ------------------------------------------------------------------
    @property
    def trabalhadores_empregados(self) -> int:
        return sum(c.trabalhadores for c in self.construcoes.values())

    @property
    def populacao_livre(self) -> int:
        return max(0, self.populacao - self.trabalhadores_empregados - self.soldados)

    @property
    def capacidade_populacao(self) -> int:
        return (
            8
            + 6 * self._soma_niveis("casas")
            + 4 * self.quantidade_instancias("posto")
        )

    @property
    def capacidade_alimento(self) -> float:
        return 100.0 + 100.0 * self._soma_niveis("celeiro")

    @property
    def capacidade_troncos(self) -> float:
        return 30.0 + 30.0 * self._soma_niveis("madeireira")

    @property
    def max_soldados(self) -> int:
        return 5 * self._soma_niveis("quartel")

    @property
    def max_arqueiros(self) -> int:
        return 3 * self._soma_niveis("arquearia")

    @property
    def max_magos(self) -> int:
        return 3 * self._soma_niveis("torre_magia")

    @property
    def max_curandeiros(self) -> int:
        return 3 * self._soma_niveis("santuario")

    @property
    def total_tropas(self) -> int:
        return self.soldados + self.arqueiros + self.magos + self.curandeiros

    @property
    def max_total_tropas(self) -> int:
        return (
            self.max_soldados
            + self.max_arqueiros
            + self.max_magos
            + self.max_curandeiros
        )

    @property
    def forca_soldado(self) -> float:
        return 2.0 + 0.25 * self._soma_niveis("ferraria")

    @property
    def bonus_muralha(self) -> float:
        return 0.0

    @property
    def poder_defesa(self) -> float:
        return self.soldados * self.forca_soldado + self.bonus_muralha

    @property
    def hp_castelo_max(self) -> float:
        return 300.0 + 150.0 * (self.nivel_castelo - 1)

    @property
    def nivel_castelo(self) -> int:
        return self.construcoes[CASTELO_ID].nivel

    def custo_melhoria_castelo(self) -> dict[str, float]:
        if self.nivel_castelo >= 5:
            return {}
        fator = 1.6 ** self.nivel_castelo
        return {
            "madeira": float(math.ceil(100 * fator)),
            "pedra": float(math.ceil(60 * fator)),
            "dinheiro": float(math.ceil(50 * fator)),
        }

    @property
    def toque_disponivel(self) -> bool:
        return self.nivel_castelo >= 3

    def pode_melhorar_castelo(self) -> bool:
        if self.nivel_castelo >= 5:
            return False
        return self.pode_pagar(self.custo_melhoria_castelo())

    def melhorar_castelo(self) -> tuple[bool, str]:
        if self.nivel_castelo >= 5:
            return False, "O castelo já é uma fortaleza."
        custo = self.custo_melhoria_castelo()
        if not self.pode_pagar(custo):
            return False, "Recursos insuficientes."
        for recurso, quantidade in custo.items():
            self.recursos[recurso] -= quantidade
        construcao = self.construcoes[CASTELO_ID]
        construcao.nivel += 1
        construcao.hp_max = self.hp_castelo_max
        construcao.hp = construcao.hp_max
        self.hp_castelo = construcao.hp_max
        nomes = {1: "Choupana", 2: "Casa", 3: "Solar", 4: "Forte", 5: "Fortaleza"}
        self._log(
            f"Castelo melhorado para {nomes.get(construcao.nivel, 'Castelo')} "
            f"(nível {construcao.nivel})."
        )
        return True, "ok"

    @property
    def trabalhadores_postos(self) -> int:
        return sum(c.trabalhadores for c in self.instancias("posto"))

    @property
    def consumo_diario(self) -> float:
        no_reino = max(0, self.populacao - self.trabalhadores_postos)
        return no_reino * CONSUMO_POR_PESSOA

    @property
    def dias_de_comida(self) -> float:
        if self.consumo_diario <= 0:
            return float("inf")
        return self.recursos["alimento"] / self.consumo_diario

    def taxa_crescimento(self) -> dict[str, float]:
        espaco = max(0, self.capacidade_populacao - self.populacao)
        dias = self.dias_de_comida
        fator_comida = max(0.0, min(1.0, dias / 8.0))
        fator_riqueza = max(
            0.0,
            min(1.0, self.recursos["dinheiro"] / (self.populacao * 12 + 20)),
        )
        fator_ouro = max(
            0.0,
            min(1.0, self.recursos["ouro"] / (self.populacao * 3 + 10)),
        )
        conforto = 1.0 + 0.20 * self._soma_niveis("casas")
        taxa = (
            0.25
            + 0.25 * fator_comida
            + 0.10 * fator_riqueza
            + 0.05 * fator_ouro
        ) * conforto
        taxa = min(taxa, 3.0)
        if espaco <= 0:
            taxa = 0.0
        return {
            "taxa": taxa,
            "espaco": float(espaco),
            "comida": fator_comida,
            "riqueza": fator_riqueza,
            "ouro": fator_ouro,
        }

    def poder_ataque_previsto(self) -> int:
        return int(8 + self.dia * 1.4)

    # ------------------------------------------------------------------
    # Produção
    # ------------------------------------------------------------------
    def taxas_instancia(self, construcao: Construcao) -> dict[str, float]:
        config = self._config(construcao.tipo)
        if config is None or construcao.nivel <= 0 or construcao.trabalhadores <= 0:
            return {}
        eficiencia = (
            1.0 + 0.10 * (construcao.nivel - 1)
        ) * construcao.bonus_producao
        taxas: dict[str, float] = {}
        if config["tipo"] == "mina":
            taxas["ferro"] = (
                construcao.trabalhadores * config["taxa_ferro"] * eficiencia
            )
            taxas["ouro"] = (
                construcao.trabalhadores * config["taxa_ouro"] * eficiencia
            )
            taxas["pedra"] = (
                construcao.trabalhadores
                * config.get("taxa_pedra", 0.0)
                * eficiencia
            )
        elif config["tipo"] == "producao":
            taxas[config["recurso"]] = (
                construcao.trabalhadores * config["taxa"] * eficiencia
            )
        return taxas

    def producao_posto(self, construcao: Construcao) -> dict[str, float]:
        config = self._config(construcao.tipo)
        if config is None or "producao" not in config:
            return {}
        if construcao.nivel <= 0 or construcao.trabalhadores <= 0:
            return {}
        fator = (
            1.0 + 0.25 * (construcao.nivel - 1)
        ) * construcao.bonus_producao
        return {
            recurso: valor * construcao.trabalhadores * fator
            for recurso, valor in config["producao"].items()
        }

    def defesa_posto(self, construcao: Construcao) -> dict[str, float]:
        config = self._config(construcao.tipo)
        if config is None or "defesa_dano" not in config:
            return {"dano": 0.0, "alcance": 0.0, "intervalo": 1.0}
        if construcao.nivel <= 0:
            return {"dano": 0.0, "alcance": 0.0, "intervalo": 1.0}
        fator = 1.0 + 0.35 * (construcao.nivel - 1)
        return {
            "dano": float(config["defesa_dano"]) * fator,
            "alcance": float(config["defesa_alcance"])
            + 0.4 * (construcao.nivel - 1),
            "intervalo": float(config.get("defesa_intervalo", 1.1)),
        }

    def capacidade_armazem(self, construcao: Construcao) -> float:
        config = self._config(construcao.tipo)
        if config is None or "armazem_base" not in config:
            return 0.0
        return float(config["armazem_base"]) * (1.0 + (construcao.nivel - 1))

    def total_armazem(self, construcao: Construcao) -> float:
        return sum(construcao.armazem.values())

    def taxas_producao(self) -> dict[str, float]:
        """Produção por dia de cada recurso."""
        taxas = {r: 0.0 for r in RECURSOS}
        for construcao in self.construcoes.values():
            for recurso, valor in self.taxas_instancia(construcao).items():
                taxas[recurso] += valor
        return taxas

    def _produzir(self, dt: float) -> None:
        fator = dt / DIA_SEGUNDOS
        for construcao in self.construcoes.values():
            if construcao.tipo == "posto":
                capacidade = self.capacidade_armazem(construcao)
                if self.total_armazem(construcao) >= capacidade:
                    continue
                for recurso, taxa in self.producao_posto(construcao).items():
                    if taxa <= 0:
                        continue
                    progresso = (
                        construcao.progressos.get(recurso, 0.0) + taxa * fator
                    )
                    produzido = int(progresso)
                    construcao.progressos[recurso] = progresso - produzido
                    if produzido <= 0:
                        continue
                    espaco = max(
                        0.0, capacidade - self.total_armazem(construcao)
                    )
                    construcao.armazem[recurso] = (
                        construcao.armazem.get(recurso, 0.0)
                        + min(float(produzido), espaco)
                    )
                continue
            for recurso, taxa in self.taxas_instancia(construcao).items():
                if taxa <= 0:
                    continue
                progresso = construcao.progressos.get(recurso, 0.0) + taxa * fator
                produzido = int(progresso)
                construcao.progressos[recurso] = progresso - produzido
                if produzido > 0:
                    self.recursos[recurso] += produzido
        if self.recursos["alimento"] > self.capacidade_alimento:
            self.recursos["alimento"] = self.capacidade_alimento

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def treinar_soldado_disponivel(self) -> bool:
        return (
            self._soma_niveis("quartel") > 0
            and self.soldados < self.max_soldados
            and self.recursos["dinheiro"] >= CUSTO_SOLDADO["dinheiro"]
            and self.recursos["ouro"] >= CUSTO_SOLDADO["ouro"]
        )

    # Mantido para compatibilidade com chamadas antigas.
    pode_treinar_soldado = treinar_soldado_disponivel

    def cobrar_treinamento(self) -> tuple[bool, str]:
        if self._soma_niveis("quartel") <= 0:
            return False, "Construa um Quartel primeiro."
        if self.soldados >= self.max_soldados:
            return False, "Quartel lotado. Melhore o Quartel."
        if self.recursos["dinheiro"] < CUSTO_SOLDADO["dinheiro"]:
            return False, "Dinheiro insuficiente."
        if self.recursos["ouro"] < CUSTO_SOLDADO["ouro"]:
            return False, "Ouro insuficiente."
        self.recursos["dinheiro"] -= CUSTO_SOLDADO["dinheiro"]
        self.recursos["ouro"] -= CUSTO_SOLDADO["ouro"]
        return True, "ok"

    def pode_treinar_arqueiro(self) -> bool:
        return self.pode_treinar_tropa("arqueiro")

    def cobrar_treinamento_arqueiro(self) -> tuple[bool, str]:
        return self.cobrar_treinamento_tropa("arqueiro")

    def _contagem_base(self, base: str) -> int:
        return {
            "soldado": self.soldados,
            "arqueiro": self.arqueiros,
            "mago": self.magos,
            "curandeiro": self.curandeiros,
        }.get(base, 0)

    def _limite_base(self, base: str) -> int:
        return {
            "soldado": self.max_soldados,
            "arqueiro": self.max_arqueiros,
            "mago": self.max_magos,
            "curandeiro": self.max_curandeiros,
        }.get(base, 0)

    def pode_treinar_tropa(self, classe: str) -> bool:
        dados = CLASSES_TROPA.get(classe)
        if dados is None:
            return False
        base = dados["base"]
        if self._limite_base(base) <= 0:
            return False
        if self._contagem_base(base) >= self._limite_base(base):
            return False
        custo = CUSTO_TROPA[classe]
        for recurso, quantidade in custo.items():
            if recurso in self.recursos:
                if self.recursos[recurso] < quantidade:
                    return False
            elif self.recursos_raros.get(recurso, 0.0) < quantidade:
                return False
        return True

    def cobrar_treinamento_tropa(self, classe: str) -> tuple[bool, str]:
        if not self.pode_treinar_tropa(classe):
            return False, "Recursos insuficientes ou limite atingido."
        for recurso, quantidade in CUSTO_TROPA[classe].items():
            if recurso in self.recursos:
                self.recursos[recurso] -= quantidade
            else:
                self.recursos_raros[recurso] = (
                    self.recursos_raros.get(recurso, 0.0) - quantidade
                )
        return True, "ok"

    def adicionar_recurso_raro(self, recurso: str, quantidade: float) -> None:
        if recurso in self.recursos_raros and quantidade > 0:
            self.recursos_raros[recurso] += quantidade

    def coletar_madeira(self) -> None:
        self.recursos["madeira"] += 2.0

    def vender_recurso(
        self, recurso: str, quantidade: float
    ) -> tuple[bool, str]:
        if self.mercador_dias <= 0:
            return False, "Nenhum mercador disponível."
        if quantidade <= 0:
            return False, "Quantidade inválida."
        preco = self.mercador_precos.get(recurso, 0.0)
        if preco <= 0:
            return False, "Recurso não negociável."
        if self.recursos.get(recurso, 0.0) < quantidade:
            return False, "Estoque insuficiente."
        ganho = round(quantidade * preco, 1)
        self.recursos[recurso] -= quantidade
        self.recursos["dinheiro"] += ganho
        self._log(
            f"Vendeu {quantidade:.0f} {NOMES_RECURSOS.get(recurso, recurso)} "
            f"por {ganho} de dinheiro."
        )
        return True, "ok"

    def pode_reparar_castelo(self) -> bool:
        return (
            self.hp_castelo < self.hp_castelo_max
            and self.recursos["madeira"] >= 25
            and self.recursos["ferro"] >= 10
        )

    def reparar_castelo(self) -> tuple[bool, str]:
        if self.hp_castelo >= self.hp_castelo_max:
            return False, "O castelo já está intacto."
        custo = {"madeira": 25.0, "ferro": 10.0}
        if not self.pode_pagar(custo):
            return False, "Recursos insuficientes para reparar."
        for recurso, quantidade in custo.items():
            self.recursos[recurso] -= quantidade
        self.hp_castelo = min(
            self.hp_castelo + self.hp_castelo_max * 0.3, self.hp_castelo_max
        )
        self._log("Castelo reparado.")
        return True, "ok"

    def custo_reparo_instancia(self, id_instancia: int) -> dict[str, float]:
        construcao = self.construcoes.get(id_instancia)
        if construcao is None:
            return {}
        if construcao.tipo == "barricada":
            return {"madeira": 8.0}
        if construcao.tipo == "muralha":
            return {"pedra": 10.0, "madeira": 5.0}
        return {"madeira": 12.0, "pedra": 6.0}

    def pode_reparar_instancia(self, id_instancia: int) -> bool:
        construcao = self.construcoes.get(id_instancia)
        if construcao is None or construcao.hp_max <= 0:
            return False
        if construcao.hp >= construcao.hp_max:
            return False
        return self.pode_pagar(self.custo_reparo_instancia(id_instancia))

    def reparar_instancia(self, id_instancia: int) -> tuple[bool, str]:
        construcao = self.construcoes.get(id_instancia)
        if construcao is None or construcao.hp_max <= 0:
            return False, "Estrutura inválida."
        if construcao.hp >= construcao.hp_max:
            return False, "Estrutura intacta."
        custo = self.custo_reparo_instancia(id_instancia)
        if not self.pode_pagar(custo):
            return False, "Recursos insuficientes para reparar."
        for recurso, quantidade in custo.items():
            self.recursos[recurso] -= quantidade
        construcao.hp = min(
            construcao.hp_max, construcao.hp + construcao.hp_max * 0.4
        )
        self._log(
            f"{NOMES_CONSTRUCOES[construcao.tipo]} #{id_instancia} reparada."
        )
        return True, "ok"

    # ------------------------------------------------------------------
    # Tempo
    # ------------------------------------------------------------------
    def atualizar(self, dt: float) -> None:
        if self.pausado or self.derrota:
            return
        dt_sim = dt * self.velocidade
        self._produzir(dt_sim)
        self.tempo_dia += dt_sim
        passos = 0
        while self.tempo_dia >= DIA_SEGUNDOS and passos < 120:
            self.tempo_dia -= DIA_SEGUNDOS
            self._passar_dia()
            passos += 1
            if self.derrota:
                break

    def _passar_dia(self) -> None:
        self.dia += 1
        self.recorde_dias = max(self.recorde_dias, self.dia)
        if self.mercador_dias > 0:
            self.mercador_dias -= 1
            if self.mercador_dias == 0:
                self.mercador_precos = {}
                self._log("O mercador viajante partiu.")
        self._consumir_alimento()
        if self.derrota:
            return
        self._crescimento_populacional()
        self._processar_eventos()
        self._verificar_derrota()

    def _consumir_alimento(self) -> None:
        consumo = self.consumo_diario
        if self.recursos["alimento"] >= consumo:
            self.recursos["alimento"] -= consumo
            self.dias_sem_comida = 0
            return
        self.recursos["alimento"] = 0.0
        self.dias_sem_comida += 1
        mortos = max(1, math.ceil(self.populacao * 0.05))
        self.populacao = max(0, self.populacao - mortos)
        self._ajustar_para_populacao()
        self._log(f"FOME! {mortos} pessoa(s) morreram.")
        if self.populacao <= 0:
            self._derrota("A população pereceu de fome.")

    def _crescimento_populacional(self) -> None:
        if self.populacao >= self.capacidade_populacao:
            self.crescimento = 0.0
            return
        dados = self.taxa_crescimento()
        self.crescimento += dados["taxa"]
        if self.crescimento >= 1.0:
            vagas_livres = self.capacidade_populacao - self.populacao
            novos = min(int(self.crescimento), vagas_livres)
            if novos > 0:
                self.populacao += novos
                self.crescimento -= novos
                self._log(f"{novos} novo(s) habitante(s) no reino.")
            else:
                self.crescimento = 0.0

    def _ajustar_para_populacao(self) -> None:
        while self.trabalhadores_empregados + self.soldados > self.populacao:
            if self.trabalhadores_empregados > 0:
                for construcao in self.construcoes.values():
                    if construcao.trabalhadores > 0:
                        construcao.trabalhadores -= 1
                        break
            elif self.soldados > 0:
                self.soldados -= 1
            else:
                break

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _processar_eventos(self) -> None:
        if (
            self.ataques_ativos
            and not self.aviso_ataque
            and self.dia == self.proximo_ataque_dia - 1
        ):
            self.aviso_ataque = True
            self._log(
                f"Batedores avistam inimigos! Ataque previsto para o dia "
                f"{self.proximo_ataque_dia}."
            )
        if random.random() < 0.22:
            self._evento_aleatorio()

    def _evento_aleatorio(self) -> None:
        opcoes = ["mercador", "colheita", "refugiados", "veio", "guilda", "praga"]
        tipo = random.choice(opcoes)
        if tipo == "mercador":
            self.mercador_dias = random.randint(2, 4)
            self.mercador_precos = {
                "madeira": round(random.uniform(0.8, 1.4), 2),
                "pedra": round(random.uniform(0.9, 1.6), 2),
                "troncos": round(random.uniform(0.6, 1.0), 2),
                "ferro": round(random.uniform(2.0, 3.5), 2),
                "ouro": round(random.uniform(4.0, 7.0), 2),
            }
            self._log(
                f"Mercador viajante chegou e fica por {self.mercador_dias} dia(s)."
            )
        elif tipo == "colheita":
            ganho = 15 + self.dia
            self.recursos["alimento"] = min(
                self.capacidade_alimento, self.recursos["alimento"] + ganho
            )
            self._log(f"Colheita farta rendeu {ganho} de alimento.")
        elif tipo == "refugiados":
            vagas = self.capacidade_populacao - self.populacao
            if vagas > 0:
                novos = min(2, vagas)
                self.populacao += novos
                self._log(f"{novos} refugiado(s) juntaram-se ao reino.")
            else:
                self._log("Refugiados chegaram, mas não há moradia disponível.")
        elif tipo == "veio":
            ganho = 10 + self.dia
            self.recursos["ferro"] += ganho
            self._log(f"Um veio de minério rendeu {ganho} de ferro.")
        elif tipo == "guilda":
            ganho = 8 + self.dia
            self.recursos["ouro"] += ganho
            self._log(f"A guilda pagou {ganho} de ouro em tributos.")
        elif tipo == "praga":
            perda = self.recursos["alimento"] * 0.15
            self.recursos["alimento"] -= perda
            self._log(f"Praga na fazenda destruiu {perda:.1f} de alimento.")

    def _verificar_derrota(self) -> None:
        if self.derrota:
            return
        if self.rei_morto:
            self._derrota("O Rei morreu.")

    def _derrota(self, motivo: str) -> None:
        if self.derrota:
            return
        self.derrota = True
        self.pausado = True
        self.recorde_dias = max(self.recorde_dias, self.dia)
        self.melhor_periodo = max(self.melhor_periodo, self.dia)
        self._log(f"DERROTA no dia {self.dia}: {motivo}")

    def _log(self, mensagem: str) -> None:
        self.log.append(f"[Dia {self.dia}] {mensagem}")

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "versao": SAVE_VERSION,
            "recursos": self.recursos,
            "populacao": self.populacao,
            "soldados": self.soldados,
            "arqueiros": self.arqueiros,
            "magos": self.magos,
            "curandeiros": self.curandeiros,
            "recursos_raros": self.recursos_raros,
            "dia": self.dia,
            "tempo_dia": self.tempo_dia,
            "hp_castelo": self.hp_castelo,
            "nivel_castelo": self.nivel_castelo,
            "castelos_perdidos": self.castelos_perdidos,
            "melhor_periodo": self.melhor_periodo,
            "rei_morto": self.rei_morto,
            "proximo_id_construcao": self.proximo_id_construcao,
            "construcoes": [
                {
                    "id": c.id,
                    "tipo": c.tipo,
                    "nivel": c.nivel,
                    "trabalhadores": c.trabalhadores,
                    "bonus_producao": c.bonus_producao,
                    "hp": c.hp,
                    "hp_max": c.hp_max,
                    "progressos": c.progressos,
                    "armazem": c.armazem,
                }
                for c in self.construcoes.values()
                if c.tipo != "castelo"
            ],
            "crescimento": self.crescimento,
            "dias_sem_comida": self.dias_sem_comida,
            "recorde_dias": self.recorde_dias,
            "proximo_ataque_dia": self.proximo_ataque_dia,
            "aviso_ataque": self.aviso_ataque,
            "ataques_ativos": self.ataques_ativos,
            "toque_de_recolher": self.toque_de_recolher,
            "mercador_dias": self.mercador_dias,
            "mercador_precos": self.mercador_precos,
            "pausado": self.pausado,
            "velocidade": self.velocidade,
            "log": list(self.log)[-40:],
        }

    def salvar(self, caminho: str) -> None:
        temporario = caminho + ".tmp"
        with open(temporario, "w", encoding="utf-8") as arquivo:
            json.dump(self.to_dict(), arquivo, ensure_ascii=False, indent=2)
        os.replace(temporario, caminho)

    @classmethod
    def carregar(cls, caminho: str) -> "Reino":
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return cls.from_dict(dados)

    @classmethod
    def from_dict(cls, dados: dict) -> "Reino":
        reino = cls()
        reino.construcoes = {
            CASTELO_ID: Construcao(id=CASTELO_ID, tipo="castelo", nivel=1)
        }
        reino.proximo_id_construcao = 1

        for recurso in RECURSOS:
            if recurso in dados.get("recursos", {}):
                reino.recursos[recurso] = float(dados["recursos"][recurso])
        reino.populacao = int(dados.get("populacao", reino.populacao))
        reino.soldados = int(dados.get("soldados", reino.soldados))
        reino.arqueiros = int(dados.get("arqueiros", reino.arqueiros))
        reino.magos = int(dados.get("magos", 0))
        reino.curandeiros = int(dados.get("curandeiros", 0))
        raros = dados.get("recursos_raros", {})
        reino.recursos_raros = {
            chave: float(raros.get(chave, 0.0)) for chave in RECURSOS_RAROS
        }
        reino.dia = int(dados.get("dia", reino.dia))
        reino.tempo_dia = float(dados.get("tempo_dia", 0.0))
        reino.construcoes[CASTELO_ID].nivel = int(
            dados.get("nivel_castelo", 1)
        )
        reino.hp_castelo = min(
            float(dados.get("hp_castelo", reino.hp_castelo)),
            reino.hp_castelo_max,
        )
        reino.construcoes[CASTELO_ID].hp = reino.hp_castelo
        reino.construcoes[CASTELO_ID].hp_max = reino.hp_castelo_max
        reino.castelos_perdidos = int(dados.get("castelos_perdidos", 0))
        reino.melhor_periodo = int(dados.get("melhor_periodo", reino.dia))
        reino.rei_morto = bool(dados.get("rei_morto", False))
        reino.crescimento = float(dados.get("crescimento", 0.0))
        reino.dias_sem_comida = int(dados.get("dias_sem_comida", 0))
        reino.recorde_dias = int(dados.get("recorde_dias", reino.dia))
        reino.proximo_ataque_dia = int(
            dados.get("proximo_ataque_dia", reino.proximo_ataque_dia)
        )
        reino.aviso_ataque = bool(dados.get("aviso_ataque", False))
        reino.ataques_ativos = bool(dados.get("ataques_ativos", True))
        reino.toque_de_recolher = bool(
            dados.get("toque_de_recolher", False)
        )
        reino.mercador_dias = int(dados.get("mercador_dias", 0))
        precos = dados.get("mercador_precos", {})
        reino.mercador_precos = (
            {str(k): float(v) for k, v in precos.items()}
            if isinstance(precos, dict)
            else {}
        )
        reino.pausado = bool(dados.get("pausado", False))
        reino.velocidade = int(dados.get("velocidade", 1))

        construcoes = dados.get("construcoes")
        alias = {"lenhador": "madeireira"}
        if isinstance(construcoes, dict):
            for nome, info in construcoes.items():
                tipo = alias.get(nome, nome)
                if tipo not in CONSTRUCOES:
                    continue
                nivel = int(info.get("nivel", 0))
                if nivel <= 0:
                    continue
                identificador = reino._criar_instancia(tipo, nivel)
                reino.construcoes[identificador].trabalhadores = int(
                    info.get("trabalhadores", 0)
                )
        elif isinstance(construcoes, list):
            maior_id = 0
            for info in construcoes:
                tipo = alias.get(str(info.get("tipo", "")), str(info.get("tipo", "")))
                if tipo not in CONSTRUCOES:
                    continue
                identificador = int(info.get("id", reino.proximo_id_construcao))
                maior_id = max(maior_id, identificador)
                nivel = int(info.get("nivel", 1))
                hp_max = reino._hp_max_tipo(tipo, nivel)
                hp = float(info.get("hp", hp_max))
                reino.construcoes[identificador] = Construcao(
                    id=identificador,
                    tipo=tipo,
                    nivel=nivel,
                    trabalhadores=int(info.get("trabalhadores", 0)),
                    bonus_producao=float(info.get("bonus_producao", 1.0)),
                    hp=min(hp, hp_max) if hp_max > 0 else 0.0,
                    hp_max=hp_max,
                    progressos={
                        str(chave): float(valor)
                        for chave, valor in info.get("progressos", {}).items()
                    }
                    if isinstance(info.get("progressos"), dict)
                    else {},
                    armazem={
                        str(chave): float(valor)
                        for chave, valor in info.get("armazem", {}).items()
                    }
                    if isinstance(info.get("armazem"), dict)
                    else {},
                )
            reino.proximo_id_construcao = max(
                maior_id + 1,
                int(dados.get("proximo_id_construcao", 1)),
                reino.proximo_id_construcao,
            )
        else:
            reino._criar_instancia("madeireira")
            reino._criar_instancia("fazenda")
            reino._criar_instancia("casas")

        if dados.get("log"):
            reino.log = deque(dados["log"][-40:], maxlen=160)

        reino._ajustar_para_populacao()
        reino._verificar_derrota()
        return reino
