# import gradio as gr


# def reverse_text(text):
#     return text[::-1]


# demo = gr.Interface(fn=reverse_text, inputs="text", outputs="text")

# demo.launch()

# import gradio as gr


# def reverse_and_count(text):
#     reversed_text = text[::-1]
#     length = len(text)
#     return reversed_text, length


# demo = gr.Interface(
#     fn=reverse_and_count,
#     inputs="text",
#     outputs=["text", "number"],
#     title="文本处理工具",
#     description="输入一段文字，查看其倒序形式及字符数。",
#     examples=[["你好，世界"], ["Hello,World"]],
# )

# demo.launch()