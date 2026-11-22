# 트러블슈팅 보고서

상태: **AWS 인증 준비 전 — 실제 AWS 장애 재현은 미실행**.
이 문서는 실행 계획이며 해결 사례를 완료했다고 주장하지 않습니다.
`python scripts/lab.py --profile mission-b3 troubleshoot` 실행 시 실제 관찰 결과와 로그로 자동 교체합니다.

| 항목 | 재현 및 검증 계획 |
|---|---|
| 증상 | 정상 /health 응답을 먼저 확인한 후 Nginx를 의도적으로 중지하여 외부 HTTP 접속 실패 재현 |
| 가설 | 웹 서버 프로세스가 중지되어 TCP 80에서 수신하지 않음 |
| 검증 | SSH로 systemctl is-active nginx, ss -lntp, journalctl -u nginx 실행. 외부 /health 요청 실패와 비교 |
| 조치 | finally 블록에서 sudo systemctl start nginx, sudo nginx -t 실행 |
| 결과 | 외부 /health가 다시 HTTP 200, OK를 반환하는지 검증하고 실제 로그 저장 |
| 재발방지 | 부팅 시 Nginx 자동 실행, 배포 후 로컬·외부 응답 점검, 재현 중 예외 발생 시 서비스 복구 |

자동화가 저장할 실제 근거: `docs/evidence/troubleshooting.json`.

SSH가 먼저 실패한다면 지정한 /32 주소가 실제 실행 PC의 공인 IPv4인지, 인스턴스가 Public IP를 가졌는지,
Subnet의 기본 경로가 IGW인지 확인합니다. SSH를 0.0.0.0/0으로 확대하여 해결하지 않습니다.
