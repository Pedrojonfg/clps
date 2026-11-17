# Speaker notes — guion hablado (≈3:30, ~500 palabras)

Ritmo de referencia: ~140 palabras/min. Los números en **negrita** son los que conviene decir tal cual.

---

### 1 · Gancho — 0:00–0:20

> Imaginad que sois una empresa que va a posar un lander en el polo sur de la Luna. Allí el Sol nunca sube: va rozando el horizonte, y cerca del polo su altura cambia unos **0,004 grados por hora**. Eso significa que si os equivocáis una décima de grado al medir una cresta, os habéis equivocado **un día entero** de luz. Y sin luz no hay batería; sin la Tierra a la vista no hay comunicación.

### 2 · El hueco — 0:20–0:55

> ¿Qué hay hoy? PGDA, de la NASA, publica mapas de iluminación excelentes, pero son **medias de 18,6 años**: no te dicen nada de *tu* semana. Horizons te da dónde está el Sol, pero sobre una Luna lisa, sin terreno. Y STK o SPICE lo hacen todo, pero son herramientas de especialista. El propio enunciado del reto lo dice: comparar sitios y fechas exige saltar entre interfaces y datos en bruto. Y cuando el lanzamiento se retrasa, hay que replanificar rápido.

### 3 · Qué hace — 0:55–1:25

> Así que hice un evaluador sitio por tiempo. Le das un punto, una ventana y lo que tu misión aguanta: horas máximas de noche, horas sin ver la Tierra… o eliges una plantilla, como Blue Ghost, VIPER o Artemis III. Te devuelve, hora a hora, qué ves, si la misión es viable, una nota y, si no lo es, el sitio u hora viable más cercano. Detrás hay dos fuentes reales: los kernels SPICE para el Sol y la Tierra, y los modelos de elevación LOLA para el terreno.

### 4 · Decisión 1, el horizonte — 1:25–2:05

> La decisión técnica más importante fue cómo calcular el horizonte. Primero lo probé con un solo mapa a 240 metros y la noche más larga salía mal por **1.289 horas**. Así que medí. El terreno que tapa el horizonte nunca estaba a más de **196 km**, así que el rayo llega a 250. Y los primeros 250 metros dominan el error, así que la resolución va de 20 metros cerca a 240 lejos. Con una primera versión, un punto de 28 fallaba por 7 horas; lo corregí hasta que ninguno pasaba de **1 hora**. El umbral, 5 horas, no me lo inventé: es lo que aguantó Blue Ghost con batería tras la puesta de Sol. Y como el horizonte no depende de la fecha, precalculé todo el casquete polar en una noche: **290.000 máscaras en 4 horas y media**.

### 5 · Decisión 2, la nota — 2:05–2:45

> La segunda decisión: cómo puntuar. Muchas herramientas normalizan contra el mejor sitio. Yo me negué, porque eso esconde que *ningún* sitio sirve. Así que la nota es **fail-closed**: si violas un mínimo, cero. Si los cumples, la nota es una probabilidad de supervivencia: cada margen dividido por la incertidumbre de la medida. Y esa incertidumbre, sigma igual a 5 horas, es *el mismo* error que medí en el horizonte: validación y puntuación comparten un único modelo de error. El truco: aunque todo dé cero, calculo una nota «dentro de lo imposible» para que el buscador sepa hacia dónde moverse.

### 6 · Honestidad + proceso — 2:45–3:20

> Lo último y lo que más me importa: todo está documentado en **78 decisiones** y respaldado por **110 tests**; hay más código de tests que de motor. La regla es que solo afirmo lo que un test o una decisión respalda. Por eso la interfaz dice qué está calculado y qué está simulado, el fondo 3D lleva la etiqueta «no es nuestro modelo», y el buscador global dice «mejor encontrado», no «óptimo». Vamos a verlo.

---

## Demo — ruta de 90 s (después del pitch)

> Antes: **decide si enseñas datos reales en local** (`uvicorn api.app:app`) o la demo de Pages (máscaras simuladas) y dilo en voz alta. Haz un ensayo: los pasos 3 y 4 están predichos a partir de las plantillas, no observados.

1. **(10 s)** Planner en Site01. Señala la etiqueta de procedencia: «aquí digo qué es real».
2. **(20 s)** Plantilla *VIPER conservative*, ventana de 7 días → gráfico polar (Sol rozando el borde, traza de la Tierra), franja horaria, nota.
3. **(15 s)** Cambia a *Direct-to-Earth priority* → previsiblemente 0,000 (infeasible). «Mismo sitio, misma fecha, otra misión, otra respuesta.»
4. **(15 s)** Activa la búsqueda local → tabla de desplazamientos de horas que lo vuelven viable. «El lanzamiento se retrasó: ¿cuándo puedo posarme?»
5. **(15 s)** Deep search en el rectángulo por defecto → ranking + CSV.
6. **(15 s)** Vista en primera persona: mueve la hora, el Sol roza la cresta; señala «Backdrop: Cesium Moon — not our model». Sin token, panorama 2D.

**Plan B si la demo falla:** captura del gráfico polar + franja horaria preparada en una diapositiva oculta.

## Lo que NO hay que decir

- «Validado contra PGDA 69» → el arnés existe; la ejecución nocturna no se ha hecho.
- «Óptimo global» → el modo `optimized` es *best seen*; el megatest contra cobertura total no se ha ejecutado.
- «Tasa de levantamiento de polvo» → es resistencia del suelo (Metzger), no lofting.
- «La app de escritorio» como hecha → es un esqueleto Tauri; es la dirección del producto.
- «Funciona para noches cortas tipo VIPER» → los 28 puntos de error tenían noches ≥ 392 h; el régimen de ~50 h no está medido.
