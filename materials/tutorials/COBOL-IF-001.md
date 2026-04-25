Reading IF Logic

Big picture:
This program checks an account balance and prints one of two messages depending
on whether the balance is above a threshold.

Key COBOL ideas:
- `IF` checks whether a condition is true.
- `ELSE` handles the false case.
- `END-IF` marks the end of the decision block.

Walkthrough:
- `ACCOUNT-BALANCE` starts at `1200`.
- The condition checks whether `ACCOUNT-BALANCE > 1000`.
- Because `1200` is greater than `1000`, the program displays `PRIORITY ACCOUNT`.
- The `ELSE` path is skipped.
- `STOP RUN` ends the program.

Business interpretation:
This is a simple business rule. A balance above a threshold leads to one
customer category, while lower balances lead to another.
