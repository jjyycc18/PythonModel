import random

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
        result_last_10times[3].append(num)

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
    draws = []
    with open(csv_filepath, encodng='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row['count'].isdigit()]
        rows.sort(key=lambda x: int(x['count']), reverse=True)
        for row in rows[:last_n]:
            draw = [int(row[k]) for k in ['aa','bb','cc','dd','ee','ff'] if row[k].is disit()]
            if len(draw) == 6:
                draws.append(draw)
    draws.reverse()
    return draws
    

if __name__ == "__main__":
    meke_except_nums()
    print("조건에 맞는 10세트 번호:")
    valid_sets = generate_sets(10)
    if valid_sets:
        for idx, nums in enumerate(valid_sets, 1):
            print(f"세트 {idx}: {nums}")
    else:
        print("조건을 만족하는 세트를 찾지 못했습니다.")

    predict_1194_from_csv('d:/lott.csv')

# 이소스를 가지고 lott.csv 파일의 1000회 부터 1191회 까지 generate_sets(100) 를 호출하여 100set 중에 정답 3개이상을 맞춘 set가 몇개인지
# 테스트 해줘, 출력형식은 다음과 같이 해줘 ( 1000회 정답율 : 3개정답율 3/100개 , 4개정답율 4/100, 5개정답율 5/100, 1등당첨 1/100 )  
# 1000회의 정답은 이전 990회~999회의 자료를 바탕으로 generate_sets(100)을 한 후 1000회의 추첨결과로 산출한다, 1001회도 동일한 방법으로
