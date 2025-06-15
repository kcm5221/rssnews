import textwrap, re

BULLET = "•"

def simple_summary(text: str, max_sent=3) -> str:
    # 가장 긴 문장 n개 뽑기 (매우 단순)
    sents = re.split(r"(?<=[.!?]) +", text)
    sents = sorted(sents, key=lambda s: len(s), reverse=True)[:max_sent]
    return " ".join(sents)

def build_script(title, body, source, license):
    summary = simple_summary(body)
    return textwrap.dedent(f"""
    ▶ 오늘의 기사: {title}

    {BULLET} 요약
    {summary}

    {BULLET} 해설
    - (여기에 당신의 의견/배경 설명 추가)

    출처: {source} / 라이선스: {license}
    """).strip()
