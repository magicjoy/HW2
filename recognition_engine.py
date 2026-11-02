import io, re, os, shutil

ALLOWED = {"png": b"\x89PNG\r\n\x1a\n", "jpg": b"\xff\xd8\xff", "jpeg": b"\xff\xd8\xff", "gif": b"GIF8", "webp": b"RIFF"}
DAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
class ValidationError(Exception): pass

def validate_image(data):
    if not data: raise ValidationError("이미지 파일이 비어 있습니다.")
    if len(data) > 8 * 1024 * 1024: raise ValidationError("파일 크기는 8MB 이하만 지원합니다.")
    if not any(data.startswith(sig) for sig in ALLOWED.values()): raise ValidationError("지원하지 않는 이미지 형식입니다. PNG, JPG, GIF, WEBP만 지원합니다.")
    return True

def _local_ocr(data):
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = ("C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        from PIL import Image
        # Windows에서 PATH에 등록되지 않은 기본 설치도 자동으로 찾습니다.
        candidates = [
            shutil.which("tesseract"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        executable = next((p for p in candidates if p and os.path.isfile(p)), None)
        if not executable:
            return [], False, "Tesseract 실행 파일을 찾지 못했습니다. 설치 경로를 PATH에 추가하거나 기본 경로에 설치했는지 확인하세요.", ""
        pytesseract.pytesseract.tesseract_cmd = executable
        image = Image.open(io.BytesIO(data)); image.verify(); image = Image.open(io.BytesIO(data)).convert("RGB")
        grid_items = extract_grid_schedule(image, pytesseract)
        if grid_items:
            return grid_items, True, "고정 격자 기반 로컬 OCR을 사용했습니다. 결과를 확인·수정하세요.", ""
        try:
            text = pytesseract.image_to_string(image, lang="kor+eng")
        except pytesseract.TesseractError:
            # 한국어 학습 데이터가 빠진 경우 영어 OCR이라도 시도합니다.
            text = pytesseract.image_to_string(image, lang="eng")
        # Conservative parser: only accept clear lines such as '월 09:00-10:30 과목명'.
        out = parse_ocr_text(text)
        return out, True, "로컬 Tesseract OCR을 사용했습니다. 결과를 확인·수정하세요.", text
    except Exception as e:
        return [], False, f"로컬 OCR을 실행하지 못했습니다: {e}", ""

def analyze_image_bytes(data):
    validate_image(data)
    items, ocr_available, message, raw_text = _local_ocr(data)
    if not items and ocr_available:
        message = "OCR은 실행되었지만 시간표 형식으로 해석된 항목이 없습니다. 아래에서 수업을 직접 추가하세요."
    return {"items": items, "ocr_available": ocr_available, "message": message, "raw_text": raw_text[:4000]}

def extract_grid_schedule(image, pytesseract_module):
    """첨부된 에브리타임 스타일(요일 7열, 10교시) 고정 격자용 OCR."""
    from PIL import ImageOps
    w, h = image.size
    # 기준 이미지(1479x756)의 상대 좌표. 좌측 교시 라벨과 우측 시간 라벨을 제외합니다.
    x_edges = [0.046, 0.227, 0.409, 0.591, 0.773, 0.955]
    y0, row_h = 0.049, 0.095
    days = ["월", "화", "수", "목", "금"]
    period_times = [("09:00","10:00"),("10:00","11:00"),("11:00","12:00"),("12:00","13:00"),("13:00","14:00"),("14:00","15:00"),("15:00","16:00"),("16:00","17:00"),("17:00","18:00"),("18:00","19:00")]
    blocks = []
    for col, day in enumerate(days):
        x1, x2 = int(w*x_edges[col]), int(w*x_edges[col+1])
        r = 0
        while r < 10:
            y1 = int(h*(y0 + r*row_h)); y2 = int(h*(y0 + (r+1)*row_h))
            sample = image.crop((x1+5, y1+5, x2-5, y2-5)).resize((1,1)).getpixel((0,0))
            # 흰색/회색 빈 셀과 달리 과목 셀은 옅은 색 배경을 가집니다.
            colored = max(sample)-min(sample) > 5 and min(sample) < 245
            if not colored:
                r += 1; continue
            end = r + 1
            while end < 10:
                yy1 = int(h*(y0 + end*row_h)); yy2 = int(h*(y0 + (end+1)*row_h))
                s = image.crop((x1+5, yy1+5, x2-5, yy2-5)).resize((1,1)).getpixel((0,0))
                if max(s)-min(s) <= 5 or min(s) >= 245: break
                end += 1
            crop = image.crop((x1+4, y1+4, x2-4, int(h*(y0 + end*row_h))-4))
            crop = ImageOps.autocontrast(crop.convert("L")).resize((crop.width*2, crop.height*2))
            text = pytesseract_module.image_to_string(crop, lang="kor+eng", config="--psm 6").strip()
            text = re.sub(r"\s+", " ", text)
            # 담당자/강의실 보조 줄은 과목명에서 제거하지 않고 사용자가 수정할 수 있도록 보존합니다.
            if text:
                blocks.append({"day": day, "start": period_times[r][0], "end": period_times[min(end-1, 9)][1], "subject": text})
            r = end
    return blocks

def parse_ocr_text(text):
    """Tesseract의 표 텍스트를 보수적으로 수업 레코드로 변환하는 순수 함수."""
    out = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        patterns = [
            r"(월|화|수|목|금|토|일)(?:요일)?\s*(\d{1,2})[:.](\d{2})\s*[-~–]\s*(\d{1,2})[:.](\d{2})\s+(.+)",
            r"(\d{1,2})[:.](\d{2})\s*[-~–]\s*(\d{1,2})[:.](\d{2})\s+(월|화|수|목|금|토|일)(?:요일)?\s+(.+)",
        ]
        m = re.search(patterns[0], line)
        if m:
            out.append({"day": m.group(1), "start": f"{int(m.group(2)):02d}:{m.group(3)}", "end": f"{int(m.group(4)):02d}:{m.group(5)}", "subject": m.group(6).strip()})
            continue
        m = re.search(patterns[1], line)
        if m:
            out.append({"day": m.group(5), "start": f"{int(m.group(1)):02d}:{m.group(2)}", "end": f"{int(m.group(3)):02d}:{m.group(4)}", "subject": m.group(6).strip()})
    return out
