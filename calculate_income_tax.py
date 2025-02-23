import pandas as pd
from decimal import Decimal, ROUND_FLOOR

def preprocess_file(tax_file_path, hr_file_path):
    # 간이세액표 파일 읽기
    # 기본 인사정보 엑셀 파일 읽기 (header=5로 읽고, 인덱스 10번 행 삭제)
    df = pd.read_excel(tax_file_path, sheet_name='Sheet1', header=5)
    df = df.drop(10)

    df2 = pd.read_excel(hr_file_path)
    df2.head(10)

    # 컬럼 이름 재정의 (모두 문자열로 지정)
    df.columns = ['이상', '미만', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']

    # 천만원 이상 처리를 위한 기준행
    df['이상'] = df['이상'].apply(lambda x: 10000 if x == '10,000천원' else x)

    # '이상'과 '미만' 컬럼을 숫자형으로 변환
    df['이상'] = pd.to_numeric(df['이상'], errors='coerce')
    df['미만'] = pd.to_numeric(df['미만'], errors='coerce')

    return df, df2

def get_base_salary_row(df):
    # 특정 값으로 표시된 행 처리 (예: 10,000천원)
    specific_value_row = df[(df['이상'] == 10000)]

    if not specific_value_row.empty:
        # 특정 값 행이 있다면 반환
        return specific_value_row.iloc[0]
    else:
        # 해당하는 행이 없으면 예외 발생
        raise ValueError("기준 급여 범위를 찾을 수 없습니다.")

def calculate_child_deduction(num_children):
    """8세 이상 20세 이하 자녀 수에 따른 공제 금액 계산"""
    if num_children == 1:
        return 12500
    elif num_children == 2:
        return 29160
    elif num_children >= 3:
        return 29160 + (num_children - 2) * 25000
    else:
        return 0

def calculate_income_tax(df, df2, monthly_salary, num_dependents, num_children):
    # 모든 숫자를 Decimal로 변환
    monthly_salary_dec = Decimal(monthly_salary)

    # 월급여액을 천원 단위로 변환 (입력은 원 단위)
    salary_th = monthly_salary_dec / Decimal('1000')

    child_deduction = Decimal(calculate_child_deduction(int(num_children)))

    # 770천원 이하인 경우 0원
    if salary_th < Decimal('770'):
        national_tax = Decimal('0')
    # salary_th가 10,000천원 이하인 경우 기존 표 조회 (<= 로 변경)
    elif salary_th < Decimal('10000'):
        salary_row = df[(df['이상'] <= float(salary_th)) & (df['미만'] > float(salary_th))]
        if salary_row.empty:
            raise ValueError("급여 범위를 찾을 수 없습니다.")
        column_name = str(num_dependents)
        if column_name not in df.columns:
            raise ValueError("공제대상 가족 수에 대한 컬럼을 찾을 수 없습니다.")
        national_tax = Decimal(salary_row.iloc[0][column_name])
    elif salary_th == Decimal('10000'):
      # 정확히 10,000천원인 경우 -> 기준 행(10,000천원인 경우의 세액) 조회
      salary_row = df[(df['이상'] == float(salary_th))]
      if salary_row.empty:
          raise ValueError("급여 범위를 찾을 수 없습니다.")
      column_name = str(num_dependents)
      if column_name not in df.columns:
          raise ValueError("공제대상 가족 수에 대한 컬럼을 찾을 수 없습니다.")
      national_tax = Decimal(salary_row.iloc[0][column_name])
    else:
        # 10,000천원 초과인 경우 추가 과세 계산
        base_row = get_base_salary_row(df)  # 기준 행을 가져오는 함수
        column_name = str(num_dependents)
        if column_name not in df.columns:
            raise ValueError("공제대상 가족 수에 대한 컬럼을 찾을 수 없습니다.")
        base_tax = Decimal(base_row[column_name])

        if salary_th <= Decimal('14000'):
            excess = salary_th - Decimal('10000')
            additional = (excess * Decimal('0.98') * Decimal('0.35')) + Decimal('25000')
            national_tax = base_tax + additional
        elif salary_th <= Decimal('28000'):
            additional = Decimal('1397000') + (salary_th - Decimal('14000')) * Decimal('0.98') * Decimal('0.38')
            national_tax = base_tax + additional
        elif salary_th <= Decimal('30000'):
            additional = Decimal('6610600') + (salary_th - Decimal('28000')) * Decimal('0.98') * Decimal('0.40')
            national_tax = base_tax + additional
        elif salary_th <= Decimal('45000'):
            additional = Decimal('7394600') + (salary_th - Decimal('30000')) * Decimal('0.40')
            national_tax = base_tax + additional
        elif salary_th <= Decimal('87000'):
            additional = Decimal('13394600') + (salary_th - Decimal('45000')) * Decimal('0.42')
            national_tax = base_tax + additional
        else:
            additional = Decimal('31034600') + (salary_th - Decimal('87000')) * Decimal('0.45')
            national_tax = base_tax + additional

    # 적용 전 자녀 공제
    national_tax = max(national_tax - child_deduction, Decimal('0'))

    # 국세는 1원 단위로 버림
    national_tax = national_tax.quantize(Decimal('1'), rounding=ROUND_FLOOR)
    # 지방소득세: 국세의 10%
    local_tax = (national_tax * Decimal('0.1')).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)
    total_tax = national_tax + local_tax

    return int(national_tax), int(local_tax), int(total_tax)

# 각 행에 대해 계산 수행
def pipeline():
    # 엑셀 파일 경로
    tax_file_path = '근로소득_간이세액표(조견표).xlsx'
    hr_file_path = 'hr_data_output.xlsx'

    df, df2 = preprocess_file(tax_file_path, hr_file_path)

    for index, row in df2.iterrows():
        monthly_salary = row['급여']
        num_dependents = row['공제대상 가족 수']
        num_children = row['8세 이상 20세 이하 자녀 수']

        try: # 임직원별 개별적 계산을 하므로 단일 셀의 값을 업데이트할 때 사용하는 at 메서드를 이용
            nat_tax, loc_tax, tot_tax = calculate_income_tax(df, df2, monthly_salary, num_dependents, num_children)
            df2.at[index, '국세(소득세)'] = nat_tax
            df2.at[index, '지방소득세'] = loc_tax
            df2.at[index, '총 세액'] = tot_tax
        except ValueError as e:
            print(f"Error for row {index}: {e}")

    # "실수령액" 칼럼을 추가하는 경우에는 모든 행에 대해 계산된 값을 한 번에 처리하는 벡터화(vectorized) 연산이 훨씬 효율적
    df2['실수령액'] = df2['4대보험공제후금액'] - df2['총 세액']

    df2.to_excel('final_result.xlsx', index=False)  # 결과를 엑셀 파일로 저장
    return df2
