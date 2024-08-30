from core import module, compose, compile, Optimizer, EvalFunc, Program, State
from typing import List, Dict, Any
import ast
import inspect

"""optimizers should be defined by a decoration

@optimizer
def my_optimizer(program: Program, eval_func: EvalFunc) -> Program:
    # a program is just function, so we can inspect it. though idk if this is the best approach

modules will need to have some state that can be optimized — what's the cleanest way to do this??
"""
