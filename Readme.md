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

```bash
pip install -r requirements.txt
```

프로젝트를 개발 모드로 설치합니다. 프로젝트 루트 디렉토리에서 다음 명령을 실행합니다:

```bash
# 가상환경이 활성화된 상태에서
pip install -e .
```

프로그램 실행

```bash
# 프로젝트 루트 디렉토리에서
python run.py
```

프로젝트 구조

```
프로젝트/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── viewer/
│   │   ├── __init__.py
│   │   ├── image_viewer.py
│   │   └── image_processor.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── setup.py
├── run.py
├── requirements.txt
└── pyproject.toml
```

프로그램 사용 방법:
'O' 키를 눌러 이미지가 있는 폴더를 선택합니다.
← → 방향키로 이미지를 탐색합니다.
설정 커스터마이징:
홈 디렉토리에 .dark_reader/config.yaml 파일을 생성하여 설정을 변경할 수 있습니다:

```yaml
# 설정 예시
background_color: [0, 0, 0] # RGB 값 (검정)
text_color: [200, 200, 200] # RGB 값 (밝은 회색)
threshold: 240 # 흰색 감지 임계값
```

ruff 설정을 위한 pyproject.toml 파일

```toml
[tool.ruff]
line-length = 88
target-version = "py39"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
```

프로젝트 구조가 올바르게 설정되었는지 확인하기 위해 다음 명령을 실행할 수 있습니다:

```
# 프로젝트 구조 확인
tree .

# 가상환경에 설치된 패키지 확인
pip list
```

문제가 발생하면 다음을 확인해보세요:
가상환경이 활성화되어 있는지 확인
모든 필요한 패키지가 설치되어 있는지 확인
프로젝트 구조가 올바른지 확인
Python 경로가 올바르게 설정되어 있는지 확인
