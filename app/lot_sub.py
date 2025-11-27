import csv
import numpy as np
from sklearn.ensemble import RandomForestClassifier

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

# 사용 예시 (main 함수 등에서 호출)
if __name__ == "__main__":
    predict_1194_from_csv("lott.csv")

'''
lott.csv 의 count 칼럼이 추첨회수이다. [aa,bb,cc,dd,ee,ff]는 추첨수들이다.
['count'] 가 '990' ~ '1190' 회까지의 추첩 결과를 나타낸다.
아래 번호에 열거한 기능을 class로 구현해라
1. [aa,bb,cc,dd,ee,ff] 들의 sum을 구해서, '990' ~ '1190' 회까지의 그 흐름을 파악해서, 1200회차의 sum을 min ~ max (40 이내의 범위) 값으로 예측 후 return하라.
   예측 알고리즘은 머신러닝으로 하든 평균이동법으로하든, 너가 가장 정확하다고 판단되는 방법으로 lott.csv 실측자료를 가지고 모두 검증 한 후 모델을 선정,구현해라.
2. 과거 자료를 보면 1199회차의 결과를 보면 1189회차 부터 1198회차까지 지난 10번의 당첨결과중에서 3개가 당첨되었고,
    그 외 숫자에서 3개가 당첨되었다.  모든 회차들에 대해 지난 10번의 당첨결과내 재당첨 수와 아닌 수들의 당첨결과를 바탕으로
    '1200'회차의 예측을, 지난 10번의 당첨결과중 x개 예측, 그 외 수에서 y개 예측하여 return 해라.
3. 각 회차들의 당첨수들을 분석하여 '1200'회차의 예측수에서 1의자리 당첨 예측개수 x개, 10의 자리 예측개수 x1개, 20 자리 예측개수 x2, 30자리 예측개수 x3, 40자리 예측개수 x4 를 return 해라
4. 각 회차들의 당첨수들을 분석하여 '1200'회차의 예측 홀수 개수 x, 예측 짝수 개수 y, 를 return 하라 
5. 1,2,3,4번의 return결과를 받아,  그 조건에 맞는  1200회차의 예측수를 20 sets를 예측하여 print해라
6. '1200'회차의 결과를 입력 후 '1201'회차의 예측에도 사용 할 수 있게 유동적으로 구현하라.
'''




























