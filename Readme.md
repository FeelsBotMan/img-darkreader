## 프로젝트 목적

이미지의 색상을 반전하여 데스크톱용 다크리더 프로그램

## 프로젝트 설정

Python 가상환경 활성화

```bash
# 가상환경 생성
python -m venv venv

# Windows에서 가상환경 활성화
source venv/Scripts/activate

# Linux/Mac에서 가상환경 활성화
source venv/bin/activate
```

의존성은 `pyproject.toml`의 `[project]`에 정의되어 있습니다. 가상환경에서 프로젝트 루트에서 다음을 실행합니다:

```bash
pip install -e ".[dev]"
```

(`requirements.txt`는 안내용이며, 실제 패키지 목록은 `pyproject.toml`을 따릅니다.)

프로그램 실행 (택일)

```bash
# 개발: 저장소 루트에서 (editable 설치 없이도 동작)
python run.py

# 패키지 설치 후
python -m dark_reader
dark-reader
```

프로젝트 구조 (요약)

```
프로젝트/
├── src/
│   └── dark_reader/
│       ├── __init__.py
│       ├── __main__.py
│       ├── main.py
│       ├── viewer/
│       ├── models/
│       ├── config/
│       └── utils/
├── tests/
├── run.py
├── requirements.txt
└── pyproject.toml
```

프로그램 사용 방법:
`O` 키를 눌러 이미지가 들어 있는 ZIP 파일을 선택합니다.
(ZIP 루트의 `.png` / `.jpg` / `.jpeg`만 페이지로 사용됩니다.)
← → 방향키로 이미지를 탐색합니다.

상세 단축키·동작은 [docs/usage.md](docs/usage.md)를 참고하세요.

```
X: 현재 위치를 문제로 저장/제거 (토글)
S: 현재 위치를 정답으로 저장/제거 (토글)
Z: 저장된 문제 위치로 이동
A: 저장된 정답 위치로 이동
```

설정은 `~/.dark_reader/config.yaml`에 저장됩니다:

```yaml
is_dark_mode: true
threshold: 240
```

데이터 위치는 모두 `~/.dark_reader/` 아래입니다 (설정, 라이브러리, 썸네일, 업스케일 캐시).

테스트:

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

Ruff 설정은 `pyproject.toml`의 `[tool.ruff]`를 참고하세요.
