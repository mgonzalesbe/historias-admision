"""
Carga métricas de contraseña del grupo experimental (GE) en Azure SQL.

Uso (desde la raíz del proyecto, con .env apuntando a Azure):
  python scripts/seed_metricas_grupo_experimental.py
  python scripts/seed_metricas_grupo_experimental.py --dry-run

Asigna fila GE #1 al primer usuario (admission), #2 al segundo, etc.
Excluye usuarios con rol admin.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from Persistencia.Conexion.DatabaseConnection import DatabaseConnection

# Cuadro de tesis (GE) por fila N° 1..30.
# En el cuadro el orden de indicadores es: I1, I2, I3.
# En la app el orden de columnas es al revés: I3, I2, I1.
#
#   Cuadro (GE)              →  Columna en la app
#   I1 tiempo (segundos)     →  Tiempo de generación (último)
#   I2 caracteres            →  Caracteres (última contraseña)
#   I3 cantidad              →  Contraseñas generadas
GE_DATA = [
    {"i1_tiempo_s": 14.66, "i2_caracteres": 9, "i3_cantidad": 3},
    {"i1_tiempo_s": 22.4, "i2_caracteres": 9, "i3_cantidad": 1},
    {"i1_tiempo_s": 9.1, "i2_caracteres": 9, "i3_cantidad": 2},
    {"i1_tiempo_s": 18.4, "i2_caracteres": 12, "i3_cantidad": 3},
    {"i1_tiempo_s": 11.52, "i2_caracteres": 12, "i3_cantidad": 4},
    {"i1_tiempo_s": 6.07, "i2_caracteres": 9, "i3_cantidad": 2},
    {"i1_tiempo_s": 14.35, "i2_caracteres": 9, "i3_cantidad": 1},
    {"i1_tiempo_s": 9.45, "i2_caracteres": 9, "i3_cantidad": 3},
    {"i1_tiempo_s": 9.55, "i2_caracteres": 12, "i3_cantidad": 1},
    {"i1_tiempo_s": 15.67, "i2_caracteres": 12, "i3_cantidad": 2},
    {"i1_tiempo_s": 9.28, "i2_caracteres": 9, "i3_cantidad": 4},
    {"i1_tiempo_s": 14.48, "i2_caracteres": 9, "i3_cantidad": 3},
    {"i1_tiempo_s": 16.58, "i2_caracteres": 12, "i3_cantidad": 1},
    {"i1_tiempo_s": 11.49, "i2_caracteres": 12, "i3_cantidad": 4},
    {"i1_tiempo_s": 15.84, "i2_caracteres": 12, "i3_cantidad": 4},
    {"i1_tiempo_s": 9.2, "i2_caracteres": 9, "i3_cantidad": 3},
    {"i1_tiempo_s": 12.78, "i2_caracteres": 9, "i3_cantidad": 2},
    {"i1_tiempo_s": 23.12, "i2_caracteres": 13, "i3_cantidad": 1},
    {"i1_tiempo_s": 11.81, "i2_caracteres": 9, "i3_cantidad": 2},
    {"i1_tiempo_s": 28.34, "i2_caracteres": 12, "i3_cantidad": 4},
    {"i1_tiempo_s": 16.21, "i2_caracteres": 12, "i3_cantidad": 1},
    {"i1_tiempo_s": 24.79, "i2_caracteres": 9, "i3_cantidad": 3},
    {"i1_tiempo_s": 6.91, "i2_caracteres": 12, "i3_cantidad": 1},
    {"i1_tiempo_s": 6.76, "i2_caracteres": 9, "i3_cantidad": 3},
    {"i1_tiempo_s": 12.69, "i2_caracteres": 9, "i3_cantidad": 3},
    {"i1_tiempo_s": 6.93, "i2_caracteres": 13, "i3_cantidad": 1},
    {"i1_tiempo_s": 24.6, "i2_caracteres": 12, "i3_cantidad": 3},
    {"i1_tiempo_s": 26.45, "i2_caracteres": 9, "i3_cantidad": 2},
    {"i1_tiempo_s": 19.09, "i2_caracteres": 12, "i3_cantidad": 4},
    {"i1_tiempo_s": 13.77, "i2_caracteres": 9, "i3_cantidad": 4},
]

# 15 días con actividad dentro de los últimos 35 (el resto sin registros).
WINDOW_DAYS = 35
ACTIVE_DAYS = 15
RANDOM_SEED = 2026
ACTIVE_DAY_OFFSETS: list[int] = []


def build_active_day_offsets() -> list[int]:
    rng = random.Random(RANDOM_SEED)
    return sorted(rng.sample(range(1, WINDOW_DAYS + 1), ACTIVE_DAYS))


def strength_label_for_length(length: int) -> str:
    if length >= 12:
        return "Fuerte"
    if length >= 9:
        return "Regular"
    return "Fragil"


def fetch_target_users(cursor):
    cursor.execute(
        """
        SELECT IdUsuario, NombreUsuario, NombreCompleto, Rol
        FROM Usuarios
        WHERE Rol <> 'admin'
        ORDER BY IdUsuario ASC
        """
    )
    return cursor.fetchall()


def delete_metrics_for_users(cursor, user_ids: list[int]) -> int:
    if not user_ids:
        return 0
    placeholders = ",".join("?" for _ in user_ids)
    cursor.execute(
        f"DELETE FROM MetricasContrasena WHERE IdUsuario IN ({placeholders})",
        user_ids,
    )
    return cursor.rowcount


def build_metric_timestamps(user_index: int, password_count: int, end_utc: datetime) -> list[datetime]:
    """Fechas aleatorias en 15 días activos dentro de los últimos 35."""
    if password_count <= 0:
        return []

    rng = random.Random(RANDOM_SEED + user_index * 997)
    pool = ACTIVE_DAY_OFFSETS[:]
    rng.shuffle(pool)

    offsets: list[int] = []
    for i in range(password_count):
        offsets.append(rng.choice(pool if pool else ACTIVE_DAY_OFFSETS))

    timestamps: list[datetime] = []
    for days_ago in offsets:
        hour = rng.randint(8, 20)
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        timestamps.append(
            end_utc - timedelta(days=days_ago, hours=hour, minutes=minute, seconds=second)
        )

    timestamps.sort()
    return timestamps


def insert_metrics_for_user(
    cursor,
    user_id: int,
    time_seconds: float,
    password_length: int,
    password_count: int,
    created_times: list[datetime],
) -> int:
    strength = strength_label_for_length(password_length)
    time_ms = int(round(time_seconds * 1000))
    inserted = 0

    for created_at in created_times:
        cursor.execute(
            """
            INSERT INTO MetricasContrasena
                (IdUsuario, LongitudContrasena, TiempoGeneracionMs, NivelFortaleza, FechaCreacion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, password_length, time_ms, strength, created_at),
        )
        inserted += 1
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Sembrar métricas GE en MetricasContrasena")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra el plan sin escribir en la base de datos",
    )
    parser.add_argument(
        "--include-admin",
        action="store_true",
        help="Incluir usuarios admin (por defecto se excluyen)",
    )
    args = parser.parse_args()

    global ACTIVE_DAY_OFFSETS
    ACTIVE_DAY_OFFSETS = build_active_day_offsets()

    db = DatabaseConnection.get_instance()
    conn = db.get_connection()
    cursor = conn.cursor()

    if args.include_admin:
        cursor.execute(
            """
            SELECT IdUsuario, NombreUsuario, NombreCompleto, Rol
            FROM Usuarios
            ORDER BY IdUsuario ASC
            """
        )
        users = cursor.fetchall()
    else:
        users = fetch_target_users(cursor)

    if not users:
        print("No hay usuarios para actualizar.")
        cursor.close()
        return 1

    if len(users) > len(GE_DATA):
        print(
            f"ADVERTENCIA: hay {len(users)} usuarios pero solo {len(GE_DATA)} filas GE. "
            f"Se usarán las primeras {len(GE_DATA)} filas GE."
        )
        users = users[: len(GE_DATA)]
    elif len(users) < len(GE_DATA):
        print(
            f"INFO: hay {len(users)} usuarios; se usarán las primeras {len(users)} filas GE "
            f"(de {len(GE_DATA)} disponibles)."
        )

    user_ids = [int(row[0]) for row in users]
    plan = []
    end_utc = datetime.now(UTC).replace(tzinfo=None)

    for idx, user in enumerate(users):
        user_id, username, nombre, rol = user
        ge = GE_DATA[idx]
        created_times = build_metric_timestamps(idx, ge["i3_cantidad"], end_utc)
        last_at = created_times[-1] if created_times else None
        plan.append(
            {
                "ge_row": idx + 1,
                "user_id": user_id,
                "username": username,
                "nombre": nombre,
                "rol": rol,
                "time_s": ge["i1_tiempo_s"],
                "length": ge["i2_caracteres"],
                "count": ge["i3_cantidad"],
                "created_times": created_times,
                "last_at": last_at,
            }
        )

    print("\nMapeo cuadro GE -> columnas de la app (orden de la tabla web):\n")
    print("  I3 cantidad (cuadro)  ->  Contraseñas generadas")
    print("  I2 caracteres (cuadro) ->  Caracteres (última contraseña)")
    print("  I1 tiempo (cuadro)    ->  Tiempo de generación (último)\n")

    print(
        f"Ventana de fechas: últimos {WINDOW_DAYS} días, "
        f"{ACTIVE_DAYS} días con actividad (resto sin registros).\n"
    )

    print("Plan de asignación (fila GE N° -> usuario, columnas como en la app):\n")
    print(
        f"{'GE':>3}  {'Usuario':<14} {'Pwd':>3} {'Chr':>3} {'T(s)':>6}  {'Último registro (UTC)':>20}"
    )
    print("-" * 62)
    for row in plan:
        last_label = row["last_at"].strftime("%d/%m/%Y %H:%M") if row["last_at"] else "-"
        print(
            f"{row['ge_row']:>3}  {row['username']:<14} {row['count']:>3} {row['length']:>3} "
            f"{row['time_s']:>6.2f}  {last_label:>20}"
        )

    day_usage: dict[str, int] = {}
    for row in plan:
        for ts in row["created_times"]:
            key = ts.strftime("%Y-%m-%d")
            day_usage[key] = day_usage.get(key, 0) + 1
    print(f"\nDías con registros en el lote: {len(day_usage)} / {WINDOW_DAYS}")
    print(f"Días activos usados: {', '.join(str(d) for d in ACTIVE_DAY_OFFSETS)}")

    if args.dry_run:
        print("\n[dry-run] No se modificó la base de datos.")
        cursor.close()
        return 0

    deleted = delete_metrics_for_users(cursor, user_ids)
    total_inserted = 0
    for row in plan:
        total_inserted += insert_metrics_for_user(
            cursor,
            row["user_id"],
            row["time_s"],
            row["length"],
            row["count"],
            row["created_times"],
        )

    conn.commit()
    cursor.close()

    print(f"\nListo.")
    print(f"  Métricas eliminadas (usuarios objetivo): {deleted}")
    print(f"  Métricas insertadas: {total_inserted}")
    print(f"  Usuarios actualizados: {len(plan)}")
    print("\nRevisa en la app: Admin -> Métricas Password -> Métricas por usuario")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
