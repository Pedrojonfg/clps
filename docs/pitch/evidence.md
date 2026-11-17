# Evidence ledger — de dónde sale cada afirmación

Rutas relativas a la raíz del repo. `D-xxxx` = `docs/records/decisions/D-2026111x-pj-xxxx-*.md`. Informes completos de los subagentes en `docs/pitch/research/`.

| # | Afirmación | Fuente | Tag |
|---|---|---|---|
| L1 | Sol a ±2,9° del horizonte liso; su elevación cambia ~0,004°/h cerca del polo → 0,1° ≈ 25 h | D-f369 (Evidence, punto «Sun») | FACT (25 h = cálculo derivado) |
| L2 | Pequeños cambios de sitio o fecha cambian mucho la energía y las ventanas de comunicación | `docs/sources/challenge-statements/clps-lunar-mission-browser.md:17` | FACT |
| L3 | PGDA 69 = medias de ~18,6 años; «las medias esconden la fecha del planificador» | `docs/research/briefs/research-brief-data-viz-sources.md:58` | FACT |
| L4 | Horizons ignora el terreno | D-41fa, D-f369 (Context) | FACT |
| L5 | Herramientas difíciles para no especialistas; varias interfaces y datos en bruto | challenge statement :21 | FACT |
| L6 | Pipeline SPICE + LOLA → máscara → serie → nota → búsqueda | `lunar_eval/ephemeris/spice.py:52`, `horizon/mask.py:20`, `visibility.py:57`, `score.py:116`, `search/deep.py:108` | FACT |
| L7 | 10 plantillas de misión (Blue Ghost, VIPER, Artemis III…) | D-8588, `lunar_eval/planner_templates.py` | FACT |
| L8 | 240 m en todo el rayo → hasta 37 pp de iluminación y 1.289 h de error en la noche más larga | D-f369 (Options, A) | FACT |
| L9 | Horizonte nunca a más de 196 km; corte a 150 km pierde 0,49° | D-f369 (Evidence, Reach) | FACT |
| L10 | Esquema elegido: noche más larga ≤ 1 h de error en 28 puntos; la primera versión fallaba por 7 h en uno → 80 m | D-f369 (Evidence + Checks) | FACT |
| L11 | 290.289 máscaras, 16.174 s (4,49 h), 1 km, 839 MB | `data/masks/cap_1km/summary.json`, `docs/demo-data-and-masks.md` | FACT |
| L12 | Tolerancia 5 h = Blue Ghost M1 ~5 h con batería tras la puesta | D-f369 (Mission data, Rationale) | FACT |
| L13 | Sin normalizar contra el mejor sitio («sería hacer trampa») | D-de42:40,71 | FACT |
| L14 | Capa 0 fail-closed; capa 1 R = ∏Φ(slack/σ); σ = 5 h noche/luz, 1 h sin Tierra; β = 0,25 | `lunar_eval/score.py:9-13,75-159`, D-7520, D-48ee | FACT |
| L15 | Companion score dentro de lo infactible para guiar la búsqueda | D-5577:35, `search/deep.py` | FACT |
| L16 | 78 decisiones (115 records en total) | `ls docs/records/decisions \| wc -l` | FACT |
| L17 | 110 tests recogidos, 109 pasan, 1 skip intencionado, ~10 s; tests 2.176 líneas vs motor ~1.970 | ejecución de pytest 2026-11-15, `research/tests-git.md`, `research/code.md` | FACT |
| L18 | 15 scopes en ~22 h (14-11 mediodía → 15-11 13:19) | `git log`, `research/tests-git.md` | FACT (incluye trabajo sin commitear S10/S11) |
| L19 | Claims evidence-gated; prohibido: mocks como calculados, Cesium como modelo propio, polvo como lofting, PGDA 69 validado, óptimo global | D-de70:50, D-358b:47-52, D-671e, D-54f0:64 | FACT |
| L20 | Kernels vs Horizons: 0,0013° en elevación | D-f369 (Evidence, Sun) | FACT |

## Confianza por diapositiva

| Diapo | Confianza | Punto débil |
|---|---|---|
| 1 | FACT | «un día entero» es un cálculo derivado (0,1° / 0,004°/h); dilo como orden de magnitud |
| 2 | FACT | — |
| 3 | FACT | — |
| 4 | FACT | Los 28 puntos solo cubren noches largas (≥ 392 h) |
| 5 | FACT | σ y la independencia entre modos de fallo son supuestos v1, no derivados |
| 6 | FACT | 22 h cuenta trabajo aún sin commitear |

## Preguntas para ti (MISSING)

- ¿Vas a enseñar la demo en local con datos reales o la de Pages (mocks)? Cambia la frase de la diapo 6.
- ¿Tienes una imagen/render del polo sur para la diapo 1? El repo no tiene una lista para usar (la vista Cesium sirve, con la etiqueta).
- ¿Quieres mencionar que el proyecto nació del reto de Space Apps pero no es una entrega oficial (D-6663)? Ante otros participantes, conviene decirlo en una frase.
