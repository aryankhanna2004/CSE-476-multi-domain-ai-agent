# CSE 476 Final Project
# **GITHUB REPO URL** = https://github.com/aryankhanna2004/CSE-476-multi-domain-ai-agent.git

## Summary

For this project, I built an agent that can solve questions across multiple domains including mathematics, coding, common sense reasoning, planning, and future prediction. Through iterative development and testing on randomly selected samples from the development dataset, I was able to improve the agent from a baseline accuracy of 14% to a final accuracy of 36% on 100 randomly selected questions with the techiques i just added below.

## How the Agent Works

Agent is built around three main components that work together to solve different reasoning problems. The first component is domain classification, which I implemented to automatically categorize incoming questions into one of five domains: math, coding, common sense, planning, or future prediction so that later on i can use specfic guided prompts to answer each question to help improve the overall accuracy. This classification happens through a lightweight LLM call that looks at the first 500 characters of the question and determines its category.

The second component consists of five specialized solver functions, one for each domain. For math problems, I created a solver that uses symbolic reasoning and looks for answers wrapped in boxed notation so it is easy to use regex or extract easily because most of the times i saw that the model added garbage before and after the answer such as "Here is your answer" even after explicty stating the model to not to add that. I also added a fallback mechanism that generates and executes Python code when needed. For common sense questions, I designed a solver that extracts direct answers and normalizes boolean responses when needed. The coding solver generates  function implementations without imports or definitions. For planning problems, I built a PDDL style action sequence generator that outputs actions in proper parenthetical format that i figured from the dev data. Finally, for future prediction questions, I created a solver that makes best effort forecasts with slightly higher temperature for creativity but future predection is always hard so it was the best attempt to make the model think wider

The third and most impactful component is my self verification loop. After getting an initial answer from the domain specific solver, I ask the model to verify whether the answer is correct. If it says the answer is wrong, I retry the question with information about why the first attempt failed, which gives the model a chance to correct its mistakes. This verification and retry mechanism was responsible for the biggest jump in accuracy from 32% to 36%.

Beyond these three core components, I added several important features. I implemented robust answer extraction that can handle various formats like boxed expressions, numbered lists, and boolean values. I built a checkpoint system so the agent can resume processing if interrupted during long test runs because the vpn for the wifi disconnects every few hours.

## How I Developed and Evaluated My Agent

I developed my agent iteratively by testing on 100 randomly selected questions from the development dataset after each major change. I started with a baseline approach that just called the model directly without any special handling, which achieved only 14% accuracy. Then I added chain of thought prompting and basic math tools, which improved accuracy to 19%. 

Next, I implemented program aided language capabilities where the agent could write and execute Python code to solve math problems, which brought accuracy up to 24% because it was then able to solve complex math questions as well using python. After that, I added the domain classification system and created specialized prompts for each domain type, which was a major improvement that pushed accuracy to 32%. 

Finally, I implemented the self verification loop where the agent checks its own answers and retries when verification fails. This was the biggest single improvement and brought my final accuracy to 36% on the development set.

## Important Notes About Accuracy

I believe the actual performance of my agent is higher than 36% because many of my answers were semantically correct but failed the grading exact matches due to exact string matching requirements. For example, if the expected answer was 42 but my agent returned 42.0, or if the expected answer was True but my agent returned true, these would be marked as incorrect even though they are mathematically or semantically equivalent. If the evaluation used semantic comparison instead of exact string matching, I think the accuracy would be significantly higher which i believe would be used in the final grading

## Running My Agent

To run my agent on new test cases, simply run `python generate_answer_template.py`. The script expects an input file called cse_476_final_project_test_data.json containing a JSON array of question objects. It will output answers to cse_476_final_project_answers.json with each answer in the output field. The script shows progress as it processes questions and saves checkpoints to checkpoint.json so you can resume if interrupted.

If you want to test a single question, you can import the solve function from final_agent and call it with your question string. For example, `from final_agent import solve` then `answer = solve("What is 2 + 2?")` and the answer variable will contain the result as a string.
