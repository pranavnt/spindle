import pytest
from spindle.core import module, compose, branch, State, Config, ModuleState, ModuleFunc, OptimizerFunc

@module(input_keys=["input"], output_keys=["output"])
def simple_module_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
    return {"output": state["input"] + "processed"}, module_state

def test_simple_module():
    result, _ = simple_module_func({"input": "test"}, {})
    assert result == {"output": "testprocessed"}

@module(input_keys=["input"], output_keys=["output"])
def stateful_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
    count = module_state.get("count", 0) + 1
    return {"output": f"{state['input']}{count}"}, {"count": count}

def test_stateful_module():
    result1, _ = stateful_func({"input": "test"}, {})
    assert result1 == {"output": "test1"}

    result2, _ = stateful_func({"input": "test"}, {})
    assert result2 == {"output": "test2"}

@module(input_keys=["input"], output_keys=["output"])
def config_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
    prefix = config.get("prefix", "")
    return {"output": f"{prefix}{state['input']}"}, module_state

def test_configurable_module():
    result1, _ = config_func({"input": "test"}, {"prefix": "Pre-"})
    assert result1 == {"output": "Pre-test"}

    result2, _ = config_func({"input": "test"}, {})
    assert result2 == {"output": "test"}

def test_branch_module():
    @module(input_keys=["input"], output_keys=["output"])
    def true_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": "true"}, module_state

    @module(input_keys=["input"], output_keys=["output"])
    def false_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": "false"}, module_state

    condition = lambda state, config: state["input"] > 0

    branched = branch(condition, true_func, false_func)

    result1, _ = branched({"input": 1}, {})
    assert result1 == {"output": "true"}

    result2, _ = branched({"input": -1}, {})
    assert result2 == {"output": "false"}

def test_optimizer_usage():
    @module(input_keys=["input"], output_keys=["output"])
    def optimizable_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        multiplier = config.get("multiplier", 1)
        return {"output": state["input"] * multiplier}, module_state

    # User-defined optimizer function
    def my_optimizer(module_func: ModuleFunc, config: Config) -> Config:
        # Here we could use properties of module_func if needed
        return {**config, "multiplier": 2}

    original_config = {}
    optimized_config = my_optimizer(optimizable_func, original_config)

    result1, _ = optimizable_func({"input": 5}, original_config)
    assert result1 == {"output": 5}

    result2, _ = optimizable_func({"input": 5}, optimized_config)
    assert result2 == {"output": 10}

def test_error_handling():
    @module(input_keys=["input"], output_keys=["output"])
    def error_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"wrong_key": state["input"]}, module_state

    with pytest.raises(KeyError, match="Missing required input keys"):
        error_func({}, {})

    with pytest.raises(KeyError, match="Missing required output keys"):
        error_func({"input": "test"}, {})

def test_compose_modules():
    @module(input_keys=["input"], output_keys=["intermediate"])
    def module_a(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"intermediate": state["input"] * 2}, module_state

    @module(input_keys=["intermediate"], output_keys=["output"])
    def module_b(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": state["intermediate"] + 1}, module_state

    composed = compose(module_a, module_b)

    result, _ = composed({"input": 5}, {})
    assert result == {"output": 11}

def test_complex_composition():
    @module(input_keys=["input"], output_keys=["intermediate"])
    def multiply(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"intermediate": state["input"] * config.get("multiplier", 2)}, module_state

    @module(input_keys=["intermediate"], output_keys=["output"])
    def add(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState]:
        return {"output": state["intermediate"] + config.get("addend", 1)}, module_state

    composed = compose(multiply, add)

    result, _ = composed({"input": 5}, {"multiplier": 3, "addend": 2})
    assert result == {"output": 17}

if __name__ == "__main__":
    pytest.main()
