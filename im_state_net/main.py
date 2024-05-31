import random
import time
from typing import Any, TypeVar

from im_state_net.additional_nodes import LambdaCalcNode, ProductNode, SumNode
from im_state_net.state_core import AbstractNode, InputNode, StateBuilder

T = TypeVar("T")

if __name__ == "__main__":
    start_time = time.time()

    builder = StateBuilder()
    nodes: list[AbstractNode[Any]] = []
    for i in range(1000):
        if i % 5 == 0:
            nodes.append(builder.add_input(InputNode(name=f"input-{i}"), i))
        elif i % 5 == 1:
            nodes.append(builder.add_input(InputNode(name=f"input-{i}"), i + 1))
        elif i % 5 == 2:  # noqa: PLR2004
            random_input = random.choice(nodes)
            increment_node = LambdaCalcNode(
                lambda x: x[0] + random.randint(1, 10), [random_input], name=f"lambda-{i}"
            )
            nodes.append(builder.add_calculation(increment_node))
        elif i % 5 == 3:  # noqa: PLR2004
            random_inputs = random.choices(nodes, k=random.randint(1, 5))
            nodes.append(builder.add_calculation(SumNode(random_inputs, name=f"sum={i}")))
        else:
            random_inputs = random.choices(nodes, k=random.randint(1, 5))
            nodes.append(builder.add_calculation(ProductNode(random_inputs, name=f"product={i}")))

    inputs = {node: random.randint(0, 100) for node in nodes if isinstance(node, InputNode)}

    state = builder.build()

    end_time = time.time()
    print(f"Setup time: {end_time - start_time} seconds")

    start_time = time.time()

    batch_size = 20
    number_of_commits = 0

    change = 0
    for node, value in inputs.items():
        state = state.change_value(node, value)
        change += 1
        if change >= batch_size:
            state, _changes = state.commit()
            number_of_commits += 1
            change = 0

    end_time = time.time()
    print(f"Update time: {end_time - start_time} seconds for {number_of_commits} commits")
