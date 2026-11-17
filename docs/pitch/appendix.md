# Appendix — preguntas difíciles y respuestas de respaldo

## Preguntas probables (con respuesta corta)

**«¿Lo habéis validado contra algo real?»**
Sí en tres capas: Sol/Tierra contra JPL Horizons (0,0013° en elevación, D-f369; fixtures en `tests/fixtures`); el horizonte contra un DEM de referencia de 5 m en 28 puntos (≤ 1 h de error en la noche más larga); y un golden de agregados semanales en Site01 (D-beb5). Pendiente: comparación con PGDA 69 y re-check de noches cortas; los scripts existen y la ejecución está planificada (`docs/validation.md`).

**«¿Por qué no usáis directamente PGDA 69?»**
Porque es una media de 18,6 años: no dice qué pasa *en tu fecha*, y cuenta la Tierra como visible si asoma cualquier trozo del disco (optimista para un enlace). Lo usamos como evidencia externa en un informe, no en la nota (D-fe17).

**«¿Por qué no usar la API de Horizons en cada petición?»**
Fair use y coste por cálculo; además quería entender el cálculo. Kernels SPICE locales, con Horizons como oráculo de tests (D-4ffe).

**«¿El buscador encuentra el óptimo?»**
Hay dos modos: `total_coverage` recorre toda la rejilla y puede decir «óptimo de la rejilla» (~1 min para 10×10 km × 7 días); `optimized` hace hill-climb multi-arranque con presupuesto de 5 min y solo puede decir «mejor visto» (D-54f0, D-8a25). ML/RL descartado para v1.

**«¿Y el polvo?»**
Es un proxy de resistencia del suelo (Metzger 2024, β = cos θ en el término de grano, D-06cb, D-050d) con constantes medias de Apollo. Etiquetado explícitamente como *no* tasa de levantamiento.

**«¿Y la temperatura?»**
Climatología Diviner por estación y hora local, no un pronóstico (D-41a2). Huecos rellenados con IDW por cuadrantes (D-affb).

**«¿Dónde corre el cálculo en producción?»**
El servidor solo sirve máscaras; la evaluación corre en la máquina del usuario (D-8c03). Las agencias tienen buen hardware y el coste para mí es casi cero. Producto previsto: escritorio con Tauri (D-bdaf, D-cc6f); la web de Pages es una demo, no el producto (D-c973).

**«¿Por qué precalcular?»**
La máscara depende del sitio, no de la fecha. Ocupa 2,9 KB; lo caro es calcularla (~150 ms). 290k máscaras en 4,5 h; 100 m (~29 M máscaras) queda para un servidor de pago (D-5994 → D-8c03, D-573b).

## Cambios de rumbo que puedes contar (si preguntan por el proceso)

| De → a | Por qué | Registro |
|---|---|---|
| Entrega de hackathon 48 h → portfolio en solitario | Ir solo; las búsquedas pasaron de «stretch» a núcleo | D-5cf6 → D-9f04, D-7e2a, D-d7d9 |
| Público educativo → técnico | Un lector técnico juzga la claridad del modelo y la honestidad | D-ea51 → D-3c91 |
| min(slack) → ∏Φ(slack/σ) × bonus con tope | Que un buen bonus no tape un riesgo malo | D-de42 → D-7520 → D-6ce5 → D-48ee |
| 240 m a 5–25 km → 80 m | Fallaba por 7 h en 1 de 28 puntos | D-f369 |
| App en servidor propio → máscaras remotas + cálculo en cliente | Coste; el CX43 estaba agotado | D-5994 → D-8c03 |
| «Máscaras precalculadas ⇒ búsqueda barata» → dos modos + presupuesto | La efeméride cuesta ~0,4–0,5 s por sitio | D-54f0, D-8a25 |
| Placeholder de polvo → Metzger publicado | Física publicada en vez de un índice inventado | D-050d → D-06cb |

## Cosas que conviene saber antes de que te las saquen (no en el pitch)

- **El ajuste de β no pasó su propio gate.** La banda 2–40 % de inversiones se fijó antes (D-7c70); con β = 0,15 salió 0,94 % / 0,00 % → REOPEN. β = 0,25 se eligió después con varianza y solapamiento top-k (D-48ee, T-d567:63). Respuesta honesta: «el gate dijo que el bonus apenas cambiaba el orden; cambié de métrica y lo dejé documentado».
- **El tope de 0,40 nunca actúa.** Con β = 0,25 y B ≤ 1 la subida máxima es 25 % (`lunar_eval/score.py:12-13,105-109`). Es una barandilla por si β cambia, no un efecto real.
- **PSR no fuerza el cero.** `psr_precheck` avisa, pero `score()` no mira `in_psr` (D-bf69 lo plantea como precheck).
- **Deep search ignora los hazards** (`api/app.py` ~327) y va marcada `provisional`.
- **La búsqueda local solo desplaza el tiempo** en producción (`neighbour_sites = []`, `planner_payload.py:136`).
- **Hora solar local aproximada** (`hazards/lst.py:9`, UTC + lon/15).
- **Tests flojos en:** hazards (8 tests para ~490 líneas), `api/app.py`, la UI web, `precompute.py`/`cap_index.py` sin tests directos.
- **σ e independencia** de los modos de fallo son supuestos v1; altura del observador 2 m y 720 azimuts fueron ajustes de prueba (D-f369, Checks).

## Fuera de alcance a propósito

Optimización de trayectorias (D-b8d3), multi-cuerpo (solo las costuras), ML para la búsqueda, máscaras a 100 m, API de máscaras, app de escritorio terminada.
