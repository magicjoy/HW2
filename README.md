# Local Timetable Planner

에브리타임 주간 시간표 이미지를 로컬에서 분석하고, 확인된 수업/공강을 기반으로 공부·휴식 일정을 추천하는 경량 웹앱입니다.

## 실행

```powershell
python app.py
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다.

선택 기능: 로컬 OCR 자동 인식을 사용하려면 `Pillow`, `pytesseract`, 그리고 PC의 Tesseract 실행 파일이 필요합니다. 미설치 환경에서도 이미지 형식/크기를 검증하고, 인식 결과를 직접 추가·수정할 수 있습니다. 이미지 원본은 메모리에서만 처리하며 요청 종료 후 저장하지 않습니다.

## 테스트

```powershell
python -m unittest discover -s tests -v
```

OCR와 추천 로직은 분리되어 있으며, 일정 계산 핵심 함수는 순수 함수입니다.
