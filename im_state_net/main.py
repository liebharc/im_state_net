from im_state_net.additional_nodes import LambdaCalcNode
from im_state_net.network_core import InputNode, NetworkBuilder

if __name__ == "__main__":
    new_net = NetworkBuilder()
    val1 = new_net.add_input(InputNode(name="input1"), 1)
    val2 = new_net.add_input(InputNode(name="input2"), 2)
    val3 = new_net.add_calculation(LambdaCalcNode(lambda x: x[0] + x[1], [val1, val2], name="sum"))

    network = new_net.build()
    network = network.commit()
    print(network)

    update = network.change_value(val1, 3)
    print(update)

    update = update.commit()
    print(update)
