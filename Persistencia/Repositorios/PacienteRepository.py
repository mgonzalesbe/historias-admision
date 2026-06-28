from datetime import date
from typing import List, Optional

from Dominio.Entidades.Paciente import Paciente
from Dominio.Interfaces.IPacienteRepository import IPacienteRepository
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection


class PacienteRepository(IPacienteRepository):
    _SELECT_COLS = """
        IdPaciente, NumeroHistoriaClinica, DNI, NombreCompleto,
        FechaNacimiento, Direccion, NombrePadre, NombreMadre, Activo
    """

    def __init__(self):
        self.db = DatabaseConnection.get_instance()

    def _map_to_entity(self, row) -> Paciente:
        return Paciente(
            id=row[0],
            numero_historia_clinica=row[1],
            dni=row[2],
            nombre_completo=row[3],
            fecha_nacimiento=row[4],
            direccion=row[5],
            nombre_padre=row[6],
            nombre_madre=row[7],
            activo=bool(row[8]),
        )

    def get_by_id(self, id: int) -> Optional[Paciente]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {self._SELECT_COLS} FROM Pacientes WHERE IdPaciente = ? AND Activo = 1",
            id,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def search(
        self, termino: str, tipo: str = "nombre", limite: int = 100
    ) -> List[Paciente]:
        termino = (termino or "").strip()
        if not termino:
            return []

        limite = max(1, min(limite, 200))
        like = f"%{termino}%"
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if tipo == "dni":
            sql = f"""
                SELECT TOP (?) {self._SELECT_COLS}
                FROM Pacientes
                WHERE Activo = 1 AND DNI LIKE ?
                ORDER BY NombreCompleto
            """
            params = (limite, like)
        elif tipo == "historia":
            sql = f"""
                SELECT TOP (?) {self._SELECT_COLS}
                FROM Pacientes
                WHERE Activo = 1 AND NumeroHistoriaClinica LIKE ?
                ORDER BY NumeroHistoriaClinica, NombreCompleto
            """
            params = (limite, like)
        else:
            sql = f"""
                SELECT TOP (?) {self._SELECT_COLS}
                FROM Pacientes
                WHERE Activo = 1 AND NombreCompleto LIKE ?
                ORDER BY NombreCompleto
            """
            params = (limite, like)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def create(self, paciente: Paciente) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Pacientes (
                NumeroHistoriaClinica, DNI, NombreCompleto, FechaNacimiento,
                Direccion, NombrePadre, NombreMadre
            )
            OUTPUT INSERTED.IdPaciente
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paciente.numero_historia_clinica,
                paciente.dni,
                paciente.nombre_completo,
                paciente.fecha_nacimiento,
                paciente.direccion,
                paciente.nombre_padre,
                paciente.nombre_madre,
            ),
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return int(new_id)

    def update(self, paciente: Paciente) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Pacientes SET
                NumeroHistoriaClinica = ?,
                DNI = ?,
                NombreCompleto = ?,
                FechaNacimiento = ?,
                Direccion = ?,
                NombrePadre = ?,
                NombreMadre = ?
            WHERE IdPaciente = ? AND Activo = 1
            """,
            (
                paciente.numero_historia_clinica,
                paciente.dni,
                paciente.nombre_completo,
                paciente.fecha_nacimiento,
                paciente.direccion,
                paciente.nombre_padre,
                paciente.nombre_madre,
                paciente.id,
            ),
        )
        conn.commit()
        cursor.close()
        return True

    def delete(self, id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Pacientes SET Activo = 0 WHERE IdPaciente = ?",
            id,
        )
        conn.commit()
        cursor.close()
        return True

    def count_all(self) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Pacientes WHERE Activo = 1")
        total = cursor.fetchone()[0]
        cursor.close()
        return int(total)

    def bulk_insert(self, pacientes: List[Paciente], batch_size: int = 500) -> int:
        if not pacientes:
            return 0

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.fast_executemany = True
        insertados = 0
        sql = """
            INSERT INTO Pacientes (
                NumeroHistoriaClinica, DNI, NombreCompleto, FechaNacimiento,
                Direccion, NombrePadre, NombreMadre
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        for i in range(0, len(pacientes), batch_size):
            lote = pacientes[i : i + batch_size]
            cursor.executemany(
                sql,
                [
                    (
                        p.numero_historia_clinica,
                        p.dni,
                        p.nombre_completo,
                        p.fecha_nacimiento,
                        p.direccion,
                        p.nombre_padre,
                        p.nombre_madre,
                    )
                    for p in lote
                ],
            )
            conn.commit()
            insertados += len(lote)
            print(f"  Insertados {insertados}/{len(pacientes)}...", flush=True)
        cursor.close()
        return insertados
