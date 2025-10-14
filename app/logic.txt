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
    if len(draws) < 3:
        print("학습 데이터가 부족합니다.")
        return []
    X, y = prepare_ml_data(draws, n_numbers)
    last_x = [1 if num in draws[-1] else 0 for num in range(1, n_numbers+1)]
    preds = np.zeros(n_numbers)
    for i in range(n_numbers):
        clf = RandomForestClassifier(n_estimators=30, random_state=42)
        clf.fit(X, y[:, i])
        probas = clf.predict_proba([last_x])[0]
        if len(probas) == 2:
            preds[i] = probas[1]
        else:
            preds[i] = 1.0 if clf.classes_[0] == 1 else 0.0
    sets = []
    for _ in range(n_sets):
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
