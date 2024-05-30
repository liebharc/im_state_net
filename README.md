# im-state-net

Small example on how to create a persistent network of state or calculation nodes in Python:

```python
builder = NetworkBuilder()
val1 = builder.add_input(InputNode(), 1)
val2 = builder.add_input(InputNode(), 2)
result = builder.add_calculation(LambdaCalcNode(lambda x: x[0] + x[1], [val1, val2]))
network = builder.build()

assert network.get_value(result) == 3

# Changes are detected
network = network.change_value(val1, 2)
assert network.is_consistent() == False

# The network detects if changes get reverted
network = network.change_value(val1, 1)
assert network.is_consistent() == True

# or executed them and calculates derived values
network = network.change_value(val1, 2).commit()
assert network.is_consistent() == True
assert network.get_value(result) == 4
```

Use Case: This solution is particularly beneficial when dealing with settings that are interdependent and time-consuming to apply. This could be due to the need to transmit them to hardware, which then adjusts electrical or mechanical parameters. In such scenarios, the overhead associated with this solution is justified by the reduction in the number of changes required.

Advantages:

- Detects and allows for the reversal of changes.
- Permits temporary inconsistent states, provided everything is valid upon commit.
- Offers thread safety, enabling the preparation of subsequent settings while previous ones are still being executed.

Disadvantages:

- Adds complexity and increases execution time.