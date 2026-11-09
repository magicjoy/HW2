import unittest
from recognition_engine import validate_image, ValidationError, parse_ocr_text
from recommendation_engine import compute_free_slots, estimate_subjects

class EngineTests(unittest.TestCase):
    def test_validation_rejects_bad_file(self):
        with self.assertRaises(ValidationError): validate_image(b"not-image")
    def test_free_slot_keeps_travel_buffer(self):
        slots=compute_free_slots([{"day":"월","start":"10:00","end":"11:00"}])
        self.assertEqual(next(x for x in slots if x['day']=='월')['end'], '09:55')
    def test_subject_estimation(self):
        out=estimate_subjects([{"day":"화","subject":"수학","start":"10:00","end":"11:30"}])
        self.assertEqual(out[0]['lecture_minutes'],90); self.assertGreaterEqual(out[0]['study_minutes'],60)
    def test_timetable_like_ocr_text(self):
        text = """월요일 09:00-10:30 운영체제SW개발방법및도구(컴퓨터공학과)\n화 13.00~15.00 기계학습(컴퓨터공학과)\n17:00-18:00 목 네트워크서비스"""
        out = parse_ocr_text(text)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[0]['day'], '월')
        self.assertEqual(out[1]['start'], '13:00')
        self.assertEqual(out[2]['day'], '목')

if __name__=='__main__': unittest.main()
