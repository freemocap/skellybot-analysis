import json
from datetime import datetime
from typing import Any


class JSONDateTimeEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


if __name__ == "__main__":
    # Example data that includes an emoji
    example_data = {
        "message": "Hello, world! 🌍",
        "timestamp": datetime.now()
    }

    with open('example_output.json', 'w', encoding='utf-8') as file:
        json.dump(example_data, file, indent=2, cls=JSONDateTimeEncoder, ensure_ascii=False)