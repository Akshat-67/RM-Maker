from typing import List
from .base import BaseValidator

class ValidatorRegistry:
    def __init__(self):
        self._validators: List[BaseValidator] = []

    def register(self, validator: BaseValidator) -> None:
        self._validators.append(validator)

    def get_validators(self) -> List[BaseValidator]:
        return self._validators

# Global registry instance
registry = ValidatorRegistry()
