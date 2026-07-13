# 누적 소형 업데이트

`Vegas_Total_Solution_Doc_Update.exe`는 기존 전체 설치본에 최신 메인 EXE와 패키지 리소스만 덮어쓰는 Windows 업데이트입니다.

## 사용자 적용 방법

1. 최초 한 번은 `Vegas_Total_Solution_Doc_Setup.exe`로 전체 프로그램을 설치합니다.
2. 프로그램을 종료합니다.
3. 최신 `Vegas_Total_Solution_Doc_Update.exe`를 실행합니다.
4. 업데이트 프로그램이 기존 설치 위치를 자동으로 찾아 파일을 교체합니다.

소형 업데이트는 누적형입니다. 예를 들어 0.1.1을 건너뛰고 이후 0.1.3만 설치해도 0.1.1과 0.1.2의 프로그램 코드 변경이 최신 EXE에 함께 포함됩니다.

## 제한사항

- 기본 전체 설치본이 없는 PC에는 적용할 수 없습니다.
- Python, PySide6 또는 네이티브 DLL 등 런타임 의존성이 변경된 버전은 전체 설치파일로 배포해야 합니다.
- 업데이트는 사용자 설정, Credential Manager의 Secret Key, 프로젝트 및 생성 문서를 수정하지 않습니다.
- GitHub Actions artifact는 30일 동안 보관됩니다. 장기 보관이 필요한 승인 버전은 별도의 GitHub Release asset으로 승격해야 합니다.

## GitHub Actions

**Actions → Build Lightweight Windows Update**에서 실행 결과를 열고 `Vegas-Total-Solution-Doc-Update-0.1.2` artifact를 내려받습니다.
