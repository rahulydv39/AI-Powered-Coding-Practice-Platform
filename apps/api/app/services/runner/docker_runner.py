"""Docker-based isolated code execution runner.

SECURITY BOUNDARY:
- Student code is NEVER executed directly on the host machine.
- Ephemeral containers run with dropped network, non-root user, read-only root,
  and strict cgroup limits (CPU, RAM, PID limits, execution timeout).
- If Docker is unavailable, the runner refuses execution and returns a clear
  prerequisite message rather than falling back to host execution.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

from app.services.runner.models import RunResult, TestItemResult

logger = logging.getLogger(__name__)

# Configurable execution parameters
DOCKER_IMAGE = "python:3.12-slim"
EXECUTION_TIMEOUT_SECONDS = 5.0
MAX_OUTPUT_BYTES = 10 * 1024  # 10 KB output limit
MAX_SOURCE_CODE_BYTES = 20 * 1024  # 20 KB limit


class DockerSandboxRunner:
    """Manages ephemeral containerized execution of student code."""

    def __init__(
        self,
        image: str = DOCKER_IMAGE,
        timeout: float = EXECUTION_TIMEOUT_SECONDS,
        max_output_bytes: int = MAX_OUTPUT_BYTES,
    ):
        self.image = image
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes

    @staticmethod
    def get_docker_binary() -> Optional[str]:
        """Resolve path to Docker binary including common macOS install locations."""
        docker_bin = shutil.which("docker")
        if docker_bin:
            return docker_bin
        for candidate in [
            os.path.expanduser("~/.docker/bin/docker"),
            "/usr/local/bin/docker",
            "/opt/homebrew/bin/docker",
            "/Applications/Docker.app/Contents/Resources/bin/docker",
        ]:
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None

    @classmethod
    def is_docker_available(cls) -> bool:
        """Check if Docker CLI and daemon are operational on the host system."""
        docker_bin = cls.get_docker_binary()
        if not docker_bin:
            return False
        try:
            result = subprocess.run(
                [docker_bin, "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            return result.returncode == 0
        except Exception:
            return False

    def run_submission(
        self,
        student_code: str,
        test_harness_code: str,
    ) -> RunResult:
        """Execute student code and test suite in an isolated ephemeral container.

        If Docker is not running or not installed, refuses execution and returns
        a structured runner_unavailable response.
        """
        # Validate input size
        if len(student_code.encode("utf-8")) > MAX_SOURCE_CODE_BYTES:
            return RunResult(
                status="error",
                error_message=f"Source code exceeds maximum allowed size ({MAX_SOURCE_CODE_BYTES} bytes)",
                docker_available=self.is_docker_available(),
            )

        # Check Docker availability
        if not self.is_docker_available():
            logger.warning(
                "Execution requested but Docker is not available on host. "
                "Refusing host execution for security."
            )
            return RunResult(
                status="runner_unavailable",
                passed=0,
                failed=0,
                total=0,
                tests=[],
                execution_time_ms=0.0,
                stdout="",
                stderr="",
                error_message=(
                    "Docker sandbox is unavailable on this host. For security reasons, "
                    "student-submitted code is never executed directly on the host machine. "
                    "Please install and start Docker Desktop or OrbStack to run tests."
                ),
                docker_available=False,
            )

        start_time = time.time()
        temp_dir: Optional[str] = None

        try:
            # 1. Create a dedicated temporary directory with no access to host secrets
            temp_dir = tempfile.mkdtemp(prefix="ai_coding_gym_sandbox_")

            # 2. Write the student code and the test harness into the sandbox directory
            solution_path = os.path.join(temp_dir, "solution.py")
            harness_path = os.path.join(temp_dir, "test_harness.py")

            with open(solution_path, "w", encoding="utf-8") as f:
                f.write(student_code)

            with open(harness_path, "w", encoding="utf-8") as f:
                f.write(test_harness_code)

            # Ensure files are readable by non-root user (1000:1000)
            os.chmod(temp_dir, 0o755)
            os.chmod(solution_path, 0o644)
            os.chmod(harness_path, 0o644)

            # 3. Construct hardened Docker command
            # Security controls:
            # - --rm: Remove container immediately on exit
            # - --network none: Drop all networking (prevents SSRF, data exfiltration)
            # - --user 1000:1000: Non-root execution
            # - --read-only: Read-only root filesystem
            # - --tmpfs /tmp: Disposable memory-backed tmpfs with noexec and nosuid
            # - --cpus 0.5: Limit CPU consumption to 0.5 cores
            # - --memory 128m: Limit RAM to 128 MB (prevents host OOM)
            # - --pids-limit 32: Prevent fork-bombs
            # - -v temp_dir:/workspace:ro: Mount sandbox directory read-only
            # - No Docker socket mounted
            docker_bin = self.get_docker_binary() or "docker"
            docker_cmd = [
                docker_bin,
                "run",
                "--rm",
                "--network",
                "none",
                "--user",
                "1000:1000",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=16m",
                "--cpus",
                "0.5",
                "--memory",
                "128m",
                "--pids-limit",
                "32",
                "-v",
                f"{temp_dir}:/workspace:ro",
                "-w",
                "/workspace",
                self.image,
                "python3",
                "test_harness.py",
            ]

            logger.info("Starting isolated container execution with timeout=%ss", self.timeout)

            # 4. Execute with strict subprocess timeout
            process = subprocess.run(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
            )

            execution_time_ms = round((time.time() - start_time) * 1000, 2)

            raw_stdout = (process.stdout or "")[: self.max_output_bytes]
            raw_stderr = (process.stderr or "")[: self.max_output_bytes]

            # 5. Parse test results from test harness JSON output
            # The test harness emits structured JSON as its final output line
            return self._parse_harness_output(
                raw_stdout, raw_stderr, process.returncode, execution_time_ms
            )

        except subprocess.TimeoutExpired:
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning("Sandbox execution timed out after %ss", self.timeout)
            return RunResult(
                status="timeout",
                passed=0,
                failed=0,
                total=0,
                tests=[],
                execution_time_ms=execution_time_ms,
                error_message=f"Execution timed out ({self.timeout}s limit exceeded). Check for infinite loops.",
                docker_available=True,
            )

        except Exception as exc:
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.exception("Unexpected error during container execution: %s", exc)
            return RunResult(
                status="error",
                passed=0,
                failed=0,
                total=0,
                tests=[],
                execution_time_ms=execution_time_ms,
                error_message=f"Container execution error: {str(exc)}",
                docker_available=True,
            )

        finally:
            # 6. Always clean up temporary directory and files
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_harness_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
        execution_time_ms: float,
    ) -> RunResult:
        """Parse structured JSON emitted by the test harness."""
        # Find JSON payload in stdout lines
        lines = stdout.strip().splitlines()
        json_data = None

        for line in reversed(lines):
            line_str = line.strip()
            if line_str.startswith("{") and line_str.endswith("}"):
                try:
                    json_data = json.loads(line_str)
                    break
                except json.JSONDecodeError:
                    continue

        if json_data and isinstance(json_data, dict) and "tests" in json_data:
            tests = [
                TestItemResult(
                    name=t.get("name", "Unknown test"),
                    passed=bool(t.get("passed", False)),
                    message=t.get("message"),
                    duration_ms=t.get("duration_ms"),
                )
                for t in json_data.get("tests", [])
            ]
            passed = sum(1 for t in tests if t.passed)
            failed = len(tests) - passed
            status = "passed" if failed == 0 and len(tests) > 0 else "failed"

            return RunResult(
                status=status,
                passed=passed,
                failed=failed,
                total=len(tests),
                tests=tests,
                execution_time_ms=execution_time_ms,
                stdout=stdout,
                stderr=stderr,
                error_message=json_data.get("error"),
                docker_available=True,
            )

        # Non-zero exit without parsed JSON indicates syntax error, import error, or crash
        if returncode != 0:
            err_msg = stderr.strip() or stdout.strip() or f"Process exited with code {returncode}"
            return RunResult(
                status="error",
                passed=0,
                failed=0,
                total=0,
                tests=[],
                execution_time_ms=execution_time_ms,
                stdout=stdout,
                stderr=stderr,
                error_message=err_msg,
                docker_available=True,
            )

        # Fallback for unexpected empty output
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            total=0,
            tests=[],
            execution_time_ms=execution_time_ms,
            stdout=stdout,
            stderr=stderr,
            error_message="Test runner did not return structured results.",
            docker_available=True,
        )


# Default singleton instance
runner_instance = DockerSandboxRunner()


def get_sandbox_runner() -> DockerSandboxRunner:
    """Dependency provider for sandbox runner."""
    return runner_instance
