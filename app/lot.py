import random
import csv
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# 최근 10회 추첨 결과
recent_draws = [
    [5, 6, 11, 27, 43, 44],
    [3, 16, 18, 24, 40, 44],
    [6, 12, 18, 37, 40, 41],
    [8, 10, 14, 20, 33, 41],
    [1, 13, 21, 25, 28, 31],
    [4, 15, 17, 23, 27, 36],
    [14, 16, 23, 25, 31, 37],
    [6, 17, 22, 28, 29, 32],
    [2, 8, 13, 16, 23, 28],
    [5, 13, 26, 29, 37, 40]
]

# 1~45까지 번호
all_numbers = set(range(1, 46))

# 제외할 숫자들 (전역 변수)
except_nums = [1,2,3,4,5,6,7,8,9,10]

# 각 번호별 출현 횟수 계산
freq = {num: 0 for num in all_numbers}
for draw in recent_draws:
    for num in draw:
        freq[num] += 1

# 지난 출현 숫자
recent_numbers = []
for numbers in recent_numbers
    recent_numbers.extend(numbers)
recent_numbers.sort()
recent_numbers2 = set(recent_numbers)
print(f" 최근10회 출현수들 : {recent_numbers2}")
cold_numbers = [nums for nums in range(1,46) if nums not in recent_numbers2 ]
print(f" 최근10회 비 출현수들 : {cold_numbers}")

# 그룹별 분류
result_last_10times = {0: [], 1: [], 2: [], 3: []}
for num, count in freq.items():
    if count == 0:
        result_last_10times[0].append(num)
    elif count == 1:
        result_last_10times[1].append(num)
    elif count == 2:
        result_last_10times[2].append(num)
    else:
        result_last_10times[2].append(num)

# dit print
for keys,values in result_last_10times.items():
    print(f" keys : {keys} => values : {values} ")

def digit_group(num):
    """1의자리, 10의자리, 20의자리, 30의자리, 40의자리 그룹 반환"""
    if 1 <= num <= 9:
        return 1
    elif 10 <= num <= 19:
        return 10
    elif 20 <= num <= 29:
        return 20
    elif 30 <= num <= 39:
        return 30
    elif 40 <= num <= 45:
        return 40

def is_valid_set(numbers):
    # except_nums 에 포함된 수가 있으면 False 반환
    if any(num in except_nums for num in numbers):
        return False

    total = sum(numbers)
    if not (105 <= total <= 169):
        return False

    # 자리수 그룹 체크
    group_count = {1: 0, 10: 0, 20: 0, 30: 0, 40: 0}
    for num in numbers:
        group_count[digit_group(num)] += 1
    if any(v >= 3 for v in group_count.values()):
        return False

    # 홀수 세기
    odd_count = sum(1 for n in numbers if n % 2 == 1)
    if odd_count < 3:
        return False

    return True

def generate_sets(n_sets=10, max_try=5000):
    sets = []
    tries = 0
    while len(sets) < n_sets and tries < max_try:
        tries += 1
        # 그룹에서 숫자 뽑기
        # 조건: 그룹에 숫자가 부족하면 continue
        if len(result_last_10times[0]) < 1 or len(result_last_10times[1]) < 4 or len(result_last_10times[2]) < 1:
            break

        pick_0 = random.sample(result_last_10times[0], 1)
        pick_1 = random.sample(result_last_10times[1], 4)
        pick_2 = random.sample(result_last_10times[2], 1)
        candidate = pick_0 + pick_1 + pick_2
        candidate.sort()
        if is_valid_set(candidate):
            # 중복 방지
            if candidate not in sets:
                sets.append(candidate)
    return sets

def make_except_nums():
    grobal except_nums
    except_nums =[]
    pick_0 = random.sample(result_last_10times[0], 5)
    pick_1 = random.sample(result_last_10times[1], 8)
    pick_2 = random.sample(result_last_10times[2], 8)
    except_nums = pick_0 + pick_1 + pick_2
    except_nums.sort()
    print(f"자동생성 제외수 : {except_nums}")
    return except_nums

###머신러닝""
def read_recent_draws_from_csv(csv_filepath, last_n=10):
    """lott.csv 파일에서 최근 last_n회 추첨 결과만을 리스트로 반환"""
    draws = []
    with open(csv_filepath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row['count'].isdigit()]
        # count로 내림차순 정렬 (최신 회차가 맨 앞)
        rows.sort(key=lambda x: int(x['count']), reverse=True)
        for row in rows[:last_n]:
            draw = [int(row[k]) for k in ['aa', 'bb', 'cc', 'dd', 'ee', 'ff'] if row[k].isdigit()]
            if len(draw) == 6:
                draws.append(draw)
    draws.reverse() # 최신 -> 오래된 순서로 변경
    return draws

def prepare_ml_data(draws, n_numbers=45):
    X, y = [], []
    for i in range(len(draws)-1):
        x_row = [1 if num in draws[i] else 0 for num in range(1, n_numbers+1)]
        y_row = [1 if num in draws[i+1] else 0 for num in range(1, n_numbers+1)]
        X.append(x_row)
        y.append(y_row)
    return np.array(X), np.array(y)

def predict_next_draw(draws, n_numbers=45, n_sets=3):
    """랜덤포레스트로 다음 회차 번호 n_sets 세트 예측"""
    if len(draws) < 3:
        print("학습 데이터가 부족합니다.")
        return []
    X, y = prepare_ml_data(draws, n_numbers)
    last_x = [1 if num in draws[-1] else 0 for num in range(1, n_numbers+1)]
    preds = np.zeros(n_numbers)
    for i in range(n_numbers):
        clf = RandomForestClassifier(n_estimators=30, random_state=42)
        clf.fit(X, y[:, i])
        preds[i] = clf.predict_proba([last_x])[0][1]
    # 여러 세트 추출을 위해 확률값 기반 랜덤 추출
    sets = []
    for _ in range(n_sets):
        # 확률을 가중치로 6개 샘플링
        candidate = list(np.random.choice(range(1, n_numbers+1), 6, replace=False, p=preds/preds.sum()))
        candidate.sort()
        sets.append(candidate)
    return sets

def predict_1194_from_csv(csv_path):
    recent_draws = read_recent_draws_from_csv(csv_path, last_n=10)
    sets = predict_next_draw(recent_draws, n_numbers=45, n_sets=3)
    print("1194회 머신러닝 예측 3세트:")
    for idx, nums in enumerate(sets, 1):
        print(f"Set {idx}: {nums}")    

if __name__ == "__main__":
    #자동으로 제외수 만들기, 아님 수동으로할거면 주석처리
    meke_except_nums()
    
    print("조건에 맞는 10세트 번호:")
    valid_sets = generate_sets(10)
    if valid_sets:
        for idx, nums in enumerate(valid_sets, 1):
            print(f"세트 {idx}: {nums}")
    else:
        print("조건을 만족하는 세트를 찾지 못했습니다.")

    predict_1194_from_csv('d:/lott.csv')
