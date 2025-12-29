

lesson_data  = [
    {
    "id": 1,
    "title": "Introduction to Python",
    "content": "This is the first lesson.",
    "order": 1,
    "content_url": "http://example.com/lesson1",
    "duration_minutes": 10},
    {
    "id": 2,
    "title": "Advanced Python",
    "content": "This is the second lesson.",
    "order": 2,
    "content_url": "http://example.com/lesson2",
    "duration_minutes": 15}

]


existing_lessons = {lesson["id"]: lesson for lesson in lesson_data}

print(existing_lessons)