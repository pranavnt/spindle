# core.py

from typing import Callable, Any, Dict, List, Optional, Tuple, Union
from functools import wraps, reduce

State = Dict[str, Any]
SimpleModuleFunc = Callable[[State], State]
ComplexModuleFunc = Callable[[State], Tuple[State, Optional[str]]]
ModuleFunc = Union[SimpleModuleFunc, ComplexModuleFunc]
Program = Callable[[State], State]

def module(input_keys: Optional[List[str]] = None, output_keys: Optional[List[str]] = None, has_transition: bool = True):
    def decorator(func: Union[SimpleModuleFunc, ComplexModuleFunc]) -> ModuleFunc:
        @wraps(func)
        def wrapper(state: State) -> Union[State, Tuple[State, Optional[str]]]:
            if input_keys:
                missing_keys = set(input_keys) - set(state.keys())
                if missing_keys:
                    raise KeyError(f"Missing required input keys: {missing_keys}")

            result = func(state)

            if has_transition:
                new_state, next_module = result
            else:
                new_state, next_module = result, None

            if output_keys:
                missing_keys = set(output_keys) - set(new_state.keys())
                if missing_keys:
                    raise KeyError(f"Missing required output keys: {missing_keys}")

            return (new_state, next_module) if has_transition else new_state

        wrapper.is_module = True
        wrapper.has_transition = has_transition
        return wrapper
    return decorator

def compose(*modules: ModuleFunc) -> ModuleFunc:
    @module()
    def composed_module(state: State) -> Tuple[State, Optional[str]]:
        def reducer(acc: Tuple[State, Optional[str]], mod: ModuleFunc) -> Tuple[State, Optional[str]]:
            if acc[1] is not None:  # If a transition has been specified, stop processing
                return acc
            if mod.has_transition:
                return mod(acc[0])
            else:
                return mod(acc[0]), None

        return reduce(reducer, modules, (state, None))

    return composed_module

def compile(modules: List[ModuleFunc], args: Dict[str, Any] = {}) -> Program:
    def program(initial_state: State) -> State:
        state = {**initial_state, **args}

        def reducer(acc: Tuple[State, Optional[str]], mod: ModuleFunc) -> Tuple[State, Optional[str]]:
            state, next_module = acc
            if next_module is not None:
                if next_module not in [m.__name__ for m in modules]:
                    raise ValueError(f"Invalid transition to non-existent module: {next_module}")
                return state, next_module  # Skip until we reach the specified next module

            if mod.__name__ == next_module or next_module is None:
                if mod.has_transition:
                    return mod(state)
                else:
                    return mod(state), None

            return state, next_module  # Keep skipping

        final_state, _ = reduce(reducer, modules, (state, None))
        return final_state

    return program

def branch(condition: Callable[[State], bool], if_true: ModuleFunc, if_false: ModuleFunc) -> ModuleFunc:
    @module()
    def branching_module(state: State) -> Tuple[State, Optional[str]]:
        if condition(state):
            result = if_true(state)
        else:
            result = if_false(state)

        if isinstance(result, tuple):
            return result
        else:
            return (result, None)
    return branching_module
