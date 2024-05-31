import pytest

from im_state_net.additional_nodes import PlaceholderNode, ProductNode, SumNode
from im_state_net.network_core import InputNode, NetworkBuilder


def test_unset_placeholder():

    builder = NetworkBuilder()
    val1 = builder.add_input(InputNode(), 1)
    val2 = builder.add_input(InputNode(), 2)
    builder.add_calculation(PlaceholderNode())
    builder.add_calculation(SumNode([val1, val2]))
    with pytest.raises(Exception):
        builder.build()


def test_valid_network():

    builder = NetworkBuilder()
    val1 = builder.add_input(InputNode(), 1)
    val2 = builder.add_input(InputNode(), 2)
    placeholder = builder.add_calculation(PlaceholderNode())
    result = builder.add_calculation(SumNode([placeholder, val2]))
    placeholder.assign(ProductNode([val1, val2]))
    network = builder.build()

    assert network.get_value(result) == 4


def test_direct_circular_dependency():

    builder = NetworkBuilder()
    val1 = builder.add_input(InputNode(), 1)
    placeholder = builder.add_calculation(PlaceholderNode())
    placeholder.assign(ProductNode([val1, placeholder]))
    with pytest.raises(Exception):
        builder.build()


def test_indirect_circular_dependency():

    builder = NetworkBuilder()
    val1 = builder.add_input(InputNode(), 1)
    val2 = builder.add_input(InputNode(), 2)
    placeholder = builder.add_calculation(PlaceholderNode())
    result = builder.add_calculation(SumNode([placeholder, val2]))
    placeholder.assign(ProductNode([val1, result]))

    with pytest.raises(Exception):
        builder.build()
