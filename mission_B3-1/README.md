# mission_B3-1 · 클라우드 웹 서비스 배포

AWS 서울 리전(ap-northeast-2)에 독립 VPC, Public Subnet, Internet Gateway,
Route Table, Security Group, EC2 한 대를 구성하고 기존 `mission_B1-1` 웹사이트를 Nginx로 배포합니다.

**현재 상태: 실제 AWS 배포·외부 접속·장애 복구·실습 리소스 삭제 확인 완료.**
서울 리전에서 전용 IAM 사용자 `mission-b3`로 실행했습니다. 기존 계정은 유료 플랜으로 전환했으며,
계정 소유자가 확인한 유효 크레딧을 활용하는 실습입니다. 무료 계정 플랜으로 실행한 것은 아닙니다.
최종 크레딧 적용/청구액은 Billing의 지연 반영 내역에서 별도로 확인해야 합니다.
과제의 “프리 티어 범위” 조건을 무료 계정 플랜 가입으로 엄격히 해석하는 교육 과정이라면 이 계정 조건을 담당자에게 확인해야 합니다.

## 외부 접속 증빙

<!-- live-result:start -->
검증 방식: **B — GET /health**

URL: `http://3.39.242.203/health`

검증 시각(UTC): `2026-11-24T08:28:16.261110+00:00`

HTTP **200**, 응답 `OK` 확인. [실제 브라우저 캡처](docs/evidence/external-health.png), [검증 로그](docs/evidence/verification.json).

실습 종료 후 cleanup을 실행하면 해당 URL은 더 이상 서비스하지 않습니다.
<!-- live-result:end -->

## 제출 파일

| 요구 결과물 | 경로 | 현황 |
|---|---|---|
| 아키텍처 PNG | [docs/architecture.png](docs/architecture.png) | 실제 배포 구성 반영 완료 |
| 외부 접속 URL·스크린샷 | 위 증빙 영역, docs/evidence/external-health.png | 실제 HTTP 200 확인 및 캡처 완료 |
| 트러블슈팅 보고서 | [docs/troubleshooting.md](docs/troubleshooting.md) | 실제 장애 재현/복구 기록 완료 |
| 리소스 정리 체크리스트 | [docs/cleanup-checklist.md](docs/cleanup-checklist.md) | 이번 실습 잔존 리소스 0개 확인 |
| IAM 권한·설정 | [iam/README.md](iam/README.md), [정책](iam/mission-policy.json) | 전용 IAM 사용자·제한 정책 적용 완료 |

## 실행

Python 3.10+, OpenSSH(ssh, scp, ssh-keygen), 인터넷 연결, 전용 IAM 프로필이 필요합니다.
저장소 전체를 내려받아 기존 mission_B1-1 폴더와 함께 사용합니다.

```bash
cd mission_B3-1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
# Linux라면 python -m playwright install --with-deps chromium
```

AWS IAM 설정은 [전용 안내](iam/README.md)를 따릅니다. AWS CLI는 로그인 설정에 사용할 수 있으며,
배포 스크립트 자체는 boto3로 실행합니다. 프로필명 예시는 `mission-b3`입니다.
인스턴스에는 AWS Role/자격 증명을 넣지 않습니다.

AWS Billing/Free Tier에서 이 계정의 적용 기간, t3.micro·8GiB gp3·퍼블릭 IPv4의 무료 혜택 또는 크레딧을
먼저 확인합니다. 계정 생성 시점과 잔여 혜택에 따라 달라지며 무료 실행을 보장하지 않습니다.
조건이 맞지 않으면 실행을 보류합니다. NAT Gateway, ALB, RDS, Elastic IP를 생성하지 않습니다.

다음 한 명령은 생성 → SSH/내부·외부 확인 → 실제 브라우저 캡처 → 의도적 장애 재현/복구 → 삭제를 수행합니다.
SSH 주소는 이 명령을 실행하는 PC의 공인 IPv4 **한 개(/32)**로 바꿉니다.

```bash
python scripts/run_lab.py --profile mission-b3 --ssh-cidr YOUR_PUBLIC_IPV4/32 --free-tier-checked
```

실패 시에도 finally에서 현재 실행의 정리를 시도합니다. 강제 프로세스 종료/PC 종료 시에는 자동 정리가
실행되지 않을 수 있으므로 상태 파일을 보존하고 아래 cleanup을 직접 실행합니다.

단계별 실행이 필요한 경우:

```bash
python scripts/lab.py --profile mission-b3 deploy --ssh-cidr YOUR_PUBLIC_IPV4/32 --free-tier-checked
python scripts/lab.py --profile mission-b3 verify
python scripts/lab.py --profile mission-b3 troubleshoot
python scripts/lab.py --profile mission-b3 cleanup
```

cleanup은 같은 실습 태그만 삭제하며 재실행할 수 있습니다. 새 실습 전에 기존 정리 결과를 확인하고,
`.local`을 안전한 위치에 보관하거나 제거합니다. Git에는 올리지 않습니다.
스크린샷·검증 로그·교체된 보고서와 체크리스트를 검토하여 커밋합니다.
실행이 전부 성공한 뒤에만 첫 상태 문구와 제출 파일 표를 완료로 갱신합니다.
마지막으로 Billing Dashboard의 잔여 사용 내역을 확인합니다.

## 구성과 보안

- VPC `10.30.0.0/16`, Public Subnet `10.30.1.0/24`, 기본 경로 `0.0.0.0/0 → IGW`.
- Amazon Linux 2023 최신 x86_64 AMI(amazon 소유), t3.micro 1대, 암호화된 gp3 루트 볼륨 8GiB.
- 루트 볼륨과 기본 ENI는 종료 시 삭제. IPv4는 자동 할당, Elastic IP 미사용.
- HTTP 80만 전 세계에 공개. SSH 22는 지정한 운영자 공인 IPv4 /32만 허용. 전체 포트 허용 없음.
- 아웃바운드는 OS 패키지 설치, DNS, 필수 인터넷 curl 검증을 위해 기본 허용.
- IMDSv2 필수, T3 CPU 크레딧 standard로 추가 CPU 크레딧 과금 방지.
- 키는 로컬에서 생성한 Ed25519 공개키만 AWS에 등록. 개인키·상태·known_hosts는 Git 제외.
- Security Group은 네트워크 트래픽을 제어하고, IAM 정책은 AWS API로 리소스를 조작할 권한을 제어.
- EC2에는 IAM instance profile을 부여하지 않음. 실습 운영자만 전용 IAM 권한 사용.

외부 요청: 사용자 → 인터넷 → IGW → Public IP 매핑 → SG 80 허용 → EC2 Nginx.
응답/아웃바운드에는 Subnet과 연결된 Route Table의 IGW 기본 경로가 필요합니다.
SG는 상태 저장 방식이므로 허용된 요청의 응답 트래픽은 자동 추적합니다.
IGW 경로만 있거나 Public IP만 있는 것으로는 외부 접근이 성립하지 않습니다.

## 검증 범위

로컬 검증 명령: `python -m unittest discover -s tests -v`.
총 11개 테스트가 통과했습니다. 입력 안전장치, 잘못된 HTTP 응답 거부, 보안 그룹 검증, 정리 범위,
중복 삭제 및 AWS waiter 조회 권한 누락 방지를 확인합니다.
이 검증은 실제 AWS 실행을 대체하지 않습니다.

실제 실행에서 생성되는 파일은 `docs/evidence/verification.json`, `external-health.png`,
`troubleshooting.json`, `cleanup.json`입니다. 성공하지 않은 단계의 증빙은 만들지 않습니다.
이 기록은 전체 계정의 기존 리소스/비용이 0임을 의미하지 않습니다.

## 근거 문서

- [AWS EC2 프리 티어: 계정 생성 시점별 차이](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)
- [EC2 IAM 정책 예시와 리소스 범위](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ExamplePolicies_EC2.html)
- [퍼블릭 서브넷과 IGW 라우팅](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)

## 실제 실행 근거

- [배포 웹사이트 캡처](docs/evidence/external-website.png)
- [외부 헬스체크 캡처](docs/evidence/external-health.png) 및 [SSH·라우팅·보안 그룹 검증](docs/evidence/verification.json)
- [실제 장애 재현·복구 로그](docs/evidence/troubleshooting.json)
- [최종 리소스 삭제·재조회](docs/evidence/cleanup.json)
- [최초 IAM 상태 조회 권한 누락 사례](docs/evidence/first-attempt-incident.json)와 [첫 실행 정리 결과](docs/evidence/first-attempt-cleanup.json)
- [실습 IAM 정책 적용 기록](docs/evidence/iam-setup.json)

계정의 최초 IAM 사용자를 만들기 위한 준비에만 기존 루트 임시 인증을 사용했습니다.
실제 VPC·EC2 생성, SSH·HTTP 검증, 장애 재현 및 리소스 삭제는 전용 IAM 사용자로 수행했습니다.
루트로 실습 인프라를 운영하지 않았으며, 서버에 AWS 자격 증명을 넣지 않았습니다.
검증 URL은 증빙 수집 뒤 인스턴스를 종료했으므로 현재는 접속되지 않습니다.
