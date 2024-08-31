from typing import Callable, Any, Dict, List, Tuple, Optional
from functools import wraps

State = Dict[str, Any]
Config = Dict[str, Any]
ModuleState = Dict[str, Any]

ModuleFunc = Callable[[State, Config, ModuleState], Tuple[State, ModuleState]]

# Type definition for optimizer functions
OptimizerFunc = Callable[[ModuleFunc, Config], Config]

def module(input_keys: List[str], output_keys: List[str]):
    def decorator(func: ModuleFunc) -> Callable[[State, Config], Tuple[State, Optional[Callable]]]:
        module_state: ModuleState = {}

        @wraps(func)
        def wrapper(state: State, config: Config) -> Tuple[State, Optional[Callable]]:
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

        wrapper.input_keys = input_keys
        wrapper.output_keys = output_keys
        return wrapper

    return decorator

def compose(*modules: Callable) -> Callable[[State, Config], Tuple[State, Optional[Callable]]]:
    @module(modules[0].input_keys, modules[-1].output_keys)
    def composed(state: State, config: Config, module_state: ModuleState) -> Tuple[State, ModuleState]:
        current_state = state
        for module in modules:
            current_state, _ = module(current_state, config)
        return current_state, module_state

    return composed

def branch(
    condition: Callable[[State, Config], bool],
    if_true: Callable,
    if_false: Callable
) -> Callable[[State, Config], Tuple[State, Optional[Callable]]]:
    input_keys = list(set(if_true.input_keys + if_false.input_keys))
    output_keys = list(set(if_true.output_keys + if_false.output_keys))

    @module(input_keys, output_keys)
    def branched(state: State, config: Config, module_state: ModuleState) -> Tuple[State, ModuleState]:
        if condition(state, config):
            return if_true(state, config)[0], module_state
        else:
            return if_false(state, config)[0], module_state

    return branched
