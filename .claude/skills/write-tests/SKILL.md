---
name: write-tests
description: Use this skill to write unit tests for Python code using pytest.
---

Use this skill to write unit tests for Python code. Tests should be thorough,
maintainable, and follow pytest best practices.

## Test Structure

### File Organization

- Test files go in `tests/` directory mirroring the source structure
- Name test files `test_<module>.py`
- Name test functions `test_<behavior_being_tested>`

### No Classes

Do NOT use classes to group tests. Use plain functions instead:

```python
# WRONG - Don't use classes
class TestCalculator:
    def test_add(self):
        ...

# CORRECT - Use plain functions
def test_calculator_adds_two_numbers():
    ...

def test_calculator_handles_negative_numbers():
    ...
```

Group related tests by placing them in the same file or using pytest markers.

## Arrange-Act-Assert Pattern

Every test MUST follow the AAA pattern with clear visual separation:

```python
def test_player_gains_points_when_solving_puzzle():
    # Arrange
    player = Player(name="Alice")
    puzzle = SimplePuzzle(points=100)

    # Act
    result = player.solve_puzzle(puzzle, solution="correct_answer")

    # Assert
    assert result is True
    assert player.score == 100
```

### Guidelines

1. **Arrange**: Set up test data and dependencies (1-5 lines ideally)
2. **Act**: Execute exactly ONE action being tested (1 line)
3. **Assert**: Verify the expected outcome immediately after the action

Use blank lines to visually separate each section. Add comments (`# Arrange`, `# Act`,
`# Assert`) only when the separation isn't obvious.

## Fixtures

Move complex setup logic to fixtures. Inline setup should be minimal (1-3 lines).

### When to Use Fixtures

- Setup requires more than 3 lines
- Same setup is used across multiple tests
- Setup involves external resources (files, databases, etc.)
- Cleanup is required after tests

### Fixture Patterns

```python
import pytest

@pytest.fixture
def player():
    """A basic player with default settings."""
    return Player(name="Test Player")

@pytest.fixture
def game_with_rooms(player):
    """A fully initialized game with rooms loaded."""
    game = EscapeRoomGame()
    game.load_rooms()
    game.player = player
    return game

@pytest.fixture
def temp_config_file(tmp_path):
    """A temporary config file for testing file operations."""
    config = tmp_path / "config.json"
    config.write_text('{"difficulty": "normal"}')
    return config
```

### Fixture Scoping

Use appropriate scope to balance isolation and performance:

- `function` (default): Fresh instance per test
- `module`: Shared across tests in a file (for expensive, read-only resources)
- `session`: Shared across all tests (use sparingly)

```python
@pytest.fixture(scope="module")
def expensive_resource():
    """Shared across all tests in this module."""
    return create_expensive_resource()
```

## Pytest Features to Use

### Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("input,expected", [
    ("north", RoomName.BRIDGE),
    ("south", RoomName.ENGINEERING),
    ("invalid", None),
])
def test_parse_direction(input, expected):
    result = parse_direction(input)
    assert result == expected
```

### Testing Exceptions

```python
def test_invalid_room_raises_error():
    game = EscapeRoomGame()

    with pytest.raises(ValueError, match="Room not found"):
        game.goto_room("nonexistent")
```

### Temporary Files

Use `tmp_path` fixture for file operations:

```python
def test_save_game_creates_file(tmp_path):
    save_file = tmp_path / "save.json"
    game = EscapeRoomGame()

    game.save(save_file)

    assert save_file.exists()
```

## Assertion Guidelines

- Use plain `assert` statements
- Be specific about what you're checking
- Test behavior, not implementation details
- One logical assertion per test (multiple asserts for the same behavior is OK)

```python
# GOOD - Testing behavior
def test_puzzle_marks_as_solved_after_correct_answer():
    puzzle = SimplePuzzle()

    puzzle.attempt("correct")

    assert puzzle.is_solved is True

# BAD - Testing implementation details
def test_puzzle_internal_state():
    puzzle = SimplePuzzle()
    puzzle.attempt("correct")
    assert puzzle._internal_counter == 1  # Don't test private state
```

## Test Naming

Use descriptive names that explain the scenario and expected behavior:

```python
# GOOD
def test_player_cannot_exit_room_with_unsolved_puzzle():
def test_hint_command_shows_next_hint_when_available():
def test_solve_command_accepts_multiword_answers():

# BAD
def test_exit():
def test_hint():
def test_solve():
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_player.py

# Run with coverage
pytest --cov=src

# Run tests matching pattern
pytest -k "puzzle"
```