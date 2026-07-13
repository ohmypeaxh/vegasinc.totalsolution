# Vegas Total Solution Doc

Vegas Inc.의 Windows용 사내 문서 자동화 플랫폼입니다. 현재 DQ Generator는 URS PDF 텍스트 우선 추출, 필요한 페이지의 CLOVA OCR 보완, 요구사항 검토, 프로젝트 저장, Word 템플릿 치환과 반복 표 생성을 지원합니다.

## 주요 구성

- PySide6 플러그인 기반 데스크톱 UI
- Vegas 공식 로고와 브랜드 테마를 적용한 `Manual / DQ / F&DS / Raw Data / Settings` 작업 공간
- 숫자 계층을 인식하는 URS 범위 추출 (`6.9 < 6.10`, 하위 항목 포함)
- 검색 가능한 PDF 텍스트 우선 사용 및 페이지별 OCR 실패 격리
- 작은 표 번호를 위한 고해상도 OCR 렌더링과 `7.I`, `7,10` 같은 숫자 오인식 보정
- 요구사항 추가·삭제·편집·순서 변경·제외·OCR 재실행
- 일반 문단, 표, 머리글, 바닥글 및 분할 Run의 Word Placeholder 처리
- 0.82cm 비율 유지 로고, 맑은 고딕 10pt 반복 표와 병합 제목 행
- Windows Credential Manager/keyring 기반 Secret Key 보관
- PyInstaller one-folder 배포와 Inno Setup 설치 프로그램

## 개발 실행

Windows와 Python 3.12에서 다음을 실행합니다.

```bat
scripts\setup_dev.bat
scripts\run_dev.bat
```

테스트만 실행하려면:

```bat
scripts\test.bat
```

## DQ 문서 생성

1. Settings에서 CLOVA Invoke URL, Secret Key, 요청 제한 시간을 입력하고 연결을 테스트합니다.
2. DQ Generator에서 회사 로고, DOCX 템플릿, URS PDF와 문서 정보를 입력합니다.
3. 시작·종료 요구사항 번호를 입력하고 `URS 분석`을 누릅니다.
4. 낮은 신뢰도 항목과 번호, 제목, 내용을 검토하고 필요한 행을 추가·삭제·재정렬합니다.
5. 출력 폴더와 파일명을 확인하고 `Word 문서 생성`을 누릅니다.
6. 저장 직전 문서 검토 경고를 확인합니다. 자동 생성 결과의 페이지 번호와 OCR 내용을 반드시 원문과 대조해야 합니다.

Secret Key는 프로젝트, 설정 JSON, 로그, 생성 문서에 기록하지 않습니다. 입력 템플릿은 직접 수정하지 않고 임시 복사본에서 처리한 뒤 결과를 원자적으로 저장합니다.

> 확장자만 `.docx`로 바꾼 구형 Word 97-2003 (`.doc`) 파일은 템플릿으로 사용할 수 없습니다. Microsoft Word에서 **다른 이름으로 저장 → Word 문서 (*.docx)** 로 실제 변환한 뒤 선택해 주세요. 앱은 이 형식을 사전에 감지하고 변환 방법을 안내합니다.

## Manual Generator

기존 **Manual Maker v9**의 기능을 PySide6 플러그인으로 통합했습니다. 별도 Tkinter 실행 프로그램 없이 다음 기능을 동일한 앱에서 사용할 수 있습니다.

- Weighing Booth, Clean Booth, Sampling Booth, ORABS 장비 선택과 `GR-OM-*` 문서번호 자동 구성
- Main Screen, Data Setting, Alarm Screen 및 선택적 Alarm Setting 이미지 삽입
- Emergency Stop, Fan/Blower 수량 및 온도·습도·차압·풍속 High/Low 알람 표 생성
- `[##장비명##]`, `[##문서번호##]`, `[##작성일##]`, `[##제품선택##]`, `[##사진1##]`~`[##사진4##]`, `[##알람리스트##]` 자리표시자 처리
- 파일/폴더 찾아보기와 드래그앤드롭, 생성 완료 후 Word 파일 열기

## F&DS Generator

1. `F&DS Generator` 탭에서 URS PDF를 드래그앤드롭하고 시작·종료 요구사항 번호를 입력합니다.
2. `선택 범위 URS 분석`을 실행하면 검색 가능한 PDF 텍스트를 우선 사용하고 필요한 페이지만 Settings의 CLOVA OCR 연결로 읽습니다.
3. 변환된 문장을 표에서 검토·수정합니다. `F&DS Rules` 탭에서는 `URS 원문 끝 표현 → F&DS 변환 끝 표현` 규칙을 추가·수정·삭제하고 사용자 설정에 저장할 수 있습니다. 한 요구사항 안에 문장이 여러 개 있거나 종결 표현 뒤에 괄호 설명이 있어도 각 문장 경계에 규칙을 적용하며 괄호 내용은 유지합니다.
4. 문서번호 초기값은 `MD-FDS-##01-26`이며, `##`를 장비명 축약형(예: Pass Box `PB`, Clean Booth `CB`)으로 바꿉니다.
5. `##장비명##`, `##문서번호##`, `##로고##`, `##작성일##`, `##F&DS내용##`이 들어 있는 DOCX 템플릿과 저장 폴더를 선택합니다.
6. `F&DS 문서 생성`을 누르면 `##F&DS내용##` 위치에 `5.2.1.`부터 맑은 고딕 10pt로 순서대로 삽입됩니다.

## Raw Data Generator

- Raw Data Type은 `HEPA Filter`, `2 cut Picture (comment)`, `2 cut Picture (non-comment)` 중에서 선택합니다.
- 적격성평가 종류와 문서번호는 각각 `##적격성종류##`, `##문서번호##`에 삽입됩니다. 회사 로고는 `##로고##` 위치에 높이 0.95cm, 원본 비율 유지로 삽입됩니다.
- HEPA 형식은 `##HEPA번호##`가 포함된 표 전체를 개수만큼 복제하고 `HEPA-01`부터 순서대로 번호를 붙입니다.
- 사진형은 `##검증명##`과 사진 삽입 위치 `##사진##`을 사용합니다. 여러 사진을 드래그앤드롭한 뒤 버튼이나 목록 드래그로 순서를 변경할 수 있습니다.
- 모든 첨부사진은 높이 9.88cm, 원본 가로세로 비율 유지로 삽입되며 두 장마다 다음 페이지로 넘어갑니다. `comment` 형식은 확장자를 뺀 파일명을 Arial 10pt로 먼저 쓰고, `non-comment` 형식은 빈 줄만 둡니다.

## 브랜드 에셋

`assets\vegas_logo.png`는 프로그램 내부에 표시하는 Vegas 공식 워드마크입니다. `assets\app.png`와 `assets\app.ico`는 실행파일, 설치파일, 제거 프로그램, 시작 메뉴 및 바탕화면 바로가기에 공통으로 적용하는 전용 V-DOC 아이콘입니다. 워드마크만 갱신할 때는 기존 앱 아이콘을 유지하며, 앱 아이콘도 함께 갱신할 때만 `--app-icon`을 지정합니다.

```bat
python scripts\generate_brand_assets.py "경로\vegas_logo_new.png" --output assets
python scripts\generate_brand_assets.py "경로\vegas_logo_new.png" --app-icon "경로\app_icon.png" --output assets
```

## Windows 설치 프로그램 빌드

Python 3.12와 Inno Setup 6이 설치된 Windows에서:

```bat
scripts\package_release.bat
```

결과:

- `dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe`
- `dist\installer\Vegas_Total_Solution_Doc_Setup.exe`
- `dist\installer\checksums.txt`
- `dist\installer\build_manifest.json`
- `artifacts\package_size_after.txt`

GitHub Actions의 **Build Windows Installer** workflow도 같은 테스트·빌드·크기 검증을 수행하고 `Vegas-Total-Solution-Doc-Installer` artifact를 생성합니다. 설치 파일의 권장 목표는 100MB 이하이며, 120MB 초과 시 추가 경고, 160MB 초과 시 빌드를 실패시킵니다. 실제 크기는 Windows 빌드 결과만 보고하며 추정값을 사용하지 않습니다.

자세한 내용은 `docs/windows-packaging.md`와 `docs/package-size-optimization.md`를 참고하세요.

## 실제 UI 미리보기

GitHub에서 **Actions → Generate UI Previews → Run workflow**를 실행한 뒤 `Vegas-Total-Solution-Doc-UI-Previews` artifact를 내려받습니다.

로컬에서는:

```bat
scripts\preview_ui.bat
```

실제 PySide6 위젯으로 만든 12개 PNG가 `artifacts\ui-previews\`에 생성됩니다. F&DS Generator, F&DS Rules, Raw Data Generator 화면을 포함하며, 샘플 데이터와 마스킹된 자격증명만 사용합니다.

## 데이터 위치와 보안

설정과 로그는 설치 폴더가 아닌 Windows 사용자별 쓰기 가능한 AppData 위치에 저장됩니다. 로그는 UTF-8 `RotatingFileHandler`를 사용하고 `logs\yyyy-mm-dd.log` 형식입니다. 실제 CLOVA URL, Secret Key, 고객 URS 또는 생성된 고객 문서는 저장소와 배포 artifact에 포함하면 안 됩니다.
