def parse_test_questions(text):
    questions = []
    errors = []
    number = 0
    
    current_q = {}
    lines = text.split("\n")

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        if clean_line[0].isdigit() and ". " in clean_line:
            number += 1
            current_q = {
                'text': clean_line.split(". ", 1)[1].strip(),
                'option_a': '',
                'option_b': '',
                'option_c': '',
                'option_d': '',
                'correct_option': ''
            }

        elif clean_line.startswith("A)"):
            current_q['option_a'] = clean_line[2:].strip()
        elif clean_line.startswith("B)"):
            current_q['option_b'] = clean_line[2:].strip()
        elif clean_line.startswith("C)"):
            current_q['option_c'] = clean_line[2:].strip()
        elif clean_line.startswith("D)"):
            current_q['option_d'] = clean_line[2:].strip()

        elif clean_line.startswith("Cavab:"):
            current_q['correct_option'] = clean_line.split(":")[1].strip().upper()

            if not all([current_q['option_a'], current_q['option_b'], current_q['option_c'], current_q['option_d']]):
                errors.append(f"Sual {number}: bəzi variantı çatışmır")
            else:
                questions.append(current_q)

            current_q = {}

    return questions, errors