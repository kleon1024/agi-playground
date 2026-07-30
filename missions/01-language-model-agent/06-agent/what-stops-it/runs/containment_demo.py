import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from harness import PermissionDenied, check_permission, default_confirm
from tools import ToolError, build_tools, read_file, run_command

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "workspace").mkdir()
    (root / "workspace" / "notes.txt").write_text("hello from inside the jail\n")

    print("=== 1. absolute path rejected before joining ===")
    try:
        read_file(root, "/etc/passwd")
    except ToolError as e:
        print(f"ToolError: {e}")

    print()
    print("=== 2. .. walk rejected by ancestry check ===")
    try:
        read_file(root, "../../../../../../etc/passwd")
    except ToolError as e:
        print(f"ToolError: {e}")

    print()
    print("=== 3. symlink escape caught by resolve() + ancestry check ===")
    outside = Path(tempfile.mkdtemp())
    secret = outside / "outside_secret.txt"
    secret.write_text("this must never be readable through the jail\n")
    link = root / "escape_link"
    link.symlink_to(secret)
    try:
        read_file(root, "escape_link")
    except ToolError as e:
        print(f"ToolError: {e}")

    print()
    print("=== 4. legitimate read inside the jail still works ===")
    print(read_file(root, "workspace/notes.txt"))

    print()
    print("=== 5. default_confirm denies every CONFIRM-tier call non-interactively ===")
    tools = build_tools(root)
    try:
        check_permission(tools["run_command"], default_confirm, {"command": "echo hi"})
        print("NOT REACHED")
    except PermissionDenied as e:
        print(f"PermissionDenied: {e}")

    print()
    print("=== 6. shell metacharacters refused even without shell=True ===")
    try:
        run_command(root, "echo hi; rm -rf /tmp/should-not-run")
    except ToolError as e:
        print(f"ToolError: {e}")

    print()
    print("=== 7. unallowlisted binary refused ===")
    try:
        run_command(root, "rm -rf workspace")
    except ToolError as e:
        print(f"ToolError: {e}")
    print("workspace/notes.txt still present:", (root / "workspace" / "notes.txt").exists())

    print()
    print("=== 8. THE DOCUMENTED GAP: allowlisted argv[0], unvalidated argument ===")
    result = run_command(root, "cat /etc/passwd")
    lines = result.splitlines()
    print(f"exit line: {lines[0]}")
    print(f"first data line: {lines[1] if len(lines) > 1 else '(none)'}")
    print(f"total lines returned: {len(lines)}")
    print("This is a real absolute-path read of a file entirely outside root, via an allowlisted binary.")
