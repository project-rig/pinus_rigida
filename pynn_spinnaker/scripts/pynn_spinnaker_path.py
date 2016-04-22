"""A command-line utility which prints the path to pynn_spinnaker.
For use by plugins etc to find make files etc.

Installed as "pynn_spinnaker_path" by setuptools.
"""

import os.path
import pynn_spinnaker
import sys

def main(args=None):
    print(os.path.dirname(pynn_spinnaker.__file__))
    return 0

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
