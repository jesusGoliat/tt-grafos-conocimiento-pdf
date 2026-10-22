# Alcance: qué cubre TT I y qué queda para TT II

El proyecto conserva su naturaleza original: mismo objetivo general, misma
metodología de prototipado evolutivo y mismos componentes. Lo que cambia es el
periodo en que se entrega cada uno.

La columna **«Definido para»** indica el periodo que el protocolo registrado asignaba
a cada elemento. Un elemento marcado «TT II» **no era una entrega de TT I**.

| Ámbito | Definido para | En este repositorio (TT I) |
|---|---|---|
| Objetivo general | Todo el TT | Íntegro; se desarrollan dos módulos |
| OE-01. Extracción de texto y CER | TT I | Cumplido: CER de 7.56 % en 42 páginas |
| OE-02. Entidades y relaciones | TT I | Cumplido: P/R/F1 en Re-DocRED |
| OE-03. LLM y tripletas | TT II (P3) | **Se adelanta a TT I**: juez LLM y autoentrenamiento |
| OE-04. Grafo de conocimiento | TT II (P3) | Programado para TT II |
| OE-05. Visualización | TT II (P4) | Programado para TT II |
| OE-06. Interfaz web | TT I (base) / TT II (integración) | Cumplido: base de TT I |
| OE-07. Documentos variados y experto | TT II (P4) | Programado para TT II |
| Base de datos de grafos | TT I (P1) | **Se traslada a TT II** (única excepción real de periodo) |
| Metodología | Transversal | Prototipado evolutivo; módulos paralelos, integración en P3 |

## Lectura

- **Solo la base de datos del grafo** estaba definida para TT I y cambia de periodo.
  El Prototipo 1 persiste los resultados en archivos; el diseño y la creación de la
  base de datos se harán en el Prototipo 3.
- **OE-04, OE-05 y OE-07** ya estaban previstos para TT II en el protocolo. No son
  entregables pendientes de TT I.
- **OE-03** estaba previsto para TT II y se adelantó a TT I.
- **Ningún componente se elimina.** Lo que no está en este repositorio está en el
  repositorio del Prototipo 2 o queda programado para TT II.
