# check_langchain.py
# LangChain이 정상적으로 작동하는지 확인하는 테스트 스크립트입니다.

import os
import sys

# 1단계: .env 파일에서 환경 변수 불러오기
from dotenv import load_dotenv
load_dotenv()

# 2단계: API 키가 설정되어 있는지 확인
api_key = os.getenv("OPENAI_API_KEY")

if not api_key or api_key == "여기에_본인의_API_KEY를_입력하세요":
    print("=" * 50)
    print("OPENAI_API_KEY가 설정되지 않았습니다!")
    print()
    print("해결 방법:")
    print("1. 프로젝트 폴더에 .env 파일이 있는지 확인하세요.")
    print("2. .env 파일을 열어서 아래처럼 본인의 API 키를 입력하세요:")
    print("   OPENAI_API_KEY=sk-proj-여기에본인키입력")
    print()
    print("API 키는 https://platform.openai.com/api-keys 에서 발급받을 수 있습니다.")
    print("=" * 50)
    sys.exit(1)

# 3단계: LangChain으로 AI에게 질문 보내기
try:
    from langchain_openai import ChatOpenAI

    # 비용이 적은 모델 사용
    llm = ChatOpenAI(model="gpt-5-nano")

    # 간단한 질문 보내기
    question = "LangChain이 무엇인지 초등학생도 이해할 수 있게 한 문장으로 설명해줘."
    response = llm.invoke(question)

    # 4단계: 성공 결과 출력
    print("=" * 50)
    print("LangChain 정상 작동 확인 완료!")
    print()
    print(f"질문: {question}")
    print()
    print("AI 응답:")
    print(response.content)
    print("=" * 50)

except Exception as e:
    # 5단계: 오류 발생 시 친절한 안내
    error_message = str(e)
    print("=" * 50)
    print("오류가 발생했습니다!")
    print()
    print(f"오류 내용: {error_message}")
    print()
    print("예상 원인과 해결 방법:")
    print()

    if "api_key" in error_message.lower() or "auth" in error_message.lower():
        print("[API 키 문제]")
        print("  - .env 파일의 OPENAI_API_KEY 값이 올바른지 확인하세요.")
        print("  - https://platform.openai.com/api-keys 에서 키를 다시 확인하세요.")
    elif "model" in error_message.lower() or "permission" in error_message.lower():
        print("[모델 접근 권한 문제]")
        print("  - OpenAI 콘솔에서 해당 모델 접근 권한을 확인하세요.")
        print("  - 다른 모델(gpt-3.5-turbo, gpt-5-nano)로 변경해보세요.")
    elif "module" in error_message.lower() or "import" in error_message.lower():
        print("[패키지 설치 문제]")
        print("  - 아래 명령어로 패키지를 설치하세요:")
        print("  pip install -r requirements.txt")
    elif "connection" in error_message.lower() or "network" in error_message.lower():
        print("[인터넷 연결 문제]")
        print("  - 인터넷 연결 상태를 확인하세요.")
        print("  - 방화벽이나 프록시 설정을 확인하세요.")
    elif "rate" in error_message.lower() or "quota" in error_message.lower() or "billing" in error_message.lower():
        print("[API 사용량/결제 문제]")
        print("  - OpenAI 결제 설정을 확인하세요: https://platform.openai.com/settings/organization/billing")
        print("  - 무료 크레딧이 소진되었을 수 있습니다.")
    else:
        print("일반적인 해결 방법:")
        print("1. .env 파일이 프로젝트 폴더에 있는지 확인")
        print("2. OPENAI_API_KEY가 올바른지 확인")
        print("3. pip install -r requirements.txt 실행")
        print("4. 인터넷 연결 상태 확인")
        print("5. OpenAI 결제 설정 확인")

    print("=" * 50)
