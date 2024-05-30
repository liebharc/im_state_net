import abc
import uuid
from typing import Any, Generic, TypeVar, cast

from pyrsistent import pmap, pset, pvector
from pyrsistent.typing import PMap, PSet, PVector

T = TypeVar("T")


class AbstractNode(abc.ABC, Generic[T]):

    def __init__(self, name: str | None) -> None:
        super().__init__()
        self._name = name or str(uuid.uuid4())

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
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


class DerivedNode(AbstractNode[T], Generic[T]):
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
            changes = self._changes.discard(node)
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

    def add_input(self, node: InputNode[T], value: T) -> InputNode[T]:
        self.nodes.append(node)
        self.initial_values[node] = value
        return node

    def add_calculation(
        self,
        node: DerivedNode[T],
    ) -> DerivedNode[T]:
        self.initial_values[node] = node.calculate(
            [self.initial_values[dep] for dep in node.dependencies]
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
                if isinstance(node, DerivedNode):
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
