# 필요한 라이브러리 임포트
import argparse  # 커맨드 라인 인자 파싱을 위한 라이브러리
import pandas as pd  # 데이터 처리 및 엑셀 파일 읽기/쓰기를 위한 라이브러리
from decimal import Decimal, ROUND_FLOOR  # 정확한 소수 계산을 위한 Decimal 클래스
import tkinter as tk  # GUI 창 생성을 위한 Tkinter 라이브러리
from tkinter import filedialog  # 파일 다이얼로그를 위한 모듈
import time  # 시간 지연을 위한 라이브러리

from calculate_income_tax import pipeline
from calculate_age import calculate_age

# 급여를 입력받아 각종 보험료를 계산하는 함수
def calculate_insurance(salary, birth_date):
    """
    급여를 입력받아 각종 보험료를 계산하여 반환합니다.
    """
    age = calculate_age(birth_date) # 현재 만 나이 계산 함수 호출
    salary_dec = Decimal(str(salary))  # 급여를 Decimal로 변환하여 정확한 계산 수행
    truncated_salary = (int(salary) // 1000) * 1000  # 천원 단위로 절사
    truncated_salary_dec = Decimal(truncated_salary)  # 절사된 급여를 Decimal로 변환

    # 국민연금 기준소득월액 상한액과 하한액 설정
    upper_limit = Decimal('6170000')  # 617만원
    lower_limit = Decimal('390000')  # 39만원

    # 국민연금 기준소득월액 상한액과 하한액 적용
    if truncated_salary_dec > upper_limit:
        truncated_salary_dec = upper_limit
    elif truncated_salary_dec < lower_limit:
        truncated_salary_dec = lower_limit

    # 각 보험료 계산
    # 나이가 65세 이상이면 국민연금을 0으로 설정
    if age >= 65:
        national_pension = Decimal('0')
    else:
        national_pension = (truncated_salary_dec * Decimal('0.045')).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)

    health_insurance = (salary_dec * Decimal('0.0709') * Decimal('0.5')).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)
    long_term_care_insurance = (health_insurance * (Decimal('0.009182') / Decimal('0.0709'))).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)
    employment_insurance = (salary_dec * Decimal('0.009')).quantize(Decimal('1E1'), rounding=ROUND_FLOOR)

    return {
        "national_pension": int(national_pension),  # 국민연금
        "health_insurance": int(health_insurance),  # 건강보험료
        "long_term_care_insurance": int(long_term_care_insurance),  # 장기요양보험료
        "employment_insurance": int(employment_insurance)  # 고용보험료
    }

# 입력된 Excel 파일을 처리하여 보험료를 계산하고 결과를 새로운 Excel 파일로 저장하는 함수
def process_excel(input_file, output_file):
    """
    입력된 Excel 파일을 읽어 보험료를 계산한 후, 결과를 새로운 Excel 파일로 저장합니다.
    """
    df = pd.read_excel(input_file)  # 입력 파일 읽기
    insurance_data = []  # 결과를 저장할 리스트

    for index, row in df.iterrows():
        salary = row['급여']  # 급여 값 가져오기
        birth_date = row['주민등록번호']
        insurance = calculate_insurance(salary, birth_date)  # 보험료 계산
        total_deductions = sum(insurance.values())  # 총 공제액 계산
        net_salary = salary - total_deductions  # 실수령액 계산

        # 각 정보를 딕셔너리 형태로 리스트에 추가
        insurance_data.append({
            "사번": row['사번'],
            "이름": row['이름'],
            "주민등록번호": row['주민등록번호'],
            "공제대상 가족 수": row['공제대상 가족 수'],
            "8세 이상 20세 이하 자녀 수": row['8세 이상 20세 이하 자녀 수'],
            "급여": salary,
            "국민연금": insurance["national_pension"],
            "건강보험료": insurance["health_insurance"],
            "장기요양보험료": insurance["long_term_care_insurance"],
            "고용보험료": insurance["employment_insurance"],
            "총공제액": total_deductions,
            "4대보험공제후금액": net_salary
        })

    result_df = pd.DataFrame(insurance_data)  # 결과를 데이터프레임으로 변환
    result_df.to_excel(output_file, index=False)  # 결과를 엑셀 파일로 저장
    return result_df

# 메인 함수
def main():
    print("프로그램을 시작합니다. 잠시만 기다려 주세요...")  # 안내 메시지 출력
    time.sleep(1)  # 1초 대기

    parser = argparse.ArgumentParser(description="급여 데이터를 처리하는 프로그램입니다.")  # 인자 파서 생성
    parser.add_argument('-i', '--input', type=str, help="입력 Excel 파일 경로")  # 입력 파일 인자
    parser.add_argument('-o', '--output', type=str, help="출력 Excel 파일 경로")  # 출력 파일 인자
    args = parser.parse_args()  # 인자 파싱

    if not args.input:
        root = tk.Tk()
        root.withdraw()  # Tkinter 기본 창 숨기기
        args.input = filedialog.askopenfilename(title="입력 파일을 선택하세요", filetypes=[("Excel files", "*.xlsx")])  # 파일 선택 다이얼로그 표시
        if not args.input:
            print("입력 파일이 선택되지 않았습니다.")
            return

    if not args.output:
        args.output = args.input.replace('.xlsx', '_output.xlsx')  # 출력 파일 경로 설정

    process_excel(args.input, args.output)  # 엑셀 파일 처리
    
    # 근로소득세 처리 함수 호출
    pipeline()

    print(f"처리가 완료되었습니다. 결과는 {args.output}에 저장되었습니다.")  # 완료 메시지 출력

if __name__ == "__main__":
    main()  # 메인 함수 실행
