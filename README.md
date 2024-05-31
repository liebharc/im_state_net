# im-state-net

Small example on how to create a persistent graph of state or calculation nodes in Python:

```python
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
assert changes == set([val1, result])
```

Use Case: This solution is particularly beneficial when dealing with settings that are interdependent and time-consuming to apply. This could be due to the need to transmit them to hardware, which then adjusts electrical or mechanical parameters. In such scenarios, the overhead associated with this solution is justified by the reduction in the number of changes required.

Advantages:

- Detects and allows for the reversal of changes.
- Allows to combine multiple settings into a single commit.
- Permits temporary inconsistent states, provided everything is valid upon commit.
- Offers thread safety, enabling the preparation of subsequent settings while previous ones are still being executed.

Disadvantages:

- Adds complexity and increases execution time.
