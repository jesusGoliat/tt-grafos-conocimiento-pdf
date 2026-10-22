# Reglas para agentes

Instrucciones operativas para cualquier agente que trabaje en este repositorio.

## Antes de empezar

Lee [`docs/CONTEXTO.md`](docs/CONTEXTO.md) y [`docs/alcance.md`](docs/alcance.md).
Son la fuente normativa: si el código contradice a esos documentos, señálalo, no
adaptes el documento al código sin justificarlo.

## Reglas

1. **Un solo escritor.** Los agentes de auditoría son de **solo lectura**. Las
   modificaciones las hace el coordinador, en la rama `consolidacion-tt1`.
2. **Checkpoint inmediato.** Escribe tus hallazgos a disco en cuanto cierres cada
   bloque, no al final del turno. Una sesión puede cancelarse en cualquier momento.
3. **No inventar.** Toda afirmación necesita evidencia: `ruta:línea`, o el comando y
   su salida. Si no lo pudiste comprobar, dilo explícitamente.
4. **Separar hechos de inferencias.** Marca cada recomendación como inferencia.
5. **No ejecutar destructivamente.** Nada de `rm`, `git reset --hard`, `git push
   --force` ni reescritura de historial. El historial se conserva: es lo que permite
   revertir una retirada equivocada.
6. **Nada de datos sensibles.** No incluyas tokens de MinerU ni rutas personales del
   equipo del autor en código, documentación ni commits.

## Idioma

Español, impersonal, sin primera persona. Términos: «tripleta», «grafo», «backend»,
«frontend», «TT I»/«TT II», «Re-DocRED», «OmniDocBench», «GLiNER-Relex»,
«gpt-oss-120b».

## Verificación mínima antes de dar algo por terminado

```bash
cd backend && pytest -m "not integration" -q
```

Y para la evaluación del CER, desde `backend/scripts/omnidocbench/`:

```bash
python3 aggregate.py resultados_cer_2026-10-22/cer_results.csv
```

Debe devolver 7.56 % global y 3.13 % sin fórmulas. Si no coincide, algo se rompió.
