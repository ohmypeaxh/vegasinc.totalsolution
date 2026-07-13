# Vegas Total Solution Doc

Vegas Inc.의 Windows용 사내 문서 자동화 플랫폼입니다. 현재 DQ Generator는 URS PDF 텍스트 우선 추출, 필요한 페이지의 CLOVA OCR 보완, 요구사항 검토, 프로젝트 저장, Word 템플릿 치환과 반복 표 생성을 지원합니다.

## 주요 구성

- PySide6 플러그인 기반 데스크톱 UI
- 숫자 계층을 인식하는 URS 범위 추출 (`6.9 < 6.10`, 하위 항목 포함)
- 검색 가능한 PDF 텍스트 우선 사용 및 페이지별 OCR 실패 격리
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

Secret Key는 프로젝트, 설정 JSON, 로그, 생성 문서에 기록하지 않습니다. 입력 템플릿은 직접 수정하지 않고 임시 복사본에서 처리한 뒤 결과를 원자적으로 저장합니다.

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

실제 PySide6 위젯으로 만든 9개 PNG가 `artifacts\ui-previews\`에 생성됩니다. 샘플 데이터와 마스킹된 자격증명만 사용합니다.

## 데이터 위치와 보안

설정과 로그는 설치 폴더가 아닌 Windows 사용자별 쓰기 가능한 AppData 위치에 저장됩니다. 로그는 UTF-8 `RotatingFileHandler`를 사용하고 `logs\yyyy-mm-dd.log` 형식입니다. 실제 CLOVA URL, Secret Key, 고객 URS 또는 생성된 고객 문서는 저장소와 배포 artifact에 포함하면 안 됩니다.
