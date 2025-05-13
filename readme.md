# Redis Core

A lightweight, Python-based implementation of a Redis-like in-memory key-value store server. This project demonstrates the core concepts of Redis by implementing a simplified version with basic functionality.

## Features

- In-memory key-value storage
- RESP (Redis Serialization Protocol) implementation
- Support for basic Redis commands:
  - GET: Retrieve a value by key
  - SET: Store a key-value pair
  - DELETE: Remove a key-value pair
  - FLUSH: Clear all stored data
  - MGET: Retrieve multiple values by keys
  - MSET: Store multiple key-value pairs
- Concurrent client handling using Gevent
- Simple client library for interacting with the server

## Architecture

The implementation consists of three main components:

1. **ProtocolHandler**: Handles the RESP protocol implementation
   - Supports various data types (strings, integers, arrays, bulk strings)
   - Handles serialization and deserialization of data

2. **Server**: The main server implementation
   - Manages client connections using Gevent
   - Implements command handling and execution
   - Maintains the in-memory key-value store

3. **Client**: A simple client library
   - Provides a convenient interface for interacting with the server
   - Handles connection management and protocol communication

## Requirements

- Python 3.x
- Gevent

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd redis-core
```

2. Install dependencies:
```bash
pip install gevent
```

## Usage

### Starting the Server

```python
from redis_core import server

# Start the server on default host (127.0.0.1) and port (31337)
server().run()
```

### Using the Client

```python
from redis_core import client

# Create a client instance
redis_client = client()

# Basic operations
redis_client.set('key', 'value')
value = redis_client.get('key')
redis_client.delete('key')

# Multiple operations
redis_client.mset('key1', 'value1', 'key2', 'value2')
values = redis_client.mget('key1', 'key2')

# Clear all data
redis_client.flush()
```

## Protocol Details

The server implements the RESP (Redis Serialization Protocol) with support for:
- Simple Strings: `+OK\r\n`
- Errors: `-Error message\r\n`
- Integers: `:1000\r\n`
- Bulk Strings: `$6\r\nfoobar\r\n`
- Arrays: `*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n`

## Limitations

This is a simplified implementation and does not include:
- Persistence
- Advanced data structures (lists, sets, etc.)
- Authentication
- Replication
- Pub/Sub functionality

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.