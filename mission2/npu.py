import json
import time
import sys
from typing import List, Tuple, Dict, Any

# ----------------------------------------------------
# 1. 상수 정의 및 라벨 정규화
# ----------------------------------------------------
EPSILON = 1e-9  # 부동소수점 허용 오차

def normalize_label(label: str) -> str:
    """
    다양한 형태의 라벨('+', 'cross', 'x', 'X' 등)을
    표준 라벨('Cross', 'X')로 정규화합니다.
    """
    s = str(label).strip().lower()
    if s in ['+', 'cross']:
        return 'Cross'
    elif s in ['x']:
        return 'X'
    return str(label)


# ----------------------------------------------------
# 2. MAC 연산 함수 (외부 라이브러리 금지: 순수 반복문)
# ----------------------------------------------------
def mac_operation(pattern: List[List[float]], filter_matrix: List[List[float]]) -> float:
    """
    N x N 패턴과 필터를 2중 반복문으로 위치별 곱셈 후 누적 합을 계산합니다.
    """
    n = len(pattern)
    score = 0.0
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filter_matrix[i][j]
    return score


def measure_mac_avg_time(pattern: List[List[float]], filter_matrix: List[List[float]], iterations: int = 10) -> float:
    """
    I/O 구간을 제외하고 MAC 연산 순수 실행 시간만 10회 측정하여 평균(ms)을 반환합니다.
    """
    start_time = time.perf_counter()
    for _ in range(iterations):
        _ = mac_operation(pattern, filter_matrix)
    end_time = time.perf_counter()
    
    avg_seconds = (end_time - start_time) / iterations
    return avg_seconds * 1000.0  # ms 변환


def classify_pattern(score_cross: float, score_x: float) -> str:
    """
    Cross 점수와 X 점수를 비교하여 판정 결과를 반환합니다.
    """
    diff = score_cross - score_x
    if abs(diff) < EPSILON:
        return 'UNDECIDED'
    elif diff > 0:
        return 'Cross'
    else:
        return 'X'


# ----------------------------------------------------
# 3. 콘솔 입력 및 검증 함수 (모드 1)
# ----------------------------------------------------
def get_matrix_input(name: str, size: int = 3) -> List[List[float]]:
    """
    사용자로부터 size x size 크기의 행렬을 한 줄씩 입력받고 검증합니다.
    """
    print(f"\n--- [{name}] 입력 ({size}x{size}) ---")
    print(f"각 줄마다 {size}개의 숫자를 공백으로 구분하여 입력하세요.")
    
    matrix = []
    row_count = 0
    while row_count < size:
        try:
            line = input(f"{row_count + 1}번째 행 입력: ").strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != size:
                print(f"[입력 오류] 정확히 {size}개의 숫자를 공백으로 구분해 입력해 주세요.")
                continue
            row = [float(x) for x in parts]
            matrix.append(row)
            row_count += 1
        except ValueError:
            print("[입력 오류] 숫자 형식이 올바르지 않습니다. 다시 입력하세요.")
            
    return matrix


def run_mode_1():
    """모드 1: 사용자 3x3 콘솔 입력 모드"""
    print("\n==========================================")
    print("   [모드 1] 사용자 3x3 직접 입력 시뮬레이션")
    print("==========================================")
    
    filter_a = get_matrix_input("필터 A (예: Cross 필터)", 3)
    filter_b = get_matrix_input("필터 B (예: X 필터)", 3)
    pattern = get_matrix_input("입력 패턴", 3)
    
    # MAC 연산 수행
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    
    # 성능 측정 (10회 평균)
    time_a = measure_mac_avg_time(pattern, filter_a, 10)
    time_b = measure_mac_avg_time(pattern, filter_b, 10)
    avg_time = (time_a + time_b) / 2.0
    
    # 판정
    diff = score_a - score_b
    if abs(diff) < EPSILON:
        decision = "판정 불가 (UNDECIDED)"
    elif diff > 0:
        decision = "필터 A와 유사"
    else:
        decision = "필터 B와 유사"
        
    print("\n================ [결과 리포트] ================")
    print(f"필터 A 점수 : {score_a:.4f}")
    print(f"필터 B 점수 : {score_b:.4f}")
    print(f"최종 판정   : {decision}")
    print(f"평균 연산시간: {avg_time:.6f} ms (10회 평균)")
    print("===============================================")


# ----------------------------------------------------
# 4. JSON 로드 및 배치 분석 함수 (모드 2)
# ----------------------------------------------------
def run_mode_2(filepath: str = "data.json"):
    """모드 2: data.json 로드 및 배치 판정/성능 분석 모드"""
    print("\n==========================================")
    print("   [모드 2] data.json 파일 데이터 분석")
    print("==========================================")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[파일 오류] {filepath} 파일을 읽는 중 오류가 발생했습니다: {e}")
        return

    filters_data = data.get("filters", {})
    patterns_data = data.get("patterns", {})
    
    test_results = []
    performance_records = {}  # {size: list_of_avg_times}

    print(f"\n{'패턴 키':<15} | {'Cross 점수':<10} | {'X 점수':<10} | {'판정':<10} | {'기대값':<8} | {'결과'}")
    print("-" * 75)

    for pattern_key, item in patterns_data.items():
        try:
            # 키에서 N 추출 (예: size_5_1 -> N=5)
            key_parts = pattern_key.split('_')
            N = int(key_parts[1])
            filter_group_key = f"size_{N}"
            
            # 필터 추출 및 검증
            if filter_group_key not in filters_data:
                test_results.append({
                    "id": pattern_key,
                    "status": "FAIL",
                    "reason": f"크기 {N}에 해당하는 필터 그룹이 filters에 존재하지 않음"
                })
                print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {'-':<8} | FAIL (필터 미존재)")
                continue

            filter_group = filters_data[filter_group_key]
            
            # 라벨 정규화를 통해 Cross/X 필터 찾기
            cross_filter = None
            x_filter = None
            for fk, fval in filter_group.items():
                norm_fk = normalize_label(fk)
                if norm_fk == 'Cross':
                    cross_filter = fval
                elif norm_fk == 'X':
                    x_filter = fval

            if not cross_filter or not x_filter:
                test_results.append({
                    "id": pattern_key,
                    "status": "FAIL",
                    "reason": f"크기 {N} 필터 그룹 내 Cross 또는 X 필터 정의 누락"
                })
                print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {'-':<8} | FAIL (필터 누락)")
                continue

            input_matrix = item.get("input", [])
            raw_expected = item.get("expected", "")
            expected_label = normalize_label(raw_expected)

            # 크기 검증
            if len(input_matrix) != N or any(len(row) != N for row in input_matrix):
                test_results.append({
                    "id": pattern_key,
                    "status": "FAIL",
                    "reason": f"패턴 크기({len(input_matrix)}x{len(input_matrix[0])})와 정의된 N({N}) 불일치"
                })
                print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {expected_label:<8} | FAIL (크기 불일치)")
                continue

            # MAC 연산 수행
            score_cross = mac_operation(input_matrix, cross_filter)
            score_x = mac_operation(input_matrix, x_filter)
            pred_label = classify_pattern(score_cross, score_x)

            # 성능 측정 (10회 평균)
            time_c = measure_mac_avg_time(input_matrix, cross_filter, 10)
            time_x = measure_mac_avg_time(input_matrix, x_filter, 10)
            avg_time = (time_c + time_x) / 2.0
            
            if N not in performance_records:
                performance_records[N] = []
            performance_records[N].append(avg_time)

            # 검증 (PASS / FAIL)
            is_pass = (pred_label == expected_label)
            status = "PASS" if is_pass else "FAIL"
            
            reason = "" if is_pass else f"판정({pred_label}) != 기대값({expected_label})"
            test_results.append({
                "id": pattern_key,
                "status": status,
                "reason": reason
            })

            print(f"{pattern_key:<15} | {score_cross:<10.2f} | {score_x:<10.2f} | {pred_label:<10} | {expected_label:<8} | {status}")

        except Exception as err:
            test_results.append({
                "id": pattern_key,
                "status": "FAIL",
                "reason": f"예외 발생: {str(err)}"
            })
            print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {'-':<8} | FAIL ({err})")

    # 결과 요약 출력
    total_cnt = len(test_results)
    pass_cnt = sum(1 for r in test_results if r["status"] == "PASS")
    fail_cnt = total_cnt - pass_cnt

    print("\n================ [최종 리포트 요약] ================")
    print(f"전체 테스트 : {total_cnt}건 | 통과 : {pass_cnt}건 | 실패 : {fail_cnt}건")
    
    if fail_cnt > 0:
        print("\n[실패 케이스 목록 및 사유]")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"- {r['id']}: {r['reason']}")
    else:
        print("모든 테스트 케이스를 통과했습니다!")

    # 성능 분석 표 출력
    print("\n================ [성능 분석 표] ================")
    print(f"{'크기 (N x N)':<15} | {'평균 시간 (ms)':<15} | {'연산 횟수 (N²)':<15}")
    print("-" * 52)
    
    for size in sorted(performance_records.keys()):
        times = performance_records[size]
        avg_ms = sum(times) / len(times) if times else 0.0
        op_count = size * size
        print(f"{size:<2} x {size:<10} | {avg_ms:<15.6f} | {op_count:<15}")
    print("===============================================")


# ----------------------------------------------------
# 5. 메인 함수
# ----------------------------------------------------
def main():
    print("==========================================")
    print("      Mini NPU 시뮬레이터 프로그램")
    print("==========================================")
    print("1. 사용자 입력 모드 (3x3 패턴 직접 입력)")
    print("2. data.json 로드 및 분석 모드")
    
    choice = input("\n모드를 선택하세요 (1 또는 2): ").strip()
    if choice == '1':
        run_mode_1()
    elif choice == '2':
        run_mode_2("data.json")
    else:
        print("잘못된 선택입니다. 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()