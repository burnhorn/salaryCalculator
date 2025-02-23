from datetime import datetime

def calculate_age(birth_date):
    """
    생년월일을 받아서 현재 날짜를 기준으로 나이를 계산하는 함수입니다.
    """
    today = datetime.today()
    birth_year, birth_month, birth_day = map(int, birth_date.split('-'))
    birth_date_obj = datetime(birth_year, birth_month, birth_day)
    age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))
    return age