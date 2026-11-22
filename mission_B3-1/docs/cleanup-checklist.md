# 리소스 정리 체크리스트

상태: **이 작업에서는 AWS 리소스를 아직 생성하지 않았습니다.**
아래는 실행 후 실제 재조회로 확인할 항목입니다. 삭제 완료 증빙은 아직 없습니다.
`lab.py cleanup`이 성공하면 이 문서를 실제 확인 결과와 시각으로 교체합니다.

- [ ] EC2: 종료 요청 후 terminated waiter 완료, 실행 중 인스턴스 0개
- [ ] EBS: DeleteOnTermination + 실습 태그 볼륨 삭제 및 재조회 0개
- [ ] Elastic IP: 이 자동화는 생성하지 않음, 실습 태그 주소 조회 0개
- [ ] Security Group: 인스턴스 ENI 삭제 후 실습 SG 삭제
- [ ] Route Table: 서브넷 연결 해제 후 사용자 정의 테이블 삭제
- [ ] Subnet: 삭제 후 재조회 0개
- [ ] Internet Gateway: VPC에서 분리 후 삭제
- [ ] VPC: 의존 리소스 정리 후 삭제
- [ ] Key Pair: AWS 공개키 삭제, 로컬 개인키는 .local에서 안전하게 보관 후 수동 삭제
- [ ] NAT Gateway, ELB/ALB, RDS: 자동화에서 생성하지 않는 서비스임을 확인
- [ ] Billing Dashboard: 계정 소유자가 사용량/크레딧과 지연 반영 내역 확인

삭제 범위는 `Project=mission_B3-1` 및 고유 `LabRun` 태그가 모두 일치하는 리소스입니다.
기존 계정의 다른 리소스는 이 체크리스트의 삭제 대상이 아닙니다.
정리 실패 시 .local/state.json을 지우지 말고 동일 프로필로 cleanup을 다시 실행합니다.
실제 근거 파일: `docs/evidence/cleanup.json` (성공/잔존 조회 결과 포함).

EC2를 중지만 해서는 EBS/IPv4 관련 비용까지 정리되었다고 볼 수 없습니다.
실습 종료 후 종료(terminate), 볼륨 삭제, 네트워크 정리를 완료합니다.
