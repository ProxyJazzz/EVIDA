"""Deterministic Regression Test AST and Path Validator

Ensures AI-proposed regression tests are strictly bounded, syntactically valid,
and free from dangerous execution constructs prior to sandbox verification.
"""

from __future__ import annotations

import ast
from pathlib import PurePosixPath
from typing import Final

from app.domain.investigations.state_machine import LifecycleException

# Disallowed module names that must never be imported in regression tests
DISALLOWED_MODULES: Final[set[str]] = {
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "urllib3",
    "http.client",
    "httpx",
    "aiohttp",
    "pty",
    "commands",
    "multiprocessing",
    "ctypes",
    "paramiko",
    "fabric",
}

# Dangerous call names that must not be invoked
DISALLOWED_CALLS: Final[set[str]] = {
    "eval",
    "exec",
    "__import__",
    "compile",
}

# Dangerous os / shutil attributes that must not be invoked
DISALLOWED_OS_ATTRS: Final[set[str]] = {
    "system",
    "popen",
    "remove",
    "unlink",
    "rmdir",
    "chmod",
    "chown",
    "kill",
}

DISALLOWED_SHUTIL_ATTRS: Final[set[str]] = {
    "rmtree",
    "move",
}


class RegressionTestValidationError(LifecycleException):
    """Raised when an AI-generated regression test fails deterministic safety or structure validation."""

    def __init__(self, message: str, code: str = "REGRESSION_TEST_INVALID") -> None:
        super().__init__(message=message, code=code, status_code=400)


class DangerousASTVisitor(ast.NodeVisitor):
    """AST Visitor that traverses python code to detect prohibited or dangerous constructs."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.has_test_function: bool = False

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if alias.name in DISALLOWED_MODULES or base_module in DISALLOWED_MODULES:
                self.errors.append(
                    f"Import of prohibited module '{alias.name}' at line {node.lineno}"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_module = node.module.split(".")[0]
            if node.module in DISALLOWED_MODULES or base_module in DISALLOWED_MODULES:
                self.errors.append(
                    f"Import from prohibited module '{node.module}' at line {node.lineno}"
                )
            elif node.module == "os":
                for alias in node.names:
                    if alias.name in DISALLOWED_OS_ATTRS:
                        self.errors.append(
                            f"Import of prohibited os attribute '{alias.name}' at line {node.lineno}"
                        )
            elif node.module == "shutil":
                for alias in node.names:
                    if alias.name in DISALLOWED_SHUTIL_ATTRS:
                        self.errors.append(
                            f"Import of prohibited shutil attribute '{alias.name}' at line {node.lineno}"
                        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # 1. Direct built-in calls like eval(), exec(), system()
        if isinstance(node.func, ast.Name):
            if (
                node.func.id in DISALLOWED_CALLS
                or node.func.id in DISALLOWED_OS_ATTRS
                or node.func.id in DISALLOWED_SHUTIL_ATTRS
            ):
                self.errors.append(
                    f"Invocation of prohibited function '{node.func.id}' at line {node.lineno}"
                )
            elif node.func.id == "open":
                # Disallow open() in write/append modes
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = str(node.args[1].value)
                    if any(m in mode for m in ("w", "a", "x", "+")):
                        self.errors.append(
                            f"Write/append open() mode '{mode}' prohibited at line {node.lineno}"
                        )

        # 2. Attribute calls like os.system(), shutil.rmtree()
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                if module_name == "os" and attr_name in DISALLOWED_OS_ATTRS:
                    self.errors.append(
                        f"Invocation of prohibited os function 'os.{attr_name}' at line {node.lineno}"
                    )
                elif module_name == "shutil" and attr_name in DISALLOWED_SHUTIL_ATTRS:
                    self.errors.append(
                        f"Invocation of prohibited shutil function 'shutil.{attr_name}' at line {node.lineno}"
                    )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name.startswith("test_") or node.name.endswith("_test"):
            self.has_test_function = True
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node.name.startswith("test_") or node.name.endswith("_test"):
            self.has_test_function = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name.startswith("Test"):
            self.has_test_function = True
        self.generic_visit(node)


def validate_test_path(test_path: str) -> None:
    """Validate that the test path is relative, safe, and targets a python test file.

    Raises:
        RegressionTestValidationError: If path is unsafe or invalid.
    """
    if not test_path or not test_path.strip():
        raise RegressionTestValidationError(
            "Regression test path cannot be empty.",
            code="REGRESSION_PATH_INVALID",
        )

    clean_path = test_path.strip().replace("\\", "/")

    if clean_path.startswith("/") or clean_path.startswith("\\"):
        raise RegressionTestValidationError(
            f"Regression test path must be relative: '{test_path}'",
            code="REGRESSION_PATH_INVALID",
        )

    if "\0" in clean_path:
        raise RegressionTestValidationError(
            "Regression test path contains null bytes.",
            code="REGRESSION_PATH_INVALID",
        )

    parts = PurePosixPath(clean_path).parts
    if ".." in parts or "." in parts[:-1]:
        raise RegressionTestValidationError(
            f"Path traversal ('..') is prohibited in test path: '{test_path}'",
            code="REGRESSION_PATH_INVALID",
        )

    if not clean_path.endswith(".py"):
        raise RegressionTestValidationError(
            f"Regression test must be a Python (.py) file: '{test_path}'",
            code="REGRESSION_PATH_INVALID",
        )

    file_name = PurePosixPath(clean_path).name
    if not (file_name.startswith("test_") or file_name.endswith("_test.py")):
        raise RegressionTestValidationError(
            f"Regression test filename must start with 'test_' or end with '_test.py': '{file_name}'",
            code="REGRESSION_PATH_INVALID",
        )


def validate_regression_test_content(
    test_content: str,
    max_bytes: int = 20000,
) -> None:
    """Parse and inspect the test code with Python AST for syntax and safety.

    Raises:
        RegressionTestValidationError: If content is empty, oversized, invalid syntax,
                                      lacks a test function, or contains unsafe operations.
    """
    if not test_content or not test_content.strip():
        raise RegressionTestValidationError(
            "Regression test content cannot be empty.",
            code="REGRESSION_CONTENT_EMPTY",
        )

    content_bytes = len(test_content.encode("utf-8"))
    if content_bytes > max_bytes:
        raise RegressionTestValidationError(
            f"Generated test size ({content_bytes} bytes) exceeds maximum limit ({max_bytes} bytes).",
            code="REGRESSION_CONTENT_TOO_LARGE",
        )

    # Parse with Python AST
    try:
        tree = ast.parse(test_content)
    except SyntaxError as e:
        raise RegressionTestValidationError(
            f"Generated test contains invalid Python syntax: {e.msg} (line {e.lineno})",
            code="REGRESSION_SYNTAX_ERROR",
        ) from e

    # Traverse AST with safety visitor
    visitor = DangerousASTVisitor()
    visitor.visit(tree)

    if visitor.errors:
        reasons = "; ".join(visitor.errors)
        raise RegressionTestValidationError(
            f"Generated test contains unsafe operations: {reasons}",
            code="REGRESSION_SECURITY_VIOLATION",
        )

    if not visitor.has_test_function:
        raise RegressionTestValidationError(
            "Generated test must define at least one test function (e.g. def test_...) or Test class.",
            code="REGRESSION_STRUCTURE_INVALID",
        )


def validate_regression_test_proposal(
    test_path: str,
    test_content: str,
    max_bytes: int = 20000,
) -> None:
    """Validate both test path and test content."""
    validate_test_path(test_path)
    validate_regression_test_content(test_content, max_bytes=max_bytes)
