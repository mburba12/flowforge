import {PublicClientApplication,type Configuration} from "@azure/msal-browser";
const config:Configuration={auth:{clientId:process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID??"",authority:`https://login.microsoftonline.com/${process.env.NEXT_PUBLIC_ENTRA_TENANT_ID??"common"}`,redirectUri:process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI},cache:{cacheLocation:"sessionStorage"}};
export const msal=new PublicClientApplication(config);
export const loginScopes=["openid","profile","email","api://flowforge/access"];
