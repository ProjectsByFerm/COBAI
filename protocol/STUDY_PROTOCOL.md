# COBAI Study Protocol

## Participant Flow

1. Screen for basic eligibility
2. Collect consent
3. Collect background questions
4. Assign condition
5. Run pre-test
6. Deliver lesson content
7. Run timed comprehension task
8. Run post-test
9. Collect short survey

## Conditions

### LLM Condition

Participants receive lesson explanations from the guardrailed COBOL coach
through the external API.

### Static Condition

Participants receive matched written tutorial content for the same lesson.

## Researcher Checklist

Before a session:

- confirm the prompt version is locked
- confirm the lesson content version is locked
- confirm the API key is available for LLM sessions
- confirm exports are writing correctly

After a session:

- confirm completion status
- note technical issues
- preserve raw records without editing them manually

## Pilot Questions

- Are the instructions clear?
- Are the tasks too easy or too hard?
- Does timing get recorded correctly?
- Does the coach stay within the guardrails?
- Are treatment and control materials balanced?
