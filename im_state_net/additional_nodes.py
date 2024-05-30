from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

from im_state_net.network_core import AbstractNode, DerivedNode, InputNode

U = TypeVar("U", int, float)

T = TypeVar("T")


class LambdaCalcNode(DerivedNode[T], Generic[T]):
    def __init__(
        self,
        calculation: Callable[[list[T]], T],
        dependencies: list[AbstractNode[Any]],
        name: str | None = None,
    ):
        super().__init__(dependencies=dependencies, name=name)
        self._calculation = calculation

    def calculate(self, inputs: list[T]) -> T:
        return self._calculation(inputs)


class SumNode(DerivedNode[U], Generic[U]):
    def __init__(self, dependencies: list[AbstractNode[Any]], name: str | None = None) -> None:
        super().__init__(dependencies=dependencies, name=name)

    def calculate(self, inputs: list[Any]) -> U:
        return cast(U, sum(inputs))


class ProductNode(DerivedNode[U], Generic[U]):
    def __init__(self, dependencies: list[AbstractNode[Any]], name: str | None = None) -> None:
        super().__init__(dependencies=dependencies, name=name)

    def calculate(self, inputs: list[Any]) -> U:
        result = 1
        for value in inputs:
            result *= value
        return result


class NumericMinMaxNode(InputNode[U]):
    def __init__(self, min_value: U, max_value: U, name: str | None = None) -> None:
        super().__init__(name)
        self._min_value: U = min_value
        self._max_value: U = max_value

    @property
    def min_value(self) -> U:
        return self._min_value

    @property
    def max_value(self) -> U:
        return self._max_value

    def validate(self, value: U) -> U:
        if value < self._min_value:
            return self._min_value
        elif value > self._max_value:
            return self._max_value
        return value

    def __repr__(self) -> str:
        return str(self)
