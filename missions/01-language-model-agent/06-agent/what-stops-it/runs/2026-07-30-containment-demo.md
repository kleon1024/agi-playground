# Run — containment controls demonstrated for real

`runs/containment_demo.py` imports `resolve_in_jail`, `read_file`,
`run_command`, `build_tools` from `../core/tools.py`, and `default_confirm`,
`check_permission`, `PermissionDenied` from `../core/harness.py` directly --
no reimplementation, no mocking. It builds a temporary sandbox root with one
legitimate file inside it, one secret file outside it, and one symlink
crossing that boundary, then exercises every control this chapter documents.

## Hardware and environment

CPU only, no GPU or model involved -- this is pure sandbox-mechanism testing.
macOS (Darwin 24.6.0, arm64), Python 3.11.14. Cost: \$0.

## Command

```bash
cd missions/01-language-model-agent/06-agent/what-stops-it
python3 runs/containment_demo.py
```

## Full real output

```
=== 1. absolute path rejected before joining ===
ToolError: absolute paths are not allowed: '/etc/passwd'

=== 2. .. walk rejected by ancestry check ===
ToolError: path escapes sandbox root: '../../../../../../etc/passwd'

=== 3. symlink escape caught by resolve() + ancestry check ===
ToolError: path escapes sandbox root: 'escape_link'

=== 4. legitimate read inside the jail still works ===
hello from inside the jail

=== 5. default_confirm denies every CONFIRM-tier call non-interactively ===
PermissionDenied: 'run_command' requires confirmation, which was not granted

=== 6. shell metacharacters refused even without shell=True ===
ToolError: command contains a shell metacharacter, refused: 'echo hi; rm -rf /tmp/should-not-run'

=== 7. unallowlisted binary refused ===
ToolError: 'rm' is not in the command allowlist ['cat', 'echo', 'find', 'grep', 'head', 'ls', 'pwd', 'pytest', 'python3', 'tail', 'wc']
workspace/notes.txt still present: True

=== 8. THE DOCUMENTED GAP: allowlisted argv[0], unvalidated argument ===
exit line: exit=0
first data line: ##
total lines returned: 71
This is a real absolute-path read of a file entirely outside root, via an allowlisted binary.
```

Test 8 ran `run_command(root, "cat /etc/passwd")` against this machine's real
`/etc/passwd` (71 lines, first line `##`, the standard macOS header comment).
The file contents are not reproduced beyond the first line here, since the
point is that the read happened and returned real data from outside the
jail, not the file's contents themselves.

## What this confirms, one claim at a time

- **Absolute-path rejection fires before joining** (test 1): the exact
  `pathlib`-replaces-not-extends gotcha the README describes never gets a
  chance to matter, because `resolve_in_jail` rejects the absolute input
  outright first.
- **The `..`-walk escape is caught by resolving then checking ancestry**
  (test 2), not by string-matching `..` -- confirmed by using six levels of
  `../` well past the jail's actual depth.
- **The symlink escape is caught too** (test 3): a symlink planted inside
  the sandbox pointing at a real file outside it is followed by
  `Path.resolve()` before the ancestry check runs, so it is rejected exactly
  like the `..`-walk.
- **A legitimate in-jail read still works** (test 4) -- containment is not
  simply refusing everything.
- **`default_confirm` fails closed** (test 5): `check_permission` on a
  `CONFIRM`-tier tool with no real confirm function supplied raises
  `PermissionDenied`, confirmed via the harness's actual permission-check
  function, not a hand-written stand-in.
- **Shell metacharacters are refused before any allowlist check runs**
  (test 6), and **an unallowlisted binary is refused** (test 7) -- in both
  cases the real file (`workspace/notes.txt`) is confirmed still present
  afterward, not just that an exception was raised.
- **The documented gap is real, not theoretical** (test 8): `cat
  /etc/passwd` passes the allowlist (`cat` is an allowed name) and reads 71
  real lines from a file entirely outside the sandbox root, because
  `run_command` never validates its arguments against `resolve_in_jail` --
  only `read_file`/`list_dir` do. This is exactly the gap the README names
  and the exact command it uses as the example.

Every one of the chapter's claims about `resolve_in_jail`, the allowlist, the
default-deny permission ladder, and the argv[0]-only gap holds under a real,
executed test -- none of it required adjustment.
