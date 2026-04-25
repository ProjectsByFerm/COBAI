COMPUTE for Simple Business Math

Big picture:
This program calculates a bonus amount by multiplying base pay by a bonus rate,
then prints the result.

Key COBOL ideas:
- Numeric items are declared in `WORKING-STORAGE SECTION`.
- `COMPUTE` evaluates an arithmetic expression and stores the result.
- `DISPLAY` prints the calculated value.

Walkthrough:
- `BASE-PAY` starts at `2000`.
- `BONUS-RATE` starts at `0.10`, which means ten percent.
- `COMPUTE BONUS-AMOUNT = BASE-PAY * BONUS-RATE` calculates the bonus.
- `DISPLAY BONUS-AMOUNT` prints the result.
- `STOP RUN` ends the program.

Business interpretation:
This reflects a simple business rule where a percentage rate is applied to a
base salary or payment to determine a bonus amount.
