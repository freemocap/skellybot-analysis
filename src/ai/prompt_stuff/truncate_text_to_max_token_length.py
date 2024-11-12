import tiktoken


def truncate_string_to_max_tokens(input_string: str,
                                  llm_model: str,
                                  max_tokens: int) -> str:
    # Initialize the tokenizer
    tokenizer = tiktoken.encoding_for_model(llm_model)
    # Tokenize the input string
    tokens = tokenizer.encode(input_string)

    # Truncate the list of tokens
    truncated_tokens = tokens[:max_tokens]

    # Decode the tokens back to a string
    truncated_string = tokenizer.decode(truncated_tokens)

    return truncated_string


if __name__ == "__main__":
    print( truncate_string_to_max_tokens(
        input_string="Wow, this is a long sentence that will be truncated to the max token length of 4.",
        llm_model="gpt-4o-mini",
        max_tokens=4))
