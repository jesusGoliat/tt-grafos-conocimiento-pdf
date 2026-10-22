# Contexto del proyecto

Documento normativo para cualquier persona o agente que trabaje en este repositorio.
Si algo aquí contradice a otro archivo del repositorio, este documento y el reporte
técnico de TT I prevalecen.

## Qué es este repositorio

Versión oficial del **Trabajo Terminal I** *«Generación de grafos de conocimiento a
partir de documentos en formato PDF mediante LLM y NLP»* (ESCOM, IPN), de González
Arellano Jesús Ángel.

Contiene el código final del **Prototipo 1**, la evaluación del **CER** con sus
artefactos, y una descripción breve del **Prototipo 2** con enlace a su repositorio
especializado.

No es un repositorio de desarrollo: no incluye bitácoras, hipótesis descartadas ni
versiones obsoletas de scripts.

## Objetivo general

Construir un sistema que, a partir de documentos PDF, genere una representación
estructurada, navegable y con procedencia verificable del conocimiento contenido en
ellos, mediante extracción de texto, procesamiento de lenguaje natural y modelos de
lenguaje extensos.

## Objetivos específicos

Siete objetivos, conservando los identificadores del protocolo registrado. Cuatro se
cerraron en TT I; tres están programados para TT II y **no son entregables de TT I**.

La columna **entrega** indica dónde se entrega cada uno, no dónde lo situaba el
protocolo; esa correspondencia está en [`alcance.md`](alcance.md).

| ID | Objetivo | Entrega | Estado |
|---|---|---|---|
| OE-01 | Extracción de texto de PDF, evaluada con CER | TT I | Cumplido |
| OE-02 | Extracción de entidades y relaciones, evaluada con P/R/F1 | TT I | Cumplido |
| OE-03 | LLM como verificador y generador de pseudo-etiquetas | TT I (adelantado de TT II) | Cumplido |
| OE-04 | Construcción y consolidación del grafo de conocimiento | TT II | Programado |
| OE-05 | Visualización interactiva del grafo | TT II | Programado |
| OE-06 | Interfaz web de carga y consulta | TT I | Cumplido |
| OE-07 | Pruebas con documentos variados y valoración experta | TT II | Programado |

La correspondencia entre el protocolo registrado y este repositorio está en
[`alcance.md`](alcance.md).

## Arquitectura

Dos módulos paralelos de una arquitectura común; la integración corresponde al
Prototipo 3.

| Prototipo | Qué hace | Dónde |
|---|---|---|
| **P1** | Carga de PDF, extracción con MinerU, normalización a Markdown y a bloques, interfaz web | Este repositorio (`backend/`, `frontend/`) |
| **P2** | Extracción de entidades y relaciones con GLiNER-Relex sobre Re-DocRED, juez LLM y autoentrenamiento | [`gliner-relex-docre-benchmark`](https://github.com/jesusGoliat/gliner-relex-docre-benchmark) |
| **P3** | Integración de ambos módulos, grafo de conocimiento y visualización | TT II |

P1 y P2 **no** son una derivación uno del otro: son módulos independientes que se
integran en TT II.

## Resultados finales

| Métrica | Resultado | Dónde se evalúa |
|---|---|---|
| CER global | 7.56 % (42 páginas de OmniDocBench) | `backend/scripts/omnidocbench/` |
| CER sin fórmulas en línea | 3.13 % (22 páginas) | ídem |
| F1 estricto con tipo, N = 10 | 23.62 ± 2.01 (B0) · 25.85 ± 1.62 (J0) | Repositorio de P2 |
| F1 estricto con tipo, N = 50 | 31.34 ± 0.71 (B0) · 33.41 ± 0.15 (J0) | ídem |
| ΔF1 del juez LLM | +2.23 (N = 10) · +2.07 (N = 50), 5/5 subconjuntos | ídem |
| ΔF1 del autoentrenamiento | +2.42, 5/5 subconjuntos | ídem |
| Pruebas automatizadas | 30/30 y 4/4 criterios de aceptación | `backend/tests/` |

## Qué no reintroducir

Decisiones ya cerradas. No reabrir sin instrucción explícita del autor.

- **Diseño C1 / GLiDRE / destilación**: eliminado del trabajo final. Aparece solo en
  el capítulo 2 del reporte como antecedente.
- **Comparación con el estado del arte**: no se hace, porque los conjuntos y los
  regímenes de datos no son comparables.
- **F1 de 31.3 atribuido a la ficha de GLiNER-Relex**: la ficha no publica ese dato.
  No citarlo.
- **Anotación manual propia**: descartada por complejidad y tiempo. OE-02 se evalúa
  con Re-DocRED, anotado por personas.
- **Evaluación del Prototipo 2 en español**: descartada.
- **Cobertura multidominio de NER**: no forma parte del alcance.

## Limitaciones

- El CER se midió sobre 42 páginas de OmniDocBench **en inglés**. No se demostró
  fidelidad sobre PDF digitales nativos ni sobre documentos en español.
- Los experimentos de P2 usan 1 000 documentos por subconjunto (5 000 en total), no
  el conjunto completo de Re-DocRED.
- Reejecutar MinerU no garantiza resultados idénticos: depende de una API en la nube
  que puede cambiar de modelo. Lo reproducible es el cálculo de las métricas a partir
  de los artefactos archivados.
- Las capturas de la interfaz incluidas en el reporte corresponden a un protocolo de
  ejemplo y conservan la portada con el marcador `20XX-XXXX`.

## Fuente normativa

`main.pdf`, reporte técnico de TT I, 127 páginas, 22 de octubre de 2026. Vive en el
repositorio de documentación, no en este.
