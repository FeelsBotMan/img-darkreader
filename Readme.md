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
pip install -e .
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
├── run.py
├── requirements.txt
└── pyproject.toml
```

프로그램 사용 방법:
'O' 키를 눌러 이미지가 있는 폴더를 선택합니다.
← → 방향키로 이미지를 탐색합니다.
설정 커스터마이징:
홈 디렉토리에 .dark_reader/config.yaml 파일을 생성하여 설정을 변경할 수 있습니다:

X: 현재 위치를 문제로 저장/제거 (토글)
S: 현재 위치를 정답으로 저장/제거 (토글)
A: 저장된 문제 위치로 이동
Z: 저장된 정답 위치로 이동

```yaml
# 설정 예시
background_color: [0, 0, 0] # RGB 값 (검정)
text_color: [200, 200, 200] # RGB 값 (밝은 회색)
threshold: 240 # 흰색 감지 임계값
```

Ruff 설정은 `pyproject.toml`의 `[tool.ruff]`를 참고하세요.

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
