from typing import Callable, Any, Dict, List, Tuple, Optional, Union
from functools import wraps

State = Dict[str, Any]
Config = Dict[str, Any]
ModuleState = Dict[str, Any]

ModuleFunc = Callable[[State, Config, ModuleState], Tuple[Union[State, List[State]], ModuleState]]

OptimizerFunc = Callable[[ModuleFunc, Config], Config]

def module(input_keys: List[str], output_keys: Union[List[str], List[List[str]]]):
    def decorator(func: ModuleFunc) -> Callable[[State, Config], Tuple[Union[State, List[State]], Optional[Callable]]]:
        module_state: ModuleState = {}

        @wraps(func)
        def wrapper(state: State, config: Config) -> Tuple[Union[State, List[State]], Optional[Callable]]:
            nonlocal module_state
            missing_keys = set(input_keys) - set(state.keys())
            if missing_keys:
                raise KeyError(f"Missing required input keys: {missing_keys}")

            new_states, new_module_state = func(state, config, module_state)
            module_state = new_module_state  # Update closure state

            if isinstance(new_states, dict):
                new_states = [new_states]

            for i, new_state in enumerate(new_states):
                if isinstance(output_keys[0], list):
                    current_output_keys = output_keys[i]
                else:
                    current_output_keys = output_keys
                missing_keys = set(current_output_keys) - set(new_state.keys())
                if missing_keys:
                    raise KeyError(f"Missing required output keys: {missing_keys}")

            return new_states if len(new_states) > 1 else new_states[0], None

        wrapper.input_keys = input_keys
        wrapper.output_keys = output_keys
        return wrapper

    return decorator

def compose(*modules: Callable) -> Callable[[State, Config], Tuple[Union[State, List[State]], Optional[Callable]]]:
    @module(modules[0].input_keys, modules[-1].output_keys)
    def composed(state: State, config: Config, module_state: ModuleState) -> Tuple[Union[State, List[State]], ModuleState]:
        current_state = state
        for module in modules:
            result, _ = module(current_state, config)
            if isinstance(result, list):
                # If a module returns multiple states, merge them into a single state
                current_state = {}
                for r in result:
                    current_state.update(r)
            else:
                current_state = result
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

def fork(*modules: Callable) -> Callable[[State, Config], Tuple[List[State], Optional[Callable]]]:
    input_keys = modules[0].input_keys
    output_keys = [m.output_keys for m in modules]

    @module(input_keys, output_keys)
    def forked(state: State, config: Config, module_state: ModuleState) -> Tuple[List[State], ModuleState]:
        results = []
        for module in modules:
            result, _ = module(state, config)
            results.append(result)
        return results, module_state

    return forked
