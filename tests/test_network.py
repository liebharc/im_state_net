from typing import TypeVar

from im_state_net.additional_nodes import (
    LambdaCalcNode,
    NumericMinMaxNode,
    ProductNode,
    SumNode,
)
from im_state_net.network_core import AbstractNode, InputNode, NetworkBuilder

T = TypeVar("T")


class SimpleSumNetwork:
    def __init__(self):
        builder = NetworkBuilder()
        self.val1 = builder.add_input(InputNode(), 1)
        self.val2 = builder.add_input(NumericMinMaxNode(1, 5), 2)
        self.calc = builder.add_calculation(
            LambdaCalcNode(lambda x: x[0] + x[1], [self.val1, self.val2])
        )
        self.sum = builder.add_calculation(SumNode([self.val1, self.val2]))
        self.product = builder.add_calculation(ProductNode([self.val1, self.val2]))
        self.network = builder.build()

    def get_value(self, node: AbstractNode[T]) -> T:
        return self.network.get_value(node)

    def set_value(self, node: AbstractNode[T], value: T) -> None:
        self.network = self.network.change_value(node, value)

    def commit(self) -> None:
        self.network = self.network.commit()

    def number_of_changes(self) -> int:
        return len(self.network._changes)


def test_valid_network():
    network = SimpleSumNetwork()
    assert network.get_value(network.calc) == 3

    network.set_value(network.val1, 3)
    network.commit()

    assert network.get_value(network.calc) == 5
    assert network.get_value(network.sum) == 5
    assert network.get_value(network.product) == 6


def test_change_min_max_node():
    network = SimpleSumNetwork()
    assert network.get_value(network.val2) == 2

    network.set_value(network.val2, 6)
    network.commit()

    assert network.get_value(network.val2) == 5


def test_reverting_changes():
    network = SimpleSumNetwork()
    value1 = network.get_value(network.val1)
    network.set_value(network.val1, value1 + 5)

    assert network.number_of_changes() == 1

    network.set_value(network.val1, value1)

    assert network.number_of_changes() == 0
