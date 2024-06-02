from typing import TypeVar

import pytest

from im_state_net.additional_nodes import NumericMinMaxNode, SumNode
from im_state_net.state_core import AbstractNode, InputNode, State, StateBuilder

T = TypeVar("T")


class StateMut:
    """
    A mutable state that allows changing values of the nodes.
    This illustrated how you can create an interface between the
    immutable state to code which expects mutable state.

    The advantage is that you can at any point get the immutable state,
    which then gives you isolation and immutability guarantees.
    """

    def __init__(self) -> None:

        builder = StateBuilder()
        self._val1 = builder.add_input(InputNode(name="val1"), 1)
        self._val2 = builder.add_input(NumericMinMaxNode(1, 5, name="val2"), 2)
        self._result = builder.add_calculation(SumNode([self._val1, self._val2], name="result"))
        self._state = builder.build()

    def _get_value(self, node: AbstractNode[T]) -> T:
        return self._state.get_value(node)

    def _set_value(self, node: AbstractNode[T], value: T) -> None:
        self._state, _ignored = self._state.change_value(node, value).commit()

    @property
    def result(self) -> int:
        # Depending on the language and library one can generate a lot of boilerplate code
        # to define the getters and setters for the properties.
        # We stick to basic Python here.
        return self._get_value(self._result)

    @property
    def val1(self) -> int:
        return self._get_value(self._val1)

    @val1.setter
    def val1(self, value: int) -> None:
        self._set_value(self._val1, value)

    @property
    def val2(self) -> int:
        return self._get_value(self._val2)

    def set_val1_and_val2(self, val1: int, val2: int) -> None:
        """
        Sets both values in one commit
        """
        self._state, _ignored = (
            self._state.change_value(self._val1, val1).change_value(self._val2, val2).commit()
        )


def merge_changes(state1: State, state2: State) -> State:
    """
    Moves from all changes from src to dest. States must be at the same version
    and changes must be disjoint.

    Merges could be useful in concurrent systems with mutable state
    if you receive multiple updates concurrently and don't want to raise an error.
    Note: If we discuss concurrency then we think about the concept itself and not
    about the implementation in Python.
    """
    if state1.version_id != state2.version_id:
        raise ValueError("States must be at the same version")
    are_changes_disjoint = not any(change in state1.changes for change in state2.changes)
    if not are_changes_disjoint:
        raise ValueError("Changes are not disjoint")
    for change in state2.changes:
        state1 = state1.change_value(change, state2.get_value(change))
    return state1


def rebase_changes(state: State, base: State) -> State:
    """
    Rebase changes from state to base.

    Rebases could be useful in concurrent systems with mutable state
    if you receive multiple updates concurrently and don't want to raise an error.
    Note: If we discuss concurrency then we think about the concept itself and not
    about the implementation in Python.
    """
    if state._nodes != base._nodes:
        raise ValueError("States must have the same nodes")
    if not base.is_consistent():
        raise ValueError("Base state must not have any uncommitted changes")
    for change in state.changes:
        base = base.change_value(change, state.get_value(change))
    return base


def test_state_mut():
    state = StateMut()
    assert state.result == 3
    assert state.val1 == 1
    assert state.val2 == 2

    state.val1 = 3
    assert state.result == 5

    state.set_val1_and_val2(4, 5)
    assert state.result == 9


def test_merge_changes():
    builder = StateBuilder()
    val1 = builder.add_input(InputNode(), 1)
    val2 = builder.add_input(InputNode(), 2)
    val3 = builder.add_input(InputNode(), 3)
    result = builder.add_calculation(SumNode([val1, val2, val3]))
    state1 = builder.build()

    state2 = state1.change_value(val1, 5)

    state3 = state1.change_value(val2, 6)

    merged = merge_changes(state2, state3)

    assert merged.get_value(val1) == 5
    assert merged.get_value(val2) == 6
    assert merged.get_value(val3) == 3

    merged, _ignored = merged.commit()

    conflict = state1.change_value(val2, 7)

    with pytest.raises(ValueError):
        merge_changes(state1, merged)

    with pytest.raises(ValueError):
        merge_changes(conflict, state3)


def test_rebase_changes():
    builder = StateBuilder()
    val1 = builder.add_input(InputNode(), 1)
    val2 = builder.add_input(InputNode(), 2)
    val3 = builder.add_input(InputNode(), 3)
    result = builder.add_calculation(SumNode([val1, val2, val3]))
    state1 = builder.build()

    state2, _ignored = state1.change_value(val1, 5).commit()

    state3 = state1.change_value(val2, 6)

    state4, _ignored = state2.change_value(val3, 3).commit()

    rebased = rebase_changes(state3, state4)

    assert rebased.get_value(val1) == 5
    assert rebased.get_value(val2) == 6
    assert rebased.get_value(val3) == 3

    different_state = StateBuilder()
    different_state.add_input(InputNode(), 1)

    with pytest.raises(ValueError):
        rebase_changes(state4, state3)

    with pytest.raises(ValueError):
        rebase_changes(different_state.build(), state4)
