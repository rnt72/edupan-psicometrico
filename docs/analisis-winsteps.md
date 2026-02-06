# Módulo de Análisis y Exportación Winsteps

## Descripción General

Se creó el módulo **Análisis** (`core/responses/`) para capturar respuestas de exámenes aplicados y generar un archivo `.txt` compatible con **Winsteps** (software de análisis psicométrico basado en el modelo Rasch).

El archivo exportado contiene **una línea por alumno**, donde cada carácter representa la puntuación de un ítem:
- **Dicotómico (D):** `0` = incorrecto, `1` = correcto
- **Politómico (P):** `0` = incorrecto, `1` = parcialmente correcto, `2` = correcto

Ejemplo de salida para un examen con 3 ítems (P, D, D):
```
100
210
201
```

---

## Modelos Creados (`core/responses/models.py`)

### `ExamApplication`
Representa una sesión de aplicación de un examen (ej: "Aplicación Marzo 2026").

| Campo        | Tipo                  | Descripción                                |
|--------------|-----------------------|--------------------------------------------|
| `exam`       | FK → `Exam`           | Examen asociado                            |
| `name`       | CharField(255)        | Nombre de la aplicación                    |
| `created_by` | FK → `User`           | Usuario que creó la aplicación             |
| `created_at` | DateTimeField         | Fecha de creación (auto)                   |

- **unique_together:** `[exam, name]`

### `ResponseRow`
Fila de respuestas — un alumno anónimo identificado solo por número secuencial. **No se manejan datos de estudiantes** (nombres, cédulas, etc.); cada fila es simplemente "Alumno 1", "Alumno 2", etc.

| Campo         | Tipo                      | Descripción                     |
|---------------|---------------------------|---------------------------------|
| `application` | FK → `ExamApplication`    | Aplicación a la que pertenece   |
| `row_number`  | PositiveIntegerField      | Número secuencial del alumno    |

- **unique_together:** `[application, row_number]`

### `Response`
Respuesta individual: qué opción eligió un alumno en una subpregunta.

| Campo             | Tipo                  | Descripción                                    |
|-------------------|-----------------------|------------------------------------------------|
| `row`             | FK → `ResponseRow`    | Fila/Alumno                                    |
| `subquestion`     | FK → `SubQuestion`    | Subpregunta respondida                         |
| `selected_option` | FK → `Option` (null)  | Opción seleccionada                            |
| `is_correct`      | BooleanField          | Auto-calculado en `save()` según `Option.is_correct` |

- **unique_together:** `[row, subquestion]`
- El método `save()` auto-computa `is_correct` y asegura que se persiste incluso en `update_or_create`.

### `ItemScore`
Puntuación directa a nivel de ítem. Se usa para:
- Preguntas abiertas (sin opciones) donde el digitador asigna 0/1/2 manualmente.
- Override: se puede ajustar la puntuación incluso si hay opciones seleccionadas.

| Campo   | Tipo                  | Descripción                                        |
|---------|-----------------------|----------------------------------------------------|
| `row`   | FK → `ResponseRow`    | Fila/Alumno                                        |
| `item`  | FK → `Item`           | Ítem evaluado                                      |
| `score` | PositiveIntegerField  | 0=Incorrecta, 1=Parcial (o Correcta si D), 2=Correcta |

- **unique_together:** `[row, item]`

---

## Relación entre Modelos

```
ExamApplication
  └── ResponseRow (Alumno 1, 2, 3...)
        ├── Response (subpregunta → opción seleccionada)
        └── ItemScore (ítem → puntuación directa 0/1/2)
```

---

## Flujo de Captura

1. **Dashboard** (`/analysis/`): El usuario ve los exámenes activos con sus aplicaciones existentes.
2. **Crear aplicación**: Se ingresa nombre y cantidad de alumnos → se crean las `ResponseRow` en lote.
3. **Captura por alumno**: Se muestra el examen completo (ítems, subpreguntas, opciones) y el digitador:
   - **Selecciona opciones** en las subpreguntas con opciones → se guarda `Response` vía AJAX y se auto-calcula `ItemScore`.
   - **Asigna puntaje directo** (0/1/2) en la cabecera del ítem → se guarda `ItemScore` vía AJAX. Esto es especialmente útil para preguntas abiertas.
4. **Navegación**: Botones Anterior/Siguiente y selector de alumno para moverse entre filas.
5. **Agregar alumno**: Botón "+ Alumno" que crea una nueva `ResponseRow` al final.

### Sobre los Estudiantes

- **No se maneja información personal de estudiantes.** Los alumnos son filas anónimas numeradas (Alumno 1, Alumno 2, etc.).
- No hay CRUD de estudiantes — solo se define la cantidad al crear la aplicación y se pueden agregar más durante la captura.
- El digitador es quien captura las respuestas; el alumno no interactúa directamente con el sistema.

---

## Cálculo de Puntuación por Ítem

Cada **ítem** (no subpregunta) genera un solo dígito en la cadena Winsteps:

### Automático (al seleccionar opciones)
- **Dicotómico (D):** Todas las subpreguntas correctas → `1`, cualquier incorrecta → `0`
- **Politómico (P):** Todas correctas → `2`, algunas correctas → `1`, ninguna correcta → `0`

### Manual (puntuación directa)
- El digitador puede asignar directamente 0/1 (dicotómico) o 0/1/2 (politómico) desde los botones en la cabecera del ítem.
- Los criterios de calificación del ítem (`correct_criteria`, `partial_criteria`, `incorrect_criteria`) se muestran como guía.

### Prioridad en la Exportación
`ItemScore` tiene **prioridad** sobre el cálculo automático: si existe un `ItemScore` para un ítem/alumno, se usa ese valor; si no, se calcula desde las `Response` de sus subpreguntas.

---

## Exportación (`/analysis/application/<pk>/export/`)

Genera un archivo `.txt` descargable:

1. Se obtienen los ítems del examen ordenados por `order`.
2. Para cada alumno (fila), se construye una cadena:
   - Si existe `ItemScore` → usar ese `score`.
   - Si no → calcular desde las respuestas de las subpreguntas.
3. El archivo contiene una línea por alumno, sin cabeceras ni delimitadores.

**Nombre del archivo:** `winsteps_{nombre_examen}_{nombre_aplicacion}.txt`

---

## Archivos Modificados/Creados

| Archivo | Acción |
|---------|--------|
| `core/responses/models.py` | Creado — 4 modelos |
| `core/responses/views.py` | Creado — 8 vistas (dashboard, create, capture, 3 APIs, export, delete) |
| `core/responses/urls.py` | Creado — 9 rutas |
| `core/responses/admin.py` | Creado — registro de los 4 modelos en admin |
| `core/responses/apps.py` | Creado — AppConfig |
| `core/responses/migrations/0001_initial.py` | Migración: ExamApplication, ResponseRow, Response |
| `core/responses/migrations/0002_itemscore.py` | Migración: ItemScore |
| `core/templates/pages/analysis-dashboard.html` | Creado — listado de exámenes y aplicaciones |
| `core/templates/pages/application-create.html` | Creado — formulario de nueva aplicación |
| `core/templates/pages/response-capture.html` | Creado — interfaz de captura estilo examen |
| `core/templates/partials/main-nav.html` | Modificado — enlace "Análisis" en sidebar |
| `config/settings/base.py` | Modificado — `core.responses` agregado a `LOCAL_APPS` |
| `config/urls.py` | Modificado — ruta `analysis/` incluida |

---

## URLs del Módulo

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/analysis/` | `AnalysisDashboardView` | Dashboard principal |
| `/analysis/application/create/<exam_pk>/` | `ApplicationCreateView` | Crear aplicación |
| `/analysis/application/<pk>/capture/` | `ResponseCaptureView` | Redirige al primer alumno |
| `/analysis/application/<pk>/capture/<row_pk>/` | `ResponseCaptureView` | Captura para un alumno |
| `/analysis/application/<pk>/export/` | `WinstepsExportView` | Descargar TXT |
| `/analysis/application/<pk>/delete/` | `ApplicationDeleteView` | Eliminar aplicación |
| `/analysis/application/<pk>/api/save-response/` | `SaveResponseAPI` | AJAX: guardar opción |
| `/analysis/application/<pk>/api/save-item-score/` | `SaveItemScoreAPI` | AJAX: guardar puntaje directo |
| `/analysis/application/<pk>/api/add-row/` | `AddRowAPI` | AJAX: agregar alumno |
| `/analysis/application/<pk>/api/delete-row/` | `DeleteRowAPI` | AJAX: eliminar último alumno |
