from typing import Callable, Any, Dict, List, Tuple, Optional

State = Dict[str, Any]
Config = Dict[str, Any]
ModuleState = Dict[str, Any]

ModuleFunc = Callable[[State, Config, ModuleState], Tuple[State, ModuleState]]

def create_module(
    func: ModuleFunc,
    input_keys: List[str],
    output_keys: List[str]
) -> Callable[[State, Config], Tuple[State, Optional[Callable]]]:
    module_state: ModuleState = {}

    def module_wrapper(state: State, config: Config) -> Tuple[State, Optional[Callable]]:
        nonlocal module_state
        missing_keys = set(input_keys) - set(state.keys())
        if missing_keys:
            raise KeyError(f"Missing required input keys: {missing_keys}")

        new_state, new_module_state = func(state, config, module_state)
        module_state = new_module_state  # Update closure state

        if isinstance(new_state, dict):
            missing_keys = set(output_keys) - set(new_state.keys())
            if missing_keys:
                raise KeyError(f"Missing required output keys: {missing_keys}")

        return new_state, None

    module_wrapper.input_keys = input_keys
    module_wrapper.output_keys = output_keys
    return module_wrapper

def compose(*modules: Callable) -> Callable[[State, Config], Tuple[State, Optional[Callable]]]:
    def composed(state: State, config: Config, module_state: ModuleState) -> Tuple[State, ModuleState]:
        current_state = state
        for module in modules:
            current_state, _ = module(current_state, config)
        return current_state, module_state

    input_keys = getattr(modules[0], 'input_keys', [])
    output_keys = getattr(modules[-1], 'output_keys', [])
    return create_module(composed, input_keys, output_keys)

def branch(
    condition: Callable[[State, Config], bool],
    if_true: Callable,
    if_false: Callable
) -> Callable[[State, Config], Tuple[State, Optional[Callable]]]:
    def branched(state: State, config: Config, module_state: ModuleState) -> Tuple[State, ModuleState]:
        if condition(state, config):
            return if_true(state, config)[0], module_state
        else:
            return if_false(state, config)[0], module_state

    input_keys = list(set(getattr(if_true, 'input_keys', []) + getattr(if_false, 'input_keys', [])))
    output_keys = list(set(getattr(if_true, 'output_keys', []) + getattr(if_false, 'output_keys', [])))
    return create_module(branched, input_keys, output_keys)

def optimize(
    module: Callable[[State, Config], Tuple[State, Optional[Callable]]],
    optimizer_func: Callable[[ModuleState], ModuleState]
) -> Callable[[State, Config], Tuple[State, Optional[Callable]]]:
    original_func = module.__closure__[0].cell_contents

    def optimized_func(state: State, config: Config, module_state: ModuleState) -> Tuple[State, ModuleState]:
        optimized_state = optimizer_func(module_state)
        return original_func(state, config, optimized_state)

    return create_module(optimized_func, module.input_keys, module.output_keys)
