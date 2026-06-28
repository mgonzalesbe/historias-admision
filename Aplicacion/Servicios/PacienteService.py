from datetime import date, datetime
from typing import Any, Optional

from Dominio.Entidades.Paciente import Paciente
from Persistencia.Repositorios.PacienteRepository import PacienteRepository


class PacienteService:
    def __init__(self):
        self.repo = PacienteRepository()

    @staticmethod
    def _parse_fecha(valor: Any) -> Optional[date]:
        if valor is None or valor == "":
            return None
        if isinstance(valor, date) and not isinstance(valor, datetime):
            return valor
        if isinstance(valor, datetime):
            return valor.date()
        texto = str(valor).strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(texto[:10], fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _to_dict(p: Paciente) -> dict:
        return {
            "id": p.id,
            "numero_historia_clinica": p.numero_historia_clinica,
            "dni": p.dni or "",
            "nombre_completo": p.nombre_completo,
            "fecha_nacimiento": (
                p.fecha_nacimiento.strftime("%d/%m/%Y") if p.fecha_nacimiento else ""
            ),
            "direccion": p.direccion or "",
            "nombre_padre": p.nombre_padre or "",
            "nombre_madre": p.nombre_madre or "",
        }

    def buscar(self, termino: str, tipo: str = "nombre") -> list[dict]:
        tipo = (tipo or "nombre").lower()
        if tipo not in ("dni", "nombre", "historia"):
            tipo = "nombre"
        resultados = self.repo.search(termino, tipo=tipo)
        return [self._to_dict(p) for p in resultados]

    def obtener(self, paciente_id: int) -> Optional[dict]:
        paciente = self.repo.get_by_id(paciente_id)
        return self._to_dict(paciente) if paciente else None

    def _validar_campos(
        self,
        numero_historia_clinica: str,
        nombre_completo: str,
    ) -> None:
        if not (numero_historia_clinica or "").strip():
            raise ValueError("El número de historia clínica es obligatorio.")
        if not (nombre_completo or "").strip():
            raise ValueError("Apellidos y nombres es obligatorio.")

    def crear(self, data: dict) -> dict:
        numero_hc = (data.get("numero_historia_clinica") or "").strip()
        nombre = (data.get("nombre_completo") or "").strip()
        self._validar_campos(numero_hc, nombre)

        paciente = Paciente.create(
            numero_historia_clinica=numero_hc,
            nombre_completo=nombre,
            dni=(data.get("dni") or "").strip() or None,
            fecha_nacimiento=self._parse_fecha(data.get("fecha_nacimiento")),
            direccion=(data.get("direccion") or "").strip() or None,
            nombre_padre=(data.get("nombre_padre") or "").strip() or None,
            nombre_madre=(data.get("nombre_madre") or "").strip() or None,
        )
        new_id = self.repo.create(paciente)
        paciente.id = new_id
        return self._to_dict(paciente)

    def actualizar(self, paciente_id: int, data: dict) -> Optional[dict]:
        existente = self.repo.get_by_id(paciente_id)
        if not existente:
            return None

        numero_hc = (data.get("numero_historia_clinica") or "").strip()
        nombre = (data.get("nombre_completo") or "").strip()
        self._validar_campos(numero_hc, nombre)

        paciente = Paciente(
            id=paciente_id,
            numero_historia_clinica=numero_hc,
            nombre_completo=nombre,
            dni=(data.get("dni") or "").strip() or None,
            fecha_nacimiento=self._parse_fecha(data.get("fecha_nacimiento")),
            direccion=(data.get("direccion") or "").strip() or None,
            nombre_padre=(data.get("nombre_padre") or "").strip() or None,
            nombre_madre=(data.get("nombre_madre") or "").strip() or None,
            activo=True,
        )
        self.repo.update(paciente)
        return self._to_dict(paciente)

    def eliminar(self, paciente_id: int) -> bool:
        return self.repo.delete(paciente_id)

    def contar(self) -> int:
        return self.repo.count_all()
