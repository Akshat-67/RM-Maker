from .base import BaseValidator
from .models import Discrepancy, ValidationResult, FixAction
from .registry import registry
from .engine import ValidationEngine

# Import and register domain validators
from .identity_validator import IdentityValidator
registry.register(IdentityValidator())
