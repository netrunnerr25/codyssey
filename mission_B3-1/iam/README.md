# 전용 IAM 설정

현재 계정의 IAM 사용자/Role 연결은 아직 하지 않았습니다.
이 저장소에 있는 정책 파일만으로 계정 권한이 자동 변경되지는 않습니다.

## 계정 소유자가 한 번 할 작업

루트가 아닌 기존 IAM 관리 담당자 또는 IAM Identity Center 관리자로 진행합니다.
이미 사용할 수 있는 관리용 IAM 로그인이 없다면 계정 관리 담당자에게 아래 설정을 요청합니다.
실습 운영자에게 AdministratorAccess를 주지 않습니다.

1. IAM → Policies → Create policy → JSON에 [mission-policy.json](mission-policy.json) 내용을 붙여넣고
   `CodysseyMissionB3Seoul` 이름으로 생성합니다.
2. 기존 전용 IAM 사용자 또는 Identity Center 권한 세트/Role에 이 정책을 연결합니다.
   별도 IAM 사용자라면 MFA를 설정하고 실습용 콘솔 로그인을 활성화합니다.
3. 해당 사용자/Role의 다른 직접 연결 정책, 그룹 정책, 권한 세트도 확인하여
   AdministratorAccess, PowerUserAccess, S3/RDS 등 무관한 서비스 권한을 제거합니다.
   이 정책을 추가하는 것만으로 기존의 넓은 Allow 권한이 줄어들지는 않습니다.
4. 로컬에 AWS CLI를 설치한 뒤 프로필을 설정합니다. Identity Center가 있다면 단기 인증을 우선 사용합니다.

```bash
aws configure sso --profile mission-b3
aws sso login --profile mission-b3
aws sts get-caller-identity --profile mission-b3
```

Identity Center가 없는 전용 IAM 사용자라면 AWS CLI용 접근 키를 로컬에서만 설정할 수 있습니다.
장기 키가 필요할 때만 발급하고 종료 후 비활성화/삭제합니다.

```bash
aws configure --profile mission-b3
# 대화형 입력에 자격 증명, 기본 리전 ap-northeast-2 입력
aws sts get-caller-identity --profile mission-b3
```

비밀 키는 채팅, GitHub, .env, 스크린샷에 넣지 않습니다. 이 저장소는 키를 받거나 저장하지 않습니다.
확인한 ARN은 IAM 사용자 또는 assumed-role이어야 하며 `:root`이면 실행하면 안 됩니다.
SSO 조직의 permission boundary/SCP가 생성이나 삭제를 막는다면 관리자에게 필요한 액션을 확인받습니다.

## 정책 범위

`mission-policy.json`은 필요한 EC2/VPC/SG 관련 액션만 열거하고 서울 리전으로 제한합니다.
생성 리소스는 Project 및 LabRun 태그로 추적하고 삭제·정리 작업은 Project 태그로 제한합니다.
RunInstances는 t3.micro만 허용합니다. IAM, S3, RDS, ELB, NAT Gateway, EIP 할당, PassRole 권한은 없습니다.
GetCallerIdentity는 AWS에서 별도 Allow 없이 호출할 수 있는 자기 신원 확인 API입니다.

Describe 계열과 일부 생성/연결 작업은 Resource `*`가 포함되어 있습니다.
특히 최초 VPC/서브넷 생성 전에는 리소스 ARN을 미리 확정할 수 없으며, 이 정책은
서비스/액션/리전 단위의 실습용 범위입니다. 조직 환경의 보편적인 보안 경계로 재사용하지 않습니다.
해당 자격 증명을 EC2 인스턴스 내부에 복사하지 않습니다.

실제 IAM 적용 증빙은 계정에서 정책 연결과 전체 유효 권한을 확인한 뒤 남겨야 합니다.
정책 JSON 자체는 실제 연결 완료의 증빙이 아닙니다.
