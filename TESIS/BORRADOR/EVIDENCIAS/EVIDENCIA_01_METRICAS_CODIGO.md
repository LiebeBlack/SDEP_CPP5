# EVIDENCIA 01 — MÉTRICAS DEL CÓDIGO FUENTE

**Fecha de la medición:** 23/11/2026
**Objeto:** revisión local del repositorio disponible el 23/11/2026. El archivo `VERSION` declara `3.0.1`, pero este árbol contiene cambios Android posteriores aún no asociados aquí a un tag o commit de distribución.
**Método:** conteo de líneas Python por capa y `sync_agent/`; las métricas Android vigentes se actualizan en la evidencia 06. Los comandos son reproducibles sobre el mismo estado del árbol.

## 1. Verificación de la versión

```text
$ cat VERSION
3.0.1
```

## 2. Líneas por capa del sistema (directorio src/)

| Capa | Líneas | Función |
|------|--------|---------|
| `src/config` | 1.719 | Configuración, rutas y sesión de base de datos |
| `src/gui` | 14.701 | Interfaz gráfica: ventanas, módulos, tema y widgets |
| `src/models` | 1.987 | Entidades del dominio y enumeraciones |
| `src/nomina` | 1.513 | Motor de cálculo, prestaciones, ISR y seguridad social |
| `src/repositories` | 2.692 | Acceso a datos (patrón Repositorio) |
| `src/services` | 5.512 | Reglas de negocio (capa de servicios) |
| `src/utils` | 6.457 | Seguridad, auditoría, respaldos, PDF y utilerías |
| **Total `src/`** | **35.797** | — |

## 3. Componentes entregados adicionales

| Componente | Medición | Función |
|-----------|----------|---------|
| `sync_agent/` | 11.443 líneas Python | Nodo central de sincronización entre puestos: descubrimiento UDP, captura de cambios, fusión, servidor embebido y CLI |
| `android/` | Véase la re-medición vigente en `EVIDENCIAS/EVIDENCIA_06_INVENTARIO_ANDROID.md` | Cliente móvil nativo SDEP Móvil; este legajo no conserva métricas Android vigentes |

## 4. Reproducción de la medición

```text
# Total por capa (salida de find + wc -l por directorio)
$ find src/config -name "*.py" | xargs wc -l | tail -1    → 1719 total
$ find src/gui -name "*.py" | xargs wc -l | tail -1       → 14701 total
$ find src/models -name "*.py" | xargs wc -l | tail -1    → 1987 total
$ find src/nomina -name "*.py" | xargs wc -l | tail -1    → 1513 total
$ find src/repositories -name "*.py" | xargs wc -l | tail -1 → 2692 total
$ find src/services -name "*.py" | xargs wc -l | tail -1  → 5512 total
$ find src/utils -name "*.py" | xargs wc -l | tail -1     → 6457 total
$ find src -name "*.py" | xargs wc -l | tail -1           → 35797 total

# Componentes independientes
$ find sync_agent -name "*.py" | xargs wc -l | tail -1    → 11443 total
# Métricas Android vigentes, que incluyen cambios locales posteriores:
$ find android -name "*.kt" | wc -l                       → 97
$ find android -name "*.kt" | xargs wc -l | tail -1       → 22539 total
```

## 5. Nota de concordancia documental

El total Python de `src/` (35.797 líneas) y el de `sync_agent/` (11.443 líneas) se conservan como conteos del árbol inspeccionado. El cliente Android se recontó tras nuevos cambios y se documenta en la evidencia 06; no debe describirse como métrica del tag 3.0.1 sin identificar la revisión exacta. Los conteos no demuestran compilación, calidad de pruebas o cumplimiento funcional.

**Observador:** investigador del proyecto, con supervisión del tutor.
