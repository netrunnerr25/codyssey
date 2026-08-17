import json
import os
from quiz import Quiz


class QuizGame:
    """퀴즈 게임의 흐름과 데이터 입출력을 관리하는 클래스"""

    FILE_PATH = "state.json"

    DEFAULT_QUIZZES = [
        {
            "question": "Python의 창시자는 누구일까요?",
            "choices": [
                "Guido van Rossum",
                "Linus Torvalds",
                "Bjarne Stroustrup",
                "James Gosling",
            ],
            "answer": 1,
        },
        {
            "question": "다음 중 Python의 가변(Mutable) 자료형은 무엇일까요?",
            "choices": ["tuple", "str", "list", "int"],
            "answer": 3,
        },
        {
            "question": "Python에서 리스트에 요소를 추가하는 메서드는 무엇일까요?",
            "choices": ["push()", "append()", "add()", "insert_last()"],
            "answer": 2,
        },
        {
            "question": "Python에서 조건문에 사용하는 키워드가 아닌 것은 무엇일까요?",
            "choices": ["if", "elif", "else", "switch"],
            "answer": 4,
        },
        {
            "question": "Python에서 예외 처리를 위해 사용하는 블록 키워드 조합은 무엇일까요?",
            "choices": [
                "try / except",
                "try / catch",
                "begin / rescue",
                "do / catch",
            ],
            "answer": 1,
        },
    ]

    def __init__(self):
        self.quizzes: list[Quiz] = []
        self.best_score: int = 0
        self.load_state()

    def load_state(self) -> None:
        """state.json 파일에서 데이터를 불러오고 예외 발생 시 기본 데이터로 초기화"""
        if not os.path.exists(self.FILE_PATH):
            print("📂 기존 저장 데이터가 없어 기본 데이터로 초기화합니다.")
            self._init_default_data()
            return

        try:
            with open(self.FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.quizzes = [
                    Quiz.from_dict(item) for item in data.get("quizzes", [])
                ]
                self.best_score = int(data.get("best_score", 0))

            if not self.quizzes:
                self._init_default_data()
            else:
                print(
                    f"📂 저장된 데이터를 불러왔습니다. (퀴즈 {len(self.quizzes)}개, 최고 점수: {self.best_score}점)"
                )

        except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            print(
                f"⚠️ 데이터 파일이 손상되었거나 읽을 수 없습니다 ({e}). 기본 데이터로 복구합니다."
            )
            self._init_default_data()
            self.save_state()

    def _init_default_data(self) -> None:
        """기본 퀴즈 목록 생성 및 점수 초기화"""
        self.quizzes = [Quiz.from_dict(q) for q in self.DEFAULT_QUIZZES]
        self.best_score = 0

    def save_state(self) -> None:
        """현재 퀴즈 목록과 최고 점수를 state.json에 안전하게 저장"""
        try:
            data = {
                "quizzes": [quiz.to_dict() for quiz in self.quizzes],
                "best_score": self.best_score,
            }
            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"⚠️ 파일 저장 중 오류가 발생했습니다: {e}")

    def get_valid_input(self, prompt: str, min_val: int, max_val: int) -> int:
        """사용자로부터 정수 입력을 안전하게 검증하여 받아오는 공통 메서드"""
        while True:
            try:
                user_input = input(prompt).strip()
                if not user_input:
                    print("⚠️ 빈 입력입니다. 다시 입력해 주세요.")
                    continue

                val = int(user_input)
                if min_val <= val <= max_val:
                    return val
                print(
                    f"⚠️ 허용 범위를 벗어났습니다. ({min_val}~{max_val} 사이의 숫자 입력)"
                )
            except ValueError:
                print("⚠️ 올바른 숫자를 입력해 주세요.")

    def play_quiz(self) -> None:
        """퀴즈 풀기 진행"""
        if not self.quizzes:
            print("\n⚠️ 풀 수 있는 퀴즈가 없습니다. 퀴즈를 먼저 추가해 주세요.")
            return

        print(f"\n📝 퀴즈를 시작합니다! (총 {len(self.quizzes)}문제)")
        score = 0

        for idx, quiz in enumerate(self.quizzes, 1):
            print("-" * 40)
            quiz.display(idx)
            user_ans = self.get_valid_input("\n정답 입력 (1-4): ", 1, 4)

            if quiz.check_answer(user_ans):
                print("✅ 정답입니다!")
                score += 1
            else:
                print(f"❌ 틀렸습니다! (정답: {quiz.answer}번)")

        print("=" * 40)
        print(f"🏆 결과: {len(self.quizzes)}문제 중 {score}문제 정답!")

        if score > self.best_score:
            print(
                f"🎉 축하합니다! 새로운 최고 점수 달성! ({self.best_score}점 ➔ {score}점)"
            )
            self.best_score = score
            self.save_state()
        else:
            print(f"현재 최고 점수: {self.best_score}점")

    def add_quiz(self) -> None:
        """새로운 퀴즈 등록"""
        print("\n📌 새로운 퀴즈를 추가합니다.")

        while True:
            question = input("문제를 입력하세요: ").strip()
            if question:
                break
            print("⚠️ 문제는 빈 값일 수 없습니다.")

        choices = []
        for i in range(1, 5):
            while True:
                choice = input(f"선택지 {i}: ").strip()
                if choice:
                    choices.append(choice)
                    break
                print("⚠️ 선택지는 빈 값일 수 없습니다.")

        answer = self.get_valid_input("정답 번호 (1-4): ", 1, 4)

        new_quiz = Quiz(question, choices, answer)
        self.quizzes.append(new_quiz)
        self.save_state()
        print("\n✅ 퀴즈가 성공적으로 추가되었습니다!")

    def show_quiz_list(self) -> None:
        """등록된 퀴즈 목록 보기"""
        if not self.quizzes:
            print("\n📋 등록된 퀴즈가 없습니다.")
            return

        print(f"\n📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)")
        print("-" * 40)
        for idx, quiz in enumerate(self.quizzes, 1):
            print(f"[{idx}] {quiz.question}")
        print("-" * 40)

    def show_score(self) -> None:
        """최고 점수 확인"""
        print("\n" + "=" * 40)
        print(f"🏆 현재 최고 점수: {self.best_score}점")
        print("=" * 40)

    def run(self) -> None:
        """게임 메인 실행 루프"""
        while True:
            print("\n========================================")
            print("        🎯 파이썬 기초 퀴즈 게임 🎯")
            print("========================================")
            print("1. 퀴즈 풀기")
            print("2. 퀴즈 추가")
            print("3. 퀴즈 목록")
            print("4. 점수 확인")
            print("5. 종료")
            print("========================================")

            try:
                choice = self.get_valid_input("선택: ", 1, 5)

                if choice == 1:
                    self.play_quiz()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.show_quiz_list()
                elif choice == 4:
                    self.show_score()
                elif choice == 5:
                    print("\n게임을 종료합니다. 이용해 주셔서 감사합니다!")
                    self.save_state()
                    break

            except (KeyboardInterrupt, EOFError):
                print("\n\n⚠️ 사용자에 의한 강제 종료 명령이 감지되었습니다.")
                print("데이터를 안전하게 저장하고 프로그램을 종료합니다.")
                self.save_state()
                break


if __name__ == "__main__":
    game = QuizGame()
    game.run()