
# GreenMetal Automation Suite

## 포함 기능
- DQ Generator
- Word 템플릿 직접 선택
- URS PDF 직접 선택
- CLOVA OCR 연동
- 시작/종료 요구사항 번호 범위 추출
- OCR 결과를 Word 표로 삽입
- Windows 설치 프로그램 자동 빌드
- 설치 중 바탕화면 바로가기 선택

## Word 템플릿 필수 태그
- `##로고##`
- `##문서번호##`
- `##버전번호##`
- `##장비명##`
- `##작성자##`
- `##작성일##`
- `##작성자직위##`
- `##업체명##`
- `##OCR요구사항##`

## 설치파일 만들기
1. 이 ZIP의 내용을 GitHub 저장소 최상위에 업로드합니다.
2. GitHub 저장소의 **Actions** 탭으로 이동합니다.
3. **Build Windows Installer**를 선택합니다.
4. **Run workflow**를 누릅니다.
5. 완료 후 Artifacts의 `GreenMetal-Automation-Suite-Installer`를 다운로드합니다.
6. 압축 안의 `GreenMetal_Automation_Suite_Setup.exe`가 최종 설치파일입니다.

## CLOVA OCR
프로그램에서 `OCR 설정`을 누르고 다음 값을 입력합니다.
- OCR Invoke URL
- X-OCR-SECRET

Secret Key는 GitHub에 올리지 말고 프로그램 설정창에서만 입력하세요.

## 주의
OCR 표 구조는 실제 URS PDF 양식에 따라 조정이 필요할 수 있습니다. 첫 샘플 PDF로 테스트한 뒤 번호/제목 추출 규칙을 보완하는 방식으로 개발합니다.
