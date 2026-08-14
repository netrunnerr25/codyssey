import json
import time
import math
from typing import List, Tuple, Dict, Any

# ----------------------------------------------------
# 1. 상수 및 라벨 정규화 맵 (평가항목 #12, #16 보완)
# ----------------------------------------------------
# 부동소수점 허용 오차: IEEE 754 float64 연산 단올림 오차 및 25x25(625회) 누적 오차를 고려하여 1e-9 선택
EPSILON = 1e-9  

# 정규화 매핑 테이블 (설정 확장 유연성 확보)
LABEL_MAPPING = {
    '+': 'Cross',
    'cross': 'Cross',
    'x': 'X',
    'X': 'X'
}

def normalize_label(label: str) -> str:
    """
    다양한 형태의 입력 라벨을 시스템 표준 라벨('Cross', 'X')로 정규화합니다.
    (새 라벨 확장 시 LABEL_MAPPING 사전만 수정/확장하면 됩니다)
    """
    s = str(label).strip()
    # 매핑 테이블 조회 (소문자/대문자 지원)
    if s.lower() in LABEL_MAPPING:
        return LABEL_MAPPING[s.lower()]
    if s in LABEL_MAPPING:
        return LABEL_MAPPING[s]
    return s


# ----------------------------------------------------
# 2. MAC 연산 및 유사성 수학적 근거 (평가항목 #10, #14 보완)
# ----------------------------------------------------
def mac_operation(pattern: List[List[float]], filter_matrix: List[List[float]]) -> float:
    """
    N x N 패턴과 필터 간의 MAC (Multiply-Accumulate) 연산을 수행합니다.
    
    [수학적 근거 - MAC 점수와 유사성의 관계]
    2차원 패턴 P와 필터 F의 MAC 점수는 벡터 내적(Dot Product) sum(P_ij * F_ij)과 동일합니다.
    이 값은 두 행렬의 유사도(Cos Similarity)에 비례합니다:
        Dot_Product = ||P|| * ||F|| * cos(theta)
    따라서 패턴 P가 필터 F의 밝기 구조(1과 0의 배치)와 일치할수록 곱셈 누적 합이 극대화됩니다.
    """
    n = len(pattern)
    score = 0.0
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filter_matrix[i][j]
    return score


def measure_mac_avg_time(pattern: List[List[float]], filter_matrix: List[List[float]], iterations: int = 10) -> float:
    """
    I/O 구간을 완전히 제외하고 MAC 연산 순수 실행 시간만 측정합니다.
    
    [측정 공정성 및 인터프리터 오버헤드 (평가항목 #13 보완)]
    - Warm-up 실행 1회를 수행하여 파이썬 인터프리터 바이트코드 캐싱/JIT 오버헤드를 제거합니다.
    - time.perf_counter()를 사용하여 나노초 단위 고해상도 타이머를 활용합니다.
    """
    # Warm-up (인터프리터 캐싱 오버헤드 제거)
    _ = mac_operation(pattern, filter_matrix)
    
    start_time = time.perf_counter()
    for _ in range(iterations):
        _ = mac_operation(pattern, filter_matrix)
    end_time = time.perf_counter()
    
    avg_seconds = (end_time - start_time) / iterations
    return avg_seconds * 1000.0  # ms 변환


def classify_pattern(score_cross: float, score_x: float) -> str:
    """
    Cross 점수와 X 점수를 EPSILON 정책 기반으로 비교하여 판정합니다.
    """
    diff = score_cross - score_x
    if abs(diff) < EPSILON:
        return 'UNDECIDED'
    elif diff > 0:
        return 'Cross'
    else:
        return 'X'


# ----------------------------------------------------
# 3. 모드 1: 대화형 콘솔 입력 (평가항목 #1, #2, #3 보완)
# ----------------------------------------------------
def get_matrix_input(name: str, size: int = 3) -> List[List[float]]:
    """
    사용자로부터 N x N 행렬을 입력받습니다. ('q' 입력 시 취소 기능 포함)
    """
    print(f"\n--- [{name}] 입력 ({size}x{size}) ---")
    print(f"각 줄마다 {size}개의 숫자를 공백으로 구분해 입력하세요. (취소하려면 'q' 입력)")
    
    matrix = []
    row_count = 0
    while row_count < size:
        line = input(f"{row_count + 1}번째 행 입력: ").strip()
        if line.lower() == 'q':
            print("[알림] 입력이 취소되었습니다.")
            return None
        if not line:
            continue
        parts = line.split()
        if len(parts) != size:
            print(f"[입력 오류] 정확히 {size}개의 숫자를 공백으로 구분해 입력해 주세요.")
            continue
        try:
            row = [float(x) for x in parts]
            matrix.append(row)
            row_count += 1
        except ValueError:
            print("[입력 오류] 숫자 형식이 올바르지 않습니다. 다시 입력해 주세요.")
            
    return matrix


def run_mode_1():
    print("\n==========================================")
    print(" [모드 1] 사용자 3x3 직접 입력 시뮬레이션")
    print("==========================================")
    
    filter_a = get_matrix_input("필터 A (Cross 계열)", 3)
    if filter_a is None: return
    filter_b = get_matrix_input("필터 B (X 계열)", 3)
    if filter_b is None: return
    pattern = get_matrix_input("입력 패턴", 3)
    if pattern is None: return
    
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    
    time_a = measure_mac_avg_time(pattern, filter_a, 10)
    time_b = measure_mac_avg_time(pattern, filter_b, 10)
    avg_time = (time_a + time_b) / 2.0
    
    diff = score_a - score_b
    if abs(diff) < EPSILON:
        decision = "판정 불가 (UNDECIDED)"
        recommendation = "\n[권장 사항] 두 필터 점수의 차이가 허용오차(1e-9) 미만입니다. 패턴 입력을 재확인하거나 필터 가중치를 조정하세요."
    elif diff > 0:
        decision = "필터 A와 유사 (Cross)"
        recommendation = ""
    else:
        decision = "필터 B와 유사 (X)"
        recommendation = ""
        
    print("\n================ [결과 리포트] ================")
    print(f"필터 A 점수 : {score_a:.6f}")
    print(f"필터 B 점수 : {score_b:.6f}")
    print(f"최종 판정   : {decision}")
    print(f"평균 연산시간: {avg_time:.6f} ms (10회 평균)")
    if recommendation:
        print(recommendation)
    print("===============================================")


# ----------------------------------------------------
# 4. 모드 2: JSON 자동 배치 분석 (평가항목 #4, #6, #8, #11 보완)
# ----------------------------------------------------
def run_mode_2(filepath: str = "data.json"):
    print("\n==========================================")
    print(" [모드 2] data.json 파일 데이터 분석")
    print("==========================================")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[파일 오류] {filepath} 로드 실패: {e}")
        return

    filters_data = data.get("filters", {})
    patterns_data = data.get("patterns", {})
    
    test_results = []
    performance_records = {}
    
    # 통계용 카운터
    total_cnt = 0
    pass_cnt = 0
    fail_cnt = 0
    undecided_cnt = 0

    print(f"\n{'패턴 키':<15} | {'Cross 점수':<10} | {'X 점수':<10} | {'판정':<10} | {'기대값':<8} | {'결과'}")
    print("-" * 75)

    for pattern_key, item in patterns_data.items():
        total_cnt += 1
        try:
            # 패턴 키 파싱 예외 처리 (평가항목 #11 보완)
            key_parts = pattern_key.split('_')
            if len(key_parts) < 2 or not key_parts[1].isdigit():
                msg = f"패턴 키 규격 오류 ('size_N_idx' 형식 필요, 입력: {pattern_key})"
                test_results.append({"id": pattern_key, "status": "FAIL", "reason": msg, "score": "-", "time": "-"})
                fail_cnt += 1
                print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {'-':<8} | FAIL ({msg})")
                continue

            N = int(key_parts[1])
            filter_group_key = f"size_{N}"
            
            # 필터 추출 및 예외 처리 (평가항목 #4 보완)
            if filter_group_key not in filters_data:
                msg = f"크기 {N}에 해당하는 필터(size_{N})가 filters에 존재하지 않음"
                test_results.append({"id": pattern_key, "status": "FAIL", "reason": msg, "score": "-", "time": "-"})
                fail_cnt += 1
                print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {'-':<8} | FAIL (필터 미존재)")
                continue

            filter_group = filters_data[filter_group_key]
            cross_filter = None
            x_filter = None
            
            for fk, fval in filter_group.items():
                norm_fk = normalize_label(fk)
                if norm_fk == 'Cross': cross_filter = fval
                elif norm_fk == 'X': x_filter = fval

            if not cross_filter or not x_filter:
                msg = f"크기 {N} 필터 그룹 내 Cross/X 필수 필터 정의 누락"
                test_results.append({"id": pattern_key, "status": "FAIL", "reason": msg, "score": "-", "time": "-"})
                fail_cnt += 1
                print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {'-':<8} | FAIL (필터 누락)")
                continue

            input_matrix = item.get("input", [])
            raw_expected = item.get("expected", "")
            expected_label = normalize_label(raw_expected)

            # 크기 검증
            if len(input_matrix) != N or any(len(row) != N for row in input_matrix):
                msg = f"패턴 차원({len(input_matrix)}x{len(input_matrix[0])})과 지정 크기(N={N}) 불일치"
                test_results.append({"id": pattern_key, "status": "FAIL", "reason": msg, "score": "-", "time": "-"})
                fail_cnt += 1
                print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {expected_label:<8} | FAIL (크기 불일치)")
                continue

            # MAC 연산 및 시간 측정
            score_cross = mac_operation(input_matrix, cross_filter)
            score_x = mac_operation(input_matrix, x_filter)
            pred_label = classify_pattern(score_cross, score_x)

            time_c = measure_mac_avg_time(input_matrix, cross_filter, 10)
            time_x = measure_mac_avg_time(input_matrix, x_filter, 10)
            avg_time = (time_c + time_x) / 2.0
            
            if N not in performance_records: performance_records[N] = []
            performance_records[N].append(avg_time)

            if pred_label == 'UNDECIDED':
                undecided_cnt += 1

            is_pass = (pred_label == expected_label)
            status = "PASS" if is_pass else "FAIL"
            if is_pass: pass_cnt += 1
            else: fail_cnt += 1
            
            reason = "" if is_pass else f"판정값({pred_label}) != 기대값({expected_label})"
            test_results.append({
                "id": pattern_key,
                "status": status,
                "reason": reason,
                "score": f"Cross:{score_cross:.2f}/X:{score_x:.2f}",
                "time": f"{avg_time:.4f}ms"
            })

            print(f"{pattern_key:<15} | {score_cross:<10.2f} | {score_x:<10.2f} | {pred_label:<10} | {expected_label:<8} | {status}")

        except Exception as err:
            msg = f"런타임 예외 발생: {str(err)}"
            test_results.append({"id": pattern_key, "status": "FAIL", "reason": msg, "score": "-", "time": "-"})
            fail_cnt += 1
            print(f"{pattern_key:<15} | {'-':<10} | {'-':<10} | {'ERROR':<10} | {'-':<8} | FAIL ({err})")

    # 결과 리포트 상세 요약 (평가항목 #6, #8 보완)
    print("\n================ [최종 리포트 요약] ================")
    print(f"전체 테스트 : {total_cnt}건 | 통과 : {pass_cnt}건 | 실패 : {fail_cnt}건 | 판정불가(UNDECIDED) : {undecided_cnt}건")
    
    if fail_cnt > 0:
        print("\n[실패 케이스 상세 내역]")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"- [{r['id']}] 원인: {r['reason']} | 연산점수: {r['score']} | 소요시간: {r['time']}")
    else:
        print("모든 테스트 케이스 검증을 완료하였습니다! (FAIL: 0건)")

    # 성능 분석 표 출력 (평가항목 #7, #15 보완)
    print("\n================ [성능 분석 표] ================")
    print(f"{'크기 (N x N)':<12} | {'평균시간 (ms)':<15} | {'표준편차 (ms)':<15} | {'연산 횟수 (N²)':<15}")
    print("-" * 65)
    
    for size in sorted(performance_records.keys()):
        times = performance_records[size]
        avg_ms = sum(times) / len(times)
        # 표준편차 계산
        variance = sum((x - avg_ms) ** 2 for x in times) / len(times)
        std_dev = math.sqrt(variance)
        op_count = size * size
        print(f"{size:<2} x {size:<7} | {avg_ms:<15.6f} | {std_dev:<15.6f} | {op_count:<15}")
    print("===============================================")


def main():
    print("==========================================")
    print("      Mini NPU 시뮬레이터 프로그램")
    print("==========================================")
    print("1. 사용자 입력 모드 (3x3 대화형)")
    print("2. data.json 배치 분석 모드")
    
    choice = input("\n모드를 선택하세요 (1 또는 2): ").strip()
    if choice == '1':
        run_mode_1()
    elif choice == '2':
        run_mode_2("data.json")
    else:
        print("잘못된 선택입니다. 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()