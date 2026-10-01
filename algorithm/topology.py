ROUTERS = ["r1", "r2", "r3", "r4", "r5"]


LINKS = [
    {
        "routers": ("r1", "r2"),
        "network": "10.0.12.0/30",
        "r1": {
            "ip": "10.0.12.1",
            "interface": "r1-r2",
        },
        "r2": {
            "ip": "10.0.12.2",
            "interface": "r2-r1",
        },
    },

    {
        "routers": ("r1", "r3"),
        "network": "10.0.13.0/30",
        "r1": {
            "ip": "10.0.13.1",
            "interface": "r1-r3",
        },
        "r3": {
            "ip": "10.0.13.2",
            "interface": "r3-r1",
        },
    },

    {
        "routers": ("r1", "r4"),
        "network": "10.0.14.0/30",
        "r1": {
            "ip": "10.0.14.1",
            "interface": "r1-r4",
        },
        "r4": {
            "ip": "10.0.14.2",
            "interface": "r4-r1",
        },
    },

    {
        "routers": ("r2", "r4"),
        "network": "10.0.24.0/30",
        "r2": {
            "ip": "10.0.24.1",
            "interface": "r2-r4",
        },
        "r4": {
            "ip": "10.0.24.2",
            "interface": "r4-r2",
        },
    },

    {
        "routers": ("r3", "r4"),
        "network": "10.0.34.0/30",
        "r3": {
            "ip": "10.0.34.1",
            "interface": "r3-r4",
        },
        "r4": {
            "ip": "10.0.34.2",
            "interface": "r4-r3",
        },
    },

    {
        "routers": ("r3", "r5"),
        "network": "10.0.35.0/30",
        "r3": {
            "ip": "10.0.35.1",
            "interface": "r3-r5",
        },
        "r5": {
            "ip": "10.0.35.2",
            "interface": "r5-r3",
        },
    },

    {
        "routers": ("r4", "r5"),
        "network": "10.0.45.0/30",
        "r4": {
            "ip": "10.0.45.1",
            "interface": "r4-r5",
        },
        "r5": {
            "ip": "10.0.45.2",
            "interface": "r5-r4",
        },
    },
]