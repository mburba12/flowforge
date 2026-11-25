export type Session={accessToken:string;tenantId:string;userId:string;legalEntityId?:string;permissions:ReadonlySet<string>;entitlements:ReadonlySet<string>};
export type ApiError={status:number;code:string;message:string;requestId?:string};
