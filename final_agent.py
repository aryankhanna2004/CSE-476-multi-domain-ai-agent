import os
import re
import requests

API_KEY = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")
MODEL = os.getenv("MODEL_NAME", "bens_model")

calls_used = 0

def call_llm(prompt, system, temperature, max_tokens):
    global calls_used
    calls_used = calls_used + 1
    url = API_BASE + "/chat/completions"
    payload = {
        "model": MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    }
    headers = {
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        data = resp.json()
        choices = data.get("choices", [{}])
        message = choices[0].get("message", {})
        return message.get("content", "")
    return ""

def extract_number(text):
    pattern = r"[-+]?\d+\.?\d*"
    nums = re.findall(pattern, text)
    if nums:
        return nums[-1]
    return ""

def extract_boxed(text):
    pattern = r"\\boxed\{([^}]+)\}"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return extract_number(text)

def clean_answer(text):
    text = text.strip()
    if text.lower().startswith("answer:"):
        text = text[7:].strip()
    if len(text) > 2 and text[0].isdigit() and text[1] == ")":
        text = text[2:].strip()
    if len(text) > 2 and text[0].isalpha() and text[1] == ")":
        text = text[2:].strip()
    return text

def classify_domain(question):
    short_question = question[:500]
    prompt = "Classify this question into ONE category: math, coding, common_sense, planning, future_prediction"
    prompt = prompt + " Question: " + short_question + " Category:"
    result = call_llm(prompt, "", 0.0, 20)
    r = result.strip().lower()
    domains = ["math", "coding", "common_sense", "planning", "future_prediction"]
    for d in domains:
        if d in r:
            return d
    return "common_sense"

def verify_and_retry(question, first_answer, domain):
    verify_prompt = "Question: " + question[:800]
    verify_prompt = verify_prompt + " Agent's Answer: " + str(first_answer)[:300]
    verify_prompt = verify_prompt + " Is this answer correct? Reply YES if correct. If wrong, explain why it is wrong."
    
    verify_result = call_llm(verify_prompt, "", 0.1, 200)
    verify_result = verify_result.strip()
    
    lower = verify_result.lower()
    if lower.startswith("yes") or lower == "yes" or lower == "yes.":
        return first_answer
    
    retry_prompt = "Question: " + question[:800]
    retry_prompt = retry_prompt + " A previous agent answered: " + str(first_answer)[:200]
    retry_prompt = retry_prompt + " But this is WRONG because: " + verify_result[:300]
    retry_prompt = retry_prompt + " Please solve this correctly. Give ONLY the correct answer."
    
    retry_result = call_llm(retry_prompt, "", 0.1, 300)
    retry_result = retry_result.strip()
    
    new_answer = clean_answer(retry_result)
    lines = new_answer.split("\n")
    new_answer = lines[0].strip()
    
    if domain == "math":
        num = extract_number(new_answer)
        if num:
            return num
        boxed = extract_boxed(retry_result)
        if boxed:
            return boxed
    
    if domain == "common_sense":
        l = new_answer.lower()
        if l == "yes" or l == "true":
            return "True"
        if l == "no" or l == "false":
            return "False"
    
    if len(new_answer) > 0 and len(new_answer) < 500:
        return new_answer
    
    return first_answer

def solve_math(question):
    prompt = "Solve this step by step. Put your final numeric answer in \\boxed{}."
    prompt = prompt + " Question: " + question
    result = call_llm(prompt, "", 0.1, 768)
    answer = extract_boxed(result)
    if answer:
        return answer
    
    prompt = "Write Python code to solve this math problem. Use def solution(): and return the answer."
    prompt = prompt + " Problem: " + question
    result = call_llm(prompt, "", 0.1, 512)
    
    pattern1 = r"```python\s*([\s\S]+?)```"
    match = re.search(pattern1, result)
    if match:
        code = match.group(1).strip()
        try:
            exec_globals = {}
            exec(code, exec_globals)
            if "solution" in exec_globals:
                return str(exec_globals["solution"]())
        except:
            pass
    
    pattern2 = r"def solution\(\):[\s\S]+?return[^\n]+"
    match = re.search(pattern2, result)
    if match:
        code = match.group(0).strip()
        try:
            exec_globals = {}
            exec(code, exec_globals)
            return str(exec_globals["solution"]())
        except:
            pass
    
    return extract_number(result)

def solve_common_sense(question):
    prompt = "Answer this question with ONLY the answer, no explanation, no numbering, no prefix."
    prompt = prompt + " Question: " + question
    result = call_llm(prompt, "", 0.1, 100)
    answer = result.strip()
    lines = answer.split("\n")
    answer = lines[0].strip()
    answer = clean_answer(answer)
    answer = answer.rstrip(".")
    
    lower = answer.lower()
    if lower == "yes" or lower == "true" or lower == "yes.":
        answer = "True"
    if lower == "no" or lower == "false" or lower == "no.":
        answer = "False"
    
    return answer

def solve_coding(question):
    prompt = "Complete this function. Return ONLY the function body code, no imports, no function definition, just the implementation inside the function."
    prompt = prompt + " " + question
    result = call_llm(prompt, "", 0.1, 768)
    code = result.strip()
    code = code.replace("```python", "")
    code = code.replace("```", "")
    code = code.strip()
    return code

def solve_planning(question):
    prompt = "You are a PDDL planning solver. Read the problem and output the COMPLETE plan."
    prompt = prompt + " MAIN RULES:"
    prompt = prompt + " 1. Each action on its own line"
    prompt = prompt + " 2. Each action in parentheses: (action-name arg1 arg2 arg3)"
    prompt = prompt + " 3. Use SHORT names from the problem (like t1, l1-0, yellow, red, a, b)"
    prompt = prompt + " 4. NO explanations, NO natural language, ONLY actions in parentheses"
    prompt = prompt + " Example output format:"
    prompt = prompt + " (drive-truck t1 l1-0 l1-2 c1)"
    prompt = prompt + " (load-truck p1 t1 l1-2)"
    prompt = prompt + " (unstack yellow red)"
    prompt = prompt + " (stack yellow blue)"
    prompt = prompt + " Now solve this problem: " + question
    result = call_llm(prompt, "", 0.1, 1500)
    lines = result.split("\n")
    actions = []
    for line in lines:
        line = line.strip()
        if "(" in line and ")" in line:
            start = line.find("(")
            end = line.rfind(")") + 1
            action = line[start:end]
            if len(action) > 3:
                actions.append(action)
    if actions:
        return "\n".join(actions)
    return result.strip()

def solve_prediction(question):
    prompt = "Based on the question, make your best prediction. Give ONLY the predicted value or answer, nothing else."
    prompt = prompt + " " + question
    result = call_llm(prompt, "", 0.3, 200)
    answer = result.strip()
    lines = answer.split("\n")
    answer = lines[0].strip()
    answer = clean_answer(answer)
    return answer

def solve(question):
    global calls_used
    calls_used = 0
    
    domain = classify_domain(question)
        
    if domain == "math":
        first_answer = solve_math(question)
    elif domain == "common_sense":
        first_answer = solve_common_sense(question)
    elif domain == "coding":
        first_answer = solve_coding(question)
    elif domain == "planning":
        first_answer = solve_planning(question)
    else:
        first_answer = solve_prediction(question)
    
    final_answer = verify_and_retry(question, first_answer, domain)
    
    return str(final_answer)

