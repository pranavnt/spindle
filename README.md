# Spindle

spindle is a framework for building language model programs, focused on simplicity and extensibility.

takes inspiration from dspy, moatless tools, and FP.

core ideas are:
- a program is a series of modules that are composed together
- modules are functions that take in a state and return a new state and a next module (or None to terminate)
- you can optimize modules/programs via higher order functions
- LM frameworks should be quite minimal