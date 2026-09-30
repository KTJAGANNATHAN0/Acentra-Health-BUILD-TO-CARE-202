"""Rule registry and auto-discovery system adhering to Open/Closed Principle."""
import importlib
import logging
import pkgutil
from typing import Dict, List, Type
from app.engine.base import Rule

logger = logging.getLogger(__name__)

# Registry storing rule_name -> Rule class
_REGISTRY: Dict[str, Type[Rule]] = {}


def register_rule(cls: Type[Rule]) -> Type[Rule]:
    """Decorator to register a rule class.
    
    Example:
        @register_rule
        class VelocityRule(Rule):
            name = "velocity"
            ...
    """
    if not issubclass(cls, Rule):
        raise TypeError(f"Registered class {cls.__name__} must inherit from Rule")
    if not hasattr(cls, "name") or not cls.name:
        raise ValueError(f"Rule class {cls.__name__} must define a non-empty 'name' attribute")
    
    _REGISTRY[cls.name] = cls
    logger.info(f"Registered fraud rule: '{cls.name}' ({cls.__name__})")
    return cls


def get_registered_rules() -> Dict[str, Type[Rule]]:
    """Return a copy of all currently registered rule classes."""
    return dict(_REGISTRY)


def load_rules(package: str = "app.rules") -> List[Rule]:
    """Dynamically discover and instantiate all rules in the given package.
    
    Iterates over all modules in the package and imports them, which triggers
    the @register_rule decorator on each class. Returns instantiated Rule objects.
    """
    try:
        pkg = importlib.import_module(package)
        for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
            full_module_name = f"{package}.{module_name}"
            importlib.import_module(full_module_name)
    except Exception as e:
        logger.error(f"Error loading rule modules from {package}: {e}")
        
    return [cls() for cls in _REGISTRY.values()]
