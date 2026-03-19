from __future__ import annotations

"""
Parser Registry.

Generic parser registration system following the backend's mongo_entity pattern.
Parsers are registered via decorator and can be looked up by name or data type.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional, Type, TypeVar

T = TypeVar("T", bound="BaseParser")


@dataclass(frozen=True)
class ParserBinding:
    parser_cls: Type["BaseParser"]
    name: str
    data_type: str
    description: str


_REGISTRY: list[ParserBinding] = []


class BaseParser(ABC):
    """Base class for all parsers."""
    
    @classmethod
    @abstractmethod
    def parse(cls, raw: Any) -> Optional[Any]:
        """Parse raw data into structured output."""
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def validate(cls, data: Any) -> bool:
        """Validate that data can be parsed."""
        raise NotImplementedError


def get_parsers() -> list[ParserBinding]:
    """Return all registered parsers."""
    return list(_REGISTRY)


def get_parser_by_name(name: str) -> Optional[Type[BaseParser]]:
    """Look up a parser by its registered name."""
    for binding in _REGISTRY:
        if binding.name == name:
            return binding.parser_cls
    return None


def get_parser_by_data_type(data_type: str) -> Optional[Type[BaseParser]]:
    """Look up a parser by its data type."""
    for binding in _REGISTRY:
        if binding.data_type == data_type:
            return binding.parser_cls
    return None


def register_parser(
    *,
    name: str,
    data_type: str,
    description: str = "",
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to register a parser class.
    
    Usage:
        @register_parser(name="ossd", data_type="serial")
        class OssdParser(BaseParser):
            ...
    """
    def decorator(parser_cls: Type[T]) -> Type[T]:
        binding = ParserBinding(
            parser_cls=parser_cls,
            name=name,
            data_type=data_type,
            description=description or parser_cls.__doc__ or "",
        )
        _REGISTRY.append(binding)
        return parser_cls
    
    return decorator
