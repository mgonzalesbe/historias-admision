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
import sys
from datetime import datetime, timedelta
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

# Grupo experimental (GE): tiempo (s), caracteres, cantidad generada
GE_DATA = [
    (14.66, 11, 3),
    (22.4, 10, 1),
    (9.1, 10, 2),
    (18.4, 12, 3),
    (11.52, 12, 4),
    (6.07, 11, 2),
    (14.35, 10, 1),
    (9.45, 10, 3),
    (9.55, 12, 1),
    (15.67, 12, 2),
    (9.28, 10, 4),
    (14.48, 10, 3),
    (16.58, 12, 1),
    (11.49, 12, 4),
    (15.84, 12, 4),
    (9.2, 10, 3),
    (12.78, 10, 2),
    (23.12, 13, 1),
    (11.81, 10, 2),
    (28.34, 12, 4),
    (16.21, 12, 1),
    (24.79, 10, 3),
    (6.91, 12, 1),
    (6.76, 10, 3),
    (12.69, 10, 3),
    (6.93, 13, 1),
    (24.6, 12, 3),
    (26.45, 10, 2),
    (19.09, 12, 4),
    (13.77, 10, 4),
]


def strength_label_for_length(length: int) -> str:
    if length >= 12:
        return "Fuerte"
    if length >= 10:
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


def insert_metrics_for_user(
    cursor,
    user_id: int,
    time_seconds: float,
    password_length: int,
    password_count: int,
    base_time: datetime,
) -> int:
    strength = strength_label_for_length(password_length)
    time_ms = int(round(time_seconds * 1000))
    inserted = 0

    for i in range(password_count):
        created_at = base_time - timedelta(minutes=(password_count - i) * 5)
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
    base_time = datetime.utcnow()

    for idx, user in enumerate(users):
        user_id, username, nombre, rol = user
        time_s, length, count = GE_DATA[idx]
        plan.append(
            {
                "ge_row": idx + 1,
                "user_id": user_id,
                "username": username,
                "nombre": nombre,
                "rol": rol,
                "time_s": time_s,
                "length": length,
                "count": count,
            }
        )

    print("\nPlan de asignación (GE -> usuario):\n")
    print(f"{'GE':>3}  {'Usuario':<18} {'Nombre':<28} {'#Pwd':>4} {'Chars':>5} {'Tiempo':>7}")
    print("-" * 78)
    for row in plan:
        print(
            f"{row['ge_row']:>3}  {row['username']:<18} "
            f"{(row['nombre'] or '')[:28]:<28} {row['count']:>4} "
            f"{row['length']:>5} {row['time_s']:>6.2f}s"
        )

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
            base_time,
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
