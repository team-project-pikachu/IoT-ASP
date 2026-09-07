# ADK expects `from . import agent` when the CLI loads this package.
# Soft-fail if google-adk is not installed so scripts/autoroute_dev.sh can use tools/.
try:
    from . import agent as agent  # noqa: F401
except ImportError:  # pragma: no cover
    agent = None
