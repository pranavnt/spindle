import ast
import inspect
from typing import Callable, Any, Dict, List, Optional, Tuple, Union
import textwrap
from functools import wraps, reduce

State = Dict[str, Any]
SimpleModuleFunc = Callable[[State], State]
ComplexModuleFunc = Callable[[State], Tuple[State, Optional[str]]]
ModuleFunc = Union[SimpleModuleFunc, ComplexModuleFunc]
Program = Callable[[State], State]
EvalFunc = Callable[[Program, List[State]], List[float]]
Optimizer = Callable[[Program, EvalFunc], Program]

def analyze_function(func):
    source = inspect.getsource(func)
    # Remove any common leading whitespace from every line in the source
    source = textwrap.dedent(source)
    tree = ast.parse(source)

    input_keys = set()
    output_keys = set()

    class KeyVisitor(ast.NodeVisitor):
        def visit_Subscript(self, node):
            if isinstance(node.value, ast.Name) and node.value.id == 'state':
                if isinstance(node.slice, ast.Str):  # For Python 3.8 and earlier
                    key = node.slice.s
                elif isinstance(node.slice, ast.Constant):  # For Python 3.9+
                    key = node.slice.value
                else:
                    return  # Skip if it's not a string key

                if isinstance(node.ctx, ast.Load):
                    input_keys.add(key)
                elif isinstance(node.ctx, ast.Store):
                    output_keys.add(key)
            self.generic_visit(node)

    KeyVisitor().visit(tree)
    return list(input_keys), list(output_keys)

def module(has_transition: bool = True):
    def decorator(func: Union[SimpleModuleFunc, ComplexModuleFunc]) -> ModuleFunc:
        input_keys, output_keys = analyze_function(func)

        @wraps(func)
        def wrapper(state: State) -> Union[State, Tuple[State, Optional[str]]]:
            missing_keys = set(input_keys) - set(state.keys())
            if missing_keys:
                raise KeyError(f"Missing required input keys: {missing_keys}")

            result = func(state)

            if has_transition:
                new_state, next_module = result
            else:
                new_state, next_module = result, None

            missing_keys = set(output_keys) - set(new_state.keys())
            if missing_keys:
                raise KeyError(f"Missing required output keys: {missing_keys}")

            return (new_state, next_module) if has_transition else new_state

        wrapper.is_module = True
        wrapper.has_transition = has_transition
        wrapper.input_keys = input_keys
        wrapper.output_keys = output_keys
        return wrapper
    return decorator

def compose(*modules: ModuleFunc) -> ModuleFunc:
    @module()
    def composed_module(state: State) -> Tuple[State, Optional[str]]:
        def reducer(acc: Tuple[State, Optional[str]], mod: ModuleFunc) -> Tuple[State, Optional[str]]:
            if acc[1] is not None:
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
            return result, None
    return branching_module
