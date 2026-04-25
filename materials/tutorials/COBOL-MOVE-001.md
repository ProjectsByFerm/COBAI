MOVE and DISPLAY Basics

Big picture:
This program stores a customer name, copies it into another variable, and then
prints that copied value.

Key COBOL ideas:
- `WORKING-STORAGE SECTION` is where simple program data is declared.
- `PIC X(10)` means a text field up to 10 characters long.
- `MOVE A TO B` copies the value from `A` into `B`.
- `DISPLAY` prints the value of a field.

Walkthrough:
- `CUSTOMER-NAME` starts with the value `ALICE`.
- `OUTPUT-NAME` is declared as another text field.
- `MOVE CUSTOMER-NAME TO OUTPUT-NAME` copies `ALICE` into `OUTPUT-NAME`.
- `DISPLAY OUTPUT-NAME` prints the copied value.
- `STOP RUN` ends the program.

Business interpretation:
This pattern is common when a program reads a stored value, copies it into an
output field, and then shows or reports it.
