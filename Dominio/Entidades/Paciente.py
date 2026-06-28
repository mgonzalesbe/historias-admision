from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Paciente:
    id: int
    numero_historia_clinica: str
    nombre_completo: str
    dni: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    direccion: Optional[str] = None
    nombre_padre: Optional[str] = None
    nombre_madre: Optional[str] = None
    activo: bool = True

    @staticmethod
    def create(
        numero_historia_clinica: str,
        nombre_completo: str,
        dni: Optional[str] = None,
        fecha_nacimiento: Optional[date] = None,
        direccion: Optional[str] = None,
        nombre_padre: Optional[str] = None,
        nombre_madre: Optional[str] = None,
    ) -> "Paciente":
        return Paciente(
            id=0,
            numero_historia_clinica=numero_historia_clinica.strip(),
            nombre_completo=nombre_completo.strip(),
            dni=(dni or "").strip() or None,
            fecha_nacimiento=fecha_nacimiento,
            direccion=(direccion or "").strip() or None,
            nombre_padre=(nombre_padre or "").strip() or None,
            nombre_madre=(nombre_madre or "").strip() or None,
        )
