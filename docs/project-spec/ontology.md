# Global Admission AI Ontology

## 1. 프로젝트 목적

사용자의 학력, 전공, 성적, 관심 분야, 희망 국가, 학비 및 장학금 조건을 분석하여 적합한 해외 대학과 전공 과정을 추천한다. 대학원 지원자가 원하는 경우에는 관심 연구 분야와 교수의 연구 분야 및 최근 논문을 비교하여 지도교수 후보도 추천한다.

## 2. 주요 개체(Entities)

### User

사용자의 기본 정보와 지원 자격을 나타낸다. 지원 과정과 국가별 교육제도에 따라 해당되는 정보만 입력한다.

#### 필수 입력

- applicantType: 지원 과정(학부 / 석사 / 박사)
- currentEducationLevel: 현재 또는 최종 학력
- transcriptCountry: 성적표 발급 국가
- academicScore: 현재 또는 최종 학교 성적
- gradingSystem: 성적 체계(GPA, 백분율, 내신 등급, 총점 등)
- maximumScore: 성적 체계의 최고 점수(해당되는 경우)
- interests: 관심 전공 또는 연구 분야

#### 선택 입력

- schoolName: 현재 또는 최종 출신 학교
- graduationStatus: 졸업 여부 또는 졸업 예정일
- classRank: 학년 또는 학급 석차
- englishTestType: 영어 시험 종류
- englishScore: 영어 시험 점수
- transcriptFile: 성적표 파일
- activities: 교내·외 활동
- skills: 보유 기술
- researchExperience: 연구·프로젝트·논문 경험

### Preference
사용자가 원하는 유학 조건을 나타낸다.

- preferredCountries: 희망 국가
- degreeLevel: 희망 학위 과정
- preferredMajor: 희망 전공
- maximumTuition: 부담 가능한 최대 학비
- scholarshipRequired: 장학금 필요 여부
- professorMatchingRequired: 지도교수 추천 여부

### University
추천 대상 대학 정보를 나타낸다.

- universityName: 대학명
- country: 국가
- location: 지역
- ranking: 대학 순위
- websiteUrl: 대학 공식 홈페이지

### Program
대학이 제공하는 학위 과정을 나타낸다.

- programName: 과정명
- degreeLevel: 학사·석사·박사
- fieldOfStudy: 전공 분야
- tuition: 학비
- applicationDeadline: 지원 마감일
- admissionRequirements: 입학 요건
- englishRequirement: 영어 점수 요건

### Scholarship
장학금 정보를 나타낸다.

- scholarshipName: 장학금명
- amount: 지원 금액
- eligibility: 지원 자격
- deadline: 신청 마감일
- scholarshipUrl: 공식 안내 링크

### Professor
대학원 지원자를 위한 지도교수 정보를 나타낸다.

- professorName: 교수명
- university: 소속 대학
- department: 소속 학과
- researchFields: 연구 분야
- recentPublications: 최근 논문
- profileUrl: 교수 공식 프로필

## 3. 관계(Relationships)

- User `hasPreference` Preference  
  사용자는 희망 국가, 학위, 전공, 학비 등의 조건을 가진다.

- University `offers` Program  
  대학은 학사·석사·박사 과정을 제공한다.

- Program `requires` AdmissionRequirement  
  전공 과정은 GPA, 학력, 영어 점수 등의 입학 요건을 요구한다.

- Program `provides` Scholarship  
  전공 과정 또는 대학은 신청 가능한 장학금을 제공한다.

- Professor `belongsTo` University  
  교수는 특정 대학과 학과에 소속된다.

- Professor `researches` ResearchField  
  교수는 하나 이상의 연구 분야를 연구한다.

- User `matchesWith` Program  
  사용자의 프로필과 희망 조건을 전공 과정의 정보 및 입학 요건과 비교한다.

- GraduateApplicant `matchesWith` Professor  
  지도교수 추천을 선택한 대학원 지원자에 한하여 관심 분야와 교수의 연구 분야 및 최근 논문을 비교한다.

## 4. 추천 규칙(Recommendation Rules)

### 필수조건 확인

- 사용자의 학력이 과정의 지원 자격을 충족하는지 확인한다.
- GPA와 영어 점수가 최소 입학 요건을 충족하는지 확인한다.
- 사용자가 희망한 국가와 학위 과정에 해당하는지 확인한다.
- 지원 마감일이 지나지 않았는지 확인한다.

### 적합도 계산

- 희망 전공과 과정의 전공 분야 유사도
- 관심 분야와 과정 또는 교수 연구 분야의 유사도
- 사용자 예산과 실제 학비의 적합성
- 장학금 필요 여부와 신청 가능한 장학금 존재 여부
- 입학 요건 충족 정도

### 지도교수 추천

지도교수 추천은 대학원 지원자가 해당 기능을 선택한 경우에만 수행한다. 사용자의 관심 연구 분야와 교수의 연구 분야 및 최근 논문의 초록을 비교하여 적합한 교수를 추천한다.

## 5. 추천 결과(Output)

- 추천 대학명
- 추천 전공 및 학위 과정
- 적합도 점수
- 충족한 입학 조건
- 부족한 입학 조건
- 예상 학비
- 신청 가능한 장학금
- 지원 마감일
- 공식 정보 출처
- 추천 이유
- 지도교수 후보 및 관련 논문(선택 사항)