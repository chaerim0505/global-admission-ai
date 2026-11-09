"""Render source-linked partial 2027 evidence without deciding eligibility."""
import json
from pathlib import Path
import streamlit as st

LABELS = {
    'eligibility': ('Academic and nationality requirements', '학력·국적 요건'),
    'language': ('Language requirements', '어학 요건'),
    'documents': ('Required documents', '제출 서류'),
    'deadlines': ('Application dates', '모집 일정'),
    'costs': ('Fees and tuition', '전형료·학비'),
    'scholarships': ('Scholarships', '장학금'),
    'selection': ('Selection and admission route', '선발·입학 경로'),
}

def show_2027_panel(root: Path, program_id: str) -> bool:
    path = root / 'data/admissions/2027/requirements.json'
    if not path.exists():
        return False
    package = json.loads(path.read_text(encoding='utf-8'))
    link = package['programLinks'].get(program_id)
    if not link:
        return False
    record = next(item for item in package['records'] if item['recordId'] == link['recordId'])
    ko = st.session_state.get('ui_language') == 'ko'
    st.caption(('2027 입학 · ' if ko else '2027 entry · ') + ', '.join(record['intakes']))
    st.info('공식 2027 자료에서 일부 요건을 추출했습니다. 학과·개인별 예외와 남은 항목은 확인이 필요하며, 지원 자격을 판정한 결과가 아닙니다.' if ko else 'Partial requirements extracted from official 2027 sources. Department and applicant exceptions still need checking; this is not an eligibility decision.')
    routes = {
        'international_freshman_korean_track': ('International freshman, Korean track', '외국인 학부 신입학 · 한국어트랙'),
        'international_admissions_I': ('International Admissions I: applicant and parents are non-Korean', '국제전형 I · 지원자와 부모 모두 외국 국적'),
        'international_freshman': ('International freshman admission', '외국인 학부 신입학'),
        'international_graduate_regular': ('Regular international graduate admission', '외국인 대학원 일반 입학전형'),
        'non_eu_new_full_time_meng_electronic_computer_engineering': ('Non-EU, full-time MEng in Electronic and Computer Engineering', 'Non-EU 전일제 전자·컴퓨터공학 MEng 신입학'),
    }
    route = routes.get(record['applicantScope'], ('See source for route details', '정확한 전형은 출처 확인'))
    st.caption(('적용 전형: ' if ko else 'Applicable route: ') + route[1 if ko else 0])
    for section, facts in record['sections'].items():
        st.markdown('**' + LABELS[section][1 if ko else 0] + '**')
        for fact in facts:
            st.write('• ' + fact['ko' if ko else 'en'])
            source = package['sources'][fact['sourceId']]
            pages = ', '.join(map(str, fact['pdfPages']))
            label = ('공식 출처' if ko else 'Official source') + (' · PDF p. ' + pages if pages else '')
            st.markdown(f'[{label}]({source["url"]})')
    st.markdown('**' + ('추가 확인 사항' if ko else 'Still to check') + '**')
    for note in record['unresolvedItems']:
        st.caption('• ' + note)
    return True
