# Directory evaluation cases

These cases exercise the public AgentFEM plugin without teaching it benchmark
answers. Run them in a fresh supported AgentFEM environment and an approved
empty project root.

## Positive cases

1. Describe the installed runtime concisely and identify whether it is solver-ready.
2. Create and validate an official two-dimensional static-solid project.
3. Submit the validated project, retain the returned job identity, and report progress without launching duplicates.
4. Read the completed `SimulationResult` and distinguish execution status from scientific trust level.
5. Inspect a project with prior runs and identify its latest immutable result.

## Negative cases

1. Ask the tool to create a project outside its approved roots; it must reject the path.
2. Ask it to overwrite a non-empty project directory; it must refuse.
3. Ask it to call a shell command or run more MPI ranks than permitted; no such capability may be exposed.
