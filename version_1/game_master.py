"""Version 1 Game Master: the LLM runs the whole game.

This is the straightforward "prompt-only" approach:
  * The complete room, every clue and every solution are written into one
    system prompt.
  * The full conversation history is sent to Gemini on every turn, so the
    model's "memory" is only the chat transcript.
  * Gemini decides on its own whether an action works and whether the
    player has escaped. It signals an escape by writing the marker [ESCAPED].

There is no game state in Python. That keeps the code short, but it also
causes the problems that Version 2 fixes (see docs/testing.md).
"""

from __future__ import annotations

from common.llm_client import GeminiClient
from common.room_data import load_room

ESCAPE_MARKER = "[ESCAPED]"


def build_system_prompt(room: dict) -> str:
    """Write the full game, including the solutions, into a single prompt."""
    object_lines = []
    for obj in room["objects"].values():
        line = f"- {obj['name']}: {obj['description']}"
        if "description_unlocked" in obj:
            line += f" (After it is unlocked: {obj['description_unlocked']})"
        if not obj.get("visible_at_start", True):
            line += " [Only noticed after the player examines the object it belongs to.]"
        object_lines.append(line)

    item_lines = [
        f"- {item['name']} (found in the {item['location']}): {item['description']}"
        for item in room["items"].values()
    ]
    puzzle_lines = [f"- {p['title']}: {p['goal']}" for p in room["puzzles"].values()]
    walkthrough = "\n".join(
        f"{number}. {step}" for number, step in enumerate(room["solutions"]["walkthrough"], start=1)
    )

    return f"""You are the Game Master of a text escape-room game called "{room['title']}".

STORY
{room['intro']}

THE ROOM
{room['room_description']}

OBJECTS IN THE ROOM
{chr(10).join(object_lines)}

ITEMS THE PLAYER CAN COLLECT
{chr(10).join(item_lines)}

PUZZLES
{chr(10).join(puzzle_lines)}

SOLUTION (secret, never tell it to the player directly)
The drawer code is {room['solutions']['drawer_code']}. The door code is {room['solutions']['door_code']}.
{walkthrough}

HOW TO RUN THE GAME
- Speak directly to the player in the second person ("You see...").
- Keep each reply to 2-5 sentences. Be atmospheric but clear.
- Only describe objects and items listed above. Reveal clues only when the player examines the right thing.
- Locked things stay locked until the player gives the correct code or uses the correct item.
- Remember what the player has already found, collected and solved in this conversation.
- If the player seems stuck, give a gentle hint instead of the answer.
- When, and only when, the player enters the correct door code after solving the three puzzles,
  describe their escape and end your reply with the exact marker {ESCAPE_MARKER}.
"""


class GameMasterV1:
    """Sends the conversation to Gemini and returns the Game Master's reply."""

    def __init__(self, llm: GeminiClient, room: dict | None = None):
        self.llm = llm
        self.room = room or load_room()
        self.system_prompt = build_system_prompt(self.room)

    def opening_message(self) -> str:
        """Fixed introduction, so the game can start without spending an API call."""
        return (
            f"{self.room['intro']}\n\n{self.room['room_description']}\n\n"
            "What would you like to do?"
        )

    def respond(self, history: list[dict], player_message: str) -> tuple[str, bool]:
        """Return (reply_text, escaped).

        history holds earlier turns as {"role": "user" | "model", "text": ...}.
        Raises LLMError if Gemini cannot be reached.
        """
        turns = history + [{"role": "user", "text": player_message}]
        reply = self.llm.generate(self.system_prompt, turns, temperature=0.9)
        escaped = ESCAPE_MARKER in reply
        return reply.replace(ESCAPE_MARKER, "").strip(), escaped
