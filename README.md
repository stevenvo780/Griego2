# Sistema de Estudio Colaborativo de Griego Clásico

## Descripción

Este repositorio contiene un sistema de trabajo colaborativo diseñado para el estudio del griego clásico. Los contenidos están organizados en archivos Markdown que permiten a agentes de IA y colaboradores humanos acceder al contexto completo del curso.

## Propósito

Los archivos Markdown están estructurados de manera que:

- **Agentes de IA** puedan acceder a todo el contexto y responder preguntas basadas en los materiales del curso
- **Colaboradores humanos** puedan consultar, editar y expandir los contenidos en tiempo real
- **El equipo** pueda validar traducciones y análisis de forma conjunta

## Contenidos disponibles

### Clases
Apuntes y materiales de las sesiones de clase, incluyendo conjugaciones verbales, el verbo εἰμί, y tablas de referencia.

### Diccionarios
Diccionario VOX Griego Clásico-Español en formato consultable.

### Gramáticas
Métodos filológico-didácticos y gramáticas de referencia (Berenguer Amenós).

### Libros de ejercicios
- Athenaze I y II
- Helade I y II
- Cuadernillos de griego

### Ejercicios de traducción
Traducciones realizadas en clase con análisis morfológico detallado.

## Metodología de trabajo

### Paso 1: Desglose morfológico
Cada palabra del texto griego se analiza identificando:
- Categoría gramatical
- Caso, género y número (sustantivos/adjetivos)
- Tiempo, modo, voz, persona y número (verbos)
- Raíz y terminación

### Paso 2: Traducción
- Consulta del diccionario para significados
- Consideración del contexto sintáctico
- Propuesta de traducción literal y literaria

### Paso 3: Validación colaborativa
- Revisión entre pares (humanos y agentes)
- Contraste con tablas de declinación/conjugación
- Verificación de coherencia gramatical
- Documentación de dudas y resoluciones

## Herramienta de visualización

El directorio `visor_markdown/` contiene una aplicación web que permite:

- Navegar todos los archivos Markdown del sistema
- Editar documentos en tiempo real con vista previa
- Colaboración simultánea entre múltiples usuarios
- Copiar contenido formateado para Google Docs
- Exportar a PDF

### Ejecutar el visor

```bash
cd visor_markdown
python3 servidor.py
```

Abrir en el navegador: http://localhost:8888

## Estructura del repositorio

```
Griego2/
├── README.md                    # Este archivo
├── Clases/                      # Materiales de clase
├── Diccionarios/                # Diccionario VOX
├── Gramáticas/                  # Referencias gramaticales
├── Libros de ejercicios/        # Athenaze, Helade, etc.
├── Ejercicios de traducción/    # Traducciones con análisis
├── visor_markdown/              # Herramienta web colaborativa
├── AnalisisMorfologico.md       # Plantilla de análisis
├── TallerGriego.md              # Notas del taller
└── [otros archivos .md]         # Documentos adicionales
```

## Flujo de trabajo con agentes

1. El usuario plantea una pregunta o texto a traducir
2. El agente accede a los materiales relevantes (diccionario, gramáticas, clases)
3. Se realiza el análisis morfológico siguiendo la metodología establecida
4. Se propone una traducción con justificación gramatical
5. El equipo valida y corrige colaborativamente
6. Los resultados se documentan en Markdown para referencia futura
