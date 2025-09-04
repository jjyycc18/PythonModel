"""
로또 분석기 실행 예제

이 스크립트는 LotteryDataHandler를 사용하여 로또 데이터를 분석하는 방법을 보여줍니다.
"""

import random
from collections import Counter
from lottery_data_handler import LotteryDataHandler

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
    
    print(f"\n   ⚠️  주의: 이는 통계적 분석일 뿐이며, 실제 당첨을 보장하지 않습니다.")
    print(f"      로또는 완전한 확률 게임이므로 참고용으로만 활용하세요.")


if __name__ == "__main__":
    main()
