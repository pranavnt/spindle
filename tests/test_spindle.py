import pytest
from typing import Optional, Callable
from spindle.core import module, compose, State, Config, ModuleState

def test_simple_module():
    @module(input_keys=["input"], output_keys=["output"])
    def simple_module_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"output": state["input"] + " processed"}, module_state, None

    result, _ = simple_module_func({"input": "test"}, {})
    assert result == {"output": "test processed"}

def test_stateful_module():
    @module(input_keys=["input"], output_keys=["output"])
    def stateful_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        count = module_state.get("count", 0) + 1
        return {"output": f"{state['input']}{count}"}, {"count": count}, None

    result1, _ = stateful_func({"input": "test"}, {})
    assert result1 == {"output": "test1"}

    result2, _ = stateful_func({"input": "test"}, {})
    assert result2 == {"output": "test2"}

def test_flow_enabled_module():
    @module(input_keys=["input"], output_keys=["final_output"], flow=True)
    def flow_module(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, Optional[Callable]]:
        if state["input"] > 0:
            return {"output": "positive"}, module_state, positive_handler
        else:
            return {"output": "non-positive"}, module_state, non_positive_handler

    @module(input_keys=["output"], output_keys=["final_output"])
    def positive_handler(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"final_output": f"Handled positive: {state['output']}"}, module_state, None

    @module(input_keys=["output"], output_keys=["final_output"])
    def non_positive_handler(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"final_output": f"Handled non-positive: {state['output']}"}, module_state, None

    result1, _ = flow_module({"input": 5}, {})
    assert result1 == {"output": "positive", "final_output": "Handled positive: positive"}

    result2, _ = flow_module({"input": -1}, {})
    assert result2 == {"output": "non-positive", "final_output": "Handled non-positive: non-positive"}

def test_dynamic_branching():
    @module(input_keys=["input"], output_keys=["output"], flow=True)
    def branch_module(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, Optional[Callable]]:
        if state["input"] % 2 == 0:
            return {"intermediate": state["input"]}, module_state, even_handler
        else:
            return {"intermediate": state["input"]}, module_state, odd_handler

    @module(input_keys=["intermediate"], output_keys=["output"])
    def even_handler(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"output": f"Even: {state['intermediate'] * 2}"}, module_state, None

    @module(input_keys=["intermediate"], output_keys=["output"])
    def odd_handler(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"output": f"Odd: {state['intermediate'] + 1}"}, module_state, None

    result1, _ = branch_module({"input": 4}, {})
    assert result1 == {"intermediate": 4, "output": "Even: 8"}

    result2, _ = branch_module({"input": 7}, {})
    assert result2 == {"intermediate": 7, "output": "Odd: 8"}

def test_compose_with_flow():
    @module(input_keys=["input"], output_keys=["intermediate1"], flow=True)
    def module_a(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, Optional[Callable]]:
        return {"intermediate1": state["input"] * 2}, module_state, module_b if state["input"] > 0 else module_c

    @module(input_keys=["intermediate1"], output_keys=["intermediate2"])
    def module_b(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"intermediate2": state["intermediate1"] + 1}, module_state, None

    @module(input_keys=["intermediate1"], output_keys=["intermediate2"])
    def module_c(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"intermediate2": state["intermediate1"] - 1}, module_state, None

    @module(input_keys=["intermediate2"], output_keys=["output"])
    def module_d(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"output": f"Final: {state['intermediate2']}"}, module_state, None

    program = compose(module_a, module_d)

    result1, _ = program({"input": 5}, {})
    assert result1 == {"input": 5, "intermediate1": 10, "intermediate2": 11, "output": "Final: 11"}

    result2, _ = program({"input": -3}, {})
    assert result2 == {"input": -3, "intermediate1": -6, "intermediate2": -7, "output": "Final: -7"}

def test_error_handling():
    @module(input_keys=["input"], output_keys=["output"])
    def error_func(state: State, config: Config, module_state: ModuleState) -> tuple[State, ModuleState, None]:
        return {"wrong_key": state["input"]}, module_state, None

    with pytest.raises(KeyError, match="Missing required input keys"):
        error_func({}, {})

    with pytest.raises(KeyError, match="Missing required output keys"):
        error_func({"input": "test"}, {})

if __name__ == "__main__":
    pytest.main()
