"""Interface names: the device output uses one style, people type another."""

PREFIXES = {
    "gi": "Gi", "gigabitethernet": "Gi",
    "te": "Te", "tengigabitethernet": "Te",
    "fa": "Fa", "fastethernet": "Fa",
    "po": "Po", "port-channel": "Po",
    "lo": "Lo", "loopback": "Lo",
}


def normalise_interface_name(name):
    """gi0/1 -> Gi0/1, GigabitEthernet0/1 -> Gi0/1"""
    name = str(name).strip()
    letters = ""
    for character in name:
        if character.isalpha() or character == "-":
            letters += character
        else:
            break
    rest = name[len(letters):]
    short = PREFIXES.get(letters.lower())
    return short + rest if short else name
