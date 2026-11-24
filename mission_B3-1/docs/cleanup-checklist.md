# 리소스 정리 체크리스트

검증 시각(UTC): 2026-11-24T08:28:59.050955+00:00

- [x] EC2: 해당 실습 태그의 잔존 리소스 0개
- [x] EBS: 해당 실습 태그의 잔존 리소스 0개
- [x] Elastic IP: 해당 실습 태그의 잔존 리소스 0개
- [x] Internet Gateway: 해당 실습 태그의 잔존 리소스 0개
- [x] VPC: 해당 실습 태그의 잔존 리소스 0개
- [x] Subnet: 해당 실습 태그의 잔존 리소스 0개
- [x] Route Table: 해당 실습 태그의 잔존 리소스 0개
- [x] Security Group: 해당 실습 태그의 잔존 리소스 0개
- [x] Key Pair: 해당 실습 태그의 잔존 리소스 0개

- [x] NAT Gateway, ELB/ALB, RDS: 이 자동화에서 생성하지 않음
- [ ] Billing Dashboard: 계정 소유자가 지연 반영되는 사용 내역/크레딧을 최종 확인

근거: [실제 삭제 API 실행 및 재조회 결과](evidence/cleanup.json). 범위는 Project 및 LabRun 태그가 모두 일치하는 이번 실습 리소스입니다.

- [x] 이번 실행에 발급한 임시 IAM 액세스 키 삭제 및 잔존 키 0개 확인. [IAM 근거](evidence/iam-setup.json)
- [x] 첫 실패 실행과 성공 실행을 포함한 Project 전체 리소스 재조회 0개. [최종 감사](evidence/final-audit.json)
