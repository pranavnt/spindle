from typing import Callable, Any, Dict, List, Tuple, Optional, Union
from functools import wraps

State = Dict[str, Any]
Config = Dict[str, Any]
ModuleState = Dict[str, Any]
ModuleFunc = Callable[[State, Config, ModuleState], Tuple[State, ModuleState, Optional[Callable]]]
ProgramFunc = Callable[[State, Config], Tuple[State, Optional[Callable]]]

def module(input_keys: List[str], output_keys: List[str], flow: bool = False):
    def decorator(func: ModuleFunc) -> ProgramFunc:
        module_state: ModuleState = {}

        @wraps(func)
        def wrapper(state: State, config: Config) -> Tuple[State, Optional[Callable]]:
            nonlocal module_state
            missing_keys = set(input_keys) - set(state.keys())
            if missing_keys:
                raise KeyError(f"Missing required input keys: {missing_keys}")

            new_state, new_module_state, next_module = func(state, config, module_state)
            module_state = new_module_state  # Update closure state

            if flow:
                original_state = new_state.copy()
                while next_module:
                    new_state, next_module = next_module(new_state, config)
                new_state = {**original_state, **new_state}  # Merge states

            missing_keys = set(output_keys) - set(new_state.keys())
            if missing_keys:
                raise KeyError(f"Missing required output keys: {missing_keys}")

            return new_state, None

        wrapper.input_keys = input_keys
        wrapper.output_keys = output_keys
        wrapper.flow = flow
        return wrapper
    return decorator

def compose(*modules: ProgramFunc) -> ProgramFunc:
    @module(modules[0].input_keys, modules[-1].output_keys)
    def composed(state: State, config: Config, module_state: ModuleState) -> Tuple[State, ModuleState, Optional[Callable]]:
        current_state = state
        for module in modules:
            new_state, _ = module(current_state, config)
            current_state = {**current_state, **new_state}  # Accumulate all states
        return current_state, module_state, None
    return composed
