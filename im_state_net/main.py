import abc
import uuid
from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

from pyrsistent import pmap, pset, pvector
from pyrsistent.typing import PMap, PSet, PVector

T = TypeVar("T")


class AbstractNode(abc.ABC, Generic[T]):

    def __init__(self, name: str | None) -> None:
        super().__init__()
        self._has_readable_name = False
        if name:
            self._name = name
            self._has_readable_name = True
        else:
            self._name = str(uuid.uuid4())

    @property
    def name(self) -> str:
        return self._name


class InputNode(AbstractNode[T], Generic[T]):
    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)

    def validate(self, value: T) -> T:
        """
        Validates the value before setting it. It can
        coerce the value to a valid one or throw an exception
        if the value is invalid.
        """
        return value

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        if self._has_readable_name:
            return self._name
        return "InputNode()"


U = TypeVar("U", int, float)


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

    def __str__(self) -> str:
        if self._has_readable_name:
            return self._name
        return f"NumericMinMaxNode({self._min_value}, {self._max_value})"


class DerivedNode(AbstractNode[T], abc.ABC, Generic[T]):
    def __init__(self, dependencies: list[AbstractNode[Any]], name: str | None = None) -> None:
        super().__init__(name)
        self._dependencies = dependencies

    @property
    def dependencies(self) -> list[AbstractNode[Any]]:
        return self._dependencies

    @abc.abstractmethod
    def calculate(self, inputs: list[Any]) -> T:
        """
        Calculates the value of the node based on the inputs.
        The caller guarantees that the inputs are in the same order
        as the dependencies.
        """


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

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        if self._has_readable_name:
            return self._name
        return "LambdaCalcNode()"


class Network:
    def __init__(
        self,
        nodes: PVector[AbstractNode[Any]],
        values: PMap[AbstractNode[Any], Any],
        changes: PSet[AbstractNode[Any]] | None = None,
        initial_values: PMap[AbstractNode[Any], Any] | None = None,
    ):
        self._nodes = nodes
        self._changes = changes or pset()
        self._values = values
        # initial values are the values since the last commit
        self._initial_values = initial_values or values

    def change_value(self, node: InputNode[T], new_value: T) -> "Network":
        new_value = node.validate(new_value)
        old_value = self._initial_values.get(node)
        values = self._values.set(node, new_value)
        if old_value != new_value:
            changes = self._changes.add(node)
        else:
            changes = self._changes.remove(node)
        return Network(self._nodes, values, changes, self._initial_values)

    def get_value(self, node: AbstractNode[T]) -> T:
        return cast(T, self._values[node])

    def commit(self) -> "Network":
        if len(self._changes) == 0:
            return self
        nodes = self._nodes
        values = self._values
        changes = self._changes
        for node in nodes:
            if isinstance(node, DerivedNode):
                any_deps_changed = not self._changes.isdisjoint(node.dependencies)
                if any_deps_changed:
                    new_value = node.calculate([values[dep] for dep in node.dependencies])
                    old_value = self._initial_values.get(node)
                    values = values.set(node, new_value)
                    if old_value != new_value:
                        changes = changes.add(node)
        return Network(nodes, values, pset(), values)

    def is_consistent(self) -> bool:
        """
        A consistent network is a network which has no pending changes.
        In other words: It has no changes since the last commit.
        """
        return len(self._changes) == 0

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        nodes_and_values = str.join(
            ", ", [str(node) + ": " + (str(self._values.get(node))) for node in self._nodes]
        )
        if self._changes:
            changes = str.join(", ", [str(node) for node in self._changes])
            return f"Network({nodes_and_values} | changes={changes})"
        return f"Network({nodes_and_values})"

    def dump(self) -> dict[str, Any]:
        result = {}
        for node in self._nodes:
            result[str(node._name)] = self._values.get(node)
        return result


class NetworkBuilder:
    def __init__(self) -> None:
        self.nodes: list[AbstractNode[Any]] = []
        self.initial_values: dict[AbstractNode[Any], Any] = {}

    def add_input(self, value: T, name: str | None = None) -> InputNode[T]:
        node: InputNode[T] = InputNode(name=name)
        self.nodes.append(node)
        self.initial_values[node] = value
        return node

    def add_calculation(
        self,
        calculation: Callable[[list[T]], T],
        dependencies: list[AbstractNode[Any]],
        name: str | None = None,
    ) -> LambdaCalcNode[T]:
        node = LambdaCalcNode(calculation, dependencies, name=name)
        self.initial_values[node] = node.calculate(
            [self.initial_values[dep] for dep in dependencies]
        )
        self.nodes.append(node)
        return node

    def _sorted_nodes(self) -> list[AbstractNode[Any]]:
        sorted_nodes = []
        visited = set()
        visiting = set()

        def visit(node: AbstractNode[Any]) -> None:
            if node in visiting:
                raise ValueError("Circular dependency detected")

            if node not in visited:
                visiting.add(node)
                if isinstance(node, LambdaCalcNode):
                    for dependency in node.dependencies:
                        visit(dependency)
                visiting.remove(node)
                visited.add(node)
                sorted_nodes.append(node)

        for node in self.nodes:
            visit(node)

        return sorted_nodes

    def build(self) -> Network:
        return Network(pvector(self._sorted_nodes()), pmap(self.initial_values))


if __name__ == "__main__":
    new_net = NetworkBuilder()
    val1 = new_net.add_input(1, name="input1")
    val2 = new_net.add_input(2, name="input2")
    val3 = new_net.add_calculation(lambda x: x[0] + x[1], [val1, val2], name="sum")

    network = new_net.build()
    network = network.commit()
    print(network)

    update = network.change_value(val1, 3)
    print(update)

    update = update.commit()
    print(update)
