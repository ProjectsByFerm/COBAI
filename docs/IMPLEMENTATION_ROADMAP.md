# COBAI Implementation Roadmap

## Phase 1: Lock The Product Scope

Goal: keep the project realistic.

- Define the assistant as a guardrailed COBOL learning coach
- Limit the first build to beginner COBOL concepts
- Keep the interface local and lightweight
- Use a local Ollama API instead of model training

Exit criteria:

- The product can be explained in one paragraph
- The research question matches the implemented system

## Phase 2: Build Matched Learning Materials

Goal: create balanced treatment and control content.

- Write 2-3 short COBOL lessons
- Write matched static tutorials
- Write one fixed guardrail prompt
- Create pre-test and post-test items
- Create one timed comprehension item per module

Exit criteria:

- One lesson can be run manually without writing new content

## Phase 3: Build The Application MVP

Goal: make one complete lesson runnable.

- Implement the API client
- Implement the guardrailed coach wrapper
- Implement study mode and exports
- Save CSV and JSONL results locally

Exit criteria:

- One participant can complete a full session end-to-end

## Phase 4: Pilot

Goal: test the workflow before real data collection.

- Run a few practice sessions
- Check task clarity
- Check response stability
- Check that exports and timing are captured correctly

Exit criteria:

- The study runner produces usable, consistent output

## Phase 5: Expand

Goal: strengthen the project after the MVP works.

- Add more COBOL lessons
- Add a simple web interface if needed
- Improve analysis scripts
- Refine surveys and exclusions

Exit criteria:

- The project is ready for a stronger final CS499 submission
