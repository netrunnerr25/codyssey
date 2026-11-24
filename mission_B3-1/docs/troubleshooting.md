# 트러블슈팅 보고서

실제 AWS 인스턴스에서 의도적으로 Nginx를 중지해 재현한 장애입니다.

| 항목 | 실제 관찰/조치 |
|---|---|
| 증상 | 정상 응답하던 `http://3.39.242.203/health`에서 접속 실패 |
| 가설 | 웹 서버 프로세스가 중지되어 80 포트에서 수신하지 않음 |
| 검증 | SSH 유지 상태에서 `systemctl is-active nginx`, `ss -lntp`, `journalctl -u nginx` 확인 |
| 조치 | `sudo systemctl start nginx`, `sudo nginx -t` |
| 결과 | 복구 후 외부 GET /health HTTP 200, OK |
| 재발방지 | systemctl enable 설정, 배포 후 로컬/외부 헬스체크, 장애 재현 코드는 finally에서 서비스 복구 |

실행 시각(UTC): 2026-11-24T08:28:21.380243+00:00

가공 전 실제 진단 출력과 전후 HTTP 응답: [troubleshooting.json](evidence/troubleshooting.json).

## 실제 배포 중 발견한 IAM 권한 누락

| 항목 | 관찰 및 조치 |
|---|---|
| 증상 | EC2 생성 후 instance_status_ok waiter가 UnauthorizedOperation으로 실패 |
| 가설 | 인스턴스 생성 권한과 별도로 waiter의 상태 조회 권한이 필요 |
| 검증 | 실제 오류의 ec2:DescribeInstanceStatus 거부 사유와 IAM 정책의 액션 목록 비교 |
| 조치 | 서울 리전 읽기 권한에 ec2:DescribeInstanceStatus만 추가. 첫 실행 리소스 정리 후 재실행 |
| 결과 | 재실행에서 상태 검사 완료, SSH/내부 HTTP/외부 HTTP 검증 성공 |
| 재발방지 | boto3 waiter가 사용하는 조회 API와 IAM 정책을 비교하는 회귀 테스트 추가. 총 11개 테스트 통과 |

근거: [관찰한 오류 요약](evidence/first-attempt-incident.json), [첫 실행 정리 재조회](evidence/first-attempt-cleanup.json), [재실행 검증](evidence/verification.json).
