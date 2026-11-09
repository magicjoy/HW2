# Local Timetable Planner

에브리타임 스타일의 주간 시간표 이미지를 로컬에서 분석하고, 사용자가 확인한 수업 일정과 공부 목표를 바탕으로 공부·휴식 추천 일정을 생성하는 경량 웹앱입니다.

## 주요 기능

- 시간표 이미지의 형식·크기 검증
- 로컬 Tesseract OCR 기반 수업 인식
- 고정된 5일×10교시 격자 시간표의 셀 단위 OCR
- 인식 결과의 과목명·요일·시작/종료 시간 수정
- 수업 삭제 및 수업 직접 추가
- 수업 사이 공강과 수업이 없는 요일 계산
- 과목별 중요도와 주간 공부 시간 입력
- 공부 세션 분산, 세션 사이 휴식, 색상 구분 주간 캘린더

## 개인정보 및 외부 전송

이미지는 외부 AI API나 제3자 서비스로 전송하지 않습니다. 서버는 업로드 데이터를 메모리에서 처리하며 원본 이미지를 영구 저장하지 않습니다. 실제 OCR은 로컬 Tesseract 프로세스를 사용합니다.

## 설치

Python 3.10 이상을 권장합니다.

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## OCR 모델 준비

1. Tesseract OCR Windows 설치 프로그램을 설치합니다.
   - https://github.com/UB-Mannheim/tesseract/wiki
2. 설치 시 Korean 언어 데이터(`kor.traineddata`)를 선택합니다.
3. 설치 확인:

```powershell
tesseract --version
```

Tesseract가 PATH에 없으면 앱은 다음 기본 경로도 자동 확인합니다.

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
C:\Program Files (x86)\Tesseract-OCR\tesseract.exe
```

## 실행

```powershell
python app.py
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다.

OCR을 사용할 수 없는 환경에서도 앱은 실행되며, 인식 결과 확인 화면에서 수업을 직접 추가할 수 있습니다.

## 저장소에 올릴 때 제외할 항목

`.gitignore`는 가상환경, Python 캐시, 로그, 업로드 이미지, 개인정보 파일, OCR 모델 파일을 제외합니다. 원본 시간표 이미지와 대용량 모델 파일은 이 프로젝트에 포함하지 마세요.
