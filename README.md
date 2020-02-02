# potanusi
A simple tool to create an electronic control system.

# todo:
- parsing
    - check errors in yaml
    - tests
    - factors for parameters
    - share submodule pins for connecting
    - smart comparison for input and output diapasons
    - parse reciprocals
- connecting
    - connecting of nested modules
    - connecting of pins
    - global synonyms for parameters
    - compare reciprocals while connecting
- searching
    - all paths through several points
    - points fixation (required/)
    - part of path fixation
- system configuration
    - contains fixed points and paths
    - inheritance of configurations
 
# Type of nodes
- module - structural component of the system
- pin - allow to connect modules ant other nodes to each other 
- tool
    - tool can make some actions with connected modules
    - some tools:
        - compiler/linker
        - cmake generator
        - altium designer schematic generator
        - altium designer pcb generator
        - microcap project genertor
        - isis project generator
        - ...