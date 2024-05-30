import pytest
from im_state_net.main import Network, NetworkBuilder, ValueNode

def test_valid_network():
    builder = NetworkBuilder()
    val1 = builder.add_value(1)
    val2 = builder.add_value(2)
    calc = builder.add_calculation(lambda x: x[0] + x[1], [val1, val2])
    network = builder.build()

    new_network = network.change_value(val1, 3)
    eager_committed_network = new_network.eager_commit()

    assert eager_committed_network.nodes[2].value == 5