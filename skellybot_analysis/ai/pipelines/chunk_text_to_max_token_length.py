from typing import List

import tiktoken


def chunk_string_by_max_tokens(input_string: str,
                               llm_model: str,
                               max_tokens: int,
                               overlap_ratio: float = 0.1) -> List[str]:
    # Initialize the tokenizer
    tokenizer = tiktoken.encoding_for_model(llm_model)
    # Tokenize the input string
    tokens = tokenizer.encode(input_string)
    # Chunk the original string by the max token length, with an overlap ratio of 0.1 of the max token length
    chunked_strings = []
    if overlap_ratio < 0 or overlap_ratio >= 1:
        raise ValueError("Overlap ratio must be in the range [0, 1).")

    overlap_tokens = int(max_tokens * overlap_ratio)
    if overlap_tokens == 0 and overlap_ratio != 0:
        overlap_tokens = 1

    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk = tokens[start:end]
        chunked_strings.append(tokenizer.decode(chunk))
        start += max_tokens - overlap_tokens
    return chunked_strings


if __name__ == "__main__":
    print(chunk_string_by_max_tokens(
        input_string="Wow, this is a long sentence that will be truncated to the max token length of 4.",
        llm_model="gpt-4o-mini",
        max_tokens=4,
        overlap_ratio=0.1
    ))