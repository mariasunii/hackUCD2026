
import json
from ai_service import generate_plan

brief = """
Build a library reservation website.

Requirements:
- Users must register and log in.
- Users must search for books.
- Users must reserve books.
- Users must cancel reservations.
- Submit a final project report.
"""

rubric = """
Authentication: 20%
Book search: 20%
Reservations: 30%
Testing: 10%
Documentation: 20%
"""

members = ["Sarah", "John", "Emma", "Alex"]

result = generate_plan(
    brief=brief,
    rubric=rubric,
    comments="Complete the project in two weeks.",
    members=members
)

print(json.dumps(result, indent=2))
