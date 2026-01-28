from openai import OpenAI

client = OpenAI(
    api_key="sk-02e847ab13a543798c4860e15d459293",  # 填入AccessKey
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def query_gpt_attempts(prompt, temperature, trys=1):
    try:
        output = query_turbo_model(prompt, temperature)
    except Exception as error:
        print(trys)
        print(error)
        trys += 1
        if trys <= 3:
            output = query_gpt_attempts(prompt, temperature, trys)
        else:
            output = {'content': 'NA'}
    return output


def query_turbo_model(prompt, temperature):
    chat_completion = client.chat.completions.create(
        messages=prompt,
        model="qwen-plus",
        temperature=temperature,
    )
    return chat_completion.choices[0].message.content


prompt_system = """
    你是一名关注中小学生的心理医生和心理咨询老师。你所在的学校的学生们完成了一场心理测试，目的是测量他们的心理健康程度和判断他们的性格。
"""

history_summary = None

current_answers_text = None

prompt_user = f"""
    你是一位学校心理健康专家。请根据以下信息对该学生进行心理状态评估：

【历史心理档案】：
{history_summary}

【本次答题内容】：
{current_answers_text}

请完成以下任务：
1. 分析学生当前的情绪状态、潜在风险（如焦虑、抑郁、社交回避等）。
2. 对比历史档案，指出变化趋势（改善/恶化/稳定）。
3. 用一段温和、鼓励性的语言生成反馈建议（给学生看）。
4. 输出一个简洁的内部摘要（用于下学期跟踪），格式：[摘要]...[/摘要]

注意：不要做出临床诊断，仅提供观察和建议。
"""
