
"""
로또 분석기 실행 예제

이 스크립트는 LotteryDataHandler를 사용하여 로또 데이터를 분석하는 방법을 보여줍니다.
"""

import random
from collections import Counter
from lottery_data_handler import LotteryDataHandler

#전역 변수 선언
excluded_nums = []

def main():
    print("=== 로또 데이터 분석기 ===\n")
    
    # 데이터 핸들러 생성
    handler = LotteryDataHandler()
    
    try:
        # 1. CSV 파일 로드
        print("1. CSV 파일 로딩 중...")
        data = handler.load_data("lott.csv")
        print(f"✓ {len(data)}개의 로또 추첨 데이터를 성공적으로 로드했습니다.\n")
        
        # 2. 데이터 요약 정보 출력
        print("2. 데이터 요약:")
        summary = handler.get_data_summary()
        print(f"   - 총 추첨 횟수: {summary['total_draws']}회")
        print(f"   - 회차 범위: {summary['count_range'][0]}회 ~ {summary['count_range'][1]}회")
        print(f"   - 전체 번호 개수: {summary['total_numbers']}개")
        print(f"   - 번호 범위: {summary['number_range'][0]} ~ {summary['number_range'][1]}\n")
        
        # 3. 최근 10회 추첨 결과 보기 (자동으로 최신 회차 감지)
        print("3. 최근 10회 추첨 결과:")
        latest_round = summary['count_range'][1]  # 최신 회차
        start_round = max(summary['count_range'][0], latest_round - 9)  # 최근 10회 시작점
        recent_data = handler.get_historical_range(start_round, latest_round)
        
        print(f"   (자동 감지: {start_round}회 ~ {latest_round}회)")
        for draw in recent_data:
            numbers_str = ", ".join(f"{num:2d}" for num in draw.numbers)
            print(f"   {draw.count}회: [{numbers_str}]")
        print()
        
        # 4. 특정 범위 데이터 분석 (예: 1100-1185회)
        print("4. 특정 범위 분석 (1100-1185회):")
        range_data = handler.get_historical_range(1100, 1185)
        print(f"   - 분석 대상: {len(range_data)}회")
        
        # 번호별 출현 빈도 계산
        number_frequency = {}
        for draw in range_data:
            for number in draw.numbers:
                number_frequency[number] = number_frequency.get(number, 0) + 1
        
        # 가장 많이 나온 번호 TOP 10
        sorted_numbers = sorted(number_frequency.items(), key=lambda x: x[1], reverse=True)
        print("   - 가장 많이 나온 번호 TOP 10:")
        for i, (number, count) in enumerate(sorted_numbers[:10], 1):
            print(f"     {i:2d}. 번호 {number:2d}: {count}번 출현")
        print()
        
        # 가장 적게 나온 번호 TOP 10
        print("   - 가장 적게 나온 번호 TOP 10:")
        for i, (number, count) in enumerate(sorted_numbers[-10:], 1):
            print(f"     {i:2d}. 번호 {number:2d}: {count}번 출현")
        print()
        
        # 5. 데이터 무결성 검사
        print("5. 데이터 무결성 검사:")
        is_valid, errors = handler.validate_data_integrity()
        if is_valid:
            print("   ✓ 데이터 무결성 검사 통과")
        else:
            print("   ✗ 데이터 무결성 문제 발견:")
            for error in errors:
                print(f"     - {error}")
        
        # 6. 다음 회차 예상번호 생성
        next_round = summary['count_range'][1] + 1
        print(f"6. {next_round}회 예상번호 생성:")
        generate_predictions(handler)
        
        print("\n=== 분석 완료 ===")
        
    except FileNotFoundError:
        print("❌ 오류: lott.csv 파일을 찾을 수 없습니다.")
        print("   현재 디렉토리에 lott.csv 파일이 있는지 확인해주세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def predict_ultimate_analysis(handler, all_data, latest_round):
    """궁극의 간격 패턴 분석 - 최종 TOP 1 예측 (10회 반복 분석)"""
    
    print("      🔍 50회 데이터 간격 패턴 심층 분석 중...")
    print("      🔄 10회 반복 예측을 통한 안정성 검증\n")
    
    # 10회 예측 결과를 저장할 리스트
    all_predictions = []
    
    # 10회 반복 예측 수행
    for iteration in range(1, 11):
        print(f"         📊 {iteration}회차 예측 수행 중...")
        
        # 최근 50회 데이터 (화면에 표시된 데이터와 동일)
        recent_50_data = sorted(all_data, key=lambda x: x.count, reverse=True)[:50]
        
        # 각 번호별 상세 간격 분석
        number_analysis = {}
        
        for num in range(1, 46):
            # 해당 번호가 최근 50회에서 나온 모든 회차
            appearances = []
            for draw in recent_50_data:
                if num in draw.numbers:
                    appearances.append(draw.count)
            
            if len(appearances) >= 2:
                appearances.sort(reverse=True)  # 높은 회차부터
                
                # 간격 계산
                gaps = []
                for i in range(len(appearances) - 1):
                    gap = appearances[i] - appearances[i + 1]
                    gaps.append(gap)
                
                # 마지막 출현 후 경과 회차
                last_appearance = appearances[0]
                current_gap = latest_round - last_appearance
                
                # 간격 패턴 분석
                if gaps:
                    avg_gap = sum(gaps) / len(gaps)
                    gap_variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)
                    gap_std = gap_variance ** 0.5
                    
                    # 간격의 일관성 점수 (표준편차가 낮을수록 예측 가능)
                    consistency_score = max(0, 10 - gap_std)
                    
                    # 주기성 분석 (간격이 일정한 패턴을 보이는지)
                    periodicity_score = 0
                    if len(gaps) >= 3:
                        # 연속된 간격의 유사성 체크
                        similar_gaps = 0
                        for i in range(len(gaps) - 1):
                            if abs(gaps[i] - gaps[i + 1]) <= 2:  # 2회차 이내 차이
                                similar_gaps += 1
                        periodicity_score = (similar_gaps / (len(gaps) - 1)) * 10
                    
                    # 출현 빈도 점수
                    frequency_score = len(appearances) * 2
                    
                    # 최적 출현 시점 예측
                    if avg_gap > 0:
                        expected_next_gap = avg_gap
                        # 현재 간격이 평균에 가까우면 높은 점수
                        timing_score = max(0, 10 - abs(current_gap - expected_next_gap))
                    else:
                        timing_score = 0
                    
                    # 최근 트렌드 분석 (최근 간격이 줄어드는 추세인지)
                    trend_score = 0
                    if len(gaps) >= 2:
                        recent_trend = gaps[0] - gaps[-1]  # 최신 간격 - 과거 간격
                        if recent_trend < 0:  # 간격이 줄어드는 추세
                            trend_score = 5
                        elif recent_trend > 0:  # 간격이 늘어나는 추세
                            trend_score = -2
                    
                    # 랜덤 요소 추가 (각 반복마다 약간의 변화)
                    random_factor = random.uniform(-1, 1) * iteration * 0.1
                    
                    # 종합 점수 계산
                    total_score = (
                        consistency_score * 0.25 +
                        periodicity_score * 0.25 +
                        frequency_score * 0.2 +
                        timing_score * 0.2 +
                        trend_score * 0.1 +
                        random_factor
                    )
                    
                    number_analysis[num] = {
                        'appearances': appearances,
                        'gaps': gaps,
                        'current_gap': current_gap,
                        'avg_gap': avg_gap,
                        'consistency_score': consistency_score,
                        'periodicity_score': periodicity_score,
                        'frequency_score': frequency_score,
                        'timing_score': timing_score,
                        'trend_score': trend_score,
                        'total_score': total_score,
                        'last_appearance': last_appearance
                    }
            else:
                # 출현 횟수가 적은 번호는 낮은 점수
                random_factor = random.uniform(0, 0.5) * iteration * 0.1
                number_analysis[num] = {
                    'total_score': len(appearances) * 0.5 + random_factor,
                    'current_gap': latest_round - (appearances[0] if appearances else latest_round - 50),
                    'appearances': appearances,
                    'gaps': [],
                    'avg_gap': 0
                }
        
        # 점수 기준으로 정렬
        sorted_analysis = sorted(number_analysis.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        # 고급 필터링 적용
        # 1. 기본 후보군 (상위 15개)
        top_candidates = [num for num, _ in sorted_analysis[:15]]
        
        # 2. 최근 출현 패턴 고려 (너무 최근에 나온 번호 제외)
        filtered_candidates = []
        for num in top_candidates:
            analysis = number_analysis[num]
            if analysis['current_gap'] >= 2:  # 최소 2회차 이상 간격
                filtered_candidates.append((num, analysis))
        
        # 3. 간격 패턴 최적화
        optimal_candidates = []
        for num, analysis in filtered_candidates:
            if analysis['gaps']:
                # 현재 간격이 평균 간격의 80-120% 범위에 있는 번호 우선
                gap_ratio = analysis['current_gap'] / analysis['avg_gap'] if analysis['avg_gap'] > 0 else 1
                if 0.8 <= gap_ratio <= 1.5:
                    optimal_candidates.append((num, analysis, gap_ratio))
        
        # 4. 최종 선택 알고리즘
        if len(optimal_candidates) >= 6:
            # 간격 비율이 1에 가까운 순서로 정렬
            optimal_candidates.sort(key=lambda x: abs(x[2] - 1))
            final_selection = [num for num, _, _ in optimal_candidates[:6]]
        else:
            # 부족하면 상위 점수 번호로 보충
            final_selection = [num for num, _ in filtered_candidates[:6]]
            while len(final_selection) < 6:
                for num in top_candidates:
                    if num not in final_selection:
                        final_selection.append(num)
                        break
        
        # 5. 추가 검증 및 조정
        final_prediction = sorted(final_selection[:6])
        
        # 홀짝 균형 체크
        odd_count = sum(1 for num in final_prediction if num % 2 == 1)
        if odd_count < 2 or odd_count > 4:
            # 홀짝 균형이 맞지 않으면 조정
            if odd_count < 2:
                # 홀수 추가 필요
                for num in top_candidates:
                    if num % 2 == 1 and num not in final_prediction:
                        # 가장 낮은 점수의 짝수와 교체
                        even_nums = [n for n in final_prediction if n % 2 == 0]
                        if even_nums:
                            final_prediction.remove(min(even_nums))
                            final_prediction.append(num)
                            break
            elif odd_count > 4:
                # 홀수 제거 필요
                for num in top_candidates:
                    if num % 2 == 0 and num not in final_prediction:
                        # 가장 낮은 점수의 홀수와 교체
                        odd_nums = [n for n in final_prediction if n % 2 == 1]
                        if odd_nums:
                            final_prediction.remove(min(odd_nums))
                            final_prediction.append(num)
                            break
        
        final_prediction = sorted(final_prediction)
        
        # 이번 반복의 결과를 저장
        all_predictions.append(final_prediction)
        
        # 간단한 결과 출력
        print(f"            → {iteration}회차 결과: {final_prediction}")
    
    # 10회 예측 결과 종합 분석
    print(f"\n      " + "="*60)
    print("      🔍 10회 예측 결과 종합 분석")
    print("      " + "="*60)
    
    # 모든 예측 결과 표시
    print("      📊 전체 10회 예측 결과:")
    for i, prediction in enumerate(all_predictions, 1):
        odd_count = sum(1 for num in prediction if num % 2 == 1)
        total_sum = sum(prediction)
        print(f"         {i:2d}회차: {prediction} (홀수:{odd_count}개, 합계:{total_sum})")
    
    # 번호별 출현 빈도 계산
    number_frequency = Counter()
    for prediction in all_predictions:
        number_frequency.update(prediction)
    
    # 빈도별로 정렬
    frequency_sorted = sorted(number_frequency.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n      📈 번호별 출현 빈도 (10회 중):")
    for num, freq in frequency_sorted:
        percentage = (freq / 10) * 100
        bar = "█" * freq + "░" * (10 - freq)
        print(f"         {num:2d}번: {freq:2d}회 ({percentage:4.1f}%) {bar}")
    
    # 가장 많이 반복된 수 3개
    most_frequent = [num for num, freq in frequency_sorted[:3]]
    most_frequent_freqs = [freq for num, freq in frequency_sorted[:3]]
    
    # 가장 적게 반복된 수 3개 (출현한 번호 중에서)
    appeared_numbers = [item for item in frequency_sorted if item[1] > 0]
    least_frequent = [num for num, freq in appeared_numbers[-3:]]
    least_frequent_freqs = [freq for num, freq in appeared_numbers[-3:]]
    
    print(f"\n      🏆 가장 많이 반복된 번호 TOP 3:")
    for i, (num, freq) in enumerate(zip(most_frequent, most_frequent_freqs), 1):
        print(f"         {i}위. {num:2d}번: {freq}회 출현 ({freq/10*100:.1f}%)")
    
    print(f"\n      🔻 가장 적게 반복된 번호 3개:")
    for i, (num, freq) in enumerate(zip(least_frequent, least_frequent_freqs), 1):
        print(f"         {i}. {num:2d}번: {freq}회 출현 ({freq/10*100:.1f}%)")
    
    # 안정성 분석
    unique_numbers = set()
    for prediction in all_predictions:
        unique_numbers.update(prediction)
    
    stability_score = (len(most_frequent) / len(unique_numbers)) * 100 if unique_numbers else 0
    
    print(f"\n      📊 예측 안정성 분석:")
    print(f"         • 총 등장한 서로 다른 번호: {len(unique_numbers)}개")
    print(f"         • 고빈도 번호 (5회 이상): {len([f for f in most_frequent_freqs if f >= 5])}개")
    print(f"         • 예측 일관성 점수: {stability_score:.1f}%")
    
    # 최종 추천 번호 결정 (가장 빈도가 높은 6개)
    final_recommendation = sorted([num for num, freq in frequency_sorted[:6]])
    
    print(f"\n      🌟 최종 추천 번호 (빈도 기반 TOP 6):")
    print(f"         {final_recommendation}")

    #jyc
    excluded_nums.extend( [final_recommendation[i] for i in [0,1,2,3,4,5]] )

    
    # 최종 추천 번호의 통계
    final_odd_count = sum(1 for num in final_recommendation if num % 2 == 1)
    final_sum = sum(final_recommendation)
    
    print(f"\n      📋 최종 추천 번호 분석:")
    for num in final_recommendation:
        freq = number_frequency[num]
        print(f"         • {num:2d}번: 10회 중 {freq}회 출현 ({freq/10*100:.1f}%)")
    
    print(f"\n      📈 최종 패턴 요약:")
    print(f"         • 홀수 {final_odd_count}개, 짝수 {6-final_odd_count}개")
    print(f"         • 합계: {final_sum}")
    print(f"         • 평균 출현율: {sum(number_frequency[num] for num in final_recommendation)/6:.1f}회")
    
    print("\n      💡 10회 반복 분석을 통해 가장 안정적으로 선택된 번호들입니다.")
    
    # 추가: 최종 추천번호 기반 7세트 생성
    print("\n      " + "="*50)
    print("      🎲 최종 추천번호 기반 7세트 생성")
    print("      " + "="*50)
    
    # earliest_round 계산 (all_data에서 가장 오래된 회차)
    earliest_round_calc = min(draw.count for draw in all_data) if all_data else latest_round - 50
    final_7_sets = generate_final_7_sets(handler, final_recommendation, all_data, latest_round, earliest_round_calc)
    
    return final_recommendation


def generate_final_7_sets(handler, final_prediction, all_data, latest_round, earliest_round):
    """최종 추천번호 6개에서 3개 조합을 뽑고, 지난 10회 데이터로 나머지 3개를 채워서 7세트 생성"""
    
    import itertools
    
    print(f"      🎯 기준 번호: {final_prediction}")
    
    # 1. 최종 추천번호 6개에서 3개를 선택하는 모든 조합 생성
    three_combinations = list(itertools.combinations(final_prediction, 3))
    print(f"      📊 6개 중 3개 조합 총 개수: {len(three_combinations)}개")
    
    # 2. 지난 10회 출현 번호 분석
    recent_10_start = max(earliest_round, latest_round - 9)
    recent_10_data = handler.get_historical_range(recent_10_start, latest_round)
    
    # 지난 10회에 나온 모든 번호와 빈도
    recent_10_numbers = []
    recent_10_frequency = Counter()
    for draw in recent_10_data:
        recent_10_numbers.extend(draw.numbers)
        recent_10_frequency.update(draw.numbers)
    
    # 최종 추천번호를 제외한 지난 10회 번호들
    available_recent_numbers = [num for num in set(recent_10_numbers) if num not in final_prediction]
    
    print(f"      📈 지난 10회 출현번호 (추천번호 제외): {len(available_recent_numbers)}개")
    print(f"         {sorted(available_recent_numbers)}")
    
    # 3. 지난 10회 번호들을 빈도순으로 정렬
    recent_sorted = sorted(
        [(num, recent_10_frequency[num]) for num in available_recent_numbers],
        key=lambda x: x[1], reverse=True
    )
    
    print("      🔥 지난 10회 빈도 TOP 10:")
    for i, (num, freq) in enumerate(recent_sorted[:10], 1):
        print(f"         {i:2d}. 번호 {num:2d}: {freq}회 출현")
    
    # 4. 조합별 점수 계산 및 상위 7개 선택
    combination_scores = []
    
    for combo in three_combinations:
        # 이 3개 조합의 점수 계산 (간격 분석 점수 합계)
        combo_score = 0
        for num in combo:
            # 각 번호의 최근 출현 패턴 점수
            appearances = [draw.count for draw in recent_10_data if num in draw.numbers]
            if appearances:
                # 최근 출현할수록 높은 점수
                last_appearance = max(appearances)
                recency_score = (last_appearance - (latest_round - 10)) / 10 * 5  # 0-5점
                frequency_score = len(appearances) * 2  # 빈도 점수
                combo_score += recency_score + frequency_score
            else:
                combo_score += 1  # 기본 점수
        
        combination_scores.append((combo, combo_score))
    
    # 점수 기준으로 정렬하여 상위 7개 선택
    combination_scores.sort(key=lambda x: x[1], reverse=True)
    top_7_combinations = [combo for combo, score in combination_scores[:7]]
    
    print(f"\n      🏆 선택된 3개 조합 TOP 7:")
    for i, combo in enumerate(top_7_combinations, 1):
        score = combination_scores[i-1][1]
        print(f"         {i}. {list(combo)} (점수: {score:.1f})")
    
    # 5. 각 조합에 대해 나머지 3개를 지난 10회 데이터로 채우기
    final_7_sets = []
    
    print(f"\n      🎲 최종 7세트 생성:")
    
    for i, base_combo in enumerate(top_7_combinations, 1):
        base_set = list(base_combo)
        
        # 이미 선택된 번호들 제외
        excluded_numbers = set(base_set)
        
        # 지난 10회 번호 중에서 선택 가능한 번호들
        candidates = [num for num in available_recent_numbers if num not in excluded_numbers]
        
        # 빈도 기반으로 정렬
        candidates_with_freq = [(num, recent_10_frequency[num]) for num in candidates]
        candidates_with_freq.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 후보들 중에서 3개 선택 (약간의 랜덤성 추가)
        if len(candidates_with_freq) >= 6:
            # 상위 6개 중에서 3개 랜덤 선택
            import random
            top_candidates = [num for num, freq in candidates_with_freq[:6]]
            selected_3 = random.sample(top_candidates, 3)
        elif len(candidates_with_freq) >= 3:
            # 가능한 모든 후보 중에서 3개 선택
            selected_3 = random.sample(candidates, min(3, len(candidates)))
        else:
            # 후보가 부족하면 전체 범위에서 선택
            selected_3 = candidates[:3]
            while len(selected_3) < 3:
                candidate = random.randint(1, 45)
                if candidate not in excluded_numbers and candidate not in selected_3:
                    selected_3.append(candidate)
        
        # 최종 세트 생성
        final_set = sorted(base_set + selected_3)
        final_7_sets.append(final_set)
        
        # 세트 정보 출력
        base_combo_str = ', '.join(map(str, sorted(base_combo)))
        selected_3_str = ', '.join(map(str, sorted(selected_3)))
        
        # 각 번호의 지난 10회 출현 빈도 표시
        freq_info = []
        for num in selected_3:
            freq = recent_10_frequency.get(num, 0)
            freq_info.append(f"{num}({freq}회)")
        
        print(
            f"         세트 {i}: {final_set}\n"
            f"            ├ 기준 3개: [{base_combo_str}]\n"
            f"            └ 추가 3개: [{selected_3_str}] → {', '.join(freq_info)}"
        )
    
    # 6. 세트별 통계 분석
    print(f"\n      📊 생성된 7세트 통계 분석:")
    
    for i, final_set in enumerate(final_7_sets, 1):
        odd_count = sum(1 for num in final_set if num % 2 == 1)
        even_count = 6 - odd_count
        total_sum = sum(final_set)
        
        # 지난 10회 출현 번호 개수
        recent_count = sum(1 for num in final_set if num in set(recent_10_numbers))
        
        print(
            f"         세트 {i}: 홀수 {odd_count}개, 짝수 {even_count}개, "
            f"합계 {total_sum}, 지난10회출현 {recent_count}개"
        )
    
    # 7. 추천 우선순위
    print(f"\n      🌟 추천 우선순위:")
    
    # 각 세트의 종합 점수 계산
    set_scores = []
    for i, final_set in enumerate(final_7_sets):
        score = 0
        
        # 홀짝 균형 점수 (3:3이 최고)
        odd_count = sum(1 for num in final_set if num % 2 == 1)
        balance_score = 10 - abs(odd_count - 3) * 2
        
        # 합계 점수 (120-140 범위가 최적)
        total_sum = sum(final_set)
        if 120 <= total_sum <= 140:
            sum_score = 10
        else:
            sum_score = max(0, 10 - abs(total_sum - 130) / 5)
        
        # 지난 10회 출현 점수
        recent_count = sum(1 for num in final_set if num in set(recent_10_numbers))
        recent_score = recent_count * 1.5
        
        total_score = balance_score + sum_score + recent_score
        set_scores.append((i + 1, total_score, final_set))
    
    # 점수 기준으로 정렬
    set_scores.sort(key=lambda x: x[1], reverse=True)
    
    for rank, (set_num, score, final_set) in enumerate(set_scores, 1):
        star = "⭐" if rank <= 3 else "  "
        print(f"         {star} {rank}위. 세트 {set_num}: {final_set} (점수: {score:.1f})")
    
    print(f"\n      💡 상위 3개 세트를 우선 추천합니다!")

    #jyc
    global excluded_nums
    for s in final_7_sets:
        excluded_nums.extend( [s[i] for i in [0,2,3,4,5]] )
    
    return final_7_sets


def generate_predictions(handler):
    """다양한 분석 방법으로 다음 회차 예상번호를 생성합니다."""
    
    # 데이터 범위 자동 감지
    summary = handler.get_data_summary()
    latest_round = summary['count_range'][1]  # 최신 회차
    earliest_round = summary['count_range'][0]  # 가장 오래된 회차
    next_round = latest_round + 1  # 다음 예상 회차
    
    # 전체 데이터 가져오기
    all_data = handler.get_historical_range(earliest_round, latest_round)
    
    # 최근 50회 데이터 (자동 계산)
    recent_start = max(earliest_round, latest_round - 49)
    recent_data = handler.get_historical_range(recent_start, latest_round)
    
    print(f"   다양한 분석 방법으로 {next_round}회 예상번호를 생성합니다...\n")
    
    # 방법 1: 전체 빈도 기반 예상
    print(f"   📊 방법 1: 전체 빈도 분석 ({earliest_round}-{latest_round}회)")
    all_frequency = Counter()
    for draw in all_data:
        all_frequency.update(draw.numbers)
    
    # 가장 많이 나온 번호들 중에서 선택
    top_numbers = [num for num, _ in all_frequency.most_common(15)]
    prediction1 = sorted(random.sample(top_numbers, 6))
    print(f"      예상번호: {prediction1}")
    print(f"      (가장 많이 나온 15개 번호 중 랜덤 선택)")
    
    #jyc
    global excluded_nums
    excluded_nums.extend( [prediction1[i] for i in [2,3,4,5]] )

    # 방법 2: 최근 빈도 기반 예상
    recent_count = len(recent_data)
    print(f"\n   🔥 방법 2: 최근 빈도 분석 (최근 {recent_count}회)")
    recent_frequency = Counter()
    for draw in recent_data:
        recent_frequency.update(draw.numbers)
    
    hot_numbers = [num for num, _ in recent_frequency.most_common(12)]
    prediction2 = sorted(random.sample(hot_numbers, 6))
    print(f"      예상번호: {prediction2}")
    print(f"      (최근 {recent_count}회에서 가장 많이 나온 12개 번호 중 랜덤 선택)")

    #jyc
    excluded_nums.extend( [prediction2[i] for i in [0,1,2,3,4,5]] )
    
    # 방법 3: 균형 분석 (고빈도 + 저빈도 조합)
    print("\n   ⚖️  방법 3: 균형 분석 (고빈도 + 저빈도 조합)")
    top_6 = [num for num, _ in all_frequency.most_common(10)]
    bottom_numbers = [num for num, count in all_frequency.most_common()[35:]]  # 하위 10개
    
    # 고빈도 4개 + 저빈도 2개
    high_pick = random.sample(top_6, 4)
    low_pick = random.sample(bottom_numbers, 2)
    prediction3 = sorted(high_pick + low_pick)
    print(f"      예상번호: {prediction3}")
    print(f"      (고빈도 4개 + 저빈도 2개 조합)")

    #
    excluded_nums.extend( [prediction3[i] for i in [0,1,2,3,4]] )
    
    # 방법 4: 패턴 분석 (연속번호 고려)
    print("\n   🔍 방법 4: 패턴 분석")
    # 최근 추세에서 자주 나오는 구간 분석
    recent_numbers = []
    for draw in recent_data[-20:]:  # 최근 20회
        recent_numbers.extend(draw.numbers)
    
    # 구간별 빈도 (1-10, 11-20, 21-30, 31-40, 41-45)
    ranges = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 45)]
    range_counts = {}
    
    for start, end in ranges:
        count = sum(1 for num in recent_numbers if start <= num <= end)
        range_counts[(start, end)] = count
    
    # 각 구간에서 1-2개씩 선택
    prediction4 = []
    available_numbers = list(range(1, 46))
    
    for (start, end), count in sorted(range_counts.items(), key=lambda x: x[1], reverse=True):
        range_numbers = [n for n in available_numbers if start <= n <= end]
        if range_numbers and len(prediction4) < 6:
            selected = random.choice(range_numbers)
            prediction4.append(selected)
            available_numbers.remove(selected)
    
    # 부족한 만큼 랜덤 추가
    while len(prediction4) < 6:
        remaining = random.choice(available_numbers)
        prediction4.append(remaining)
        available_numbers.remove(remaining)
    
    prediction4 = sorted(prediction4)
    print(f"      예상번호: {prediction4}")
    print(f"      (구간별 균형 고려)")

    #jyc
    excluded_nums.extend( [prediction4[i] for i in [0,2,3,4]] )
    
    # 방법 5: AI 스타일 예상 (복합 가중치)
    print("\n   🤖 방법 5: AI 복합 분석")
    
    # 각 번호별 점수 계산
    scores = {}
    for num in range(1, 46):
        score = 0
        
        # 전체 빈도 점수 (30%)
        all_count = all_frequency.get(num, 0)
        score += (all_count / max(all_frequency.values())) * 30
        
        # 최근 빈도 점수 (40%)
        recent_count = recent_frequency.get(num, 0)
        if recent_frequency:
            score += (recent_count / max(recent_frequency.values())) * 40
        
        # 최근 출현 간격 점수 (20%)
        last_appearances = []
        for i, draw in enumerate(reversed(all_data)):
            if num in draw.numbers:
                last_appearances.append(i)
                if len(last_appearances) >= 3:
                    break
        
        if last_appearances:
            avg_gap = sum(last_appearances) / len(last_appearances)
            gap_score = max(0, 20 - avg_gap) / 20 * 20  # 최근일수록 높은 점수
            score += gap_score
        
        # 랜덤 요소 (10%)
        score += random.random() * 10
        
        scores[num] = score
    
    # 점수 기반으로 상위 6개 선택
    top_scored = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    prediction5 = sorted([num for num, _ in top_scored[:6]])
    print(f"      예상번호: {prediction5}")
    print(f"      (복합 가중치 분석)")
    
    #jyc
    excluded_nums.extend( [prediction5[i] for i in [0,2,3,4,5]] )

    # 방법 6: 당첨 간격 분석
    print("\n   ⏰ 방법 6: 당첨 간격 분석")
    
    # 각 번호별 마지막 당첨 회차와 평균 간격 계산
    number_gaps = {}
    number_last_appearance = {}
    number_all_gaps = {}
    
    for num in range(1, 46):
        appearances = []
        # 최신 회차부터 역순으로 검색
        for i, draw in enumerate(reversed(all_data)):
            if num in draw.numbers:
                current_round = latest_round - i  # 실제 회차 번호
                appearances.append(current_round)
        
        if appearances:
            # 마지막 당첨 회차
            number_last_appearance[num] = max(appearances)
            
            # 당첨 간격들 계산
            appearances.sort()
            gaps = []
            for i in range(1, len(appearances)):
                gap = appearances[i] - appearances[i-1]
                gaps.append(gap)
            
            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                number_all_gaps[num] = gaps
                
                # 현재까지의 간격 (최신 회차 기준)
                current_gap = latest_round - number_last_appearance[num]
                
                # 간격 점수 계산 (평균 간격보다 길면 높은 점수)
                if avg_gap > 0:
                    gap_score = current_gap / avg_gap
                else:
                    gap_score = current_gap
                
                number_gaps[num] = {
                    'last_round': number_last_appearance[num],
                    'current_gap': current_gap,
                    'avg_gap': round(avg_gap, 1),
                    'gap_score': gap_score,
                    'total_appearances': len(appearances)
                }
        else:
            # 한 번도 나오지 않은 번호 (있을 가능성 낮음)
            number_gaps[num] = {
                'last_round': 0,
                'current_gap': latest_round,
                'avg_gap': 0,
                'gap_score': 100,  # 매우 높은 점수
                'total_appearances': 0
            }
    
    # 간격 점수 기반으로 정렬 (오래 안 나온 번호일수록 높은 점수)
    gap_sorted = sorted(number_gaps.items(), key=lambda x: x[1]['gap_score'], reverse=True)
    
    # 상위 15개 중에서 6개 선택 (너무 극단적인 것 방지)
    top_gap_candidates = [num for num, data in gap_sorted[:15] if data['total_appearances'] > 5]
    
    if len(top_gap_candidates) >= 6:
        prediction6 = sorted(random.sample(top_gap_candidates, 6))
    else:
        # 후보가 부족하면 상위에서 직접 선택
        prediction6 = sorted([num for num, _ in gap_sorted[:6]])
    
    print(f"      예상번호: {prediction6}")
    print(f"      (당첨 간격 분석 - 오래 안 나온 번호 우선)")

    #jyc
    excluded_nums.extend( [prediction6[i] for i in [0,1,2,3,4,5]] )
    
    # 간격 분석 상세 정보
    print(f"\n      📊 간격 분석 상세:")
    print(f"         오래 안 나온 번호 TOP 10:")
    for i, (num, data) in enumerate(gap_sorted[:10], 1):
        print(f"         {i:2d}. 번호 {num:2d}: {data['current_gap']:2d}회 전 (평균간격: {data['avg_gap']:4.1f}회)")
    
    # 통계 정보 출력
    print(f"\n   📈 참고 통계:")
    print(f"      - 전체 데이터: {len(all_data)}회 분석")
    print(f"      - 최근 데이터: {len(recent_data)}회 분석")
    
    # 가장 많이 나온 번호 TOP 5
    top_5_all = all_frequency.most_common(5)
    print(f"      - 전체 최다 출현: {', '.join([f'{num}({count}회)' for num, count in top_5_all])}")
    
    # 최근 가장 많이 나온 번호 TOP 5
    top_5_recent = recent_frequency.most_common(5)
    print(f"      - 최근 최다 출현: {', '.join([f'{num}({count}회)' for num, count in top_5_recent])}")
    
    # 최근 안 나온 번호들
    recent_missing = []
    for num in range(1, 46):
        if num in number_gaps and number_gaps[num]['current_gap'] >= 10:
            recent_missing.append((num, number_gaps[num]['current_gap']))
    
    recent_missing.sort(key=lambda x: x[1], reverse=True)
    if recent_missing:
        missing_str = ', '.join([f'{num}({gap}회전)' for num, gap in recent_missing[:5]])
        print(f"      - 오래 안 나온 번호: {missing_str}")
    
    # 방법 7: 최근 10회 기반 체계적 선택
    print("\n   🎯 방법 7: 최근 10회 기반 체계적 선택")
    
    # 최근 10회 데이터 가져오기
    recent_10_start = max(earliest_round, latest_round - 9)
    recent_10_data = handler.get_historical_range(recent_10_start, latest_round)
    
    # 최근 10회에 나온 모든 번호들과 빈도 계산
    recent_10_numbers = []
    recent_10_frequency = Counter()
    for draw in recent_10_data:
        recent_10_numbers.extend(draw.numbers)
        recent_10_frequency.update(draw.numbers)
    
    # 최근 10회에 나온 고유 번호들
    recent_10_unique = list(set(recent_10_numbers))
    
    # 전체 데이터에서 저빈도 번호 TOP 4 (최근 10회에 없는 번호 중에서)
    all_numbers_not_in_recent_10 = [num for num in range(1, 46) if num not in recent_10_unique]
    low_freq_candidates = []
    for num, count in all_frequency.most_common()[-20:]:  # 하위 20개에서
        if num in all_numbers_not_in_recent_10:
            low_freq_candidates.append(num)
        if len(low_freq_candidates) >= 4:
            break
    
    # 4세트 생성
    prediction_sets = []
    
    for set_num in range(1, 5):
        # 최근 10회 번호들을 빈도별로 정렬
        recent_10_sorted = sorted(recent_10_frequency.items(), key=lambda x: x[1], reverse=True)
        
        # 고빈도 TOP 7에서 2개 선택
        high_freq_pool = [num for num, _ in recent_10_sorted[:7]]
        high_freq_selected = random.sample(high_freq_pool, min(2, len(high_freq_pool)))
        
        # 저빈도 TOP 7에서 2개 선택 (최근 10회 내에서)
        low_freq_pool = [num for num, _ in recent_10_sorted[-7:]]
        low_freq_selected = random.sample(low_freq_pool, min(2, len(low_freq_pool)))
        
        # 나머지 중간 빈도에서 1개 선택
        middle_pool = [num for num, _ in recent_10_sorted[7:-7]]
        if not middle_pool:  # 중간이 없으면 전체에서 선택
            middle_pool = [num for num in recent_10_unique 
                          if num not in high_freq_selected and num not in low_freq_selected]
        
        middle_selected = []
        if middle_pool:
            middle_selected = [random.choice(middle_pool)]
        
        # 최근 10회 밖에서 저빈도 1개 선택
        external_selected = []
        if low_freq_candidates:
            external_selected = [random.choice(low_freq_candidates)]
        
        # 5개 + 1개 = 6개 조합
        prediction_set = sorted(high_freq_selected + low_freq_selected + middle_selected + external_selected)
        
        # 6개가 안 되면 부족한 만큼 추가
        while len(prediction_set) < 6:
            remaining_pool = [num for num in recent_10_unique if num not in prediction_set]
            if remaining_pool:
                prediction_set.append(random.choice(remaining_pool))
            else:
                # 최근 10회에서도 부족하면 전체에서 선택
                all_remaining = [num for num in range(1, 46) if num not in prediction_set]
                if all_remaining:
                    prediction_set.append(random.choice(all_remaining))
                else:
                    break
        
        prediction_set = sorted(prediction_set[:6])  # 6개로 제한
        prediction_sets.append(prediction_set)
        
        print(f"      세트 {set_num}: {prediction_set}")
    
    # 상세 분석 정보
    print(f"\n      📊 최근 10회 분석 상세:")
    print(f"         분석 범위: {recent_10_start}회 ~ {latest_round}회")
    print(f"         최근 10회 고빈도 TOP 7: {[num for num, _ in recent_10_sorted[:7]]}")
    print(f"         최근 10회 저빈도 TOP 7: {[num for num, _ in recent_10_sorted[-7:]]}")
    print(f"         전체 저빈도 후보 (최근 10회 제외): {low_freq_candidates[:4]}")
    
    # 방법 8: 수열 패턴 분석
    print("\n   🔢 방법 8: 수열 패턴 분석")
    
    # 각 번호별 당첨 회차 수열 분석
    number_sequences = {}
    number_probabilities = {}
    
    for num in range(1, 46):
        # 해당 번호가 당첨된 모든 회차 수집
        winning_rounds = []
        for draw in all_data:
            if num in draw.numbers:
                winning_rounds.append(draw.count)
        
        if len(winning_rounds) >= 3:  # 최소 3번 이상 당첨된 번호만 분석
            winning_rounds.sort()
            
            # 간격 수열 계산
            gaps = []
            for i in range(1, len(winning_rounds)):
                gap = winning_rounds[i] - winning_rounds[i-1]
                gaps.append(gap)
            
            # 수열 패턴 분석
            if len(gaps) >= 2:
                # 1. 평균 간격
                avg_gap = sum(gaps) / len(gaps)
                
                # 2. 최근 3개 간격의 트렌드 분석
                recent_gaps = gaps[-3:] if len(gaps) >= 3 else gaps
                
                # 3. 간격의 변화 패턴 (증가/감소/일정)
                trend_score = 0
                if len(recent_gaps) >= 2:
                    for i in range(1, len(recent_gaps)):
                        if recent_gaps[i] > recent_gaps[i-1]:
                            trend_score += 1
                        elif recent_gaps[i] < recent_gaps[i-1]:
                            trend_score -= 1
                
                # 4. 마지막 당첨 후 경과 회차
                last_winning_round = winning_rounds[-1]
                current_gap = latest_round - last_winning_round
                
                # 5. 수열 기반 다음 출현 예측
                # 최근 간격들의 가중 평균 (최근일수록 높은 가중치)
                if len(recent_gaps) >= 2:
                    weights = [i+1 for i in range(len(recent_gaps))]
                    weighted_avg = sum(gap * weight for gap, weight in zip(recent_gaps, weights)) / sum(weights)
                else:
                    weighted_avg = avg_gap
                
                # 6. 확률 계산 (여러 요소 종합)
                # 기본 확률: 현재 간격이 예상 간격에 가까울수록 높은 확률
                base_prob = max(0, 1 - abs(current_gap - weighted_avg) / weighted_avg) if weighted_avg > 0 else 0
                
                # 트렌드 보정
                trend_factor = 1 + (trend_score * 0.1)  # 트렌드에 따른 보정
                
                # 최근성 보정 (최근에 나왔으면 확률 감소)
                recency_factor = max(0.1, current_gap / avg_gap) if avg_gap > 0 else 1
                
                # 최종 확률 계산
                final_probability = base_prob * trend_factor * recency_factor * 100
                final_probability = min(100, max(0, final_probability))  # 0-100% 범위로 제한
                
                number_sequences[num] = {
                    'winning_rounds': winning_rounds,
                    'gaps': gaps,
                    'avg_gap': round(avg_gap, 1),
                    'recent_gaps': recent_gaps,
                    'weighted_avg': round(weighted_avg, 1),
                    'current_gap': current_gap,
                    'trend_score': trend_score,
                    'probability': round(final_probability, 2)
                }
                
                number_probabilities[num] = final_probability
        else:
            # 당첨 횟수가 적은 번호는 낮은 확률
            number_probabilities[num] = 1.0
    
    # 확률 기준으로 정렬
    prob_sorted = sorted(number_probabilities.items(), key=lambda x: x[1], reverse=True)
    
    # TOP 15 추출
    top_15_numbers = [num for num, prob in prob_sorted[:15]]
    
    print(f"      📊 수열 분석 결과 TOP 15:")
    for i, (num, prob) in enumerate(prob_sorted[:15], 1):
        if num in number_sequences:
            seq_info = number_sequences[num]
            recent_gaps_str = ', '.join(map(str, seq_info['recent_gaps'][-3:]))
            print(f"         {i:2d}. 번호 {num:2d}: {prob:5.2f}% (현재간격:{seq_info['current_gap']:2d}, 최근간격:[{recent_gaps_str}])")
            
            #jyc
            if i < 11:
                excluded_nums.append(num)
        else:
            print(f"         {i:2d}. 번호 {num:2d}: {prob:5.2f}% (데이터 부족)")
    
    # 4세트 생성 (TOP 15에서 랜덤 6개씩)
    print(f"\n      🎲 TOP 15 기반 4세트:")
    sequence_sets = []
    for set_num in range(1, 5):
        prediction_set = sorted(random.sample(top_15_numbers, 6))
        sequence_sets.append(prediction_set)
        print(f"         세트 {set_num}: {prediction_set}")
    
    # 최근 10회 당첨 번호와 TOP 15의 교집합
    recent_10_start = max(earliest_round, latest_round - 9)
    recent_10_data = handler.get_historical_range(recent_10_start, latest_round)
    
    recent_10_all_numbers = set()
    for draw in recent_10_data:
        recent_10_all_numbers.update(draw.numbers)
    
    intersection = [num for num in top_15_numbers if num in recent_10_all_numbers]
    
    print(f"\n      🔍 TOP 15와 최근 10회 교집합:")
    print(f"         최근 10회 범위: {recent_10_start}회 ~ {latest_round}회")
    print(f"         교집합 번호: {sorted(intersection)} ({len(intersection)}개)")
    
    if intersection:
        intersection_probs = [(num, number_probabilities[num]) for num in intersection]
        intersection_probs.sort(key=lambda x: x[1], reverse=True)
        print(f"         확률 순위:")
        for i, (num, prob) in enumerate(intersection_probs, 1):
            print(f"           {i}. 번호 {num:2d}: {prob:5.2f}%")
    
    # 상세 분석 예시 (상위 3개 번호)
    print(f"\n      📈 상위 3개 번호 상세 분석:")
    for i, (num, prob) in enumerate(prob_sorted[:3], 1):
        if num in number_sequences:
            seq = number_sequences[num]
            print(f"         {i}. 번호 {num:2d} (확률: {prob:5.2f}%)")
            print(f"            당첨 회차: {seq['winning_rounds'][-5:]}... (최근 5회)")
            print(f"            간격 수열: {seq['gaps'][-5:]}... (최근 5개)")
            print(f"            평균 간격: {seq['avg_gap']}회, 가중 평균: {seq['weighted_avg']}회")
            print(f"            현재 간격: {seq['current_gap']}회, 트렌드: {seq['trend_score']}")
    
    # 방법 9: 홀짝 패턴 및 합계 분석
    print("\n   🎲 방법 9: 홀짝 패턴 및 합계 분석")
    
    # 각 회차별 홀수/짝수 개수와 합계 분석
    draw_patterns = []
    
    for draw in all_data:
        odd_count = sum(1 for num in draw.numbers if num % 2 == 1)
        even_count = 6 - odd_count
        total_sum = sum(draw.numbers)
        
        draw_patterns.append({
            'round': draw.count,
            'odd_count': odd_count,
            'even_count': even_count,
            'total_sum': total_sum,
            'numbers': draw.numbers
        })
    
    # 홀수/짝수 개수 수열 분석
    odd_counts = [pattern['odd_count'] for pattern in draw_patterns]
    even_counts = [pattern['even_count'] for pattern in draw_patterns]
    total_sums = [pattern['total_sum'] for pattern in draw_patterns]
    
    # 최근 20회 패턴 분석
    recent_20_patterns = draw_patterns[-20:]
    recent_odd_counts = [p['odd_count'] for p in recent_20_patterns]
    recent_even_counts = [p['even_count'] for p in recent_20_patterns]
    recent_sums = [p['total_sum'] for p in recent_20_patterns]
    
    # 패턴 예측
    # 1. 홀수 개수 예측 (최근 패턴 기반)
    avg_odd = sum(recent_odd_counts) / len(recent_odd_counts)
    
    # 2. 합계 예측 (최근 패턴 기반)
    avg_sum = sum(recent_sums) / len(recent_sums)
    
    # 3. 예상 범위 계산
    predicted_odd_count = round(avg_odd)
    predicted_even_count = 6 - predicted_odd_count
    predicted_sum_min = int(avg_sum - 10)
    predicted_sum_max = int(avg_sum + 10)
    
    print(f"      📊 패턴 분석 결과:")
    print(f"         최근 20회 평균 홀수 개수: {avg_odd:.1f}개")
    print(f"         최근 20회 평균 합계: {avg_sum:.1f}")
    print(f"         예상 홀수/짝수: {predicted_odd_count}개/{predicted_even_count}개")
    print(f"         예상 합계 범위: {predicted_sum_min} ~ {predicted_sum_max}")
    
    # 최근 10회 출현 번호
    recent_10_start = max(earliest_round, latest_round - 9)
    recent_10_data = handler.get_historical_range(recent_10_start, latest_round)
    
    recent_10_all_numbers = set()
    for draw in recent_10_data:
        recent_10_all_numbers.update(draw.numbers)
    
    recent_10_list = list(recent_10_all_numbers)
    external_numbers = [num for num in range(1, 46) if num not in recent_10_all_numbers]
    
    # 홀수/짝수 분류
    recent_10_odd = [num for num in recent_10_list if num % 2 == 1]
    recent_10_even = [num for num in recent_10_list if num % 2 == 0]
    external_odd = [num for num in external_numbers if num % 2 == 1]
    external_even = [num for num in external_numbers if num % 2 == 0]
    
    print(f"\n      🔍 번호 풀 분석:")
    print(f"         최근 10회 홀수: {sorted(recent_10_odd)} ({len(recent_10_odd)}개)")
    print(f"         최근 10회 짝수: {sorted(recent_10_even)} ({len(recent_10_even)}개)")
    print(f"         외부 홀수: {sorted(external_odd)} ({len(external_odd)}개)")
    print(f"         외부 짝수: {sorted(external_even)} ({len(external_even)}개)")
    
    # 7세트 생성
    print(f"\n      🎯 조건 기반 7세트 생성:")
    pattern_sets = []
    
    for set_num in range(1, 8):
        attempts = 0
        max_attempts = 1000
        
        while attempts < max_attempts:
            # 최근 10회에서 5개 선택
            recent_5 = random.sample(recent_10_list, 5)
            
            # 외부에서 1개 선택
            external_1 = random.sample(external_numbers, 1)
            
            # 전체 조합
            candidate_set = recent_5 + external_1
            
            # 홀짝 개수 확인
            candidate_odd_count = sum(1 for num in candidate_set if num % 2 == 1)
            candidate_even_count = 6 - candidate_odd_count
            
            # 합계 확인
            candidate_sum = sum(candidate_set)
            
            # 조건 확인
            odd_match = candidate_odd_count == predicted_odd_count
            sum_match = predicted_sum_min <= candidate_sum <= predicted_sum_max
            
            if odd_match and sum_match:
                pattern_sets.append(sorted(candidate_set))
                break
            
            attempts += 1
        
        if attempts >= max_attempts:
            # 조건을 만족하는 조합을 찾지 못한 경우, 가장 가까운 조합 생성
            recent_5 = random.sample(recent_10_list, 5)
            external_1 = random.sample(external_numbers, 1)
            fallback_set = sorted(recent_5 + external_1)
            pattern_sets.append(fallback_set)
            print(f"         세트 {set_num}: {fallback_set} (조건 완화)")
        else:
            candidate_odd = sum(1 for num in pattern_sets[-1] if num % 2 == 1)
            candidate_sum = sum(pattern_sets[-1])
            print(f"         세트 {set_num}: {pattern_sets[-1]} (홀수:{candidate_odd}개, 합:{candidate_sum})")
    
    # 생성된 세트들의 통계
    print(f"\n      📈 생성된 세트 통계:")
    set_odd_counts = []
    set_sums = []
    
    for i, pset in enumerate(pattern_sets, 1):
        odd_count = sum(1 for num in pset if num % 2 == 1)
        total_sum = sum(pset)
        set_odd_counts.append(odd_count)
        set_sums.append(total_sum)
    
    print(f"         홀수 개수 분포: {set_odd_counts}")
    print(f"         합계 분포: {set_sums}")
    print(f"         평균 홀수 개수: {sum(set_odd_counts)/len(set_odd_counts):.1f}개")
    print(f"         평균 합계: {sum(set_sums)/len(set_sums):.1f}")
    
    # 최근 패턴 트렌드 분석
    print(f"\n      📊 최근 패턴 트렌드:")
    print(f"         최근 5회 홀수 개수: {recent_odd_counts[-5:]}")
    print(f"         최근 5회 합계: {recent_sums[-5:]}")
    
    # 홀짝 패턴 빈도 분석
    odd_count_freq = {}
    for count in odd_counts:
        odd_count_freq[count] = odd_count_freq.get(count, 0) + 1
    
    print(f"         전체 홀수 개수 빈도:")
    for odd_num in sorted(odd_count_freq.keys()):
        freq = odd_count_freq[odd_num]
        percentage = (freq / len(odd_counts)) * 100
        print(f"           {odd_num}개: {freq}회 ({percentage:.1f}%)")
    
    # 합계 범위 분석
    sum_ranges = {
        '60-90': 0, '91-120': 0, '121-150': 0, '151-180': 0, 
        '181-210': 0, '211-240': 0, '241-270': 0
    }
    
    for total in total_sums:
        if 60 <= total <= 90:
            sum_ranges['60-90'] += 1
        elif 91 <= total <= 120:
            sum_ranges['91-120'] += 1
        elif 121 <= total <= 150:
            sum_ranges['121-150'] += 1
        elif 151 <= total <= 180:
            sum_ranges['151-180'] += 1
        elif 181 <= total <= 210:
            sum_ranges['181-210'] += 1
        elif 211 <= total <= 240:
            sum_ranges['211-240'] += 1
        elif 241 <= total <= 270:
            sum_ranges['241-270'] += 1
    
    print(f"         합계 범위별 빈도:")
    for range_name, count in sum_ranges.items():
        percentage = (count / len(total_sums)) * 100
        print(f"           {range_name}: {count}회 ({percentage:.1f}%)")
    
    # 방법 10: 머신러닝 기반 위치별 예측
    print("\n   🤖 방법 10: 머신러닝 기반 위치별 예측")
    
    # CSV 데이터를 위치별로 분석
    position_data = {
        'aa': [], 'bb': [], 'cc': [], 'dd': [], 'ee': [], 'ff': []
    }
    
    # 각 추첨의 번호를 정렬해서 위치별로 저장
    for draw in all_data:
        sorted_numbers = sorted(draw.numbers)
        position_data['aa'].append(sorted_numbers[0])
        position_data['bb'].append(sorted_numbers[1])
        position_data['cc'].append(sorted_numbers[2])
        position_data['dd'].append(sorted_numbers[3])
        position_data['ee'].append(sorted_numbers[4])
        position_data['ff'].append(sorted_numbers[5])
    
    # 머신러닝 모델들 정의
    def moving_average_predict(data, window=5):
        """이동평균 기반 예측"""
        if len(data) < window:
            return sum(data) / len(data)
        return sum(data[-window:]) / window
    
    def linear_trend_predict(data, window=10):
        """선형 트렌드 기반 예측"""
        if len(data) < 2:
            return data[-1] if data else 22.5
        
        recent_data = data[-window:] if len(data) >= window else data
        n = len(recent_data)
        
        # 선형 회귀 계산
        x_sum = sum(range(n))
        y_sum = sum(recent_data)
        xy_sum = sum(i * y for i, y in enumerate(recent_data))
        x2_sum = sum(i * i for i in range(n))
        
        if n * x2_sum - x_sum * x_sum == 0:
            return recent_data[-1]
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        intercept = (y_sum - slope * x_sum) / n
        
        # 다음 값 예측
        next_x = n
        prediction = slope * next_x + intercept
        return max(1, min(45, prediction))
    
    def weighted_average_predict(data, window=7):
        """가중평균 기반 예측 (최근일수록 높은 가중치)"""
        if len(data) < 2:
            return data[-1] if data else 22.5
        
        recent_data = data[-window:] if len(data) >= window else data
        weights = [i + 1 for i in range(len(recent_data))]
        
        weighted_sum = sum(val * weight for val, weight in zip(recent_data, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum
    
    def pattern_based_predict(data, window=8):
        """패턴 기반 예측"""
        if len(data) < 3:
            return data[-1] if data else 22.5
        
        recent_data = data[-window:] if len(data) >= window else data
        
        # 차분 계산 (연속된 값들의 차이)
        diffs = [recent_data[i+1] - recent_data[i] for i in range(len(recent_data)-1)]
        
        if not diffs:
            return recent_data[-1]
        
        # 최근 차분의 평균을 다음 예측에 적용
        avg_diff = sum(diffs[-3:]) / len(diffs[-3:]) if len(diffs) >= 3 else sum(diffs) / len(diffs)
        prediction = recent_data[-1] + avg_diff
        
        return max(1, min(45, prediction))
    
    # 각 모델별 예측 수행
    models = {
        'moving_avg': moving_average_predict,
        'linear_trend': linear_trend_predict,
        'weighted_avg': weighted_average_predict,
        'pattern_based': pattern_based_predict
    }
    
    # 마지막 10회를 테스트 데이터로 사용
    test_size = 10
    train_data = {}
    test_data = {}
    
    for pos in position_data:
        train_data[pos] = position_data[pos][:-test_size]
        test_data[pos] = position_data[pos][-test_size:]
    
    # 각 모델의 정확도 평가
    model_scores = {model_name: {pos: [] for pos in position_data} for model_name in models}
    
    print(f"      📊 모델 정확도 평가 (최근 {test_size}회 테스트):")
    
    for model_name, model_func in models.items():
        total_mae = 0  # Mean Absolute Error
        total_predictions = 0
        
        for pos in position_data:
            pos_mae = 0
            
            # 각 테스트 포인트에 대해 예측 수행
            for i in range(test_size):
                # 훈련 데이터 + 이전 테스트 데이터로 예측
                current_train = train_data[pos] + test_data[pos][:i]
                if len(current_train) > 0:
                    prediction = model_func(current_train)
                    actual = test_data[pos][i]
                    error = abs(prediction - actual)
                    pos_mae += error
                    model_scores[model_name][pos].append(error)
            
            pos_mae /= test_size
            total_mae += pos_mae
            total_predictions += 1
        
        avg_mae = total_mae / total_predictions
        print(f"         {model_name}: 평균 오차 {avg_mae:.2f}")
    
    # 가장 정확한 모델 선택
    best_model_name = min(models.keys(), 
                         key=lambda m: sum(sum(model_scores[m][pos]) for pos in position_data))
    best_model = models[best_model_name]
    
    print(f"         ✅ 최적 모델: {best_model_name}")
    
    # 최적 모델로 다음 회차 예측 (TOP 3)
    print(f"\n      🎯 {best_model_name} 모델 기반 TOP 3 예측:")
    
    ml_predictions = []
    
    for prediction_num in range(1, 4):
        predicted_positions = {}
        
        for pos in ['aa', 'bb', 'cc', 'dd', 'ee', 'ff']:
            # 약간의 랜덤성 추가 (예측의 다양성을 위해)
            base_prediction = best_model(position_data[pos])
            
            # 각 예측마다 약간씩 다른 변형 적용
            if prediction_num == 1:
                # 기본 예측
                final_prediction = base_prediction
            elif prediction_num == 2:
                # 약간 상향 조정
                final_prediction = base_prediction + random.uniform(-1, 2)
            else:
                # 약간 하향 조정
                final_prediction = base_prediction + random.uniform(-2, 1)
            
            # 범위 제한 및 정수화
            final_prediction = max(1, min(45, round(final_prediction)))
            predicted_positions[pos] = final_prediction
        
        # 중복 제거 및 정렬
        predicted_numbers = list(predicted_positions.values())
        
        # 중복이 있으면 조정
        while len(set(predicted_numbers)) < 6:
            for i, num in enumerate(predicted_numbers):
                if predicted_numbers.count(num) > 1:
                    # 중복된 숫자를 인근 값으로 조정
                    adjustment = random.choice([-2, -1, 1, 2])
                    new_num = max(1, min(45, num + adjustment))
                    if new_num not in predicted_numbers:
                        predicted_numbers[i] = new_num
                        break
        
        # 최종 정렬
        final_set = sorted(list(set(predicted_numbers))[:6])
        
        # 6개가 안 되면 추가
        while len(final_set) < 6:
            candidate = random.randint(1, 45)
            if candidate not in final_set:
                final_set.append(candidate)
        
        final_set = sorted(final_set[:6])
        ml_predictions.append(final_set)
        
        print(f"         TOP {prediction_num}: {final_set}")
        print(f"           위치별: aa={predicted_positions['aa']}, bb={predicted_positions['bb']}, cc={predicted_positions['cc']}")
        print(f"                  dd={predicted_positions['dd']}, ee={predicted_positions['ee']}, ff={predicted_positions['ff']}")
    
    # 위치별 예측 통계
    print(f"\n      📈 위치별 예측 분석:")
    for pos in ['aa', 'bb', 'cc', 'dd', 'ee', 'ff']:
        recent_values = position_data[pos][-5:]
        predicted_value = best_model(position_data[pos])
        avg_value = sum(position_data[pos]) / len(position_data[pos])
        
        print(f"         {pos}: 예측값 {predicted_value:.1f} (최근5회: {recent_values}, 전체평균: {avg_value:.1f})")
    
    # 모델별 상세 성능
    print(f"\n      📊 모델별 상세 성능:")
    for model_name in models:
        position_errors = []
        for pos in position_data:
            pos_error = sum(model_scores[model_name][pos]) / len(model_scores[model_name][pos])
            position_errors.append(pos_error)
        
        avg_error = sum(position_errors) / len(position_errors)
        min_error = min(position_errors)
        max_error = max(position_errors)
        
        print(f"         {model_name}: 평균 {avg_error:.2f}, 최소 {min_error:.2f}, 최대 {max_error:.2f}")
    
    # 예측 신뢰도 분석
    print(f"\n      🎯 예측 신뢰도 분석:")
    
    # 각 위치별 변동성 계산
    position_volatility = {}
    for pos in position_data:
        values = position_data[pos]
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        volatility = variance ** 0.5
        position_volatility[pos] = volatility
    
    avg_volatility = sum(position_volatility.values()) / len(position_volatility)
    
    print(f"         평균 변동성: {avg_volatility:.2f}")
    print(f"         위치별 변동성: {', '.join([f'{pos}:{vol:.1f}' for pos, vol in position_volatility.items()])}")
    
    # 최종 추천
    best_prediction = ml_predictions[0]  # TOP 1 추천
    confidence_score = max(0, 100 - (avg_volatility * 10))  # 변동성 기반 신뢰도
    
    print(f"         최종 추천: {best_prediction}")
    print(f"         신뢰도: {confidence_score:.1f}%")
    
    # 방법 11: 궁극의 간격 패턴 분석 (10회 반복)
    print("\n   🏆 방법 11: 궁극의 간격 패턴 분석 (10회 반복)")
    ultimate_prediction = predict_ultimate_analysis(handler, all_data, latest_round)
    
    print(f"\n   ⚠️  주의: 이는 통계적 분석일 뿐이며, 실제 당첨을 보장하지 않습니다.")
    print(f"      로또는 완전한 확률 게임이므로 참고용으로만 활용하세요.")

    #jyc
    excluded_nums = list(set(excluded_nums))
    excluded_nums.sort()
    print(f"**예상 제외번호 : {excluded_nums}")

    nums = list(range(1,46))
    remain_nums = list(set(nums) - set(excluded_nums))
    remain_nums.sort()
    print(f"**예상 번호 : {remain_nums}")
    
    # 새로운 규칙 기반 10세트 생성
    print(f"\n   🎯 규칙 기반 10세트 생성:")
    generate_rule_based_sets(handler, excluded_nums, remain_nums, all_data, latest_round)


def generate_rule_based_sets(handler, excluded_nums, remain_nums, all_data, latest_round):
    """주어진 규칙에 따라 10개의 로또 세트를 생성합니다."""
    
    import random
    
    # 최근 마지막 추첨 결과 가져오기
    latest_draw = None
    for draw in reversed(all_data):
        if draw.count == latest_round:
            latest_draw = draw
            break
    
    if not latest_draw:
        print("      ❌ 최근 추첨 결과를 찾을 수 없습니다.")
        return
    
    latest_numbers = latest_draw.numbers
    print(f"      📊 최근 마지막 추첨결과 ({latest_round}회): {sorted(latest_numbers)}")
    
    # 구간별로 excluded_nums와 remain_nums 분류
    excluded_ranges = {
        '1-9': [n for n in excluded_nums if 1 <= n <= 9],
        '10-19': [n for n in excluded_nums if 10 <= n <= 19],
        '20-29': [n for n in excluded_nums if 20 <= n <= 29],
        '30-39': [n for n in excluded_nums if 30 <= n <= 39]
    }
    
    remain_ranges = {
        '1-9': [n for n in remain_nums if 1 <= n <= 9],
        '40-45': [n for n in remain_nums if 40 <= n <= 45]
    }
    
    print(f"      📈 구간별 분석:")
    print(f"         excluded_nums 1-9: {excluded_ranges['1-9']}")
    print(f"         excluded_nums 10-19: {excluded_ranges['10-19']}")
    print(f"         excluded_nums 20-29: {excluded_ranges['20-29']}")
    print(f"         excluded_nums 30-39: {excluded_ranges['30-39']}")
    print(f"         remain_nums 1-9: {remain_ranges['1-9']}")
    print(f"         remain_nums 40-45: {remain_ranges['40-45']}")
    
    # 각 구간별 선택 로직 함수
    def select_from_range_1_9_excluded(candidates, latest_numbers):
        """excluded_nums 1-9 구간에서 선택"""
        if not candidates:
            return None
        
        # 최근 추첨에서 1-9 구간 찾기
        recent_1_9 = [n for n in latest_numbers if 1 <= n <= 9]
        
        if recent_1_9:
            recent_num = recent_1_9[0]  # 첫 번째 발견된 수 사용
            if recent_num < 5:
                # 5 이상에서 선택
                valid_candidates = [n for n in candidates if n >= 5]
            else:
                # 5 이하에서 선택
                valid_candidates = [n for n in candidates if n <= 5]
            
            return random.choice(valid_candidates) if valid_candidates else random.choice(candidates)
        else:
            return random.choice(candidates)
    
    def select_from_range_10_19_excluded(candidates, latest_numbers):
        """excluded_nums 10-19 구간에서 선택"""
        if not candidates:
            return None
        
        # 최근 추첨에서 10-19 구간 찾기
        recent_10_19 = [n for n in latest_numbers if 10 <= n <= 19]
        
        if recent_10_19:
            recent_num = recent_10_19[0]
            if recent_num < 15:
                # 15 이상에서 선택
                valid_candidates = [n for n in candidates if n >= 15]
            else:
                # 15 이하에서 선택
                valid_candidates = [n for n in candidates if n <= 15]
            
            return random.choice(valid_candidates) if valid_candidates else random.choice(candidates)
        else:
            return random.choice(candidates)
    
    def select_from_range_20_29_excluded(candidates, latest_numbers):
        """excluded_nums 20-29 구간에서 선택"""
        if not candidates:
            return None
        
        # 최근 추첨에서 20-29 구간 찾기 (실제로는 21-29 확인)
        recent_21_29 = [n for n in latest_numbers if 21 <= n <= 29]
        
        if recent_21_29:
            recent_num = recent_21_29[0]
            if recent_num < 25:
                # 25 이상에서 선택
                valid_candidates = [n for n in candidates if n >= 25]
            else:
                # 25 이하에서 선택
                valid_candidates = [n for n in candidates if n <= 25]
            
            return random.choice(valid_candidates) if valid_candidates else random.choice(candidates)
        else:
            return random.choice(candidates)
    
    def select_from_range_30_39_excluded(candidates, latest_numbers):
        """excluded_nums 30-39 구간에서 선택"""
        if not candidates:
            return None
        
        # 최근 추첨에서 30-39 구간 찾기 (실제로는 31-39 확인)
        recent_31_39 = [n for n in latest_numbers if 31 <= n <= 39]
        
        if recent_31_39:
            recent_num = recent_31_39[0]
            if recent_num < 35:
                # 35 이상에서 선택 (규칙에서 25이상이라 했지만 35이상이 맞는 것 같음)
                valid_candidates = [n for n in candidates if n >= 35]
            else:
                # 35 이하에서 선택
                valid_candidates = [n for n in candidates if n <= 35]
            
            return random.choice(valid_candidates) if valid_candidates else random.choice(candidates)
        else:
            return random.choice(candidates)
    
    def select_from_range_1_9_remain(candidates, latest_numbers):
        """remain_nums 1-9 구간에서 선택"""
        if not candidates:
            return None
        
        # 최근 추첨에서 1-9 구간 찾기
        recent_1_9 = [n for n in latest_numbers if 1 <= n <= 9]
        
        if recent_1_9:
            recent_num = recent_1_9[0]
            if recent_num < 5:
                # 5 이상에서 선택
                valid_candidates = [n for n in candidates if n >= 5]
            else:
                # 5 이하에서 선택
                valid_candidates = [n for n in candidates if n <= 5]
            
            return random.choice(valid_candidates) if valid_candidates else random.choice(candidates)
        else:
            return random.choice(candidates)
    
    def select_from_range_40_45_remain(candidates, latest_numbers):
        """remain_nums 40-45 구간에서 선택"""
        if not candidates:
            return None
        
        # 최근 추첨에서 40-45 구간 찾기
        recent_40_45 = [n for n in latest_numbers if 40 <= n <= 45]
        
        if recent_40_45:
            recent_num = recent_40_45[0]
            if recent_num < 43:
                # 43 이상에서 선택
                valid_candidates = [n for n in candidates if n >= 43]
            else:
                # 43 이하에서 선택
                valid_candidates = [n for n in candidates if n <= 43]
            
            return random.choice(valid_candidates) if valid_candidates else random.choice(candidates)
        else:
            # 40-45 구간이 없으면 43 이상에서 선택
            valid_candidates = [n for n in candidates if n >= 43]
            return random.choice(valid_candidates) if valid_candidates else random.choice(candidates)
    
    # 10개 세트 생성
    generated_sets = []
    
    print(f"\n      🎲 규칙 기반 10세트 생성:")
    
    for set_num in range(1, 11):
        current_set = []
        used_numbers = set()
        
        # 1. excluded_nums 1-9에서 1개 선택
        selected = select_from_range_1_9_excluded(excluded_ranges['1-9'], latest_numbers)
        if selected and selected not in used_numbers:
            current_set.append(selected)
            used_numbers.add(selected)
        
        # 2. excluded_nums 10-19에서 1개 선택
        selected = select_from_range_10_19_excluded(excluded_ranges['10-19'], latest_numbers)
        if selected and selected not in used_numbers:
            current_set.append(selected)
            used_numbers.add(selected)
        
        # 3. excluded_nums 20-29에서 1개 선택
        selected = select_from_range_20_29_excluded(excluded_ranges['20-29'], latest_numbers)
        if selected and selected not in used_numbers:
            current_set.append(selected)
            used_numbers.add(selected)
        
        # 4. excluded_nums 30-39에서 1개 선택
        selected = select_from_range_30_39_excluded(excluded_ranges['30-39'], latest_numbers)
        if selected and selected not in used_numbers:
            current_set.append(selected)
            used_numbers.add(selected)
        
        # 5. remain_nums 1-9에서 1개 선택
        selected = select_from_range_1_9_remain(remain_ranges['1-9'], latest_numbers)
        if selected and selected not in used_numbers:
            current_set.append(selected)
            used_numbers.add(selected)
        
        # 6. remain_nums 40-45에서 1개 선택
        selected = select_from_range_40_45_remain(remain_ranges['40-45'], latest_numbers)
        if selected and selected not in used_numbers:
            current_set.append(selected)
            used_numbers.add(selected)
        
        # 6개가 안 되면 나머지 번호로 채우기
        all_available = excluded_nums + remain_nums
        while len(current_set) < 6:
            remaining_candidates = [n for n in all_available if n not in used_numbers]
            if remaining_candidates:
                selected = random.choice(remaining_candidates)
                current_set.append(selected)
                used_numbers.add(selected)
            else:
                break
        
        # 정렬하여 최종 세트 완성
        final_set = sorted(current_set[:6])
        generated_sets.append(final_set)
        
        # 세트 정보 출력
        odd_count = sum(1 for n in final_set if n % 2 == 1)
        total_sum = sum(final_set)
        
        print(f"         세트 {set_num:2d}: {final_set} (홀수:{odd_count}개, 합계:{total_sum})")
    
    # 생성된 세트들의 통계 분석
    print(f"\n      📊 생성된 10세트 통계 분석:")
    
    # 중복 체크
    unique_sets = []
    for i, set1 in enumerate(generated_sets):
        is_duplicate = False
        for j, set2 in enumerate(generated_sets):
            if i != j and set1 == set2:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_sets.append(set1)
    
    print(f"         총 생성된 세트: {len(generated_sets)}개")
    print(f"         중복 제거 후: {len(unique_sets)}개")
    
    # 구간별 선택 통계
    range_stats = {
        '1-9': {'excluded': 0, 'remain': 0},
        '10-19': {'excluded': 0, 'remain': 0},
        '20-29': {'excluded': 0, 'remain': 0},
        '30-39': {'excluded': 0, 'remain': 0},
        '40-45': {'excluded': 0, 'remain': 0}
    }
    
    for final_set in generated_sets:
        for num in final_set:
            if 1 <= num <= 9:
                if num in excluded_nums:
                    range_stats['1-9']['excluded'] += 1
                else:
                    range_stats['1-9']['remain'] += 1
            elif 10 <= num <= 19:
                if num in excluded_nums:
                    range_stats['10-19']['excluded'] += 1
                else:
                    range_stats['10-19']['remain'] += 1
            elif 20 <= num <= 29:
                if num in excluded_nums:
                    range_stats['20-29']['excluded'] += 1
                else:
                    range_stats['20-29']['remain'] += 1
            elif 30 <= num <= 39:
                if num in excluded_nums:
                    range_stats['30-39']['excluded'] += 1
                else:
                    range_stats['30-39']['remain'] += 1
            elif 40 <= num <= 45:
                if num in excluded_nums:
                    range_stats['40-45']['excluded'] += 1
                else:
                    range_stats['40-45']['remain'] += 1
    
    print(f"\n      📈 구간별 선택 통계:")
    for range_name, stats in range_stats.items():
        total = stats['excluded'] + stats['remain']
        if total > 0:
            print(f"         {range_name}: excluded {stats['excluded']}개, remain {stats['remain']}개 (총 {total}개)")
    
    # 홀짝 및 합계 분포
    odd_counts = [sum(1 for n in s if n % 2 == 1) for s in generated_sets]
    total_sums = [sum(s) for s in generated_sets]
    
    print(f"\n      🎯 패턴 분석:")
    print(f"         홀수 개수 분포: {sorted(odd_counts)}")
    print(f"         평균 홀수 개수: {sum(odd_counts)/len(odd_counts):.1f}개")
    print(f"         합계 범위: {min(total_sums)} ~ {max(total_sums)}")
    print(f"         평균 합계: {sum(total_sums)/len(total_sums):.1f}")
    
    # 최종 추천 순위
    print(f"\n      🌟 추천 순위 (홀짝 균형 및 합계 기준):")
    
    set_scores = []
    for i, final_set in enumerate(generated_sets):
        score = 0
        
        # 홀짝 균형 점수 (3:3이 최고)
        odd_count = sum(1 for n in final_set if n % 2 == 1)
        balance_score = 10 - abs(odd_count - 3) * 2
        
        # 합계 점수 (120-140 범위가 최적)
        total_sum = sum(final_set)
        if 120 <= total_sum <= 140:
            sum_score = 10
        else:
            sum_score = max(0, 10 - abs(total_sum - 130) / 5)
        
        # 구간 다양성 점수 (각 구간에서 고르게 선택되었는지)
        ranges_covered = 0
        if any(1 <= n <= 9 for n in final_set):
            ranges_covered += 1
        if any(10 <= n <= 19 for n in final_set):
            ranges_covered += 1
        if any(20 <= n <= 29 for n in final_set):
            ranges_covered += 1
        if any(30 <= n <= 39 for n in final_set):
            ranges_covered += 1
        if any(40 <= n <= 45 for n in final_set):
            ranges_covered += 1
        
        diversity_score = ranges_covered * 2
        
        total_score = balance_score + sum_score + diversity_score
        set_scores.append((i + 1, total_score, final_set))
    
    # 점수 기준으로 정렬
    set_scores.sort(key=lambda x: x[1], reverse=True)
    
    for rank, (set_num, score, final_set) in enumerate(set_scores, 1):
        star = "⭐" if rank <= 3 else "  "
        odd_count = sum(1 for n in final_set if n % 2 == 1)
        total_sum = sum(final_set)
        print(f"         {star} {rank:2d}위. 세트 {set_num:2d}: {final_set} (점수:{score:.1f}, 홀수:{odd_count}개, 합계:{total_sum})")
    
    print(f"\n      💡 상위 3개 세트를 우선 추천합니다!")
    
    return generated_sets


if __name__ == "__main__":
    main()
