class Dialogue:
    """
    Dialogue class to manage the dialogues
    """
    def __init__(self, player: Player, screen: Screen) -> None:
        self.player: Player = player
        self.screen: Screen = screen

        self.number: int | None = None
        self.id: int | None = None

        self.active: bool = False

        self.speakers: list[str] = []
        self.texts: list[str] = []

        self.dialogue_screen: DialogueScreen | None = None
        self.dialogue_data: DialogueData | None = None

    def load_data(self, number: int, id: int) -> None:
        self.player.can_move = False
        self.number = number
        self.id = id

        self.dialogue_data = DialogueData(number, id)
        self.active = True

        self.dialogue_screen = DialogueScreen(self.screen, dialogue_data=self.dialogue_data, speakers=self.speakers)

    def update(self) -> None:
        if self.dialogue_screen:
            self.dialogue_screen.update()

    def action(self) -> None:
        if self.dialogue_screen and self.dialogue_screen.finished:
            self.active = False
            self.player.can_move = True


def format_text(text: str, line_length: int = 100, max_lines: int = 10) -> str:
    words = text.split()
    formatted_line = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= line_length:
            current_line += (word + " ")
        else:
            formatted_line.append(current_line.strip())
            current_line = word + " "
            if len(formatted_line) >= max_lines - 1:
                break

    if len(formatted_line) < max_lines:
        formatted_line.append(current_line.strip())
    if len(formatted_line) > max_lines:
        formatted_line = formatted_line[:max_lines]

    return "\n".join(formatted_line)


class DialogueData:
    """
    Dialogue data class to manage the
    """
    def __init__(self, number: int, id: int) -> None:
        self.speaker_name: str = ""
        self.speaker_image: list[str] = []
        self.text: str = ""

        self.load_data(number, id)

    def load_data(self, number: int, id: int):
        file_path = f"../../assets/dialogues/{number}.csv"
        df = pd.read_csv(file_path)
        i = id
        column_name = "fr"
        if i in df.index and column_name in df.columns:
            value = df.loc[i, column_name]
        else:
            value = "error"
            print(f"line {i} or column {column_name} not found")
        self.extract_data(value)

    def extract_data(self, string: str):
        pattern = r':\[name=(.*?);face=(.*?)\]:(.*)'
        match = re.match(pattern, string)
        if match:
            self.speaker_name = match.group(1).strip()
            self.speaker_image = match.group(2).strip().split(',')
            self.text = format_text(match.group(3).strip())
        else:
            self.text = format_text(string)

    def __str__(self) -> str:
        return (f"Speaker name: {self.speaker_name},\n"
                f"Speaker image: {self.speaker_image},\n"
                f"Text: {self.text}")
