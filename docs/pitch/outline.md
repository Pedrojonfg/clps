# Pitch — outline (lo que sale en pantalla)

**Contexto:** presentación en directo ante otros participantes del hackathon · 3:20–3:40 · luego demo en directo.
**Tipo:** pitch técnico con tiempo fijo → 6 diapositivas, ≤ 20 palabras por diapositiva.
**Arco:** gancho → hueco → qué hace → 2 decisiones técnicas con números → honestidad + proceso → demo.

## Vertebras (lo que el público tiene que recordar)

1. En el polo sur lunar, **unas horas o unos cientos de metros** deciden si un lander tiene energía y habla con la Tierra.
2. Las herramientas públicas dan **medias de 18,6 años** o son para expertos; nadie puntúa *este sitio, esta semana, esta misión*.
3. El núcleo es **el horizonte real del terreno**: el error se mide en *horas de misión*, no en grados.
4. **Fail-closed:** si la misión no sobrevive, la nota es 0, y aun así el buscador sabe hacia dónde moverse.
5. **Cada afirmación está respaldada por un test o un ADR**; lo simulado se etiqueta como simulado.

---

## 1 · Gancho (≈20 s)

**Titular:** Unas horas de retraso pueden dejar un lander congelado y mudo.
**En pantalla:** foto o render del polo sur con el Sol rasante + «0,004°/h».
**Visual:** el Sol pegado al horizonte, una cresta de cráter tapándolo.
**Pregunta que responde:** ¿por qué me debería importar?
**Evidencia:** L1, L2 · confianza: FACT

## 2 · El hueco (≈35 s)

**Titular:** Las herramientas actuales dan medias de 18 años, no tu semana.
**En pantalla:** tres columnas: *PGDA 69 → media 18,6 años* · *Horizons → sin terreno* · *STK/SPICE → para expertos*.
**Visual:** tabla de tres casillas con un ✗ en «este sitio × esta fecha × esta misión».
**Pregunta:** ¿esto no existe ya?
**Evidencia:** L3, L4, L5 · confianza: FACT

## 3 · Qué hace (≈30 s)

**Titular:** Sitio + ventana + necesidades de la misión → sí/no, nota y alternativa.
**En pantalla:** diagrama de pipeline: `SPICE (Sol/Tierra) + LOLA (terreno) → máscara de horizonte → serie horaria → nota → búsqueda`.
**Visual:** flecha de 5 cajas; debajo, «10 plantillas: Blue Ghost, VIPER, Artemis III…».
**Pregunta:** ¿qué es exactamente?
**Evidencia:** L6, L7 · confianza: FACT

## 4 · Decisión 1 — el horizonte (≈40 s)

**Titular:** Un horizonte mal medido falla por 1.289 horas de noche.
**En pantalla:** escalera de resolución: 20 m → 40 m → 80 m → 240 m, hasta 250 km. «290.289 máscaras · 4,5 h · una noche».
**Visual:** rayo saliendo del lander con bandas de color por distancia.
**Pregunta:** ¿dónde está la dificultad técnica?
**Evidencia:** L8, L9, L10, L11 · confianza: FACT

## 5 · Decisión 2 — la nota fail-closed (≈40 s)

**Titular:** Si la misión no sobrevive, la nota es cero, sin excepciones.
**En pantalla:** `Capa 0: mínimos duros → 0` · `Capa 1: R = ∏ Φ(margen / σ)` · `σ = 5 h ← Blue Ghost`.
**Visual:** dos escalones; un «0,000 (infeasible)» con una flecha de «companion score» señalando a la alternativa.
**Pregunta:** ¿cómo decides qué sitio es mejor?
**Evidencia:** L12, L13, L14, L15 · confianza: FACT

## 6 · Honestidad + proceso → demo (≈30 s)

**Titular:** Solo afirmo lo que un test o una decisión respalda.
**En pantalla:** `78 decisiones · 110 tests · 15 scopes en ~22 h` + etiquetas `computed` / `mocked` / `not our model`.
**Visual:** captura de la línea de procedencia de la UI.
**Pregunta:** ¿me puedo fiar de los números?
**Evidencia:** L16, L17, L18, L19 · confianza: FACT

→ **Paso a la demo** (ver `speaker-notes.md`, ruta de 90 s).
