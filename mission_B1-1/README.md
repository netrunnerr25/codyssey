# 윤수현 · Backend Developer

신입 백엔드 개발자를 소개하는 모바일 퍼스트 포트폴리오입니다. 외부 라이브러리, 패키지 설치, 빌드 과정 없이 동작합니다.

## 주요 기능

- Hero, About, Skills, Projects, Contact와 Footer, 앵커 내비게이션
- Hero의 인사말·소개·CTA 버튼, About의 자기소개·프로필 이미지
- 모바일 햄버거 메뉴와 Escape 닫기, 부드러운 섹션 이동
- 스크롤에 따른 헤더 그림자와 맨 위로 이동 버튼
- 라이트/다크 테마 전환 및 localStorage를 통한 선택 유지
- IntersectionObserver 스크롤 등장 효과, 동작 줄이기 설정 존중
- GitHub 저장소 조회: 지정한 두 프로젝트 조회, archived 제외
- 프로젝트 로딩·성공·빈 데이터·오류 UI, 요청 한도 안내와 재시도
- 이름·이메일·메시지 검증, 입력 중 오류 재검사, 성공 후 초기화
- skip link, 키보드 포커스, 레이블, ARIA 상태 및 안내

문의 폼은 검증용 데모입니다. 실제 메시지 전송이나 입력값 저장은 하지 않습니다. GitHub 요청은 15초가 지나면 취소하고 재시도를 안내합니다.

## 사용 기술

HTML5 시맨틱 마크업, CSS3 변수·Flexbox·Grid·미디어 쿼리, 순수 JavaScript의 Fetch API·async/await·IntersectionObserver·localStorage, SVG를 사용합니다. 시스템 글꼴만 사용하며 외부 폰트를 요청하지 않습니다.

## 폴더 구조

```text
mission_B1-1/
├── index.html
├── README.md
├── css/
│   └── style.css
├── js/
│   └── main.js
├── images/
│   ├── profile.jpg
│   └── profile.svg
└── screenshots/
    ├── README.md
    ├── desktop.png
    ├── mobile.png
    └── dark-mode.png
```

## 상태 → 렌더링 흐름

`js/main.js`의 하나의 `state` 객체가 `theme`, `projects`, `formErrors` 및 메뉴·스크롤·폼 상태를 관리합니다.

1. 사용자 이벤트 리스너가 실행됩니다.
2. 이벤트에서 `state`를 변경합니다.
3. 해당 `renderTheme`, `renderMenu`, `renderScroll`, `renderProjects`, `renderForm` 함수를 호출합니다.
4. 렌더링 함수가 상태를 읽어 클래스, 속성, 텍스트 등 DOM을 갱신합니다.

예: 테마 클릭 → `state.theme` 변경 → `renderTheme()` → `data-theme`와 버튼 ARIA 갱신 → 선택값 저장. 메뉴 클릭 → `state.menuOpen` 반전 → `renderMenu()` → `classList.toggle`과 `aria-expanded` 갱신.

프로젝트 재시도 → `loadProjects()` → 로딩 상태와 렌더링 → fetch 응답 → 성공·빈 데이터·오류 상태와 렌더링. 폼 입력 및 제출 → 검증 결과를 `state.formErrors`에 저장 → `renderForm()` → 오류 텍스트와 `aria-invalid` 변경. 성공 메시지가 있으면 렌더링 함수에서 폼을 초기화합니다.

API 데이터는 구조분해 할당으로 읽고 `filter`, `map`, 템플릿 리터럴로 카드를 구성합니다. `innerHTML`에 삽입하는 동적 문자열은 `escapeHTML()`을 거칩니다. 링크는 고정 GitHub 도메인과 URL 인코딩한 사용자·저장소명으로 구성합니다. 폼 입력값은 HTML에 삽입하지 않습니다.

## Live Server 실행

1. VS Code에서 `mission_B1-1` 폴더를 엽니다.
2. 확장 탭에서 **Live Server**를 설치합니다.
3. `index.html`을 우클릭하고 **Open with Live Server**를 선택합니다.
4. 열린 로컬 주소에서 확인합니다. npm 설치나 빌드는 필요 없습니다.

Python이 설치되어 있다면 폴더에서 `python3 -m http.server 8000`을 실행하고 `http://localhost:8000`으로 접속해도 됩니다. GitHub 프로젝트를 조회하려면 인터넷 연결이 필요합니다.

## GitHub 아이디 수정

`js/main.js` 상단의 `GITHUB_USERNAME`과 `PROJECT_REPOSITORIES`를 수정합니다. 현재 값은 `netrunnerr25`이며 다음 API를 호출합니다.

```text
https://api.github.com/users/netrunnerr25/repos?sort=updated&per_page=100&page=1
```

저장소 목록에서 `PROJECT_REPOSITORIES`에 지정한 두 프로젝트만 `filter`로 선택합니다. 실제 과제는 fork 제외를 요구하지 않으므로 fork 저장소도 포함합니다. 페이지당 최대 100개를 요청하며, 두 저장소를 모두 찾거나 마지막 페이지에 도달하면 요청을 종료합니다. 짧은 시간 내 반복 새로고침을 피하세요. 카드 제목은 `PROJECT_LABELS`에서 수정합니다.

프로필을 변경할 때는 `index.html`의 이름과 GitHub 링크도 함께 수정합니다. GitHub 비인증 REST API는 일반적으로 IP 주소 기준 시간당 60회 요청 제한이 있습니다. 403 또는 429 응답이면 요청 한도 초과 안내와 다시 시도 버튼이 나타납니다. 공용 네트워크에서는 다른 사용자의 요청도 한도에 영향을 줄 수 있습니다. 토큰을 프런트엔드 코드에 넣지 마세요.

## 화면 및 기준값

- 기본은 모바일 단일 열이며 768px에서 내비게이션과 태블릿 다단 레이아웃으로 전환합니다.
- 1024px부터 Skills는 3열입니다. Hero는 인사말과 CTA 버튼으로 구성합니다.
- 프로젝트는 `repeat(auto-fit, minmax(min(100%, 290px), 1fr))`로 폭에 맞춥니다.
- 본문 글자 기본 크기는 16px 이상입니다.
- 스크롤 **60px 이상**: 헤더 `scrolled` 클래스 적용으로 배경색과 그림자 변경.
- 스크롤 **300px 이상**: 맨 위 버튼 표시.
- IntersectionObserver **threshold: 0.2**: 대상의 20%가 보이면 등장.
- `prefers-reduced-motion: reduce`에서는 부드러운 이동과 등장 전환을 생략합니다.
- 기준값은 `js/main.js` 상단의 상수, 색상·글꼴·간격·그림자·모서리는 CSS 변수에서 수정합니다.

## GitHub Pages 배포

1. GitHub 저장소에 이 폴더의 내용을 올립니다. 저장소 최상위에 `index.html`이 있어야 합니다.
2. 저장소 **Settings → Pages → Build and deployment**를 엽니다.
3. **Source: Deploy from a branch**, **Branch: main**, **Folder: / (root)**를 선택하고 저장합니다. 브랜치명이 다르면 실제 사용 중인 브랜치를 선택합니다.
4. 배포가 끝나면 Pages 화면의 주소를 엽니다. 일반적인 프로젝트 주소는 `https://netrunnerr25.github.io/저장소명/`입니다.
5. 모바일 메뉴, 테마 저장, GitHub API 및 폼 검증을 배포 주소에서도 확인합니다.

## 검증

```sh
node --check js/main.js
```

320px·375px 모바일, 768px 태블릿, 1024px·1440px 데스크톱에서 가로 스크롤과 글자 겹침을 확인합니다. 키보드 Tab 이동, 메뉴 Escape 닫기, 다크 모드 새로고침 유지, 빈 폼 및 잘못된 이메일 오류를 확인합니다. 브라우저 개발자 도구의 Network에서 오프라인으로 바꾸고 재시도하면 API 오류 UI를 확인할 수 있습니다.

## 제출 기록

- GitHub 저장소 URL: https://github.com/netrunnerr25/codyssey (과제 폴더: `mission_B1-1`)
- 배포 URL: https://netrunnerr25.github.io/codyssey/mission_B1-1/
- 데스크톱 스크린샷: [desktop.png](screenshots/desktop.png)
- 모바일 스크린샷: [mobile.png](screenshots/mobile.png)
- 다크 모드 스크린샷: [dark-mode.png](screenshots/dark-mode.png)


## 학습 개념 설명

- 시맨틱 HTML: `header`와 `nav`는 머리말과 탐색, `main`은 본문, `section`은 주제별 구역, `article`은 개별 카드, `footer`는 저작권과 소셜 링크를 구분합니다. 구조를 명확히 하여 브라우저와 보조 기술이 각 영역의 역할을 이해할 수 있게 합니다.
- Flexbox는 한 방향의 정렬에 적합해 내비게이션에 사용합니다. Grid는 행과 열을 함께 배치하기 좋아 프로젝트 카드에 사용합니다.
- `querySelector`로 요소 하나, `querySelectorAll`로 여러 요소를 선택하고 `addEventListener`로 이벤트와 함수를 연결합니다. 이벤트 함수가 상태를 변경하고 렌더링 함수가 DOM을 갱신합니다.
- 화살표 함수는 이벤트와 배열 처리 함수를 간결하게 작성합니다. 구조분해 할당은 객체의 필요한 속성을 꺼냅니다. `filter`는 프로젝트를 선택하고 `map`은 카드 HTML로 변환하며 `forEach`는 입력 필드에 이벤트를 연결합니다.
- `fetch`는 비동기 요청을 시작하고 `await`는 응답을 기다립니다. 요청 전 로딩 상태, 응답 후 성공·빈 상태, `catch`에서 오류 상태를 설정하고 `renderProjects()`가 화면을 갱신합니다.
