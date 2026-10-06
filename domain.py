"""Calendar-date rotation logic, independent of the transport and database."""
from datetime import date, timedelta

class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status

def day(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise Problem('Укажите корректную дату в формате ГГГГ-ММ-ДД.')

def date_range(start, end, limit=1830):
    a, b = day(start), day(end)
    if b < a:
        raise Problem('Дата окончания должна быть не раньше даты начала.')
    if (b-a).days > limit:
        raise Problem('Диапазон не должен превышать пять лет.')
    return a, b

def overlap(a, b):
    return a['start'] <= b['end'] and b['start'] <= a['end']

def validate_periods(periods, assignments):
    ordered = sorted(periods, key=lambda p: p['start'])
    for i, p in enumerate(ordered):
        date_range(p['start'], p['end'])
        layer=p.get('layer',0)
        if not isinstance(layer,int) or not 0 <= layer <= 31:
            raise Problem('Допускается не более 32 слоёв графика.')
        if not any(a['project_id'] == p['project_id'] and a['start'] <= p['start'] and a['end'] >= p['end'] for a in assignments):
            raise Problem('Период выходит за даты назначения работника на проект.', 409)
        for other in ordered[:i]:
            if overlap(other,p) and (other['project_id']!=p['project_id'] or other.get('layer',0)==layer):
                raise Problem('Периоды пересекаются на одном слое или относятся к разным проектам.',409)

def available_layer(periods, candidate):
    for layer in range(32):
        if not any(p.get('layer',0)==layer and overlap(p,candidate) for p in periods):
            return layer
    raise Problem('Допускается не более 32 слоёв графика.',409)

def generate_cycle(project_id, employee_id, start, end=None, repeats=None, work_weeks=6, rest_weeks=2):
    try:
        work_weeks, rest_weeks = int(work_weeks), int(rest_weeks)
        repeats = int(repeats) if repeats else None
    except (ValueError, TypeError):
        raise Problem('Недели и количество повторений должны быть целыми числами.')
    if not 1 <= work_weeks <= 52 or not 1 <= rest_weeks <= 52:
        raise Problem('Длительность работы и отдыха: от 1 до 52 недель.')
    if repeats is not None and not 1 <= repeats <= 100:
        raise Problem('Количество повторений: от 1 до 100.')
    cursor = day(start)
    if not end and repeats is None:
        raise Problem('Укажите дату окончания или количество повторений.')
    stop = day(end) if end else cursor + timedelta(days=(work_weeks+rest_weeks)*7*repeats-1)
    date_range(start, stop.isoformat())
    result, n = [], 0
    while cursor <= stop and (repeats is None or n < repeats):
        for kind, weeks in [('work',work_weeks),('rest',rest_weeks)]:
            if cursor > stop: break
            last = min(stop, cursor+timedelta(days=weeks*7-1))
            result.append(dict(project_id=project_id, employee_id=employee_id, start=cursor.isoformat(), end=last.isoformat(), kind=kind, manual=0, notes=''))
            cursor = last + timedelta(days=1)
        n += 1
    return result

def subtract_manual(periods, exceptions):
    """Keep manual exceptions byte-for-byte; split regenerated periods around them."""
    result=[]
    for p in periods:
        fragments=[p]
        for exception in exceptions:
            remaining=[]
            for f in fragments:
                if not overlap(f, exception):
                    remaining.append(f)
                    continue
                if f['start'] < exception['start']:
                    remaining.append({**f, 'end':(day(exception['start'])-timedelta(days=1)).isoformat()})
                if f['end'] > exception['end']:
                    remaining.append({**f, 'start':(day(exception['end'])+timedelta(days=1)).isoformat()})
            fragments=remaining
        result.extend(fragments)
    return result
