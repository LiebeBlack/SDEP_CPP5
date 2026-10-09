# ANEXOS DEL EXPEDIENTE

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 12 del expediente del informe del estado de la investigación.

---

## Presentación de los anexos

Este compendio reúne los instrumentos, diagramas, cuadros e inventarios que sustentan el expediente, con el fin de que el conjunto sea consultable sin depender del corpus académico ni del repositorio de código. Los anexos reproducen o consolidan información ya verificada en los documentos principales; cuando una remisión resulta suficiente, se indica el documento donde el contenido consta con mayor extensión.

| Anexo | Contenido |
|-------|-----------|
| A | Instrumentos de recolección de datos |
| B | Plantillas de registro para el piloto |
| C | Diagramas y modelos del sistema |
| D | Inventario del código y composición de la suite de pruebas |
| E | Cuadro normativo |
| F | Presupuesto del proyecto |
| G | Glosario del expediente |
| H | Índice de tablas y figuras |

---

## Anexo A. Instrumentos de recolección de datos

### A.1 Guía de entrevista para el análisis de requerimientos

**Propósito.** Recoger información sobre los procesos actuales de gestión de personal, las dificultades que enfrenta el personal y las expectativas respecto del sistema.

**Parte 1. Información general.** 1. ¿Cuál es su rol actual en la institución? 2. ¿Cuánto tiempo lleva desempeñándolo? 3. ¿Cuántas personas dependen de su gestión? 4. ¿Qué herramientas informáticas utiliza en su trabajo diario?

**Parte 2. Procesos actuales.** 5. ¿Cómo se realiza actualmente el registro de un empleado nuevo? 6. ¿Cómo se elabora la nómina del periodo? 7. ¿Cómo se administran los documentos del personal? 8. ¿Cómo se controlan las incidencias —permisos, reposos, vacaciones—? 9. ¿Qué reportes debe elaborar de manera periódica y con qué destino?

**Parte 3. Dificultades.** 10. ¿Cuáles son las principales dificultades de su trabajo diario? 11. ¿Qué tareas consumen más tiempo del que deberían? 12. ¿Qué errores se presentan con mayor frecuencia y por qué causa? 13. ¿Qué información resulta difícil de obtener en el momento en que se necesita?

**Parte 4. Expectativas.** 14. ¿Qué características debería tener un sistema de gestión de personal para resultar útil? 15. ¿Qué funcionalidades considera indispensables? 16. ¿Qué funcionalidades serían deseables pero no indispensables? 17. ¿Cómo describiría el nivel de manejo informático del personal de la institución?

**Parte 5. Restricciones.** 18. ¿De cuánto tiempo dispone el personal para aprender a usar una herramienta nueva? 19. ¿Qué limitaciones presupuestarias existen para incorporar software? 20. ¿Qué posibilidades de capacitación ofrece la institución?

**Parte 6. Comentarios finales.** 21. ¿Desea agregar alguna observación sobre la gestión de personal en la institución? 22. ¿Tiene preguntas sobre el proyecto?

### A.2 Cuestionario de satisfacción de usuarios

**Instrucciones.** Responda cada afirmación con la escala de 1 a 5, donde 1 corresponde a muy en desacuerdo y 5 a muy de acuerdo.

**Sección 1. Facilidad de uso.** 1. Aprender a usar el sistema resultó sencillo. 2. El sistema es fácil de usar en el trabajo diario. 3. La navegación entre módulos resulta intuitiva. 4. Los formularios son claros y fáciles de completar. 5. Encontrar la información que necesito es sencillo.

**Sección 2. Eficiencia.** 6. El sistema hace mi trabajo más rápido. 7. El sistema reduce los errores en mis tareas. 8. El sistema me ahorra tiempo de manera significativa. 9. Los procesos resultan más eficientes con el sistema. 10. Puedo completar más trabajo en menos tiempo.

**Sección 3. Precisión.** 11. Los resultados que produce el sistema son precisos. 12. El cálculo de la nómina resulta correcto. 13. La información del sistema es confiable. 14. Los reportes generados son exactos. 15. Cometo menos errores con el sistema que sin él.

**Sección 4. Satisfacción general.** 16. Estoy satisfecho con el sistema en su conjunto. 17. Recomendaría el sistema a otras instituciones. 18. El sistema responde a mis expectativas. 19. Prefiero el sistema frente al procedimiento manual. 20. Continuaré usando el sistema.

**Sección 5. Comentarios abiertos.** 21. ¿Qué aspectos del sistema le resultan más útiles? 22. ¿Qué aspectos deberían mejorarse? 23. ¿Alguna otra observación o sugerencia?

**Validación.** Sobre las respuestas se calcula el coeficiente alfa de Cronbach para estimar la consistencia interna del cuestionario.

### A.3 Protocolo de pruebas de usabilidad

**Datos de la sesión.** Participantes [por completar]; fecha [por completar]; lugar [por completar]; facilitador [por completar]; duración total de 60 a 90 minutos.

**Secuencia.** 1. Bienvenida (5 minutos): se explica el propósito y se advierte que se evalúa el sistema, no a la persona. 2. Instrucciones (5 minutos): se presenta la técnica de pensamiento en voz alta. 3. Tareas (30 a 45 minutos). 4. Entrevista de cierre (10 a 15 minutos). 5. Cierre (5 minutos).

**Tareas evaluadas**

| Tarea | Descripción | Métrica principal |
|-------|-------------|-------------------|
| 1 | Registrar un empleado con datos personales, laborales y un documento | Tiempo, errores |
| 2 | Localizar un empleado por número de cédula | Tiempo, éxito |
| 3 | Generar la nómina de un periodo definido | Tiempo, éxito |
| 4 | Emitir el recibo de pago de un empleado | Tiempo, éxito |
| 5 | Cargar un documento con fecha de vencimiento | Tiempo, errores |
| 6 | Registrar una incidencia y aprobarla | Tiempo, errores |

### A.4 Registro de observación directa

La observación es no participante, con registro de tiempos, herramientas y obstáculos en notas de campo estructuradas, y con una duración prevista de dos a cuatro horas por institución, distribuidas en jornadas distintas para evitar sesgos derivados de un día atípico.

---

## Anexo B. Plantillas de registro para el piloto

Las plantillas de registro de tiempos, de errores, de resultado por tarea de usabilidad y de decisión sobre hipótesis se reproducen en el documento [08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md](08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md), apartado 6. Se incorporan al expediente por remisión para evitar la duplicación de su texto y preservar una única fuente de verdad sobre su formato.

---

## Anexo C. Diagramas y modelos del sistema

### C.1 Arquitectura de capas

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA DE PRESENTACIÓN · CustomTkinter                                   │
│ LoginWindow · MainWindow · nueve módulos · atajos Ctrl+1 … Ctrl+9      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE SERVICIOS · reglas de negocio                                  │
│ auth · empleado · documento · incidencia · contrato · pago ·           │
│ configuración · académico · notas · token de sesión                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE REPOSITORIOS · patrón Repository sobre repositorio base        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE MODELOS · SQLAlchemy ORM · trece entidades                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ DOMINIO DE NÓMINA · cálculo aislado                                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ SERVICIOS TRANSVERSALES · seguridad, auditoría, respaldos y documentos │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ BASE DE DATOS · SQLite con integridad referencial y migraciones        │
└────────────────────────────────────────────────────────────────────────┘
```

*Fuente: elaboración propia a partir de la implementación en `src/`, versión 3.0.1.*

### C.2 Modelo entidad-relación

```text
empleados 1 ──── N documentos
empleados 1 ──── N incidencias
empleados 1 ──── N contratos
empleados 1 ──── N pagos
estudiantes 1 ── N matriculas N ── 1 grados
grados 1 ─────── N notas_finales
periodos_academicos 1 ── N matriculas
periodos_academicos 1 ── N notas_finales
configuraciones ─── parámetros del sistema
usuarios ───────── credenciales, rol y control de acceso
tokens_sesion ──── tokens de alcance académico
```

### C.3 Flujo de generación de nómina

```text
Inicio
  └─ Seleccionar periodo
      └─ Identificar empleados activos
          └─ Recuperar las incidencias aprobadas del periodo
              └─ Determinar días computables
                  └─ Calcular salario proporcional y horas extra con recargo
                      └─ Aplicar deducciones (seguridad social, pensión, ISR)
                          └─ Determinar salario neto
                              └─ Registrar pagos del periodo
                                  └─ Emitir recibos y planilla
                                      └─ Fin
```

### C.4 Flujo de autenticación y control de acceso

```text
Inicio
  └─ Ingresar usuario y contraseña
      └─ Verificar credenciales (PBKDF2-HMAC-SHA256, comparación en tiempo constante)
          ├─ Credenciales inválidas → registrar intento y rechazar
          └─ Credenciales válidas
              └─ Recuperar el rol del usuario
                  └─ Verificar permiso del rol sobre el módulo solicitado
                      ├─ Sin permiso → denegar y registrar el evento
                      └─ Con permiso → registrar el acceso y habilitar el módulo
                          └─ Fin
```

### C.5 Flujo de respaldo y restauración

```text
Inicio
  └─ Verificar la política de retención configurada
      └─ Crear copia con marca temporal única
          └─ Verificar la integridad de la copia
              └─ Registrar el evento en la auditoría
                  └─ Eliminar los respaldos que exceden la retención
                      └─ Restauración (a solicitud): validar, respaldar el estado
                         actual y reemplazar la base
                          └─ Fin
```

---

## Anexo D. Inventario del código y composición de la suite de pruebas

### D.1 Distribución del código por capa

| Capa o componente | Archivos | Líneas |
|-------------------|----------|--------|
| Presentación (`gui/`) | 10 | 11 598 |
| Servicios transversales (`utils/`) | 10 | 5 525 |
| Servicios de negocio (`services/`) | 11 | 4 332 |
| Repositorios (`repositories/`) | 16 | 2 383 |
| Modelos (`models/`) | 16 | 1 887 |
| Configuración (`config/`) | 3 | 1 706 |
| Dominio de nómina (`nomina/`) | 9 | 1 502 |
| Punto de entrada y raíz | 2 | 542 |
| **Total `src/`** | **77** | **29 475** |
| Agente de sincronización (`sync_agent/`) | 13 | 5 433 |

### D.2 Composición de la suite de pruebas

| Indicador | Valor |
|-----------|-------|
| Archivos de prueba | 32, más `conftest.py` |
| Funciones de prueba | 551 |
| Resultado de la ejecución del 6 de octubre de 2026 | 551 exitosas, 0 fallos, 0 errores (200 s) |
| Cobertura total | 56 % |
| Cobertura de `src/services` | 76 % |
| Cobertura de `src/nomina` | 89 % |
| Verificadores estáticos | `flake8`, `black --check`, `isort --check-only`, `mypy`: sin hallazgos |

### D.3 Cobertura verificada por área (composición de la suite)

| Área | Funciones de prueba |
|------|--------------------|
| Seguridad y credenciales | 80 |
| Validación y utilidades | 102 |
| Nómina y pagos | 35 |
| Personal y contratación | 33 |
| Documentos | 22 |
| Acceso y sesión | 16 |
| Configuración y esquema | 18 |
| Reportes y documentos PDF | 17 |
| Interfaz gráfica | 16 |
| Respaldo y actualización | 28 |
| Apariencia | 13 |
| Incidencias | 8 |
| Otras áreas no desglosadas en el corpus | 88 |
| **Total corpus académico 3.0.0** | **476** |

*Nota.* Las cifras de la tabla D.2 (551 funciones, cobertura del 56 % total, 76 % en servicios y 89 % en nómina) corresponden a la ejecución verificada sobre el repositorio vigente 3.0.1, registrada el 6 de octubre de 2026. La tabla D.3 reproduce el desglose por área declarado en el corpus académico 3.0.0, que suma 476 funciones. La diferencia entre ambos totales —75 funciones— corresponde al dominio académico y a la sincronización incorporados en la versión vigente. La cobertura debe re-medirse sobre la versión vigente conforme al pendiente declarado en el documento [01_INFORME_ESTADO_INVESTIGACION.md](01_INFORME_ESTADO_INVESTIGACION.md).

---

## Anexo E. Cuadro normativo

El cuadro normativo completo, con la identificación de cada norma, los artículos citados y su estado de verificación, se reproduce en el documento [03_BASES_LEGALES.md](03_BASES_LEGALES.md), apartado 11. Se incorpora por remisión para preservar una única fuente de verdad sobre su contenido.

---

## Anexo F. Presupuesto del proyecto

### F.1 Costos incurridos durante el desarrollo

| Concepto | Costo | Fuente de financiamiento |
|----------|-------|--------------------------|
| Tiempo del investigador | $0 | Recursos propios, no remunerados |
| Equipo de desarrollo | $0 | Equipo preexistente |
| Licencias de software | $0 | Componentes de código abierto |
| Material de oficina | $50 | Recursos propios |
| Impresión de documentación | $30 | Recursos propios |
| Transporte para visitas a instituciones | $500 | Recursos propios |
| **Total del desarrollo** | **$580** | |

### F.2 Costos anuales estimados de operación por institución

| Concepto | Costo anual | Fundamento |
|----------|-------------|------------|
| Licenciamiento de software | $0 | Todas las tecnologías son de código abierto |
| Servidor dedicado | $0 | Aplicación de instalación local |
| Actualizaciones de seguridad | $50 | Revisión periódica de dependencias |
| Soporte técnico externo | $0 | Soporte comunitario y documentación propia |
| Capacitación de nuevos usuarios | $200 | Sesiones de inducción y actualización |
| **Total anual estimado** | **$250** | |

---

## Anexo G. Glosario del expediente

Los términos técnicos se definen con extensión en el documento [05_BASES_TEORICAS.md](05_BASES_TEORICAS.md), apartado 9, y los de dominio en el documento [02_MARCO_TEORICO.md](02_MARCO_TEORICO.md), apartado 5. El glosario de siglas del expediente consta en el documento [00_INDICE_GENERAL_DEL_EXPEDIENTE.md](00_INDICE_GENERAL_DEL_EXPEDIENTE.md), apartado 5.3.

---

## Anexo H. Índice de tablas y figuras del expediente

### H.1 Tablas por documento

| Documento | Tablas principales |
|-----------|--------------------|
| 00 |Inventario de documentos, convenciones, glosario de siglas, estado de consolidación |
| 01 | Estado por componente, evidencia verificada, correspondencia de versiones, documentos del expediente, verificación de correspondencia |
| 02 | Correspondencia entre hallazgos y decisiones, glosario de términos |
| 03 | Jerarquía normativa, normativa técnica, trazabilidad norma–control, cuadro resumen normativo |
| 04 | Módulos en funcionamiento, procesos de operación, roles operativos, guía por módulo |
| 05 | Síntesis de fundamentos y decisiones, glosario técnico ampliado |
| 06 | Causas y medios, objetivos específicos, jerarquía del marco lógico, hipótesis, indicadores, coherencia, cuadro integrado |
| 07 | Procesos de operación, roles, presupuesto, costos de operación, análisis costo–beneficio |
| 08 | Instrumentos, hallazgos, matriz de avance, verificaciones, pendientes, plantillas |
| 09 | Matriz EML por niveles, operacionalización de variables, fichas de indicadores, supuestos, estado, versión compacta |
| 10 | Distribución del código, principios, esquema relacional, módulos, servicios, inventario de archivos |
| 11 | Datos generales, control de versiones, composición del expediente |
| 12 | Presentación de anexos, instrumentos, distribución del código, suite de pruebas, presupuesto |

### H.2 Figuras del expediente

| Figura | Título | Documento |
|--------|--------|-----------|
| 2.1 | Modelo conceptual por capas del sistema | 02 y 12 (C.1) |
| Ley | Jerarquía del ordenamiento aplicable | 03 |
| Arch. | Arquitectura del sistema | 10 |
| ER | Modelo entidad-relación | 02, 10 y 12 (C.2) |
| Nómina | Flujo de generación de nómina | 12 (C.3) |
| Acceso | Flujo de autenticación y control de acceso | 12 (C.4) |
| Respaldo | Flujo de respaldo y restauración | 12 (C.5) |
| Portada | Fórmula de portada y firmas | 11 |

---

## Cierre de los anexos

Los anexos precedentes completan el expediente y hacen que cada afirmación de los documentos principales disponga de su soporte en el propio conjunto. Los instrumentos permiten replicar la recolección de datos; los diagramas reproducen la estructura del sistema; el inventario del código y de la suite hace verificable la magnitud del producto; el cuadro normativo concentra la correspondencia legal; el presupuesto respalda la justificación económica; y los índices permiten localizar cada elemento del expediente sin recorrerlo íntegro.

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]

**Institución**
[Nombre de la Universidad o Instituto]
