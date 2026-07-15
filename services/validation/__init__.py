from .base import BaseValidator
from .models import Discrepancy, ValidationResult, FixAction
from .registry import registry
from .engine import ValidationEngine

# Import and register domain validators
from .identity_validator import IdentityValidator
from .gender_validator import GenderValidator
from .missing_fields_validator import MissingFieldsValidator
from .template_validator import TemplateValidator
from .name_match_validator import NameMatchValidator

registry.register(IdentityValidator())
registry.register(GenderValidator())
registry.register(MissingFieldsValidator())
registry.register(TemplateValidator())
registry.register(NameMatchValidator())
