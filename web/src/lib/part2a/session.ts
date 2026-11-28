export type Session={accessToken:string;tenantId:string;legalEntityId?:string;userId:string;permissions:string[]};
const KEY="flowforge.session";
export const sessionStore={get():Session|null{if(typeof window==="undefined")return null;const raw=sessionStorage.getItem(KEY);return raw?JSON.parse(raw):null},set(v:Session){sessionStorage.setItem(KEY,JSON.stringify(v))},clear(){sessionStorage.removeItem(KEY)}};
