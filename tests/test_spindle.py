import pytest
from spindle.core import create_module, compose, branch, optimize, State, Config, ModuleState

def test_simple_module():
    def test_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": state["input"] + "processed"}, module_state

    test_module = create_module(test_func, input_keys=["input"], output_keys=["output"])

    result, _ = test_module({"input": "test"}, {})
    assert result == {"output": "testprocessed"}

def test_stateful_module():
    def stateful_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        count = module_state.get("count", 0) + 1
        return {"output": f"{state['input']}{count}"}, {"count": count}

    stateful_module = create_module(stateful_func, input_keys=["input"], output_keys=["output"])

    result1, _ = stateful_module({"input": "test"}, {})
    assert result1 == {"output": "test1"}

    result2, _ = stateful_module({"input": "test"}, {})
    assert result2 == {"output": "test2"}

def test_configurable_module():
    def config_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        prefix = config.get("prefix", "")
        return {"output": f"{prefix}{state['input']}"}, module_state

    config_module = create_module(config_func, input_keys=["input"], output_keys=["output"])

    result1, _ = config_module({"input": "test"}, {"prefix": "Pre-"})
    assert result1 == {"output": "Pre-test"}

    result2, _ = config_module({"input": "test"}, {})
    assert result2 == {"output": "test"}

def test_branch_module():
    def true_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": "true"}, module_state

    def false_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": "false"}, module_state

    true_module = create_module(true_func, input_keys=["input"], output_keys=["output"])
    false_module = create_module(false_func, input_keys=["input"], output_keys=["output"])

    condition = lambda state, config: state["input"] > 0

    branched = branch(condition, true_module, false_module)

    result1, _ = branched({"input": 1}, {})
    assert result1 == {"output": "true"}

    result2, _ = branched({"input": -1}, {})
    assert result2 == {"output": "false"}

def test_optimize_module():
    def test_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        multiplier = module_state.get("multiplier", 1)
        return {"output": state["input"] * multiplier}, module_state

    test_module = create_module(test_func, input_keys=["input"], output_keys=["output"])

    def optimizer_func(module_state: ModuleState) -> ModuleState:
        return {**module_state, "multiplier": 2}

    optimized_module = optimize(test_module, optimizer_func)

    result1, _ = test_module({"input": 5}, {})
    assert result1 == {"output": 5}

    result2, _ = optimized_module({"input": 5}, {})
    assert result2 == {"output": 10}

def test_error_handling():
    def error_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"wrong_key": state["input"]}, module_state

    error_module = create_module(error_func, input_keys=["input"], output_keys=["output"])

    with pytest.raises(KeyError, match="Missing required input keys"):
        error_module({}, {})

    with pytest.raises(KeyError, match="Missing required output keys"):
        error_module({"input": "test"}, {})

def test_compose_modules():
    def module_a(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"intermediate": state["input"] * 2}, module_state

    def module_b(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": state["intermediate"] + 1}, module_state

    module_a = create_module(module_a, input_keys=["input"], output_keys=["intermediate"])
    module_b = create_module(module_b, input_keys=["intermediate"], output_keys=["output"])

    composed = compose(module_a, module_b)

    result, _ = composed({"input": 5}, {})
    assert result == {"output": 11}

def test_complex_composition():
    def multiply(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"intermediate": state["input"] * config.get("multiplier", 2)}, module_state

    def add(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": state["intermediate"] + config.get("addend", 1)}, module_state

    multiply_module = create_module(multiply, input_keys=["input"], output_keys=["intermediate"])
    add_module = create_module(add, input_keys=["intermediate"], output_keys=["output"])

    composed = compose(multiply_module, add_module)

    result, _ = composed({"input": 5}, {"multiplier": 3, "addend": 2})
    assert result == {"output": 17}

if __name__ == "__main__":
    pytest.main()
