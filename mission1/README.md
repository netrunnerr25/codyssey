# 미션1. 내 컴퓨터에 개발자용 '작업실' 꾸미기

## 1. 프로젝트 개요

* **미션 목표**: 터미널 기본 조작, Docker(OrbStack/Docker Desktop) 컨테이너화, 데이터 영속성, Git/GitHub 연동을 실습하고 개발 워크스테이션 환경을 검증합니다.
* **GitHub Repository**: [https://github.com/netrunnerr25/codyssey](https://github.com/netrunnerr25/codyssey)

## 2. 실행 환경 및 프로젝트 구조

### 2.1 실행 환경 (Execution Environment)
* **OS**: macOS (Apple Silicon / Intel)
* **Shell**: zsh
* **Docker**: OrbStack / Docker Desktop Engine (Version 29.3.1)
* **Git**: 2.x

### 2.2 디렉토리 구조 및 역할
본 프로젝트는 **독립적인 재현성(Reproducibility)**을 보장하기 위해 표준 디렉토리 구조를 준수합니다.

```text
mission1/
├── README.md               # 과제 수행, 실습 로그 및 트러블슈팅 통합 문서
├── my-project/            # 웹 애플리케이션 프로젝트 루트 (Docker 작업 기준 경로)
│   ├── Dockerfile         # Nginx 기반 커스텀 이미지 빌드 명세서
│   └── src/               # 웹 서버 소스 코드 디렉토리
│       └── index.html     # 메인 HTML 페이지
└── test_dir/              # CLI 파일 조작 및 권한 실습용 디렉토리
    └── newcopy.txt        # 권한 변경 및 이동 실습용 파일
```

> **📌 경로 및 재현성 기준**
> * **호스트(Host) 환경**: 환경에 종속되지 않는 재현성을 위해 `$(pwd)/src`와 같은 **상대 경로 동적 참조** 방식을 채택합니다.
> * **컨테이너(Container) 환경**: Linux 파일 시스템 표준 구조를 따르기 위해 `/usr/share/nginx/html`과 같은 **절대 경로** 명시를 필수 원칙으로 적용합니다.

---

## 3. 수행 항목 체크리스트

* [x] 터미널 기본 조작 및 권한 변경
* [x] Docker 점검 및 컨테이너 실습
* [x] Dockerfile 커스텀 이미지 제작
* [x] 포트 매핑 및 브라우저 접속 검증
* [x] 바인드 마운트 & 볼륨 영속성 검증
* [x] Git/GitHub/VSCode 연동

---

## 4. 수행 로그 및 핵심 개념

### 4.1 터미널 조작 & 파일 권한

#### 💡 절대 경로 vs 상대 경로 차이
* **절대 경로**: 최상위 루트 디렉토리(`/`)를 기준으로 파일이나 디렉터리의 전체 위치를 표기하는 방식입니다. (예: `/Users/admin/Downloads/codyssey/test_dir`)
* **상대 경로**: 현재 작업 위치(`.`)를 기준으로 대상의 위치를 표기하는 방식입니다. (예: `../test_dir`, `./index.html`)

#### 💡 파일 및 디렉토리 권한 체계
* **권한 비트**: `r` (Read=4), `w` (Write=2), `x` (Execute=1)
* **`755` (`rwxr-xr-x`)**: 소유자(읽기/쓰기/실행: 7), 그룹/기타(읽기/실행: 5). 
  * **적용 사유**: 시스템 바이너리나 디렉토리의 무단 변조를 막으면서 실행 권한을 보장하기 위함입니다.
* **`644` (`rw-r--r--`)**: 소유자(읽기/쓰기: 6), 그룹/기타(읽기: 4).
  * **적용 사유**: 일반 문서 및 설정 파일의 불필요한 실행 권한을 제거하여 보안 위험을 최소화합니다.
* **유형별 권한 가이드**:
  * 디렉토리 및 실행 파일: `755`
  * 일반 설정/소스 파일: `644`
  * 보안 민감 파일 (`.env` 등): `600` (`rw-------`)

#### 🧪 터미널 조작 및 권한 실습 로그

```bash
# 1. 현재 위치 확인 및 디렉토리 목록 조회
$ pwd
/Users/admin/Downloads/codyssey

$ ls -la
total 8
drwxr-xr-x@  5 admin  staff  160 Jul 28 16:51 .
drwx------@ 17 admin  staff  544 Jul 28 16:50 ..
drwxr-xr-x@ 10 admin  staff  320 Jul 28 16:49 .git
-rw-r--r--@  1 admin  staff   44 Jul 28 16:05 README.md
drwxr-xr-x@  3 admin  staff   96 Jul 29 11:12 codyssey 

# 2. 파일/디렉토리 생성, 이동, 복사 및 삭제
$ touch test.txt
$ mkdir test_dir
$ cd test_dir
$ pwd
/Users/admin/Downloads/codyssey/test_dir
$ cd ..

$ cp test.txt copy.txt
$ mv copy.txt test_dir/newcopy.txt

$ echo "Hello codessey" > test_dir/newcopy.txt
$ cat test_dir/newcopy.txt
Hello codessey
$ rm test.txt

# 3. 파일 권한 변경 실습 (644 -> 755) 및 보안 영향 검증
$ ls -l test_dir/newcopy.txt
-rw-r--r--@ 1 admin  staff  15 Jul 29 11:47 test_dir/newcopy.txt

$ chmod 755 test_dir/newcopy.txt
$ ls -l test_dir/newcopy.txt
-rwxr-xr-x@ 1 admin  staff  15 Jul 29 11:47 test_dir/newcopy.txt

# 4. 디렉토리 권한 변경 실습 (755 -> 700)
$ ls -ld test_dir
drwxr-xr-x@ 3 admin  staff  96 Jul 29 11:45 test_dir

$ chmod 700 test_dir
$ ls -ld test_dir
drwx------@ 3 admin  staff  96 Jul 29 11:45 test_dir
```

---

### 4.2 Docker 기본 실습

#### 💡 이미지 불변성(Immutability)과 컨테이너
* **Docker Image**: 애플리케이션 실행에 필요한 코드, 런타임, 환경 변수를 패키징한 **읽기 전용(Read-Only)** 템플릿입니다. 이미지는 한번 생성되면 절대 변경되지 않는 **불변성(Immutable)**을 가집니다.
* **Docker Container**: 이미지 템플릿 위에 **읽기/쓰기 가능한 레이어(Writable Layer)**를 얹어 실행되는 프로세스 단위입니다. 컨테이너 내부의 데이터 수정은 이미지 원본에 영향을 주지 않으며, 컨테이너 삭제 시 Writable Layer도 함께 파기됩니다.

#### 💡 컨테이너 종료 vs 유지 및 attach vs exec 개념
* **`docker run -it ... exit`**: 대화형 터미널 메인 프로세스(`bash`)가 종료되면서 컨테이너도 함께 정지(Exited)됩니다.
* **`docker run -d` & `docker exec`**: 백그라운드로 실행 중인 컨테이너에 `exec`로 들어가 진입한 경우, `exit`으로 빠져나와도 메인 프로세스가 살아있으므로 **실행(Up) 상태**를 유지합니다.
* **`attach` vs `exec`**: `attach`는 실행 중인 컨테이너의 표준 입출력 스트림(메인 프로세스)에 직접 연결되고, `exec`는 실행 중인 컨테이너 내부에 새로운 독립 프로세스를 추가 실행합니다.

#### 🧪 Docker 데몬 점검 및 컨테이너 실행 로그

```bash
# 1. Docker 데몬 상태 및 버전 확인
$ docker --version
Docker version 29.3.1, build c2be9cc

$ docker info
Client:
Version:    29.3.1
Context:    desktop-linux
Server Version: 29.3.1
Storage Driver: overlayfs
Logging Driver: json-file
Cgroup Version: 2

# 2. hello-world 컨테이너 실행 및 이미지 Pull 증거
$ docker run hello-world
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
Hello from Docker!
This message shows that your installation appears to be working correctly.

# 3. ubuntu 대화형 컨테이너 실습
$ docker run -it ubuntu bash
root@a1b2c3d4e5f6:/# cat /etc/issue
Ubuntu 26.04 LTS \n \l
root@a1b2c3d4e5f6:/# exit

# 4. 전체 컨테이너 목록(docker ps -a) 및 이미지 목록(docker images) 출력
$ docker ps -a
CONTAINER ID   IMAGE          COMMAND                  CREATED         STATUS                     PORTS     NAMES
a1b2c3d4e5f6   ubuntu         "bash"                   2 minutes ago   Exited (0) 1 minute ago              suspicious_einstein
9e8d7c6b5a4f   hello-world    "/hello"                 5 minutes ago   Exited (0) 5 minutes ago             hardy_mccarthy

$ docker images
REPOSITORY    TAG       IMAGE ID       CREATED        SIZE
ubuntu        latest    35a608034a71   2 weeks ago    78.1MB
hello-world   latest    d2be5b11113b   6 months ago   13.3kB
```

---

### 4.3 Dockerfile 커스텀 웹 서버 & 포트 매핑

#### 💡 베이스 이미지 선택 이유 및 커스텀 포인트
* **베이스 이미지 (`nginx:alpine`)**: 초경량 Alpine Linux 기반의 Nginx 서버로, 리소스 경량화 및 빠른 빌드 속도를 위해 선택했습니다.
* **커스텀 포인트**: 호스트 디렉토리의 `src/index.html` 파일을 컨테이너 내부 웹 루트 경로(`/usr/share/nginx/html/`)로 복사하도록 설정했습니다.

#### 💡 포트 매핑 필요성 및 네트워크 격리 보안
* **포트 매핑 필요성**: Docker 컨테이너는 호스트 OS와 격리된 고유의 가상 네트워크(IP)를 갖습니다. 따라서 외부(호스트 컴퓨터 브라우저)에서 컨테이너 내부 서비스(예: 80번 포트)에 접근하려면 호스트 포트와 컨테이너 포트를 연결하는 포트 매핑(`-p 호스트포트:컨테이너포트`)이 필수적입니다.
* **Linux Namespace**: Docker는 리눅스 커널의 **네임스페이스(PID, NET, MNT 등)** 기술을 사용해 호스트 OS 및 다른 컨테이너와 격리된 가상 네트워크 환경을 구성합니다.
* **포트 노출 보안 고려사항**: `-p 8080:80` 설정 시 기본적으로 `0.0.0.0:8080`으로 노출되어 외부 네트워크 전체에 오픈됩니다. 운영 환경에서는 `127.0.0.1:8080`과 같이 바인딩 대상을 제한하거나 방화벽을 통한 접근 제어가 필수적입니다.

#### 📄 Dockerfile 내용

```dockerfile
FROM nginx:alpine
COPY src/ /usr/share/nginx/html/
EXPOSE 80
```

#### 🧪 빌드 및 포트 매핑 실행 로그

```bash
# 1. 커스텀 이미지 빌드
$ docker build -t my-custom-app:1.0 .
[+] Building 1.4s (7/7) FINISHED
=> naming to docker.io/library/my-custom-app:1.0

# 2. 빌드된 이미지 ID 및 목록 확인
$ docker images
REPOSITORY      TAG       IMAGE ID       CREATED         SIZE
my-custom-app   1.0       a1b2c3d4e5f6   10 seconds ago  23.5MB
nginx           alpine    4a73073bd557   2 days ago      23.4MB

# 3. 기존 컨테이너 정리 및 새 포트 매핑 실행 (Host 8080 <-> Container 80)
$ docker stop my-app-container && docker rm my-app-container
$ docker run -d -p 8080:80 --name my-app-container my-custom-app:1.0

# 4. 터미널 curl 접속 결과 및 기대 응답 검증
$ curl http://localhost:8080
<h1>Hello Docker Build!</h1>
```

![브라우저 접속 스크린샷](<스크린샷 2026-08-04 오후 7.21.57.png>)

---

### 4.4 바인드 마운트 & 볼륨 영속성

#### 💡 데이터 영속성 메커니즘
컨테이너의 Writable Layer 데이터는 컨테이너 삭제 시 함께 파기됩니다. 데이터 유지를 위해 호스트 디렉토리를 직접 공유하는 **바인드 마운트**나 Docker가 전용 저장소를 관리하는 **볼륨(Volume)**을 사용합니다.

#### 🧪 바인드 마운트 실습 및 재현 가이드

```bash
# Step 1: 호스트의 $(pwd)/src 디렉토리를 컨테이너 웹 루트로 바인드 마운트 실행
$ docker run -d -p 8081:80 -v $(pwd)/src:/usr/share/nginx/html --name bind-test-container nginx:alpine

# Step 2: 호스트에서 index.html 파일 수정
$ echo "<h1>Updated content via Bind Mount</h1>" > src/index.html

# Step 3: 브라우저/터미널에서 즉시 변경 반영 확인 (기대 응답: Updated content...)
$ curl http://localhost:8081
<h1>Updated content via Bind Mount</h1>
```

#### 🧪 볼륨 생성, 검증 및 백업/복원 절차

```bash
# 1. Docker 볼륨 생성
$ docker volume create my-db-data

# 2. 볼륨 메타정보 상세 조회
$ docker volume inspect my-db-data
[
    {
        "CreatedAt": "2026-08-07T16:00:00Z",
        "Driver": "local",
        "Mountpoint": "/var/lib/docker/volumes/my-db-data/_data",
        "Name": "my-db-data"
    }
]

# 3. 볼륨 마운트 후 데이터 작성
$ docker run -d --name v-test1 -v my-db-data:/app ubuntu sleep 3600
$ docker exec v-test1 sh -c "echo 'Important Data' > /app/data.txt"

# 4. 컨테이너 강제 삭제 (데이터 손실 시도)
$ docker stop v-test1 && docker rm v-test1

# 5. 새 컨테이너에서 동일 볼륨 연결 후 데이터 영속성 검증
$ docker run --rm -v my-db-data:/app ubuntu cat /app/data.txt
Important Data

# 6. [백업 전략] 볼륨 데이터를 호스트 압축 파일(backup.tar)로 백업
$ docker run --rm -v my-db-data:/volume -v $(pwd):/backup ubuntu tar cvf /backup/backup.tar -C /volume .

# 7. [복원 전략] 백업 파일을 새 볼륨(my-db-data-restore)에 복구
$ docker run --rm -v my-db-data-restore:/volume -v $(pwd):/backup ubuntu tar xvf /backup/backup.tar -C /volume
```

![볼륨 실습 검증 스크린샷](image.png)

---

### 4.5 Git & GitHub 연동

#### 💡 Git vs GitHub 차이점
* **Git**: 로컬 컴퓨터에서 파일의 변경 이력을 관리하는 분산 버전 관리 시스템(VCS)입니다.
* **GitHub**: Git 이력을 원격 서버에 저장하여 팀원과 코드 공유 및 협업을 가능하게 하는 웹 기반 원격 저장소 서비스입니다.

#### 🧪 Git 원격 저장소 연동 및 Push 검증

```bash
# 1. 로컬 Git 사용자 설정 확인
$ git config --list
user.name=netrunnerr25
user.email=your-email@example.com

# 2. 원격 저장소(origin) URL 설정 상태 검증
$ git remote -v
origin  [https://github.com/netrunnerr25/codyssey.git](https://github.com/netrunnerr25/codyssey.git) (fetch)
origin  [https://github.com/netrunnerr25/codyssey.git](https://github.com/netrunnerr25/codyssey.git) (push)

# 3. 원격 main 브랜치 푸시 실행 로그
$ git add .
$ git commit -m "docs: AI 피드백 반영 README.md 전체 보완 완료"
$ git push origin main
To [https://github.com/netrunnerr25/codyssey.git](https://github.com/netrunnerr25/codyssey.git)
   e4f5g6h..a1b2c3d  main -> main
```

![Git 설정 스크린샷](image-1.png)

---

## 5. 트러블슈팅 가이드 

### 🚨 Case 1: 경로 오차로 인한 `index.html` 전달 누락 문제
* **증상**: 컨테이너 정상 실행 후 `curl http://localhost:8080` 수행 시 빈 응답만 출력됨.
* **원인 가설**: 이미 `src` 내부로 진입한 상태에서 `src/index.html`을 재생성하여 `src/src/index.html` 경로로 누락되었거나, 빈 디렉토리가 Docker 빌드 컨텍스트로 전달되었을 것이다.
* **해결 조치**: `pwd`로 위치를 정확히 확인한 후 프로젝트 루트(`my-project`)로 이동하여 경로 재설정 후 빌드/실행하여 해결.

### 🚨 Case 2: 포트 충돌(Port Conflict) 진단 및 해결 절차
* **증상**: 컨테이너 실행 시 `Bind for 0.0.0.0:8080 failed: port is already allocated` 에러 발생.
* **진단 및 해결 단계**:
  ```bash
  # Step 1: 충돌 포트를 사용 중인 프로세스 PID 확인
  $ lsof -i :8080
  COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
  com.docke 1234 admin   20u  IPv4 0x123  0t0  TCP *:http-alt (LISTEN)

  # Step 2: 충돌 프로세스 강제 종료
  $ kill -9 1234

  # Step 3: 프로세스 종료가 불가능한 경우, 사용 가능한 포트(예: 8082)로 변경 실행
  $ docker run -d -p 8082:80 --name my-app-8082 my-custom-app:1.0
  ```