# Notes

## Multi User Quirks

Currently to implement multi user without changing bisq too much, we decided to do multi user implementation as follows:

Each user context will have it's own `GlobalContainer`

Each GRPC request will get the currently active user context and pass it around to know in what context it is getting executed

Each user context will have it's own `PersistenceOrchestrator`, which is simply anything static inside persistence manager moved inside to be used as per user instead of being global

Logging has been separated into 3 parts: `Base`, `Shared`, `User`

All logs are written to the aggregated logger, placed in `logs` directory relative to the root of app data directory

Logs written to `Base` will only be logged to aggregated logger

Logs written to `Shared` will be logged to aggregated logs and to `User` Logs (This only happens if the user instance is started)

Logs written to `User` logs will only be written to the respective user logs, living in each user's `logs` directory

To switch to each user currently we shutdown each user before starting up the next one
