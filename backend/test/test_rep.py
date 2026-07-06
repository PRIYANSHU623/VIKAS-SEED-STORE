from app.services.response_generator import generate_response

tool_output = {
    "tool": "product",
    "success": True,
    "data": {
        "count": 2,
        "products": [
            {
                "name": "Arize 6444",
                "price": 2050,
                "season": "kharif",
                "stock": 15
            },
            {
                "name": "Laxmi",
                "price": 120,
                "season": "kharif",
                "stock": 40
            }
        ]
    }
}

print(
    generate_response(
        "Recommend paddy seeds",
        tool_output
    )
)