PORTS = {
    'Bailey': 17800,
    'Bona': 17801,
    'Campbell': 17802,
    'Clark': 17803,
    'Jaquez': 17804,
}

# Clark talks with Jaquez and Bona.
# Campbell talks with everyone else but Clark.
# Bona talks with Bailey.
NEIGHBORS = {
    'Bailey': ['Campbell', 'Bona'],
    'Bona': ['Clark', 'Bailey'],
    'Campbell': ['Bailey', 'Jaquez'],
    'Clark': ['Jaquez', 'Bona'],
    'Jaquez': ['Clark', 'Campbell'],
}