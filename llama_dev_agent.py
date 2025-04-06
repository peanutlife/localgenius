# llama_dev_agent.py

import os
import sys
from models.llama3_runner import LlamaRunner
from memory import Memory
from tasks import TaskPlanner
from tools.exec import run_code
from tools.file_ops import write_file, read_file
import json
import argparse



# Init components
llm = LlamaRunner(model_name="llama3:8b")  # adjust if you have llama3:70b or others
memory = Memory()
planner = TaskPlanner(llm)

PLAN_PATH = "workspace/plan.json"
RESULTS_PATH = "workspace/results.json"

# CLI loop
# def main():
#     print("\n🧠 LLaMA Dev Agent Ready. Type a task (e.g., 'create a Flask app'). Type 'exit' to quit.\n")
#
#     while True:
#         user_input = input(">> ").strip()
#         if user_input.lower() in ["exit", "quit"]:
#             break
#
#         memory.log_task(user_input)
#
#         # similar = memory.search_memory(user_input)
#         # if similar:
#         #     print("🔍 I found similar tasks in memory:")
#         #     for match in similar:
#         #         print(f"- {match}")
#         #     print()
#         # print("\n🛠️  Planning task...\n")
#         # plan = planner.plan_task(user_input)
#         # memory.log_plan(plan)
#         similar = memory.search_memory(user_input)
#         if similar:
#             print("🔍 Found similar tasks in memory:")
#             for i, match in enumerate(similar, 1):
#                 print(f"{i}. {match[:200]}{'...' if len(match) > 200 else ''}")
#             print()
#
#         print("\n🛠️  Planning task...\n")
#         plan = planner.plan_task(user_input, memory_context=similar)
#         memory.log_plan(plan)
#
#         for step_num, step in enumerate(plan, 1):
#             print(f"➡️ Step {step_num}: {step}")
#             result = planner.execute_step(step)
#             memory.log_result(step, result)
#             print(f"✅ Result: {result}\n")
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="Resume last unfinished task")
    parser.add_argument("--retry", type=int, help="Retry specific step number")
    args = parser.parse_args()

    if args.resume and os.path.exists(PLAN_PATH):
        print("🔄 Resuming previous task...\n")
        with open(PLAN_PATH, "r") as f:
            plan = json.load(f)
        completed_steps = []
        if os.path.exists(RESULTS_PATH):
            with open(RESULTS_PATH, "r") as f:
                completed_steps = json.load(f)

        for step_num, step in enumerate(plan, 1):
            if any(r["step"] == step for r in completed_steps):
                continue
            print(f"➡️ Step {step_num}: {step}")
            result = planner.execute_step(step)
            memory.log_result(step, result)
            completed_steps.append({"step": step, "result": result})
            with open(RESULTS_PATH, "w") as f:
                json.dump(completed_steps, f, indent=2)
            print(f"✅ Result: {result}\n")
        return

    if args.retry is not None:
        step_idx = args.retry - 1
        if not os.path.exists(PLAN_PATH):
            print("❌ No plan to retry from.")
            return
        with open(PLAN_PATH, "r") as f:
            plan = json.load(f)
        if step_idx >= len(plan):
            print("❌ Invalid step number.")
            return
        step = plan[step_idx]
        print(f"🔁 Retrying step {args.retry}: {step}")
        result = planner.execute_step(step)
        memory.log_result(step, result)
        return

    # Normal mode: take a new task
    print("\n🧠 LLaMA Dev Agent Ready. Type a task (e.g., 'create a Flask app'). Type 'exit' to quit.\n")

    while True:
        user_input = input(">> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        memory.log_task(user_input)
        similar = memory.search_memory(user_input)
        if similar:
            print("🔍 Found similar tasks in memory:")
            for i, match in enumerate(similar, 1):
                print(f"{i}. {match[:200]}{'...' if len(match) > 200 else ''}")
            print()

        print("\n🛠️  Planning task...\n")
        plan = planner.plan_task(user_input, memory_context=similar)
        memory.log_plan(plan)

        with open(PLAN_PATH, "w") as f:
            json.dump(plan, f, indent=2)

        results = []

        for step_num, step in enumerate(plan, 1):
            print(f"➡️ Step {step_num}: {step}")
            result = planner.execute_step(step)
            memory.log_result(step, result)
            results.append({"step": step, "result": result})
            with open(RESULTS_PATH, "w") as f:
                json.dump(results, f, indent=2)
            print(f"✅ Result: {result}\n")
if __name__ == "__main__":
    main()
