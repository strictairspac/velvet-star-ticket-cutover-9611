FIXTURES = [
    {
        "code": "SET-1124-NORTH",
        "title": "北间冬展工票转版",
        "description": "核验同工作间中大小写和重音不同的旧票号；西间相同票号单独保留。",
        "payload": {
            "tickets": [
                {"id": "N001", "workshop": "北间", "code": "ÉCLAT-27", "serial": 1},
                {"id": "N002", "workshop": "北间", "code": "eclat-27", "serial": 2},
                {"id": "N003", "workshop": "北间", "code": "OPAL-4", "serial": 3},
                {"id": "N004", "workshop": "北间", "code": "opal-4", "serial": 4},
                {"id": "N005", "workshop": "北间", "code": "R-N002", "serial": 5},
                {"id": "W001", "workshop": "西间", "code": "eclat-27", "serial": 6},
                {"id": "W002", "workshop": "西间", "code": "AMBER-11", "serial": 7},
            ],
        },
    },
    {
        "code": "SET-1124-CLEAN",
        "title": "分间重名对照卷",
        "description": "两工作间可以使用同一票号，转版不消耗改号预算。",
        "payload": {
            "tickets": [
                {"id": "E001", "workshop": "东间", "code": "TURQUOISE-9", "serial": 1},
                {"id": "W001", "workshop": "西间", "code": "turquoise-9", "serial": 2},
                {"id": "E002", "workshop": "东间", "code": "TURQUOISE-9 ", "serial": 3},
            ],
        },
    },
]
