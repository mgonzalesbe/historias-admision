from abc import ABC, abstractmethod
from typing import List, Optional

from Dominio.Entidades.Paciente import Paciente


class IPacienteRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Paciente]:
        pass

    @abstractmethod
    def search(
        self, termino: str, tipo: str = "nombre", limite: int = 100
    ) -> List[Paciente]:
        pass

    @abstractmethod
    def create(self, paciente: Paciente) -> int:
        pass

    @abstractmethod
    def update(self, paciente: Paciente) -> bool:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass

    @abstractmethod
    def count_all(self) -> int:
        pass
