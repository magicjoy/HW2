from datetime import datetime, timedelta

DAYS = ["월", "화", "수", "목", "금", "토", "일"]
def minutes(t):
    h, m = map(int, t.split(":")); return h * 60 + m
def fmt(n): return f"{n//60:02d}:{n%60:02d}"
def _valid_range(a,b): return max(0, minutes(b)-minutes(a))

def compute_free_slots(classes, day_start="09:00", day_end="21:00", travel=5):
    by = {d: [] for d in DAYS}
    for c in classes:
        if c.get("day") in by: by[c["day"]].append(c)
    result = []
    for d in DAYS:
        current = minutes(day_start); end = minutes(day_end)
        for c in sorted(by[d], key=lambda x: minutes(x["start"])):
            s, e = minutes(c["start"]), minutes(c["end"])
            if s - current > travel: result.append({"day": d, "start": fmt(current), "end": fmt(s-travel), "kind":"free", "label":"공강"})
            current = max(current, e + travel)
        if end-current > 0: result.append({"day":d,"start":fmt(current),"end":fmt(end),"kind":"free","label":"공강"})
    return result

def estimate_subjects(classes):
    totals = {}
    for c in classes: totals[c["subject"]] = totals.get(c["subject"], 0) + _valid_range(c["start"], c["end"])
    return [{"subject": k, "importance": 3, "study_minutes": max(60, round(v * 1.5 / 30) * 30), "lecture_minutes": v} for k,v in totals.items()]

def allocate_study(slots, subjects, session_minutes=75, break_minutes=15):
    """공강 후보에 공부를 분산 배치하는 순수 함수. 요일 편중과 연속 공부를 줄인다."""
    candidates = []
    for slot in slots:
        start, end = minutes(slot["start"]), minutes(slot["end"])
        cursor = start
        while end - cursor >= 45:
            take = min(session_minutes, end - cursor)
            if take < 45: break
            candidates.append({"day": slot["day"], "start": fmt(cursor), "end": fmt(cursor + take)})
            cursor += take + break_minutes
    remaining = {s["subject"]: int(s.get("study_minutes", 60)) for s in subjects}
    importance = {s["subject"]: int(s.get("importance", 3)) for s in subjects}
    day_load = {d: 0 for d in DAYS}
    result = []
    # 중요도가 높은 과목을 우선하되, 매번 가장 적게 배정된 요일의 후보를 선택한다.
    ordered = sorted(remaining, key=lambda x: importance[x], reverse=True)
    while candidates and any(v > 0 for v in remaining.values()):
        progress = False
        for subject in ordered:
            if remaining[subject] <= 0: continue
            eligible = [c for c in candidates if day_load[c["day"]] == min(day_load.values())]
            if not eligible: eligible = candidates
            chosen = eligible[0]
            candidates.remove(chosen)
            take = minutes(chosen["end"]) - minutes(chosen["start"])
            result.append({**chosen, "kind":"study", "label":subject + " 공부"})
            remaining[subject] -= take
            day_load[chosen["day"]] += take
            progress = True
            if not candidates: break
        if not progress: break
    return result

def recommend_schedule(payload):
    classes = payload.get("classes", []); prefs = payload.get("subjects") or estimate_subjects(classes)
    slots = compute_free_slots(classes); events = [{**c, "kind":"class", "label":c.get("subject","수업")} for c in classes]
    events.extend(allocate_study(slots, prefs))
    for d in DAYS:
        used = sorted([e for e in events if e["day"]==d], key=lambda x: minutes(x["start"]))
        for a,b in zip(used, used[1:]):
            gap = minutes(b["start"])-minutes(a["end"])
            if gap >= 15: events.append({"day":d,"start":a["end"],"end":b["start"],"kind":"rest","label":"휴식"})
    return {"events": events, "subjects": estimate_subjects(classes) if not payload.get("subjects") else prefs, "free_days": [d for d in DAYS if not any(c.get("day")==d for c in classes)], "free_slots": slots}
