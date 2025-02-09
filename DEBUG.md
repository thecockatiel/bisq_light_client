# Debug

## `sendproto` cli command

In bisq, all messages are encapsulated by a `NetworkEnvelope` protobuf message, which can be found [here](https://github.com/thecockatiel/bisq_light_client/blob/e9eab8844ed53ce960049a157b6ecf691e843bdf/proto/pb.proto#L23)

this command sends a custom crafted network envelope to the specified node address

It accepts two parameters:

- `--node-address`: full address of target node in the format of `hostname:port`
- `--proto`: path to the file containing the network envelope definition to send to the `--node-address` specified

### proto json file format

To create a custom network envelope, you need to create a json file in the following format. the **root** must be a json object and must **NOT** contain more than **two** keys:

```jsonc
{
  "message_version": 10,
  "field_name_from_network_envelope": { 
    "constructor_param_1": 1234,
    "constructor_param_2": "foo",
    "another_proto_field_type": {
      "constructor_param": "etc"
    },
    "repeated_field_A": [
      {
        "constructor_param_of_a": "bar"
      },
      // ...
    ]
    // ...
  }
}
```

`message_version` is calculated [here](https://github.com/thecockatiel/bisq_light_client/blob/e9eab8844ed53ce960049a157b6ecf691e843bdf/bisq/common/version.py#L98). for bisq protocol on BTC mainnet, It's currently equal to `10`.

here is an example for `GetPeersRequest`:

```json
{
  "message_version": 10,
  "get_peers_request": {
    "sender_node_address": {
      "host_name": "aio.io",
      "port": 1234
    },
    "nonce": 10,
    "supported_capabilities": [1,2],
    "reported_peers": [
      {
        "node_address": {
          "host_name": "aio.io",
          "port": 1234
        },
        "date": 1234,
        "supported_capabilities": [1,2]
      }
    ]
  }
}
```

The json file also supports a special syntax for passing bytes and hex if you need,
for example if you need bytes of a text or bytes of a hex string to be passed to constructor of a defined protobuf message, you can use:

```json
{
  "message_version": 10,
  "some_field": {
    "text_bytes": "b'my_text_to_be_encoded'",
    "hex_bytes": "bh'01010101'"
  }
}
```
