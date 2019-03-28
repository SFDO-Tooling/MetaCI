// flow-typed signature: 960bce3f9537642de3e3ec11f2cf81b2
// flow-typed version: <<STUB>>/sockette_v^2.0.0/flow_v0.93.0

declare module 'sockette' {
  declare export default class Sockette {
    constructor(url: string, opts?: { [string]: mixed }): Sockette;

    send: (data: mixed) => void;
    close: (code?: number, reason?: string) => void;
    json: (obj: { [mixed]: any }) => void;
    reconnect: () => void;
    open: () => void;
  }
}
