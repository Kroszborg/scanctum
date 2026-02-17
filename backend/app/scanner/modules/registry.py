import importlib
import logging
import pkgutil
from pathlib import Path

from app.scanner.modules.base import BaseModule

logger = logging.getLogger(__name__)

_registry: dict[str, type[BaseModule]] = {}


class ModuleRegistry:
    """Auto-discovers and manages scanner modules."""

    @staticmethod
    def register(cls: type[BaseModule]) -> type[BaseModule]:
        """Decorator to register a module class."""
        _registry[cls.name] = cls
        return cls

    @staticmethod
    def discover() -> None:
        """Auto-discover all modules in the modules package."""
        package_dir = Path(__file__).parent
        for module_info in pkgutil.iter_modules([str(package_dir)]):
            if module_info.name in ("base", "registry", "__init__"):
                continue
            try:
                importlib.import_module(f"app.scanner.modules.{module_info.name}")
            except Exception as e:
                logger.error(f"Failed to import module {module_info.name}: {e}")

    @staticmethod
    def get_all() -> dict[str, type[BaseModule]]:
        if not _registry:
            ModuleRegistry.discover()
        return _registry.copy()

    @staticmethod
    def get_for_mode(mode: str) -> list[BaseModule]:
        """Get instantiated modules for a scan mode."""
        all_modules = ModuleRegistry.get_all()
        return [
            cls() for cls in all_modules.values()
            if mode in cls.scan_modes
        ]
