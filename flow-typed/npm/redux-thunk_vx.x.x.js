// flow-typed signature: c23c95a12acfb8035253190639fc973f
// flow-typed version: <<STUB>>/redux-thunk_v^2.3.0/flow_v0.93.0

declare module 'redux-thunk' {
  import type { DispatchAPI } from 'redux';

  declare type Action = { +type: string };
  declare type GetState = () => any;
  declare type PromiseAction = Promise<Action>;
  declare export type Dispatch = (
    action: Action | ThunkAction | PromiseAction | Array<Action>,
  ) => DispatchAPI<Action | ThunkAction>;
  declare export type ThunkAction = (
    dispatch: Dispatch,
    getState: GetState,
    opts: any,
  ) => any;

  declare export default function thunk(): any;
}
