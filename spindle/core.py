from typing import Callable, Any, Dict, List, Optional, Tuple, Union
from functools import wraps, reduce

State = Dict[str, Any]
SimpleModuleFunc = Callable[[State], State]
ComplexModuleFunc = Callable[[State], Tuple[State, Optional[str]]]
ModuleFunc = Union[SimpleModuleFunc, ComplexModuleFunc]
Program = Callable[[State], State]
EvalFunc = Callable[[Program, List[State]], List[float]]
Optimizer = Callable[[Program, EvalFunc], Program]

def module(input_keys: List[str], output_keys: List[str], flow: bool = True):
    def decorator(func: Union[SimpleModuleFunc, ComplexModuleFunc]) -> ModuleFunc:
        @wraps(func)
        def wrapper(state: State) -> Union[State, Tuple[State, Optional[str]]]:
            missing_keys = set(input_keys) - set(state.keys())
            if missing_keys:
                raise KeyError(f"Missing required input keys: {missing_keys}")

            result = func(state)

            if flow:
                new_state, next_module = result
            else:
                new_state, next_module = result, None

            missing_keys = set(output_keys) - set(new_state.keys())
            if missing_keys:
                raise KeyError(f"Missing required output keys: {missing_keys}")

            return (new_state, next_module) if flow else new_state

        wrapper.is_module = True
        wrapper.has_transition = flow
        wrapper.input_keys = input_keys
        wrapper.output_keys = output_keys
        return wrapper
    return decorator

def compose(*modules):
    def composed_module(state: State) -> State:
        current_module = modules[0]
        module_dict = {m.__name__: m for m in modules}

        while current_module:
            if current_module.has_transition:
                state, next_module_name = current_module(state)
                if next_module_name is None:
                    break
                current_module = module_dict.get(next_module_name)
                if current_module is None:
                    raise ValueError(f"Invalid transition to non-existent module: {next_module_name}")
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
    input_keys = list(set(if_true.input_keys + if_false.input_keys))
    output_keys = list(set(if_true.output_keys + if_false.output_keys))

    @module(input_keys=input_keys, output_keys=output_keys, flow=False)
    def branching_module(state: State) -> State:
        if condition(state):
            result = if_true(state)
        else:
            result = if_false(state)
        return result[0] if isinstance(result, tuple) else result
    return branching_module
