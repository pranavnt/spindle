from typing import Callable, Any, Dict, List, Optional, Tuple, Union
from functools import wraps

State = Dict[str, Any]
SimpleModuleFunc = Callable[[State], State]
ComplexModuleFunc = Callable[[State], Tuple[State, Optional['ModuleFunc']]]
ModuleFunc = Callable[[State], Tuple[State, Optional['ModuleFunc']]]

def module(input_keys: List[str], output_keys: List[str], flow: bool = False):
    def decorator(func: Union[SimpleModuleFunc, ComplexModuleFunc]) -> ModuleFunc:
        @wraps(func)
        def wrapper(state: State) -> Tuple[State, Optional[ModuleFunc]]:
            missing_keys = set(input_keys) - set(state.keys())
            if missing_keys:
                raise KeyError(f"Missing required input keys: {missing_keys}")

            if flow:
                new_state, next_module = func(state)
                if next_module is not None and not hasattr(next_module, 'is_module'):
                    raise ValueError("Next module must be a valid module function or None")
            else:
                new_state = func(state)
                next_module = None

            if isinstance(new_state, dict):
                missing_keys = set(output_keys) - set(new_state.keys())
                if missing_keys:
                    raise KeyError(f"Missing required output keys: {missing_keys}")

            return new_state, next_module

        setattr(wrapper, 'is_module', True)
        setattr(wrapper, 'has_transition', flow)
        setattr(wrapper, 'input_keys', input_keys)
        setattr(wrapper, 'output_keys', output_keys)
        return wrapper
    return decorator

def compose(*modules):
    def composed_module(state: State) -> State:
        for module in modules:
            state, next_module = module(state)
            while next_module:
                state, next_module = next_module(state)
        return state

    return composed_module

def branch(condition: Callable[[State], bool], if_true: ModuleFunc, if_false: ModuleFunc) -> ModuleFunc:
    input_keys = list(set(getattr(if_true, 'input_keys', []) + getattr(if_false, 'input_keys', [])))
    output_keys = list(set(getattr(if_true, 'output_keys', []) + getattr(if_false, 'output_keys', [])))

    @module(input_keys=input_keys, output_keys=output_keys, flow=False)
    def branching_module(state: State) -> State:
        if condition(state):
            return if_true(state)[0]
        else:
            return if_false(state)[0]
    return branching_module
