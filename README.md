## FortiGate Firewall Policy Audit (API + Python)

Este repo salió de una situación bastante común: nos piden “limpiar” reglas de firewall en un entorno grande, pero no tenemos una herramienta de auditoría/hitcount a mano.

Cuando hay varios firewalls en producción y cientos de policies, revisar una por una es lento y propenso a errores

La idea acá fue armar algo simple y útil:
- Sacar **estadísticas de uso** (bytes/packets/first-used/last-used) desde el endpoint *monitor*
- Sacar la **configuración** (nombre, src/dst, interfaces, services, enable/disable, etc.) desde el endpoint *cmdb*
- Unir todo por `policy_id` y generar salidas fáciles de revisar (CSV + reporte en PDF)

---

## Qué hace

1) Consulta FortiGate vía API:
- `.../api/v2/monitor/firewall/policy` → stats por policy
- `.../api/v2/cmdb/firewall/policy` → configuración de policies

2) Genera:
- `output_monitor.csv` (stats)
- `output_cmdb.csv` (config)
- `pre_final.csv` (merge por `policy_id`)
- `policy_audit_report.pdf` (reporte con secciones)

---

## Estructura del proyecto

```
- **audit.py**: runner principal. Llama a monitor + cmdb, hace el merge y genera los CSVs (`output_monitor.csv`, `output_cmdb.csv`, `pre_final.csv`).
- **fg_audit/env.py**: carga variables desde `.env` y valida que existan las claves necesarias.
- **fg_audit/client.py**: cliente HTTP para FortiGate (maneja base URL, token, params, errores).
- **fg_audit/monitor.py**: consulta el endpoint *monitor* y normaliza stats por policy (bytes/packets/first_used/last_used).
- **fg_audit/cmdb.py**: consulta el endpoint *cmdb* y normaliza la configuración (name, src/dst, interfaces, services, status, etc.).
- **fg_audit/merge.py**: une (join) monitor + cmdb por `policy_id` para armar el `pre_final.csv`.
- **fg_audit/output.py**: utilidades de salida (imprimir tablas en consola y exportar CSV).
- **fg_audit/utils.py**: helpers generales (por ejemplo conversión/format de timestamps).
- **report_from_prefinal.py**: genera el PDF final leyendo `pre_final.csv` (tráfico vs no tráfico + reglas potencialmente permisivas).

````

## Requisitos

- Python 3.10+ recomendado
- Paquetes:
  - `requests`
  - `pandas`
  - `reportlab`

Instalación rápida:
```bash
pip install requests pandas reportlab
````

---

## Configuración

Crea un archivo `.env` en la raíz (NO se sube al repo). Tienes un ejemplo en `.env.example`.

Ejemplo mínimo:

```env
FORTIGATE_BASE_URL=http://192.168.1.166
FORTIGATE_TOKEN=PUT_YOUR_TOKEN_HERE
FORTIGATE_VDOM=root
TIMEZONE=Europe/Madrid
VERIFY_SSL=false

OUT_CSV_MONITOR=output_monitor.csv
OUT_CSV_CMDB=output_cmdb.csv
OUT_CSV_MERGED=pre_final.csv
```

> Si se usa HTTPS con certificado self-signed, deja `VERIFY_SSL=false`.

---

## Uso

1. Generar CSVs y el merge:

```bash
python audit.py
```

2. Generar el PDF desde el `pre_final.csv`:

```bash
python report_from_prefinal.py
```

---

## Criterios del reporte

* **Policies sin tráfico:** `bytes == 0`
* **Policies potencialmente permisivas:** si `srcaddr` o `dstaddr` o `services` contiene `all`
* **Excepción:** `policy_id = 0` (implícita/sistema) NO se marca como “permisiva”

Esto no significa que una regla sea “mala” automáticamente; solo la deja marcada para revisión del administrador.

---

## Ideas para mejorar

* Resolver `service -> puertos` (ej: HTTP=80, HTTPS=443, etc.)
* Ventana “sin uso hace N días” (comparando `last_used`)
* Clasificación por tipo de riesgo (muy simple, pero útil para priorizar)

---

