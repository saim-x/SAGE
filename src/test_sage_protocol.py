from sage import SAGE

if __name__ == "__main__":
    # Initialize SAGE protocol
    sage = SAGE()

    # New complex prompt for protocol testing
    prompt = (
        "You are a consultant for a hospital planning to implement an AI-powered patient triage system. "
        "1. Identify the main ethical and operational challenges in deploying such a system. "
        "2. Suggest a technical architecture, including data sources, model types, and privacy safeguards. "
        "3. Draft a communication plan to explain the system to patients and staff, addressing concerns and highlighting benefits."
    )

    # Run the protocol
    result = sage.process_prompt(prompt)

    # Print the results
    print("\n=== FINAL AGGREGATED RESPONSE ===\n")
    print(result.final_response)
    print("\n--- Execution Details ---\n")
    for exec_result in result.execution_results:
        print(f"SubPrompt ID: {exec_result.subprompt_id}")
        print(f"Model Used: {exec_result.model_used.model_name}")
        print(f"Success: {exec_result.success}")
        print(f"Similarity Score: {exec_result.similarity_score}")
        print(f"Content: {exec_result.content}\n")
    print("\n--- Metadata ---\n")
    print(result.metadata) 