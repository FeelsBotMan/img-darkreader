"""개발용 진입점. 패키지 미설치 시 `src`를 경로에 넣습니다."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_src = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from dark_reader.main import main

if __name__ == "__main__":
    main()
