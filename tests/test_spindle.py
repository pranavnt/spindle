import pytest
from spindle.core import module, compose, branch, State

def test_module_decorator():
    @module(input_keys=['input'], output_keys=['output'], flow=False)
    def test_module(state: State) -> State:
        state['output'] = state['input'] * 2
        return state

    result = test_module({'input': 5})
    assert result == {'input': 5, 'output': 10}
    assert hasattr(test_module, 'is_module')
    assert hasattr(test_module, 'has_transition')
    assert hasattr(test_module, 'input_keys')
    assert hasattr(test_module, 'output_keys')
    assert test_module.input_keys == ['input']
    assert test_module.output_keys == ['output']
    assert test_module.has_transition == False

def test_module_with_transition():
    @module(input_keys=['input'], output_keys=['output'], flow=True)
    def test_module(state: State) -> tuple[State, str]:
        state['output'] = state['input'] * 2
        return state, 'next_module'

    result, next_module = test_module({'input': 5})
    assert result == {'input': 5, 'output': 10}
    assert next_module == 'next_module'

def test_module_missing_input():
    @module(input_keys=['input'], output_keys=['output'], flow=False)
    def test_module(state: State) -> State:
        state['output'] = state['input'] * 2
        return state

    with pytest.raises(KeyError):
        test_module({})

def test_module_missing_output():
    @module(input_keys=['input'], output_keys=['output'], flow=False)
    def test_module(state: State) -> State:
        return state

    with pytest.raises(KeyError):
        test_module({'input': 5})

def test_compose():
    @module(input_keys=['input'], output_keys=['intermediate'], flow=False)
    def module1(state: State) -> State:
        state['intermediate'] = state['input'] * 2
        return state

    @module(input_keys=['intermediate'], output_keys=['output'], flow=False)
    def module2(state: State) -> State:
        state['output'] = state['intermediate'] + 1
        return state

    composed = compose(module1, module2)
    result = composed({'input': 5})
    assert result == {'input': 5, 'intermediate': 10, 'output': 11}

def test_compose_with_flow():
    @module(input_keys=['input'], output_keys=['intermediate'], flow=False)
    def module1(state: State) -> State:
        state['intermediate'] = state['input'] * 2
        return state

    @module(input_keys=['intermediate'], output_keys=['output'], flow=True)
    def module2(state: State) -> tuple[State, str]:
        state['output'] = state['intermediate'] + 1
        return state, 'module3'

    @module(input_keys=['output'], output_keys=['final'], flow=False)
    def module3(state: State) -> State:
        state['final'] = state['output'] * 3
        return state

    program = compose(module1, module2, module3)
    result = program({'input': 5})
    assert result == {'input': 5, 'intermediate': 10, 'output': 11, 'final': 33}

def test_branch():
    @module(input_keys=['input'], output_keys=['result'], flow=False)
    def even_module(state: State) -> State:
        state['result'] = 'even'
        return state

    @module(input_keys=['input'], output_keys=['result'], flow=False)
    def odd_module(state: State) -> State:
        state['result'] = 'odd'
        return state

    branching_module = branch(
        lambda state: state['input'] % 2 == 0,
        even_module,
        odd_module
    )

    even_result = branching_module({'input': 2})
    assert even_result == {'input': 2, 'result': 'even'}

    odd_result = branching_module({'input': 3})
    assert odd_result == {'input': 3, 'result': 'odd'}

def test_complex_program():
    @module(input_keys=['input'], output_keys=['processed'], flow=False)
    def input_module(state: State) -> State:
        state['processed'] = state['input'] * 2
        return state

    @module(input_keys=['processed'], output_keys=[], flow=True)
    def branching_module(state: State) -> tuple[State, str]:
        if state['processed'] > 10:
            return state, 'large_module'
        else:
            return state, 'small_module'

    @module(input_keys=['processed'], output_keys=['result'], flow=False)
    def large_module(state: State) -> State:
        state['result'] = 'large'
        return state

    @module(input_keys=['processed'], output_keys=['result'], flow=False)
    def small_module(state: State) -> State:
        state['result'] = 'small'
        return state

    program = compose(input_module, branching_module, large_module, small_module)

    large_result = program({'input': 6})
    assert large_result == {'input': 6, 'processed': 12, 'result': 'large'}

    small_result = program({'input': 4})
    assert small_result == {'input': 4, 'processed': 8, 'result': 'small'}

if __name__ == '__main__':
    pytest.main()
