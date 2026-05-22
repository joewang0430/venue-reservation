# main.py bug hypotheses

Date: 2026-05-21
Source file: src/main.py

This note records the likely bugs identified during a static review of the Selenium booking script.

## Most likely bug

### 1. `select_date()` may report success even when the click actually failed
Estimated probability: 85%

Why:
- `test_click()` catches click exceptions and only prints them.
- `select_date()` calls `test_click(...)` and then still returns `True`.
- There is no hard verification that the target date was actually selected.

Impact:
- The script may continue under the false assumption that the page is showing `TARGET_DATE`.
- Later slot checks may be running against the wrong date.

Relevant code areas:
- `test_click()`
- `select_date()`

## Other likely issues

### 2. Date switching is not confirmed before continuing
Estimated probability: 75%

Why:
- The confirmation wait after clicking the date is commented out.
- The code relies on `time.sleep(0.3)` instead of checking page state.
- On a slow or dynamic page, the old slot grid may still be visible when the next logic runs.

Impact:
- Slot detection can read stale or wrong data.

### 3. `REFRESH_DELAY` is defined but never used
Estimated probability: 70%

Why:
- `REFRESH_DELAY = 0.25` exists in config.
- The polling loop refreshes repeatedly without using that delay.

Impact:
- The page may be refreshed too aggressively.
- This can increase instability, stale references, or anti-bot risk.

### 4. `selenium` is unresolved in the current environment
Estimated probability: 65% in the current workspace environment

Why:
- Editor diagnostics report unresolved imports for `selenium` and its submodules.

Impact:
- The script may not run in the current interpreter until the package/environment issue is fixed.

Note:
- This may be an environment issue rather than a logic bug in the code itself.

### 5. `Opens at ...` time parsing is brittle
Estimated probability: 45%

Why:
- The code assumes the slot text contains `Opens at`.
- It then assumes the regex match exists and directly calls `time_match.group(0)`.

Impact:
- Small UI text changes could cause a crash or unexpected behavior.

### 6. Outer `except TimeoutException` in the polling loop is likely redundant
Estimated probability: 40%

Why:
- `book_if_open()` already catches its own `TimeoutException` and returns `False`.
- The outer try/except probably does not catch much in normal flow.

Impact:
- Not usually fatal, but suggests the control flow is misleading.

## Working conclusion

The highest-confidence issue is this:

`select_date()` does not reliably prove that the requested date became active before the script proceeds.

That can cause downstream checks and booking attempts to operate on the wrong page state.

## Intended future use

This file is meant to preserve the current bug hypotheses so later review and fixes can refer back to them.
