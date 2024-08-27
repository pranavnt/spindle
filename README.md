# Spindle

spindle is a very minimal framework for building language model programs, focused on simplicity and extensibility.

it takes some inspiration from dspy and moatless tools. it's probably pretty generous to call this a framework -- it just makes it easier to write lm programs with prettier code (core lib is like 100loc with 0 dependencies)

core ideas:
- a language model program is a series of modules that are composed together
- modules are functions that take in a state and return a new state and a next module (or None to terminate)
- you can optimize modules/programs via higher order functions
- LM frameworks should be quite minimal — users, not framework authors, should be writing the vast majority of modules

opinions behind this (basically just "oop bad"):
- modules should be pure functions, not classes
- higher order functions are a good way of implementiong LM program optimization

TODO:
- make optimization work and think through how best to do this
- add some examples