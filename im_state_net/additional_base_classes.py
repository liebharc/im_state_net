import abc
from typing import Any, Generic, TypeVar

from im_state_net.network_core import AbstractNode, DerivedNode

TOUT = TypeVar("TOUT")


TI1 = TypeVar("TI1")
TI2 = TypeVar("TI2")
TI3 = TypeVar("TI3")
TI4 = TypeVar("TI4")
TI5 = TypeVar("TI5")


class UnaryCalcNode(DerivedNode[TOUT], Generic[TOUT, TI1]):
    def __init__(self, dependency: AbstractNode[TI1], name: str | None = None) -> None:
        super().__init__(dependencies=[dependency], name=name)

    def calculate(self, inputs: list[Any]) -> TOUT:
        return self._calculation(inputs[0])

    @abc.abstractmethod
    def _calculation(self, value: TI1) -> TOUT:
        pass


class BinaryCalcNode(DerivedNode[TOUT], Generic[TOUT, TI1, TI2]):
    def __init__(
        self,
        dependency1: AbstractNode[TI1],
        dependency2: AbstractNode[TI2],
        name: str | None = None,
    ) -> None:
        super().__init__(dependencies=[dependency1, dependency2], name=name)

    def calculate(self, inputs: list[Any]) -> TOUT:
        return self._calculation(inputs[0], inputs[1])

    @abc.abstractmethod
    def _calculation(self, value1: TI1, value2: TI2) -> TOUT:
        pass


class TernaryCalcNode(DerivedNode[TOUT], Generic[TOUT, TI1, TI2, TI3]):
    def __init__(
        self,
        dependency1: AbstractNode[TI1],
        dependency2: AbstractNode[TI2],
        dependency3: AbstractNode[TI3],
        name: str | None = None,
    ) -> None:
        super().__init__(dependencies=[dependency1, dependency2, dependency3], name=name)

    def calculate(self, inputs: list[Any]) -> TOUT:
        return self._calculation(inputs[0], inputs[1], inputs[2])

    @abc.abstractmethod
    def _calculation(self, value1: TI1, value2: TI2, value3: TI3) -> TOUT:
        pass


class QuaternaryCalcNode(DerivedNode[TOUT], Generic[TOUT, TI1, TI2, TI3, TI4]):
    def __init__(
        self,
        dependency1: AbstractNode[TI1],
        dependency2: AbstractNode[TI2],
        dependency3: AbstractNode[TI3],
        dependency4: AbstractNode[TI4],
        name: str | None = None,
    ) -> None:
        super().__init__(
            dependencies=[dependency1, dependency2, dependency3, dependency4], name=name
        )

    def calculate(self, inputs: list[Any]) -> TOUT:
        return self._calculation(inputs[0], inputs[1], inputs[2], inputs[3])

    @abc.abstractmethod
    def _calculation(self, value1: TI1, value2: TI2, value3: TI3, value4: TI4) -> TOUT:
        pass


class QuinaryCalcNode(DerivedNode[TOUT], Generic[TOUT, TI1, TI2, TI3, TI5]):
    def __init__(
        self,
        dependency1: AbstractNode[TI1],
        dependency2: AbstractNode[TI2],
        dependency3: AbstractNode[TI3],
        dependency4: AbstractNode[TI4],
        dependency5: AbstractNode[TI5],
        name: str | None = None,
    ) -> None:
        super().__init__(
            dependencies=[dependency1, dependency2, dependency3, dependency4, dependency5],
            name=name,
        )

    def calculate(self, inputs: list[Any]) -> TOUT:
        return self._calculation(inputs[0], inputs[1], inputs[2], inputs[3], inputs[4])

    @abc.abstractmethod
    def _calculation(self, value1: TI1, value2: TI2, value3: TI3, value4: TI4, value5: TI5) -> TOUT:
        pass
