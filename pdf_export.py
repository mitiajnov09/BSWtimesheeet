import io, math, json
from datetime import timedelta
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from domain import Problem, day, date_range
from db import rows
from service import project_access

FONT='RotationSans'
pdfmetrics.registerFont(TTFont(FONT,str(Path(__file__).parent/'fonts/DejaVuSans.ttf')))
COLORS={'work':'#bde8c9','rest':'#e2e6ec','vacation':'#c6dcfa','sick':'#f9c7cb'}
LABELS={'work':'Работа','rest':'Отдых','vacation':'Отпуск','sick':'Больничный'}
CODES={'work':'Р','rest':'О','vacation':'У','sick':'Б'}
EVENT_LABELS={'outbound':'Перелёт на объект','return':'Обратный перелёт','arrival':'Прибытие','departure':'Отъезд','note':'Примечание'}
MONTHS=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']

def export(conn,user,data):
    language=data.get('language','ru')
    if language not in ('ru','lt','pl'):raise Problem('Неизвестный язык.')
    translations=json.loads((Path(__file__).parent/'static/translations.json').read_text())
    def tr(value):return translations.get(value,[value,value])[0 if language=='lt' else 1] if language!='ru' else value
    labels={key:tr(value) for key,value in LABELS.items()}
    event_labels={key:tr(value) for key,value in EVENT_LABELS.items()}
    months=[tr(value) for value in MONTHS]
    codes=CODES if language=='ru' else (dict(work='D',rest='P',vacation='A',sick='N') if language=='lt' else dict(work='P',rest='O',vacation='U',sick='Z'))
    extra={
        'ru':{'footer':'Даты включительно · Сб/Вс — календарные выходные · П — перелёт, С — другое событие','page':'Страница','worker':'Работник / специальность','details':'Примечания и события','continued':'Примечания и события — продолжение','week':'Н','flight':'П','event':'С'},
        'lt':{'footer':'Datos įskaitytinai · Št/Sk — savaitgaliai · S — skrydis, Į — kitas įvykis','page':'Puslapis','worker':'Darbuotojas / specialybė','details':'Pastabos ir įvykiai','continued':'Pastabos ir įvykiai — tęsinys','week':'S','flight':'S','event':'Į'},
        'pl':{'footer':'Daty włącznie · Sb/Nd — weekendy · L — lot, W — inne wydarzenie','page':'Strona','worker':'Pracownik / specjalność','details':'Notatki i wydarzenia','continued':'Notatki i wydarzenia — ciąg dalszy','week':'T','flight':'L','event':'W'},
    }[language]
    project=project_access(conn,user,data.get('project_id'))
    site=dict(conn.execute('SELECT * FROM sites WHERE id=?',(project['site_id'],)).fetchone())
    start,end=date_range(data.get('start'),data.get('end'))
    paper=data.get('paper','A4')
    if paper not in ('A4','A3'):raise Problem('Выберите A4 или A3.')
    employees=rows(conn,'SELECT DISTINCT e.* FROM employees e JOIN assignments a ON a.employee_id=e.id WHERE a.project_id=? AND a.start<=? AND a.end>=? ORDER BY e.last_name,e.first_name',(project['id'],end.isoformat(),start.isoformat()))
    selected=data.get('employee_ids')
    if selected is not None:
        if not isinstance(selected,list) or not selected:raise Problem('Выберите хотя бы одного работника.')
        if not set(selected).issubset({e['id'] for e in employees}):raise Problem('Нет доступа к выбранным работникам в этом диапазоне.',403)
        employees=[e for e in employees if e['id'] in selected]
    if not employees:raise Problem('Нет работников с назначением в выбранном диапазоне.')
    periods=rows(conn,'SELECT * FROM periods WHERE project_id=? AND start<=? AND end>=?',(project['id'],end.isoformat(),start.isoformat()))
    events=rows(conn,'SELECT * FROM events WHERE project_id=? AND date BETWEEN ? AND ? ORDER BY date,time',(project['id'],start.isoformat(),end.isoformat())) if data.get('include_events',True) else []
    width,height=landscape(A3 if paper=='A3' else A4)
    days_per_page=42 if paper=='A3' else 28
    def wrapped(value, maximum, size):
        lines=[];line=''
        for char in str(value).replace('\n',' '):
            if pdfmetrics.stringWidth(line+char,FONT,size)>maximum:
                lines.append(line);line=''
            line+=char
        if line:lines.append(line)
        return lines or ['']
    title_lines=wrapped(project['name'],width-56,17)
    title_extra=(len(title_lines)-1)*22
    for employee in employees:
        employee['_name_lines']=wrapped(employee['last_name']+' '+employee['first_name'],151,9)
        employee['_specialty_lines']=wrapped(employee['specialty'],151,8)
        employee['_layers']=max((p.get('layer',0)+1 for p in periods if p['employee_id']==employee['id']),default=1)
        employee['_row_height']=max(16+employee['_layers']*24,len(employee['_name_lines'])*12+len(employee['_specialty_lines'])*10+12)
    display_employees=[]
    max_layers=max(1,int((height-231-title_extra)//24))
    for employee in employees:
        for first in range(0,employee['_layers'],max_layers):
            last=min(employee['_layers'],first+max_layers)
            item={**employee,'_layer_start':first,'_layer_end':last}
            item['_row_height']=max(16+(last-first)*24,len(item['_name_lines'])*12+len(item['_specialty_lines'])*10+12)
            display_employees.append(item)
    worker_groups=[];group=[];used=0
    for employee in display_employees:
        if group and used+employee['_row_height']>height-215-title_extra:
            worker_groups.append(group);group=[];used=0
        group.append(employee);used+=employee['_row_height']
    if group:worker_groups.append(group)
    chunks=[]
    cursor=start
    while cursor<=end:
        last=min(end,cursor+timedelta(days=days_per_page-1))
        dates=[cursor+timedelta(days=i) for i in range((last-cursor).days+1)]
        for group in worker_groups:chunks.append((dates,group))
        cursor=last+timedelta(days=1)
    output=io.BytesIO();c=canvas.Canvas(output,pagesize=(width,height))
    c.setTitle(project['name']+' • '+tr('График ротаций'));c.setAuthor(tr('Ротации'))
    margin=28;name_width=166;cell=(width-margin*2-name_width)/days_per_page
    def text(x,y,value,size=9,color='#182b41'):
        c.setFillColor(HexColor(color));c.setFont(FONT,size);c.drawString(x,y,str(value))
    def clipped(value,max_width,size):
        value=str(value)
        if pdfmetrics.stringWidth(value,FONT,size)<=max_width:return value
        while value and pdfmetrics.stringWidth(value+'…',FONT,size)>max_width:value=value[:-1]
        return value+'…'
    def footer():
        text(margin,20,extra['footer'],8)
        text(width-100,20,extra['page']+' '+str(c.getPageNumber()),8)
    def title(subtitle):
        for i,line in enumerate(title_lines):text(margin,height-35-i*22,line,17)
        text(margin,height-54-title_extra,site['city']+', '+site['country']+' · '+subtitle,9)
    def legend(y):
        x=margin
        for kind,label in labels.items():
            c.setFillColor(HexColor(COLORS[kind]));c.rect(x,y-3,13,12,fill=1,stroke=0)
            text(x+18,y,codes[kind]+' — '+label,8);x+=max(95,pdfmetrics.stringWidth(codes[kind]+' — '+label,FONT,8)+34)
        text(x,y,'* '+tr('Ручная правка'),8)
    for dates,group in chunks:
        title(dates[0].strftime('%d.%m.%Y')+' — '+dates[-1].strftime('%d.%m.%Y'))
        y=height-82-title_extra;grid_x=margin+name_width
        c.setFillColor(HexColor('#eef2f6'));c.rect(margin,y-54,width-2*margin,54,fill=1,stroke=0)
        text(margin+8,y-31,extra['worker'],9)
        # Group month and ISO week spans within each page.
        for key_fn,level in [(lambda d:(d.year,d.month),0),(lambda d:d.isocalendar()[:2],1)]:
            j=0
            while j<len(dates):
                k=j+1
                while k<len(dates) and key_fn(dates[k])==key_fn(dates[j]):k+=1
                label=months[dates[j].month-1]+' '+str(dates[j].year) if level==0 else extra['week']+str(dates[j].isocalendar().week)
                if level==0 and (k-j)*cell<70:label=months[dates[j].month-1][:3]
                text(grid_x+j*cell+3,y-13-level*17,clipped(label,(k-j)*cell-5,8),8)
                j=k
        for j,d in enumerate(dates):
            if d.weekday()>=5:
                c.setFillColor(HexColor('#e1e6ee'));c.rect(grid_x+j*cell,y-54,cell,18,fill=1,stroke=0)
            text(grid_x+j*cell+cell/2-5,y-48,d.day,8)
        row_y=y-54
        for i,e in enumerate(group):
            row_height=e['_row_height'];row_y-=row_height
            c.setFillColor(white if i%2==0 else HexColor('#f7f9fb'));c.rect(margin,row_y,width-2*margin,row_height,fill=1,stroke=0)
            name_y=row_y+row_height-14
            for line in e['_name_lines']:
                text(margin+8,name_y,line,9);name_y-=12
            for line in e['_specialty_lines']:
                text(margin+8,name_y,line,8,'#58697d');name_y-=10
            for j,d in enumerate(dates):
                x=grid_x+j*cell
                if d.weekday()>=5:
                    c.setFillColor(HexColor('#edf0f4'));c.rect(x,row_y,cell,row_height,fill=1,stroke=0)
                matching=[p for p in periods if p['employee_id']==e['id'] and e['_layer_start']<=p.get('layer',0)<e['_layer_end'] and p['start']<=d.isoformat()<=p['end']]
                for p in matching:
                    lane_y=row_y+9+(e['_layer_end']-1-p.get('layer',0))*24
                    c.setFillColor(HexColor(COLORS[p['kind']]));c.rect(x,lane_y,cell,22,fill=1,stroke=0)
                    text(x+cell/2-3,lane_y+7,codes[p['kind']],7)
                    if p['manual'] and (j==0 or d.isoformat()==p['start']):text(x+1,lane_y+18,'*',7)
                ev=[ev for ev in events if ev['employee_id']==e['id'] and ev['date']==d.isoformat()]
                if ev:text(x+cell/2-3,row_y+2,extra['flight'] if any(v['kind'] in ('outbound','return') for v in ev) else extra['event'],6)
                c.setStrokeColor(HexColor('#d5dce5'));c.setLineWidth(.3);c.line(x,row_y,x,row_y+row_height)
            c.setStrokeColor(HexColor('#d5dce5'));c.line(margin,row_y,width-margin,row_y)
        legend(max(46,row_y-22));footer();c.showPage()
    details=[]
    allowed={e['id']:e for e in employees}
    if data.get('include_notes',True):
        if project['notes']:details.append(tr('Проект')+': '+project['notes'])
        for e in employees:
            if e['notes']:details.append(e['last_name']+' '+e['first_name']+': '+e['notes'])
        for p in periods:
            if p['employee_id'] in allowed and p['notes']:
                e=allowed[p['employee_id']];details.append(e['last_name']+' '+e['first_name']+' · '+p['start']+' — '+p['end']+' · '+labels[p['kind']]+': '+p['notes'])
    for ev in events:
        if ev['employee_id'] not in allowed:continue
        e=allowed[ev['employee_id']]
        details.append(e['last_name']+' '+e['first_name']+' · '+ev['date']+(' '+ev['time'] if ev['time'] else '')+' ('+ev['timezone']+') · '+event_labels[ev['kind']]+' · '+ev['route']+' '+ev['flight']+(' · '+ev['notes'] if data.get('include_notes',True) and ev['notes'] else ''))
    if details:
        title(extra['details']+' · '+start.isoformat()+' — '+end.isoformat());y=height-83-title_extra
        for detail in details:
            # Break long words as well as normal prose, respecting the page width.
            line=''
            lines=[]
            for char in detail.replace('\n',' '):
                if pdfmetrics.stringWidth(line+char,FONT,9)>width-margin*2-12:
                    lines.append(line);line=''
                line+=char
            if line:lines.append(line)
            for line in lines:
                if y<55:footer();c.showPage();title(extra['continued']);y=height-83-title_extra
                text(margin+4,y,line,9);y-=14
            y-=10
        footer();c.showPage()
    c.save();return output.getvalue()
