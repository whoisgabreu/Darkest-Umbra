# Lista de Assets Visuais

## Especificações gerais
- Formato: PNG-24 com transparência.
- Entrega: spritesheets horizontais (todos os frames do mesmo tamanho, sem padding).
- Estilo: pixel art em 64 px (tiles) escalada inteira, ou HD em 128–256 px.
- Nomenclatura: `categoria_objeto_acao.png` (ex.: `unidade_soldado_andar.png`).
- Tamanhos sugeridos: tiles 64×64; ícones 32×32 ou 48×48; cidadãos 32×32; soldados/inimigos 48×48; caravana 64×48; estruturas seguem a tabela de pegadas (64 px por tile); fundo 2048×1536.
- Ancoragem de unidades: centro-base (pés no chão).
- Pegada de estrutura = área de colisão/ocupação no mapa. Sprites podem ter overhang visual (telhado, bandeira, torre), desde que a base fique alinhada à pegada.
- Enquanto os arquivos não existirem, o jogo usa formas e cores como placeholder.

## Fundo e cenário
| Asset | Frames |
|---|---|
| Fundo do reino (dia) | 1 |
| Camada céu / montanhas / árvores (parallax) | 1 cada |
| Tile de grama | 1 |
| Overlay noite | 1 |

## Mapa top-down (novo)
| Asset | Frames |
|---|---|
| Tile de grama (3 variações) | 3 |
| Tile de terra / caminho (2 variações) | 2 |
| Tile de floresta (3 variações) | 3 |
| Tile de água (loop) | 4 |
| Tile de rocha (2 variações) | 2 |
| Borda/transição de terreno (autotile) | 16 |
| Destaque de seleção de prédio (anel) | 1 |
| Fantasma de posicionamento válido / inválido | 2 |
| Círculo do raio de construção | 1 |
| Trecho de muralha de pedra por nível | 3 |
| Barricada de madeira por nível | 3 |
| Posto avançado (torre/bandeira) | 2 |
| Barra de HP de estrutura | 1 |
| Acampamento inimigo (borda do mapa) | 1 |
| Árvore adulta (3 variações) | 3 |
| Toco / árvore cortada | 1 |
| Pedra adulta (2 variações) | 2 |
| Pedra esgotada / cascalho | 1 |
| Barra de vida de recurso | 1 |
| Tronco carregado por cidadão | 1 |
| Anel de seleção de unidade | 1 |
| Caixa de seleção (arraste) | 1 |
| Marcador de ordem (ping) | 1 |
| Texto flutuante de recurso (+troncos, +madeira) | 1 |
| Grupo inimigo (bandido/bárbaro/cavaleiro) | 1 cada |
| Moldura de minimapa | 1 |
| Marcador de ataque no minimapa | 1 |

## Estruturas — pegadas e dimensões
Cada tile tem 64×64 px. A pegada define colisão, ocupação, caminho e território; o canvas pode ser maior apenas para overhang visual.

| Estrutura | Pegada (tiles) | Tamanho no mundo (px) | Canvas sugerido (px) | Observações |
|---|---:|---:|---:|---|
| Castelo | 4×4 | 256×256 | 256×288 | Mastro/bandeira acima da base |
| Casas | 1×1 | 64×64 | 64×64 | Casa compacta |
| Madeireira | 2×1 | 128×64 | 128×64 | Oficina horizontal |
| Mina | 2×1 | 128×64 | 128×64 | Entrada + carrinho |
| Fazenda | 3×2 | 192×128 | 192×128 | Campo de cultivo |
| Mercado | 2×1 | 128×64 | 128×64 | Bancas |
| Ferraria | 1×1 | 64×64 | 64×64 | Forja compacta |
| Quartel | 2×2 | 128×128 | 128×128 | Pátio de treino |
| Celeiro | 2×1 | 128×64 | 128×64 | Armazenamento |
| Muralha | 1×1 | 64×64 | 64×64 | Segmento modular |
| Barricada | 1×1 | 64×64 | 64×64 | Segmento modular |
| Posto Avançado | 2×1 | 128×64 | 128×96 | Torre/bandeira acima da base |
| Arquearia | 2×1 | 128×64 | 128×64 | Estandes de tiro |
| Torre de Magia | 1×1 | 64×64 | 64×96 | Torre vertical |
| Santuário | 2×1 | 128×64 | 128×64 | Altar e área de cura |

## Castelo
| Asset | Frames |
|---|---|
| Castelo por nível (1–5) | 5 |
| Estados de dano (leve, médio, crítico, ruínas) | 4 |
| Bandeira tremulando (loop) | 4 |
| Muralha por nível | 3 |

## Prédios
Madeireira, Mina, Fazenda, Mercado, Ferraria, Quartel, Casas, Celeiro, Muralha, Barricada, Posto Avançado, Arquearia, Torre de Magia, Santuário.

| Asset | Frames |
|---|---|
| Ícone de UI (por prédio) | 1 × 14 = 14 |
| Sprite no mundo (3 variações visuais; reutilizar acima do nível 3) | 3 × 14 = 42 |
| Animação de construção (compartilhada) | 4 |
| Estado danificado (compartilhado) | 1 |

## Personagens e entidades móveis — dimensões
| Personagem | Placeholder atual | Sprite recomendado | Seleção / observações |
|---|---:|---:|---|
| Cidadão comum | 20×20 | 32×32 | Anel de seleção 30×30; sombra 22×10 |
| Rei | 20×20 + coroa | 32×32 | Anel 26×26; mesma base do cidadão |
| Soldado / Defensor / Destruidor | 24×24 | 48×48 | Anel 34×34; barra de HP 32×4 |
| Arqueiro / Patrulheiro / Guardião | 24×24 | 48×48 | Anel 34×34; barra de HP 32×4 |
| Mago / Mago Elétrico / Mago de Gelo | 24×24 | 48×48 | Anel 34×34; barra de HP 32×4 |
| Curandeiro / Bardo / Protetor | 24×24 | 48×48 | Anel 34×34; barra de HP 32×4 |
| Inimigo de horda | 24×24 | 48×48 | Barra de HP 32×4 |
| Inimigo errante | 22×22 | 48×48 | Barra de HP 30×4 |
| Caravana | 28×16 (corpo) | 64×48 | Sombra 34×12; rodas 10×10; seleção 52×52 |
| Membro de caravana | 6×6 (ponto) | Incluído no sprite da caravana | Até 5 membros visíveis |

## Cidadãos (por profissão)
Tamanho base do cidadão: corpo 20×20 px, sombra 22×10 px, anel de seleção 30×30 px; sprite recomendado 32×32 px.

| Asset | Frames |
|---|---|
| Ocioso — idle / andar | 4 / 6 |
| Madeireiro — idle / andar / cortar / carregar | 4 / 6 / 6 / 4 |
| Serrador — idle / andar / trabalhar | 4 / 6 / 4 |
| Fazendeiro — idle / andar / trabalhar | 4 / 6 / 4 |
| Minerador — idle / andar / trabalhar | 4 / 6 / 4 |
| Comerciante — idle / andar / trabalhar | 4 / 6 / 4 |
| Pedreiro — idle / andar / minerar / carregar | 4 / 6 / 6 / 4 |
| Pescador — idle / andar / pescar | 4 / 6 / 6 |
| Colonizador — idle / andar / trabalhar | 4 / 6 / 4 |
| Toco de árvore derrubada (alternativo ao sprite) | 1 |

## Unidades de combate
Tamanho base: placeholder 24×24 px; sprite recomendado 48×48 px; anel de seleção 34×34 px; barra de HP 32×4 px.

| Classe | Base visual | Frames sugeridos |
|---|---|---|
| Soldado | soldado | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Defensor | soldado | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Destruidor | soldado | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Arqueiro | arqueiro | idle / andar / atirar / morrer — 4 / 6 / 6 / 6 |
| Patrulheiro | arqueiro | idle / andar / atirar / morrer — 4 / 6 / 6 / 6 |
| Guardião | arqueiro | idle / andar / atirar / morrer — 4 / 6 / 6 / 6 |
| Mago | mago | idle / andar / conjurar / morrer — 4 / 6 / 6 / 6 |
| Mago Elétrico | mago | idle / andar / conjurar / morrer — 4 / 6 / 6 / 6 |
| Mago de Gelo | mago | idle / andar / conjurar / morrer — 4 / 6 / 6 / 6 |
| Curandeiro | curandeiro | idle / andar / curar / morrer — 4 / 6 / 6 / 6 |
| Bardo | curandeiro | idle / andar / curar / morrer — 4 / 6 / 6 / 6 |
| Protetor | curandeiro | idle / andar / curar / morrer — 4 / 6 / 6 / 6 |
| Inimigo de horda | horda | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Inimigo errante | errante | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Barra de HP de unidade | — | 1 |
| Inimigo bandido (futuro) | bandido | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Inimigo bárbaro (futuro) | bárbaro | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Inimigo cavaleiro (futuro) | cavaleiro | idle / andar / atacar / morrer — 4 / 6 / 6 / 6 |
| Chefe (futuro) | chefe | idle / andar / atacar / morrer — 6 / 6 / 8 / 8 |
| Catapulta (futuro, cerco) | cerco | idle / atacar — 2 / 6 |

## Efeitos
| Asset | Frames |
|---|---|
| Corte de espada | 6 |
| Flecha | 4 |
| Pedra de catapulta | 4 |
| Fumaça | 6 |
| Fogo | 6 |
| Poeira de construção | 6 |
| Faísca de upgrade | 6 |
| Moedas/partículas | 4 |
| Explosão | 8 |

## Interface (UI)
| Asset | Frames |
|---|---|
| Ícones de recurso (madeira, troncos, pedra, ferro, ouro, dinheiro, alimento, população, soldados) | 9 × 1 |
| Botão — normal/hover/pressionado/desabilitado | 4 por estilo (primário e secundário = 8) |
| Painel (9-slice) | 1 |
| Barra de progresso — fundo / preenchimento | 2 |
| Barra de HP do castelo — fundo / preenchimento | 2 |
| Ícones de alerta (ataque, fome, aviso) | 3 (pulso opcional: +4) |
| Ícones de controle (pause, play, 1x, 2x, 4x) | 5 |
| Logo/título do jogo | 1 |
| Cursor customizado | 1 |

## Banners de evento
| Asset | Frames |
|---|---|
| Ataque inimigo | 1 (loop 4 opcional) |
| Fome | 1 |
| Mercador | 1 |
| Praga na fazenda | 1 |

## Estrutura de pastas sugerida
```
assets/
  fundo/
  castelo/
  predios/
  unidades/
    cidadaos/  soldado/  inimigos/  cerco/  arvores/
  efeitos/
  ui/
    icones/  botoes/  paineis/  barras/
  eventos/
  fontes/
```

Total aproximado: 240–270 arquivos (contando spritesheets, ícones e variações; classes especiais podem reutilizar bases).
