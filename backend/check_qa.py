from qa_chain import qa_bot

question = "What is the refund policy?"
answer = qa_bot(question)
print("Answer:", answer)
