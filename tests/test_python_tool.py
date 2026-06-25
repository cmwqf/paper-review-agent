"""Purpose: Tests for the restricted Python calculation tool."""

from reviewer.tools.python_tool import RestrictedPythonTool


def test_python_tool_runs_small_calculation() -> None:
    result = RestrictedPythonTool({}).run(
        """
values = [83.1, 84.0, 84.4]
baseline = 82.0
print([round(value - baseline, 2) for value in values])
"""
    )

    assert result.ok
    assert "[1.1, 2.0, 2.4]" in result.stdout
    assert "status: ok" in result.render()


def test_python_tool_blocks_filesystem_import() -> None:
    result = RestrictedPythonTool({}).run(
        """
import os
print(os.listdir("."))
"""
    )

    assert not result.ok
    assert "forbidden import 'os'" in result.error


def test_python_tool_blocks_open_builtin() -> None:
    result = RestrictedPythonTool({}).run("print(open('x.txt').read())")

    assert not result.ok
    assert "forbidden name 'open'" in result.error
