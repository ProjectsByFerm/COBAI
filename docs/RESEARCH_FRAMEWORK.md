# COBAI Research Framework

## Study Intent

COBAI studies whether a guardrailed, API-backed COBOL learning agent can help
novice developers understand beginner COBOL better than a matched static
tutorial.

The project is exploratory and intentionally modest:

- no custom model training
- no fine-tuning
- no production deployment
- small pilot-friendly study design

## Research Question

Does a guardrailed, API-backed COBOL learning agent improve novice developers'
comprehension and timed task performance compared with a matched static COBOL
tutorial?

## Study Type

- exploratory between-subjects comparison
- convenience sample of CS students or beginner developers
- short local study session
- lesson-level measurement rather than full course evaluation

## Conditions

### Treatment: Guardrailed COBOL Coach

Participants use COBAI in a constrained lesson flow. The system sends a fixed
guardrail prompt plus lesson-specific context to an external LLM API.

The treatment is standardized by:

- same model
- same prompt version
- same lesson content
- same timing structure

### Control: Static Tutorial

Participants receive written COBOL learning material that covers the same code
snippet and concepts without the LLM interaction.

## Outcomes

Primary outcomes:

- post-test score
- timed task accuracy
- timed task completion time

Secondary outcomes:

- pre/post gain
- confidence rating
- usefulness rating

## Validity Risks

- Small sample sizes should be reported honestly
- Prompt changes should be versioned
- Treatment and control content must stay aligned
- API failures should be tracked clearly
- Novelty effects should be noted through participant background questions

## Deliverables

- runnable COBOL coach MVP
- 2-3 lesson modules
- matched static tutorials
- locked prompt guardrails
- exportable result files
- descriptive analysis summary
