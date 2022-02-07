from typing import Optional

path = "/home/logan/Downloads/address_hammer/README.md"

text = open(path, "r").read()


def code_chunks():
    code = ""
    for chunk in text.split("```python"):
        chunks = chunk.split("```")
        if len(chunks) == 2:
            print("#########################")
            print(chunks[0])
            if "# >> raises a" not in chunks[0]:
                code = code + chunks[0]
                yield lambda: exec(code)
            else:

                def run():
                    try:
                        exec(code + chunk[0])
                    except:
                        return None
                    raise Exception("Should have failed")

                # yield run


for code_chunk in code_chunks():
    code_chunk()