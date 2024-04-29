// import {
//   MessageType,
//   ListIntegrationReposResponse,
//   Repo,
//   ListAllAccessibleGroupsResponse,
//   ListGroupedIssuesResponse,
//   GetDetailsResponse,
//   NavigateMessage,
//   GetDetailsResponseMessage,
//   NotLoggedInMessage,
// } from "./types";

// async function listAllAccessibleGroups(
//   authToken: string,
// ): Promise<ListAllAccessibleGroupsResponse> {
//   const res = await fetch(
//     "https://app.aikido.dev/api/user/listAllAccessibleGroups",
//     {
//       method: "GET",
//       headers: {
//         Cookie: authToken,
//       },
//     },
//   )

//   if (!res.ok) {
//     console.error("failed to fetch", res);
//     throw new Error("Failed to fetch");
//   }
//   if (res.headers.get("content-type") !== "application/json") {
//     console.error("invalid content-type", res);
//     throw new Error("Invalid content-type");
//   }

//   const data: ListAllAccessibleGroupsResponse = await res.json();
//   return data;
// }
// async function listIntegrationRepos(
//   authToken: string,
//   groupId: number,
// ): Promise<ListIntegrationReposResponse> {
//   const res = await fetch(
//     "https://app.aikido.dev/api/scm_integrations/repos/listIntegrationRepos",
//     {
//       method: "GET",
//       headers: {
//         Cookie: authToken,
//         "X-Group-ID": groupId.toString(),
//       },
//     }
//   )
//   if (!res.ok) {
//     console.error("failed to fetch", res);
//     throw new Error("Failed to fetch");
//   }
//   if (res.headers.get("content-type") !== "application/json") {
//     console.error("invalid content-type", res);
//     throw new Error("Invalid content-type");
//   }

//   const data: ListIntegrationReposResponse = await res.json();
//   return data;
// }
// async function listGroupedIssues(
//   authToken: string,
//   repoId: number,
//   groupId: number,
// ): Promise<ListGroupedIssuesResponse> {
//   const res = await fetch(
//     `https://app.aikido.dev/api/issues/listGroupedIssues?filter_repo_id=${repoId}&exclude_containers=false&dont_pass_team_context=false`,
//     {
//       method: "GET",
//       headers: {
//         Cookie: authToken,
//         "X-Group-ID": groupId.toString(),
//       },
//     }
//   )

//   if (!res.ok) {
//     console.error("failed to fetch", res);
//     throw new Error("Failed to fetch");
//   }
//   if (res.headers.get("content-type") !== "application/json") {
//     console.error("invalid content-type", res);
//     throw new Error("Invalid content-type");
//   }

//   const data: ListGroupedIssuesResponse = await res.json();
//   return data;
// }

// async function handleGetDetails(
//   authToken: string,
//   repoName: string,
//   repoOwner: string,
// ): Promise<GetDetailsResponse | undefined> {
//   try {
//     // Get all accessible groups
//     const groups = await listAllAccessibleGroups(authToken);
//     // Get all repos for each group
//     const allRepos: Repo[] = [];
//     for (const group of groups.accessible_groups) {
//       const responseRepos = await listIntegrationRepos(authToken, group.id)
//       const repos = responseRepos.integration_repos.map((r) => ({ ...r, group_id: group.id }))
//       allRepos.push(...repos);
//     }

//     // find the correct repo
//     // first filter only by name
//     const filteredRepos = allRepos.filter((r) => r.scm_repo_name === repoName);
//     if (filteredRepos.length === 0) {
//       console.log("no repos", repoName, repoOwner);
//       return undefined;
//     }
//     // if there are multiple repos with the same name, filter by owner
//     let repo = filteredRepos.find((r) => r.scm_repo_owner_name === repoOwner);
//     // if no repo was found, just use the first one, the repo
//     // probably changed ownership since it was added to Aikido
//     if (!repo) repo = filteredRepos[0];

//     const issues = await listGroupedIssues(authToken, repo.id, repo.group_id);

//     return { repoName, repoOwner, repo, issues: issues.grouped_issues };
//   } catch (err) {
//     console.error(err);
//     return undefined;
//   }
// }

// chrome.runtime.onMessage.addListener(
//   function(request, sender, sendResponse): boolean {
//     if (!sender.tab?.id) {
//       console.error("No tab :/");
//       return false;
//     }

//     // Handle right message + check if sent by content script
//     if (request.type === MessageType.GET_DETAILS) {
//       chrome.cookies.get({ url: 'https://app.aikido.dev', name: 'auth' },
//       function (cookie) {
//         if (cookie) {
//           console.log(new Date().toLocaleTimeString(), cookie.value);
//           handleGetDetails(
//             cookie.value,
//             request.payload.repoName,
//             request.payload.repoOwner,
//           ).then((data: GetDetailsResponse | undefined) => {
//             chrome.tabs.sendMessage<GetDetailsResponseMessage>(
//               sender.tab!.id!,
//               {
//                 type: MessageType.GET_DETAILS_RESPONSE,
//                 payload: data,
//               }
//             )
//           });
//         } else {
//           console.log('No cookie found, login first at https://app.aikido.dev/');
//           // Wait a bit before sending the message, so the content script
//           // has time to load correctly.
//           // Also prevents a flickering loading SVG.
//           setTimeout(() => {
//             chrome.tabs.sendMessage<NotLoggedInMessage>(
//               sender.tab!.id!,
//               { type: MessageType.NOT_LOGGED_IN }
//             )
//           }, 500);
//         }
//       });
//     }
//     // important for async response
//     return true;
//   }
// );

// // We use this timer to debounce the navigation events.
// // Github triggers 3 navigation events when navigating to another page.
// // No clue why.
// let bouncyTimer: NodeJS.Timeout | undefined;

// // We use this listener to listen for navigate events that don't trigger a reload
// chrome.webNavigation.onHistoryStateUpdated.addListener((navDetails) => {

//   // Parse the repo name from the URL
//   // Only tun on Github repo pages
//   const matcher = navDetails.url.match(/^https:\/\/github\.com\/([^\/\?\#]+)\/([^\/\?\#]+)$/);
//   if (!matcher) return;
//   const repoName = matcher[2];
//   const repoOwner = matcher[1];
//   if (!repoName || !repoOwner) {
//     console.log("Failed to parse repo name from URL", navDetails.url);
//     return;
//   }

//   if (bouncyTimer) clearTimeout(bouncyTimer);
//   bouncyTimer = setTimeout(() => {
//     chrome.tabs.sendMessage<NavigateMessage>(
//       navDetails.tabId,
//       {
//         type: MessageType.NAVIGATE,
//         payload: {
//           repoName,
//           repoOwner,
//         },
//       }
//     );
//   }, 500);
// });
