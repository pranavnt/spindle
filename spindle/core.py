from typing import Callable, Any, Dict, List, Optional, TypeVar, Tuple
from functools import wraps

State = Dict[str, Any]
T = TypeVar('T')
NextModule = Callable[[State], Tuple[State, Optional['NextModule']]]
ModuleFunc = Callable[[State], Tuple[State, NextModule]]
Program = Callable[[State], State]
EvaluationFunction = Callable[[Program, List[State]], float]

ExecutionHistory = List[Tuple[State, str]]

def terminate(state: State) -> Tuple[State, None]:
    """Terminal module that signals the end of a program."""
    return state, None

def module(input_keys: Optional[List[str]] = None, output_keys: Optional[List[str]] = None):
    """Decorator for creating modules with optional input/output validation."""
    def decorator(func: ModuleFunc) -> ModuleFunc:
        @wraps(func)
        def wrapper(state: State) -> Tuple[State, NextModule]:
            if input_keys:
                missing_keys = set(input_keys) - set(state.keys())
                if missing_keys:
                    raise KeyError(f"Missing required input keys: {missing_keys}")

            new_state, next_module = func(state)

            if output_keys:
                missing_keys = set(output_keys) - set(new_state.keys())
                if missing_keys:
                    raise KeyError(f"Missing required output keys: {missing_keys}")

            return new_state, next_module

        wrapper.is_module = True
        wrapper.input_keys = input_keys
        wrapper.output_keys = output_keys
        return wrapper
    return decorator

def create_program(initial_module: ModuleFunc) -> Callable[[State], Tuple[State, ExecutionHistory]]:
    """Creates a runnable program from an initial module that returns execution history."""
    def run(initial_state: State) -> Tuple[State, ExecutionHistory]:
        state = initial_state.copy()
        current_module = initial_module
        history = []

        while current_module is not None:
            module_name = current_module.__name__
            state, current_module = current_module(state)
            history.append((state.copy(), module_name))

        return state, history

    return run

def compose(*modules: ModuleFunc) -> ModuleFunc:
    """Composes multiple modules into a single module."""
    def composed_module(state: State) -> Tuple[State, NextModule]:
        for module in modules[:-1]:
            state, _ = module(state)
        return modules[-1](state)
    return composed_module

def branch(condition: Callable[[State], bool], if_true: ModuleFunc, if_false: ModuleFunc) -> ModuleFunc:
    """Creates a conditional branching module."""
    def branching_module(state: State) -> Tuple[State, NextModule]:
        if condition(state):
            return if_true(state)
        else:
            return if_false(state)
    return branching_module

def modify_module(module: ModuleFunc, modifier: Callable[[ModuleFunc], ModuleFunc]) -> ModuleFunc:
    """Higher-order function to modify a module."""
    @wraps(module)
    def modified_module(state: State) -> Tuple[State, NextModule]:
        new_state, next_module = modifier(module)(state)
        return new_state, modify_module(next_module, modifier) if next_module else None
    return modified_module

def optimize(program: Program,
             evaluation_func: EvaluationFunction,
             test_cases: List[State],
             iterations: int = 100,
             mutation_func: Callable[[Program], Program] = lambda x: x) -> Program:
    """Optimize the program using a simple hill-climbing strategy."""
    best_program = program
    best_score = evaluation_func(program, test_cases)

    for _ in range(iterations):
        mutated_program = mutation_func(best_program)
        mutated_score = evaluation_func(mutated_program, test_cases)

        if mutated_score > best_score:
            best_program = mutated_program
            best_score = mutated_score

    return best_program