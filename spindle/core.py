from typing import Callable, Any, Dict, List, Optional, Tuple, Union
from functools import wraps, reduce

State = Dict[str, Any]
SimpleModuleFunc = Callable[[State], State]
ComplexModuleFunc = Callable[[State], Tuple[State, Optional[Callable]]]
ModuleFunc = Union[SimpleModuleFunc, ComplexModuleFunc]
Program = Callable[[State], State]
EvalFunc = Callable[[Program, List[State]], List[float]]
Optimizer = Callable[[Program, EvalFunc], Program]

def module(input_keys: List[str], output_keys: List[str], flow: bool = False):
    def decorator(func: Union[SimpleModuleFunc, ComplexModuleFunc]) -> ModuleFunc:
        @wraps(func)
        def wrapper(state: State) -> Union[State, Tuple[State, Optional[Callable]]]:
            missing_keys = set(input_keys) - set(state.keys())
            if missing_keys:
                raise KeyError(f"Missing required input keys: {missing_keys}")

            result = func(state)

            if flow:
                new_state, next_module = result
            else:
                new_state, next_module = result, None

            if isinstance(new_state, dict):
                missing_keys = set(output_keys) - set(new_state.keys())
                if missing_keys:
                    raise KeyError(f"Missing required output keys: {missing_keys}")

            return (new_state, next_module) if flow else new_state

        setattr(wrapper, 'is_module', True)
        setattr(wrapper, 'has_transition', flow)
        setattr(wrapper, 'input_keys', input_keys)
        setattr(wrapper, 'output_keys', output_keys)
        return wrapper
    return decorator

def compose(*modules):
    def composed_module(state: State) -> State:
        current_module = modules[0]

        while current_module:
            if getattr(current_module, 'has_transition', False):
                state, next_module = current_module(state)
                if next_module is None:
                    break
                current_module = next_module
            else:
                state = current_module(state)
                # Move to the next module in the original order
                current_index = modules.index(current_module)
                if current_index + 1 < len(modules):
                    current_module = modules[current_index + 1]
                else:
                    break

        return state

    return composed_module

def branch(condition: Callable[[State], bool], if_true: ModuleFunc, if_false: ModuleFunc) -> ModuleFunc:
    input_keys = list(set(getattr(if_true, 'input_keys', []) + getattr(if_false, 'input_keys', [])))
    output_keys = list(set(getattr(if_true, 'output_keys', []) + getattr(if_false, 'output_keys', [])))

    @module(input_keys=input_keys, output_keys=output_keys, flow=False)
    def branching_module(state: State) -> State:
        if condition(state):
            result = if_true(state)
        else:
            result = if_false(state)
        return result[0] if isinstance(result, tuple) else result
    return branching_module
