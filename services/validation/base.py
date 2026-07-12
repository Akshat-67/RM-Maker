from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import Discrepancy

class BaseValidator(ABC):
    @abstractmethod
    def supports(self, doc_type: str) -> bool:
        pass

    @abstractmethod
    def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
        pass
