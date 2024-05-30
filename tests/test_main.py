import pytest

from im_state_net.main import Network, NetworkBuilder


def test_valid_network():
    builder = NetworkBuilder()
    val1 = builder.add_input(1)
    val2 = builder.add_input(2)
    calc = builder.add_calculation(lambda x: x[0] + x[1], [val1, val2])
    network = builder.build()

    new_network = network.change_value(val1, 3)
    updated = new_network.commit()

    assert updated.get_value(calc) == 5
