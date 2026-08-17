class Quiz:
    """개별 퀴즈 데이터를 표현하는 클래스"""

    def __init__(self, question: str, choices: list[str], answer: int):
        self.question = question
        self.choices = choices
        self.answer = answer  # 1-based index (1~4)

    def display(self, index: int) -> None:
        """퀴즈 문제와 선택지를 화면에 출력"""
        print(f"\n[문제 {index}]")
        print(f"{self.question}\n")
        for idx, choice in enumerate(self.choices, 1):
            print(f"  {idx}. {choice}")

    def check_answer(self, user_answer: int) -> bool:
        """사용자가 입력한 정답 번호의 맞춤 여부를 확인"""
        return self.answer == user_answer

    def to_dict(self) -> dict:
        """JSON 저장을 위해 객체를 딕셔너리로 변환"""
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quiz":
        """딕셔너리 데이터로부터 Quiz 인스턴스 생성"""
        return cls(
            question=data["question"],
            choices=data["choices"],
            answer=int(data["answer"]),
        )