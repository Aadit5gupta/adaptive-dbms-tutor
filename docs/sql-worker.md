# SQL worker

SQL exercises run in a fresh Python subprocess with an empty environment and a temporary working directory. The parent checks the published fixture hash and passes the learner query on stdin. The worker builds the fixture from repository-owned SQL, closes the writable connection, and reopens the SQLite file read-only with `immutable=1`. The application database path and credentials are absent from the worker input.

SQLite parses a single statement after a SELECT/WITH prefix check. An authorizer permits reads of fixture tables and columns and allows a small set of SQL functions. The worker limits SQLite heap allocation to 16 MiB, applies statement and expression limits, interrupts expensive operations, and caps results at 200 rows and approximately 48 KB. The parent allows two concurrent workers and kills a worker after three seconds. macOS process limits cap CPU time, writable file size and file descriptors and disable core dumps.

The worker is enabled for Apple Silicon macOS, tested on macOS 27.2.1 with Python 3.12.16 and SQLite 3.54.1. This runtime rejected `RLIMIT_AS`. The SQLite heap cap applies to query allocations while the process limits and response caps also remain in force. Other platforms return a worker unavailable response until they have equivalent verification.

Preview uses the visible fixture. Grading compares typed row results across all published fixtures. Hidden rows, query text and SQLite internal errors stay server side.
