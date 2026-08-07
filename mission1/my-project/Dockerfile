# 1. 베이스 이미지 지정 (필수)
FROM nginx:alpine

# 2. 내 컴퓨터의 소스 코드를 컨테이너 내부 웹 경로로 복사
COPY src/ /usr/share/nginx/html/

# 3. 컨테이너가 사용할 포트 명시
EXPOSE 80

# 4. 컨테이너가 실행될 때 동작할 기본 명령어
# nginx 이미지에는 기본 CMD가 포함되어 있어 생략 가능하지만, 명시할 경우:
CMD ["nginx", "-g", "daemon off;"]