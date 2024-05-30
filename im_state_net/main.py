import abc
import uuid
from collections.abc import Callable
from typing import TypeVar

from pyrsistent import pset, pvector
from pyrsistent.typing import PSet, PVector

T = TypeVar("T")


class AbstractNode(abc.ABC):

    def __init__(self) -> None:
        super().__init__()
        self._id = uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    @abc.abstractmethod
    def value(self) -> T:
        pass


TInputNode = TypeVar("TInputNode", bound="InputNode")


class InputNode(AbstractNode):
    def __init__(self, value: T) -> None:
        super().__init__()
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    @abc.abstractmethod
    def change_value(self: TInputNode, new_value: T) -> TInputNode:
        pass


TValueNode = TypeVar("TValueNode", bound="ValueNode")


class ValueNode(InputNode):
    def __init__(self, value: T) -> None:
        super().__init__()
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    def change_value(self: TValueNode, new_value: T) -> TValueNode:
        copy = ValueNode(new_value)
        copy._id = self._id
        return copy

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"ValueNode({self._value})"


TNumericMinMaxNode = TypeVar("TNumericMinMaxNode", bound="NumericMinMaxNode")


class NumericMinMaxNode(ValueNode):
    def __init__(self, value: T, min_value: T, max_value: T) -> None:
        super().__init__(value)
        self._min_value = min_value
        self._max_value = max_value

    @property
    def min_value(self) -> T:
        return self._min_value

    @property
    def max_value(self) -> T:
        return self._max_value

    def change_value(self: TNumericMinMaxNode, new_value: T) -> TNumericMinMaxNode:
        if new_value < self._min_value:
            new_value = self._min_value
        elif new_value > self._max_value:
            new_value = self._max_value
        copy = NumericMinMaxNode(new_value, self._min_value, self._max_value)
        copy._id = self._id
        return copy

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"NumericMinMaxNode({self._value}, {self._min_value}, {self._max_value})"


TDerivedNode = TypeVar("TDerivedNode", bound="DerivedNode")


class DerivedNode(ValueNode):
    def __init__(
        self, value: T, dependencies: list[AbstractNode], dependency_ids: PSet[uuid.UUID] = None
    ) -> None:
        super().__init__(value)
        self._dependencies = dependencies
        self.dependency_ids = dependency_ids or pset([dep.id for dep in dependencies])

    @property
    def dependencies(self) -> list[AbstractNode]:
        return self._dependencies

    @abc.abstractmethod
    def force_calculation(self) -> None:
        pass


TLambdaCalcNode = TypeVar("TLambdaCalcNode", bound="LambdaCalcNode")


class LambdaCalcNode(DerivedNode):
    def __init__(
        self,
        calculation: Callable[[list[T]], T],
        dependencies: list[AbstractNode],
        dependency_ids: PSet[uuid.UUID] = None,
    ):
        super().__init__(dependencies=dependencies, dependency_ids=dependency_ids)
        self._calculation = calculation
        self._value: T | None = None

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def value(self):
        if self._value is None:
            self.force_calculation()
        return self._value

    def force_calculation(self):
        self._value = self._calculation([node.value for node in self._dependencies])

    def reset(self: TLambdaCalcNode, dependencies: list[AbstractNode]) -> TLambdaCalcNode:
        return LambdaCalcNode(self._calculation, dependencies, self.dependency_ids)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"LambdaCalcNode({self._value})"


TNetwork = TypeVar("TNetwork", bound="Network")


class Network:
    def __init__(self, nodes: PVector[AbstractNode], changes: PSet[uuid.UUID] = None):
        self.nodes = nodes
        self.changes = changes or pset()

    def change_value(self: TNetwork, node: ValueNode, new_value: T) -> TNetwork:
        # Get existing value by ID and replace it by the result of set_value
        index = self.nodes.index(node)
        new_node = node.change_value(new_value)
        return Network(self.nodes.set(index, new_node), self.changes.add(new_node.id))

    def commit(self: TNetwork, eager: bool = False) -> TNetwork:
        nodes = self.nodes
        changes = self.changes
        nodes_by_id = {node.id: node for node in nodes}
        for i, node in enumerate(nodes):
            if isinstance(node, DerivedNode):
                any_deps_changed = not self.changes.isdisjoint(node.dependency_ids)
                if any_deps_changed:
                    updated_dependencies = [nodes_by_id[dep.id] for dep in node.dependencies]
                    updated_node = node.reset(updated_dependencies)
                    if eager:
                        updated_node.force_calculation()
                    nodes = nodes.set(i, updated_node)
                    nodes_by_id[node.id] = updated_node
                    changes = changes.add(updated_node.id)
        return Network(nodes, pset())

    def eager_commit(self: TNetwork) -> TNetwork:
        return self.commit(eager=True)

    def __repr__(self):
        return str(self)

    def __str__(self):
        if self.changes:
            return f"Network({self.nodes}, changes={self.changes})"
        return f"Network({self.nodes})"


class NetworkBuilder:
    def __init__(self):
        self.nodes = []

    def add_value(self, value: T) -> ValueNode:
        node = ValueNode(value)
        self.nodes.append(node)
        return node

    def add_calculation(
        self, calculation: Callable[[list[AbstractNode]], T], dependencies: list[AbstractNode]
    ) -> LambdaCalcNode:
        node = LambdaCalcNode(calculation, dependencies)
        self.nodes.append(node)
        return node

    def _sorted_nodes(self):
        sorted_nodes = []
        visited = set()
        visiting = set()

        def visit(node):
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

    def build(self):
        return Network(pvector(self._sorted_nodes()))


if __name__ == "__main__":
    new_net = NetworkBuilder()
    val1 = new_net.add_value(1)
    val2 = new_net.add_value(2)
    val3 = new_net.add_calculation(lambda x: x[0] + x[1], [val1, val2])

    network = new_net.build()
    network = network.eager_commit()
    print(network)

    update = network.change_value(val1, 3)
    print(update)

    update = update.eager_commit()
    print(update)
