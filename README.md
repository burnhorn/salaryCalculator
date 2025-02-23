# 1. 4대보험 및 근로소득 모의 계산기
![Reference Image](https://github.com/burnhorn/salaryCalculator/raw/main/asssets/input_data.jpeg)

    - salary_processor.exe을 실행 후 4대보험 및 근로소득을 계산하고 싶은 데이터를 선택
        - 입력 칼럼(6개): 사번, 이름, 주민등록번호, 공제대상 가족 수, 8세 이상 20세 이하 자녀 수, 급여
        - 출력 칼럼(16개): 사번, 이름, 주민등록번호, 공제대상 가족 수, 8세 이상 20세 이하 자녀 수, 급여, 국민연금, 건강보험료, 장기요양보험료, 고용보험료, 총공제액,
                         4대보험공제후금액, 국세(소득세), 지방소득세, 총 세액, 실수령액

# 2. 접근 방법

**(1) 사용된 도구**

![Reference Image](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Reference Image](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

**(2) 사용 데이터**

    - 4대사회보험정보연계센터 4대보험요율
    - 국세청 근로소득 간이세액표(조견표)

**(3) 주요 내용**
- 4대 보험
    - 부동소수점으로 인한 4대보험 계산 오류를 방지하기 위해 decimal 활용
    - 나이에 따른 국민연금 미공제 적용
    - 국민연금 소득월액 1000원 미만 절사 및 기준소득월액 상/하한액 적용

- 소득세
    - 경계값 문제로 천만원과 천만원 이상 급여 처리를 위한 기준행 필요하나 to_numeric으로 인해 문자가 있는 열은 NaN이 되므로 미리 "10,000천원"을 숫자로 전처리 적용
    - 부양가족 본인 1인 필수 적용
    - 최저소득인 770천원 이하는 소득세 0원 적용

# 3. 입력과 출력 데이터

**입력 데이터**

![Reference Image](https://github.com/burnhorn/salaryCalculator/raw/main/asssets/input_columns.JPG)

**출력 데이터**

![Reference Image](https://github.com/burnhorn/salaryCalculator/raw/main/asssets/output2.JPG)

`2025년 4대보험요율 및 근로소득 간이세액표 적용`

For main code

```python
    # 각 보험료 계산(국민연금, 건강보험, 장기요양보험, 고용보험 순서)
    # 부동소수점 오차를 방지하기 위해 Decimal 사용
    # 나이가 65세 이상이면 국민연금을 0으로 설정
    if age >= 65:
        national_pension = Decimal('0')
    else:
        national_pension = (truncated_salary_dec * Decimal('0.045')).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)

    health_insurance = (salary_dec * Decimal('0.0709') * Decimal('0.5')).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)
    long_term_care_insurance = (health_insurance * (Decimal('0.009182') / Decimal('0.0709'))).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)
    employment_insurance = (salary_dec * Decimal('0.009')).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)
```

```python
    # 국세청 근로소득 간이세액표 및 기본 인사 데이터 전처리 자동화
    def preprocess_file(tax_file_path, hr_file_path):
        # 간이세액표 파일 읽기
        # 기본 인사정보 엑셀 파일 읽기 (header=5로 읽고, 인덱스 10번 행 삭제)
        df = pd.read_excel(tax_file_path, sheet_name='Sheet1', header=5)
        df = df.drop(10)

        df2 = pd.read_excel(hr_file_path)

        # 컬럼 이름 재정의 (모두 문자열로 지정)
        df.columns = ['이상', '미만', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']

        # 천만원 이상 처리를 위한 기준행
        df['이상'] = df['이상'].apply(lambda x: 10000 if x == '10,000천원' else x)

        # '이상'과 '미만' 컬럼을 숫자형으로 변환
        df['이상'] = pd.to_numeric(df['이상'], errors='coerce')
        df['미만'] = pd.to_numeric(df['미만'], errors='coerce')

        return df, df2
```