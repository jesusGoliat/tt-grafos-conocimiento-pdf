# Prototipo 2: Opciones para la extracción de entidades

---

## 1. Planteamiento del problema

### 1.1 Qué dice el protocolo

- **Objetivo 2.1.2**: pipeline de NLP para identificar *entidades, conceptos clave y relaciones semánticas*. Se evalúa con **Precisión, Recall y F1** sobre entidades y relaciones anotadas manualmente.
- **Prototipo 2 (§5.1.2)**: segmentación y preprocesamiento del texto, integración de modelos de NER, primeras pruebas de extracción de relaciones y análisis de la cobertura de NER *en distintos dominios*.
- **Prototipo 3 (§5.2.1)**: el LLM se vuelve el motor principal de extracción de tripletas. Por lo tanto, lo que se elija en P2 debe **servir como base o complemento del LLM**, no competir con él.
- **Objetivo 2.1.4**: normalización de entidades y resolución de correferencias (*Redundancy Rate*, *Entity Coverage*). La salida de P2 debe ser fácil de normalizar.

### 1.2 Entidades propuestas

El sistema procesa **documentos de dominio abierto** (académicos, técnicos, legales, empresariales), **mayoritariamente en español**. Propuesta inicial, a validar con el sinodal:

| Tipo | Ejemplos | Naturaleza |
|---|---|---|
| `PERSONA` | "Ary Shared Rosas Castillo", "Wadhwa" | Entidad nombrada clásica |
| `ORGANIZACION` | "Google", "Microsoft", "IPN" | Entidad nombrada clásica |
| `LUGAR` | "Shanghái", "México" | Entidad nombrada clásica |
| `FECHA` / `TIEMPO` | "2023", "agosto–junio" | Expresión temporal (se resuelve bien con reglas) |
| `OBRA` / `PRODUCTO` / `TECNOLOGIA` | "Neo4j", "LlamaIndex", "GPT", "Nougat" | Nombrada, pero muy dependiente del dominio |
| `EVENTO` | "ICDAR 2009", "ACL 2023" | Nombrada |
| `CONCEPTO` | "grafo de conocimiento", "resolución de correferencias", "CER" | **No es NER clásico**: término o frase clave del dominio |
| `METRICA` / `CANTIDAD` (opcional) | "F1-score", "200 páginas" | Con reglas y diccionario |

La categoría **`CONCEPTO` es la más importante para un grafo de conocimiento** y la que peor cubren los modelos NER tradicionales, que se entrenan solo con PER/ORG/LOC/MISC. Esto pesa mucho en la comparación.

### 1.3 Restricciones del proyecto

- **Hardware de desarrollo**: CPU Intel sin GPU dedicada, 7 GB de RAM y espacio en disco limitado. La inferencia de modelos *base* (~100–400 M de parámetros) es viable en CPU. Entrenar transformers o correr LLM locales de 7–8 B de parámetros es lento o inviable.
- **Sin corpus anotado propio** por ahora. Para medir F1 (objetivo 2.1.2) **hay que anotar un conjunto de evaluación de todos modos**, sea cual sea el enfoque.
- **Entrada**: el `content_list.json` del Prototipo 1 (MinerU), con bloques tipados (título, párrafo, tabla, imagen) y su página. Permite segmentar por sección y excluir encabezados y pies de página.

---

## 2. Enfoques

### 2.1 Algoritmos deterministas: regex, reglas, gramáticas y diccionarios (*gazetteers*)

**Descripción.** Patrones escritos a mano:
- expresiones regulares para fechas, correos, URLs, DOIs, cifras y referencias bibliográficas como `[6]`;
- reglas sobre tokens y etiquetas POS, por ejemplo `EntityRuler`, `Matcher` y `PhraseMatcher` de spaCy;
- gramáticas de frases nominales (`ADJ* NOUN (ADP NOUN)*`) para candidatos a concepto;
- listas de entidades conocidas (*gazetteers*), como países, instituciones o un glosario del dominio.

Las frases clave pueden extraerse sin supervisión con métodos estadísticos como **YAKE** (frecuencia, posición y dispersión de términos) o con métodos basados en embeddings como **KeyBERT**.

| Aspecto | Evaluación |
|---|---|
| **Ventajas** | Precisión muy alta en patrones bien definidos (fechas, correos, citas). Totalmente explicable y auditable. Costo computacional casi nulo. No requiere datos de entrenamiento. Determinista y reproducible |
| **Desventajas** | Recall bajo para entidades abiertas (nombres nuevos, conceptos). Hay que mantener reglas por dominio, lo que no escala a "documentos de distintos dominios". No resuelve ambigüedad (¿"Amazon" es empresa o río?) |
| **Datos requeridos** | Ninguno para operar; solo un conjunto pequeño para evaluar |
| **Costo computacional** | Mínimo: milisegundos por página en CPU |
| **Precisión esperada** | Alta en tipos con forma fija; baja cobertura en el resto. En extracción de palabras clave, un estudio sobre noticias en español reporta F1 de 71.1 % para YAKE y 73.3 % para KeyBERT, con YAKE ~28 veces más rápido |
| **Herramientas** | `re`, spaCy `EntityRuler`/`Matcher`, `dateparser`, YAKE, KeyBERT |
| **Idoneidad** | **Complemento indispensable, no solución principal.** Ideal para FECHA, CANTIDAD, correos, URLs y citas, y para generar candidatos a CONCEPTO |

### 2.2 Machine learning clásico: CRF, SVM, HMM, MaxEnt

**Descripción.** El NER se trata como etiquetado de secuencias (esquema BIO) con características diseñadas a mano: forma de la palabra, mayúsculas, prefijos y sufijos, POS, ventana de contexto, pertenencia a un gazetteer. El **CRF** (*Conditional Random Field*) es el modelo representativo. SVM y AdaBoost clasifican token por token.

| Aspecto | Evaluación |
|---|---|
| **Ventajas** | Ligero: se entrena en minutos en CPU. Interpretable (pesos por característica). Funciona razonablemente con corpus de miles de oraciones. Buen material didáctico como línea base |
| **Desventajas** | **Requiere corpus anotado** con exactamente las etiquetas buscadas. Ingeniería de características laboriosa. Rendimiento muy por debajo de los transformers. Generaliza mal entre dominios. No hay modelos preentrenados para la categoría CONCEPTO |
| **Datos requeridos** | Corpus anotado BIO. En español existen CoNLL-2002 (PER/ORG/LOC/MISC), AnCora y CAPITEL. Para CONCEPTO habría que anotar uno propio |
| **Costo computacional** | Bajo en entrenamiento e inferencia |
| **Precisión esperada** | En CoNLL-2002 español, el mejor sistema de la tarea compartida (AdaBoost con características ricas) obtuvo **F1 = 81.39**. Los CRF de esa época rondan 80–82 F1, unos 7–9 puntos por debajo de BETO o RoBERTa-BNE |
| **Herramientas** | `sklearn-crfsuite`, `python-crfsuite`, `scikit-learn` (SVM) |
| **Idoneidad** | **Baja como solución.** Útil solo como línea base académica si el sinodal pide comparar con un método clásico |

### 2.3 Deep learning y transformers para NER

Hay tres variantes relevantes:

**a) Pipelines preentrenados de spaCy (`es_core_news_sm/md/lg`, `es_dep_news_trf`).** Hacen en un solo paso tokenización, segmentación en oraciones, lematización, POS, dependencias y NER (PER/ORG/LOC/MISC). Están entrenados con AnCora y WikiNER.

**b) Encoders específicos del español afinados para NER.** BETO (BERT en español, U. de Chile) y RoBERTa-BNE / MarIA (BSC, entrenados con 570 GB de texto de la Biblioteca Nacional de España), afinados en CoNLL-2002 o CAPITEL. Usan las etiquetas fijas de esos corpus.

**c) NER de vocabulario abierto (*zero-shot*): GLiNER y GLiNER2.** Encoder bidireccional que recibe **las etiquetas como texto** (por ejemplo, `["persona", "organización", "concepto", "tecnología"]`) y extrae los fragmentos que les corresponden. Tiene versión multilingüe. GLiNER2 (EMNLP 2025, demo) une NER, clasificación y extracción estructurada por esquema en un solo modelo pensado para CPU.

| Aspecto | Evaluación |
|---|---|
| **Ventajas** | Estado del arte en NER supervisado. spaCy también resuelve la segmentación y el preprocesamiento que pide P2. **GLiNER permite definir tipos nuevos, como CONCEPTO o TECNOLOGIA, sin reentrenar**. Inferencia en CPU viable. Código abierto y ejecución local, sin enviar documentos a terceros |
| **Desventajas** | Los modelos (a) y (b) solo reconocen PER/ORG/LOC/MISC, sin CONCEPTO. Adaptarlos a tipos nuevos requiere anotar y afinar, lo que pide GPU. GLiNER zero-shot es notablemente menos preciso que un modelo supervisado en tipos clásicos. Contexto limitado (~512 tokens) que obliga a fragmentar el texto |
| **Datos requeridos** | (a)/(b): ninguno para usarlos tal cual y un corpus anotado para tipos nuevos. (c): ninguno; se recomiendan unos cientos de ejemplos si se quiere afinar |
| **Costo computacional** | spaCy `lg`: muy bajo en CPU. Encoders base (~110–125 M) y GLiNER: decenas o cientos de ms por fragmento en CPU. Afinar: GPU recomendable (Google Colab basta) |
| **Precisión esperada** | spaCy `es_core_news_lg` v2.3.1: F1 ≈ 90.3 en WikiNER, una anotación *silver* que sobreestima frente a anotación humana. BETO: F1 = 88.43 en CoNLL-2002. RoBERTa-BNE: 88.51 (CoNLL-2002) y 89.60/90.51 base/large (CAPITEL). GLiNER multilingüe zero-shot en español (Multi-CoNER): F1 en torno a 42–59 según variante y evaluación, aun así superior a ChatGPT zero-shot en la mayoría de los idiomas |
| **Herramientas** | `spacy` + `es_core_news_lg`, `transformers` + `PlanTL-GOB-ES/roberta-base-bne-capitel-ner`, `dccuchile/bert-base-spanish-wwm-cased`, `gliner` (`urchade/gliner_multi-v2.1`), `gliner2` (`fastino/gliner2-multi-v1`) |
| **Idoneidad** | **Alta.** spaCy para el preprocesamiento y los tipos clásicos, GLiNER para los tipos abiertos (CONCEPTO, TECNOLOGIA). Es la opción más fiel al alcance de P2 ("integración de modelos de NER") y corre en el hardware disponible |

### 2.4 LLMs: prompting, salida estructurada, few-shot y fine-tuning

**Descripción.** Un modelo generativo (GPT-4o/5, Claude, Gemini o abiertos como Llama, Qwen y Mistral) recibe el texto y una instrucción ("extrae las entidades de tipo X") y devuelve JSON. Hay cuatro variantes:

- **Zero-shot**: solo la instrucción y la definición de tipos.
- **Few-shot**: con ejemplos anotados en el prompt.
- **Salida estructurada**: la respuesta queda restringida a un JSON Schema, ya sea con la API del proveedor o con Ollama/llama.cpp en local mediante gramáticas. Esto garantiza JSON válido.
- **Fine-tuning / LoRA**: se afina un modelo abierto con ejemplos de NER.

| Aspecto | Evaluación |
|---|---|
| **Ventajas** | Máxima flexibilidad: tipos arbitrarios, incluidos conceptos, definidos en lenguaje natural. Entiende contexto largo y ambigüedad. **Puede extraer entidades y relaciones en la misma llamada**, lo que conecta directo con P3. Sin datos de entrenamiento para empezar. Calidad en español alta en modelos comerciales recientes |
| **Desventajas** | **Alucinaciones**: entidades que no están en el texto o copiadas de los ejemplos del prompt. Esto choca con el requisito de "fundamentado estrictamente en el documento", así que hay que verificar contra el texto fuente. Variabilidad entre ejecuciones. Por API: costo por token, latencia, dependencia de un tercero y privacidad de los documentos. En local, en este hardware, solo caben modelos pequeños (≤ 4 B cuantizados) y son lentos. Los límites de los fragmentos detectados son menos exactos que en el etiquetado de secuencias |
| **Datos requeridos** | Zero-shot: ninguno. Few-shot: de 5 a 20 ejemplos buenos. Fine-tuning: cientos o miles de ejemplos |
| **Costo computacional** | API: bajo en infraestructura y variable en dinero (depende de tokens y modelo). Local: de 4 a 8 GB de RAM para modelos de 3–8 B cuantizados, a pocos tokens por segundo en CPU. Fine-tuning con LoRA: requiere GPU |
| **Precisión esperada** | ChatGPT zero-shot queda **por debajo** de los modelos supervisados en NER clásico (Wei et al., 2023, ya citado en el protocolo). Con fine-tuning eficiente y formatos de salida en línea o XML, LLM abiertos de ~8 B alcanzan **F1 = 93.85 en CoNLL-2003** (inglés), comparable o superior a BERT-MRC (93.04). Destilar un LLM en un modelo pequeño (UniversalNER) supera a ChatGPT por 7–9 puntos de F1 en 43 datasets |
| **Herramientas** | API con *structured outputs* (Anthropic, OpenAI, Gemini), Ollama con `format=<JSON Schema>`, Pydantic, LangExtract (Google; liga cada extracción a su posición exacta en el texto y descarta las no fundamentadas), LlamaIndex / LangChain `LLMGraphTransformer`, KGGen |
| **Idoneidad** | **Alta para P3** (tripletas) y como **comparador** en P2. Como único extractor en P2 adelantaría el alcance de P3 y dependería de un servicio externo. Si se usa, debe incluir verificación de que cada entidad aparece en el texto |

### 2.5 Enfoques híbridos

**Descripción.** Combinar los enfoques anteriores según lo que mejor hace cada uno. Patrones frecuentes en la literatura reciente:

1. **Reglas + modelo**: un `EntityRuler` antes o después del NER estadístico para tipos con forma fija y términos de glosario.
2. **Modelo de NER como generador de candidatos y LLM como verificador o tipificador**: barato, con menos alucinaciones y salida anclada al texto.
3. **LLM como extractor y reglas como verificador**: cada entidad debe encontrarse en el texto fuente (*grounding*, como en LangExtract).
4. **LLM para anotar datos y modelo pequeño para producción**: se destila el LLM en GLiNER o un CRF, como hace UniversalNER.
5. **Pipeline por etapas** como el que describen las revisiones de construcción de grafos con LLM: ontología → extracción → fusión/normalización.

| Aspecto | Evaluación |
|---|---|
| **Ventajas** | Aprovecha la precisión de las reglas, la cobertura de los modelos y la flexibilidad del LLM. Reduce el costo, porque el LLM solo se invoca donde aporta. Cada componente se evalúa por separado, lo que facilita la discusión en el reporte |
| **Desventajas** | Más componentes que integrar y probar. Hay que resolver conflictos entre fuentes (fusión de fragmentos solapados) |
| **Datos requeridos** | Los del componente más exigente; en la variante propuesta, solo el conjunto de evaluación |
| **Costo computacional** | Bajo o medio |
| **Precisión esperada** | Mayor o igual que la de su mejor componente en cada tipo, siempre que se definan reglas de prioridad |
| **Herramientas** | spaCy (pipeline extensible), GLiNER (componente `gliner-spacy`), regex, YAKE/KeyBERT y, en P3, un LLM con salida estructurada |
| **Idoneidad** | **La más alta.** Encaja con el prototipado evolutivo: P2 construye la parte local (reglas + spaCy + GLiNER) y P3 agrega el LLM sin desechar lo anterior |

---

## 3. Tabla comparativa

Escala: ●●● alto, ●● medio, ● bajo.

| Criterio | Deterministas | ML clásico (CRF) | spaCy / BETO / RoBERTa-BNE | GLiNER (zero-shot) | LLM (API) | LLM local (CPU) | **Híbrido propuesto** |
|---|---|---|---|---|---|---|---|
| Necesita corpus anotado para operar | No | **Sí** | No (tipos clásicos) | No | No | No | No |
| Cubre CONCEPTO y tipos abiertos | ● (candidatos) | ● | ● | ●●● | ●●● | ●● | ●●● |
| Precisión en tipos clásicos (PER/ORG/LOC) | ● | ●● (~81 F1) | ●●● (~88–90 F1) | ●● | ●● / ●●● | ● / ●● | ●●● |
| Riesgo de alucinación | Nulo | Nulo | Nulo | Nulo (extractivo) | **Alto** | **Alto** | Bajo |
| Costo computacional en este equipo | ●●● muy bajo | ●●● muy bajo | ●●● bajo | ●● medio | ●●● bajo (local) | ● muy alto | ●● medio |
| Costo monetario | 0 | 0 | 0 | 0 | Por token | 0 | 0 en P2 |
| Privacidad (no sale del equipo) | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ | ✔ |
| Explicabilidad | ●●● | ●● | ● | ● | ● | ● | ●● |
| Esfuerzo de implementación | ●● | ●●● alto | ● | ● | ● | ●● | ●● |
| Extrae relaciones (útil para P3) | ● (patrones) | ✘ | ● (dependencias) | ●● (GLiNER2 / Relex) | ●●● | ●● | ●● hoy, ●●● en P3 |
| Idoneidad para P2 | Complemento | Línea base | **Núcleo** | **Núcleo** | Comparador | No recomendado | **Recomendado** |

---

## 4. Recomendación preliminar

**Pipeline híbrido local para el Prototipo 2**, evolucionable hacia el LLM en el Prototipo 3:

1. **Segmentación y preprocesamiento** a partir del `content_list.json` de MinerU. Se descartan encabezados, pies de página y números de página. Se agrupa por sección usando los títulos. Las tablas se convierten a texto o se procesan aparte. Luego spaCy `es_core_news_lg` hace oraciones, tokens, lemas y POS.
2. **Reglas**: `EntityRuler` y regex para FECHA, CANTIDAD/METRICA, correos, URLs y citas.
3. **NER clásico**: spaCy (o RoBERTa-BNE-CAPITEL si su F1 es mejor en nuestro conjunto) para PERSONA, ORGANIZACION y LUGAR.
4. **NER abierto**: GLiNER multilingüe con las etiquetas `concepto`, `tecnología`, `obra`, `evento`. Las frases clave de YAKE/KeyBERT sirven como señal adicional para CONCEPTO.
5. **Fusión**: se resuelven solapamientos por prioridad (regla > modelo supervisado > zero-shot) y se hace una normalización ligera (lema, minúsculas, siglas) como antecedente del objetivo 2.1.4.
6. **Relaciones preliminares**: co-ocurrencia de entidades en la misma oración y patrones sujeto–verbo–objeto sobre el árbol de dependencias de spaCy. Esto es solo una línea base: el LLM las reemplazará en P3.
7. **Evaluación**: se anota manualmente un conjunto pequeño (por ejemplo, 3 documentos de dominios distintos, unas 30 páginas) con Label Studio o Doccano. Se reporta P/R/F1 **por tipo de entidad y por dominio**, que es lo que pide el protocolo. **Como comparador**, se corre una vez un LLM con salida estructurada sobre el mismo conjunto para cuantificar la diferencia y justificar P3.

Por qué esta opción:
- Corre en el hardware disponible.
- No requiere entrenar.
- Cubre los conceptos que necesita un grafo de conocimiento.
- No alucina.
- Cada etapa es medible.
- Deja preparado el terreno para P3 sin adelantar su alcance.

---

## 5. Preguntas abiertas para el sinodal

1. **Tipología de entidades.** ¿Se fija un conjunto cerrado de tipos (como en la Sección 1.2) o se permite que el sistema proponga tipos (*schema-free*, como sugiere el protocolo al hablar de "sin depender de esquemas rígidos")? Esto define cómo se anota y cómo se mide F1.
2. **¿"Concepto" es una entidad?** ¿Los conceptos clave se evalúan junto con las entidades nombradas o con una métrica aparte, propia de extracción de frases clave?
3. **Conjunto de evaluación.** ¿Cuántos documentos y de qué dominios? ¿Se acepta una sola persona anotadora o hace falta medir el acuerdo entre anotadores (κ de Cohen)?
4. **Criterio de coincidencia.** ¿F1 con coincidencia exacta de fragmento y tipo (*strict*) o parcial (*relaxed*)? Los LLM suelen salir peor en *strict*.
5. **Uso de LLM vía API.** ¿Es aceptable enviar documentos de usuarios a un servicio externo (como ya ocurre con MinerU en P1) o el sistema final debe poder correr solo de forma local? Esto condiciona la elección del LLM en P3.
6. **Idioma.** ¿Se consideran documentos en inglés y en español? Afecta la elección entre modelos monolingües (BETO, RoBERTa-BNE) y multilingües (GLiNER-multi, XLM-R).
7. **Línea base clásica.** ¿Se requiere comparar contra un método clásico (CRF) por rigor académico, aunque no se use en el sistema final?
8. **Alcance de relaciones en P2.** ¿Basta con co-ocurrencia y patrones de dependencias como "primeras pruebas", dejando la extracción formal de relaciones al LLM en P3?

---

## 6. Referencias

**Benchmarks y modelos para español**
- E. F. Tjong Kim Sang, "Introduction to the CoNLL-2002 Shared Task: Language-Independent Named Entity Recognition," 2002. https://arxiv.org/abs/cs/0209010
- J. Cañete et al., "Spanish Pre-trained BERT Model and Evaluation Data" (BETO), PML4DC @ ICLR 2020. https://users.dcc.uchile.cl/~jperez/papers/pml4dc2020.pdf · https://github.com/dccuchile/beto
- A. Gutiérrez-Fandiño et al., "MarIA: Spanish Language Models," 2021. https://arxiv.org/abs/2107.07253
- PlanTL-GOB-ES, `roberta-base-bne-capitel-ner` (tarjeta del modelo). https://huggingface.co/PlanTL-GOB-ES/roberta-base-bne-capitel-ner
- PlanTL-GOB-ES, `roberta-large-bne-capitel-ner`. https://huggingface.co/PlanTL-GOB-ES/roberta-large-bne-capitel-ner
- Explosion, `es_core_news_lg` 2.3.1 (métricas de NER). https://github.com/explosion/spacy-models/releases/tag/es_core_news_lg-2.3.1

**ML clásico**
- ELI5, "Named Entity Recognition using sklearn-crfsuite" (tutorial con CoNLL-2002 en español). https://eli5.readthedocs.io/en/latest/tutorials/sklearn_crfsuite.html
- G. Lample et al., "Neural Architectures for Named Entity Recognition," NAACL 2016. https://arxiv.org/abs/1603.01360

**NER de vocabulario abierto**
- U. Zaratiana et al., "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer," NAACL 2024. https://aclanthology.org/2024.naacl-long.300.pdf
- U. Zaratiana et al., "GLiNER2: An Efficient Multi-Task Information Extraction System with Schema-Driven Interface," EMNLP 2025 (demos). https://arxiv.org/abs/2507.18546 · https://huggingface.co/fastino/gliner2-multi-v1
- "GLiNER-Relex: A Unified Framework for Joint Named Entity Recognition and Relation Extraction," 2026. https://arxiv.org/abs/2605.10108
- W. Zhou et al., "UniversalNER: Targeted Distillation from Large Language Models for Open Named Entity Recognition," ICLR 2024. https://arxiv.org/abs/2308.03279

**LLM para extracción de información**
- X. Wei et al., "Zero-Shot Information Extraction via Chatting with ChatGPT," 2023. https://arxiv.org/abs/2302.10205
- Q. Zhan, Y. Wang, H. Huang, "Assessment of Generative Named Entity Recognition in the Era of Large Language Models," 2026. https://arxiv.org/abs/2601.17898
- D. Xu et al., "Large Language Models for Generative Information Extraction: A Survey," 2023. https://arxiv.org/abs/2312.17617
- Google, LangExtract (extracción con *source grounding*). https://github.com/google/langextract · https://developers.googleblog.com/introducing-langextract-a-gemini-powered-information-extraction-library/
- Ollama, "Structured outputs." https://ollama.com/blog/structured-outputs

**Construcción de grafos de conocimiento con LLM**
- "LLM-empowered knowledge graph construction: A survey," 2025. https://arxiv.org/abs/2510.20345
- "Are Large Language Models Effective Knowledge Graph Constructors?," 2025. https://arxiv.org/abs/2510.11297
- KGGen: LLM-Powered Knowledge Graphs (resumen). https://www.emergentmind.com/topics/kggen
- "LightKGG: Simple and Efficient Knowledge Graph Generation from Textual Data," 2025. https://arxiv.org/abs/2510.23341

**Extracción de frases clave**
- R. Campos et al., "YAKE! Collection-Independent Automatic Keyword Extractor," ECIR 2018. https://www.researchgate.net/publication/323167464_YAKE_Collection-Independent_Automatic_Keyword_Extractor
- "Evaluation of Keyword Extraction using YAKE and KeyBERT in Text Preprocessing for Hoax News Detection Based on Bi-LSTM," 2025. https://www.researchgate.net/publication/394789438
- M. Grootendorst, KeyBERT. https://github.com/MaartenGr/KeyBERT

> **Nota sobre las cifras.** Los F1 provienen de benchmarks distintos (CoNLL-2002, CAPITEL, WikiNER, Multi-CoNER, CoNLL-2003 en inglés) y **no son directamente comparables entre sí**. Sirven para ordenar los enfoques, no para predecir el desempeño en nuestros documentos. Ese desempeño se medirá con el conjunto anotado de la Sección 4.
