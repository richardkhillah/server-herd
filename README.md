# Server Herd
A fault-tolerant, scalable server network built with asynchronous Python. Servers communicate bidirectionally to synchronize client location data, ensuring continuous availability even when individual servers go down.

## Why I Built This
This project explored distributed systems design — specifically how to maintain a consistent client experience across a network of interdependent servers during partial failure. Built as part of my CS coursework at UCLA.

## Stack
Python, asyncio, Google Places API

## Running Locally
```bash
git clone https://github.com/richardkhillah/server-herd
cd server-herd
pip install -r requirements.txt
python server.py <server_name>
```

Run multiple server instances in separate terminals to simulate the full herd. See `report.pdf` for full design documentation and architecture notes.
