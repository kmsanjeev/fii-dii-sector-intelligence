"""
Pipe-safe tqdm wrapper for all engine scripts.

Why file=sys.stdout:
  Subprocess runner (data_ops.py) captures stdout via PIPE. If tqdm writes to
  stderr and we use stderr=STDOUT, stderr is merged but only at the OS level —
  interleaving may cause partial-line reads. Writing directly to stdout avoids that.

Why disable=False:
  tqdm auto-disables when isatty() is False (pipe context). We always want output.

Why ascii=True:
  Windows cp1252 terminal cannot render Unicode box-drawing chars (arrow/block chars).
"""

import sys
from tqdm import tqdm


def progress(iterable=None, total=None, desc="Processing", **kwargs):
    """Return a tqdm progress bar configured for pipe-safe SSE streaming."""
    kwargs.setdefault("ncols",   100)
    kwargs.setdefault("leave",   True)
    kwargs.setdefault("ascii",   True)      # Windows cp1252 safe
    kwargs.setdefault("file",    sys.stdout)
    kwargs.setdefault("disable", False)     # always show, even over pipes
    return tqdm(iterable, total=total, desc=desc, **kwargs)
