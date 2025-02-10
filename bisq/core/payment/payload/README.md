
# Notes about account payloads

Since account payloads are serialized to json and sent with contracts, they are sensitive.
Since java bisq uses Gson and implicitly relies on `null` values to be removed from the final json, and because account payloads have a mix of empty strings and `null` values, constructor parameters and values passed around are also sensitive.
This makes the contract signature very brittle and sensitive.
Please keep these in mind when modifying these files.
