import ollama

while True:
    print("")
    q = input("You : ")
    print("")

    stream = ollama.chat(
        model="llama3",
        messages=[
            {"role": "user", "content": q}
        ],
        stream=True
    )

    print("Bot: ", end="", flush=True)

    for chunk in stream:
        print(chunk["message"]["content"], end="", flush=True)

    print("\n")






### Basic LLM Chating


# import ollama

# while True:
#     print("")
#     q = input("You : ")
#     print("")
#     res = ollama.chat(
#     model="llama3",
#     messages=[
#         {"role": "user", "content": q}
#     ]
#     )
#     print("")
#     print(res["message"]["content"])
#     print("")
