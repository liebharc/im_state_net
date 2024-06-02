from typing import TypeVar

import pytest

from im_state_net.additional_base_classes import BinaryCalcNode
from im_state_net.additional_nodes import (
    LambdaCalcNode,
    NumericMinMaxNode,
    ProductNode,
    SumNode,
)
from im_state_net.state_core import AbstractNode, InputNode, StateBuilder

T = TypeVar("T")


class MyBinaryNode(BinaryCalcNode[str, float, int]):
    def _calculation(self, value1: float, value2: int) -> str:
        return str(value1 + value2)


class SimpleSumState:
    def __init__(self):
        builder = StateBuilder()
        self.val1 = builder.add_input(InputNode(), 1)
        self.val2 = builder.add_input(NumericMinMaxNode(1, 5), 2)
        self.val3 = builder.add_input(InputNode(), 3.0)
        self.calc = builder.add_calculation(
            LambdaCalcNode(lambda x: x[0] + x[1], [self.val1, self.val2])
        )
        self.sum = builder.add_calculation(SumNode([self.val1, self.val2]))
        self.product = builder.add_calculation(ProductNode([self.val1, self.val2]))
        self.strnode = builder.add_calculation(MyBinaryNode(self.val3, self.val1))
        self.state = builder.build()

    def get_value(self, node: AbstractNode[T]) -> T:
        return self.state.get_value(node)

    def set_value(self, node: AbstractNode[T], value: T) -> None:
        self.state = self.state.change_value(node, value)

    def commit(self) -> None:
        self.state, _changes = self.state.commit()

    def number_of_changes(self) -> int:
        return len(self.state._changes)


def test_valid_state():
    state = SimpleSumState()
    assert state.get_value(state.calc) == 3

    state.set_value(state.val1, 3)
    state.commit()

    assert state.get_value(state.calc) == 5
    assert state.get_value(state.sum) == 5
    assert state.get_value(state.product) == 6
    assert state.get_value(state.strnode) == "6.0"


def test_missing_dependency():
    builder = StateBuilder()
    val1 = builder.add_input(InputNode(), 1)
    val2 = InputNode()
    result = builder.add_calculation(LambdaCalcNode(lambda x: x[0] + x[1], [val1, val2]))
    with pytest.raises(Exception):
        builder.build()


def test_change_min_max_node():
    state = SimpleSumState()
    assert state.get_value(state.val2) == 2

    state.set_value(state.val2, 6)
    state.commit()

    assert state.get_value(state.val2) == 5


def test_change_to_same_value():
    state = SimpleSumState()
    state.set_value(state.val1, 1)
    assert state.number_of_changes() == 0


def test_reverting_changes():
    state = SimpleSumState()
    value1 = state.get_value(state.val1)
    state.set_value(state.val1, value1 + 5)

    assert state.number_of_changes() == 1

    state.set_value(state.val1, value1)

    assert state.number_of_changes() == 0


def test_example():

    builder = StateBuilder()
    val1 = builder.add_input(InputNode(), 1)
    val2 = builder.add_input(InputNode(), 2)
    result = builder.add_calculation(LambdaCalcNode(lambda x: x[0] + x[1], [val1, val2]))
    state = builder.build()

    assert state.get_value(result) == 3

    state = state.change_value(val1, 2)
    # Changes are detected
    assert state.is_consistent() == False

    # The state detects if changes get reverted
    state = state.change_value(val1, 1)
    assert state.is_consistent() == True

    # or calculates derived values on commit
    state, changes = state.change_value(val1, 2).commit()
    assert state.is_consistent() == True
    assert state.get_value(result) == 4
    assert changes == {val1, result}
